"""
Edu Path - FastAPI backend (field recommendation stage).

Endpoints
  GET  /health          -> status + which model is loaded
  GET  /questions       -> the fixed field questionnaire (from src/questionnaire.py)
  POST /predict-field   -> top-3 fields with probabilities + per-student reasons (XGBoost SHAP contributions)
  GET  /model-info      -> measured accuracy + limitations, for display in the UI and the report

Encoding of answers is done by src/questionnaire.py - the SAME code used to train and evaluate the model
(scripts/05_final_model.py), so the reported accuracy applies to what this API serves.

Run (from project root):  uvicorn backend.main:app --reload
Website:                  http://127.0.0.1:8000        (frontend/ is served by this same app)
API docs:                 http://127.0.0.1:8000/docs
"""
import json, sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import questionnaire as Q  # noqa: E402
import auth  # noqa: E402
import db as DB  # noqa: E402

MODEL = "A"  # A = 12 questions incl. intermediate group (deployed); B = without group question
booster = xgb.Booster()
booster.load_model(ROOT / "models" / f"edupath_xgb_{MODEL}.json")
spec = json.load(open(ROOT / "models" / f"edupath_spec_{MODEL}.json"))
FIELDS = spec["fields"]

# feature -> question id (for turning SHAP contributions into per-question reasons)
COL_TO_Q = {c: q["id"] for q in Q.QUESTIONS for _, m in q["options"] for c in m}
FEAT_TO_Q = [COL_TO_Q[f.split("__")[0]] for f in spec["features"]]
Q_TEXT = {q["id"]: q["text"] for q in Q.QUESTIONS}

# measured in scripts/05_final_model.py (5x5 repeated stratified CV) - see reports/05_final_eval.md
MODEL_INFO = {
    "model": "XGBoost, 12-question Edu Path questionnaire (model A)",
    "training_data": "HSLS:09 (US National Center for Education Statistics), 10,585 real students",
    "accuracy_all_students": {"top1": 0.505, "top3": 0.798, "baseline_top1": 0.252, "baseline_top3": 0.573},
    "accuracy_undecided_students": {"top1": 0.336, "top3": 0.694, "baseline_top1": 0.175, "baseline_top3": 0.546},
    "limitations": [
        "Trained on US students; not yet validated on Pakistani students.",
        "Converting the Pakistani intermediate group to US course credits is an untested assumption.",
        "Biology, Chemistry and Physics map to one 'Science' answer, so the model cannot tell them apart.",
        "Students change field over time (only 77.8% kept the same field after 3 years), so no prediction is certain.",
    ],
}

app = FastAPI(title="Edu Path API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # dev setting
DB.init_db()  # create tables if missing
app.include_router(auth.router)


class FieldRequest(BaseModel):
    answers: dict[str, str] = Field(
        ..., description="question id -> chosen option text, exactly as returned by GET /questions",
        examples=[{"career": "Engineer", "career_certain": "Fairly sure", "inter_group": "FSc Pre-Engineering",
                   "fav_subject": "Physics", "math_person": "Agree"}])


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL, "fields": FIELDS, "n_features": len(spec["features"])}


@app.get("/questions")
def questions():
    return Q.questions_json()


@app.get("/model-info")
def model_info():
    return MODEL_INFO


@app.post("/predict-field")
def predict_field(req: FieldRequest, user=Depends(auth.optional_user), db=Depends(DB.get_db)):
    known = {q["id"] for q in Q.QUESTIONS}
    unknown = sorted(set(req.answers) - known)
    if unknown:
        raise HTTPException(422, f"Unknown question id(s): {unknown}")
    try:
        row = Q.answers_to_hsls(req.answers)
    except ValueError as e:
        raise HTTPException(422, str(e))

    X = Q.design_matrix(pd.DataFrame([row]), spec)
    dm = xgb.DMatrix(X, missing=np.nan)
    proba = booster.predict(dm)[0]                       # (n_fields,)
    contrib = booster.predict(dm, pred_contribs=True)[0]  # (n_fields, n_features + 1 bias), log-odds units

    order = np.argsort(-proba)
    top = []
    for rank, k in enumerate(order[:3], start=1):
        per_q = {}
        for j, qid in enumerate(FEAT_TO_Q):
            per_q[qid] = per_q.get(qid, 0.0) + float(contrib[k, j])
        answered = {qid: v for qid, v in per_q.items() if qid in req.answers}
        reasons = sorted(answered.items(), key=lambda kv: -kv[1])
        top.append({
            "rank": rank, "field": FIELDS[k], "probability": round(float(proba[k]), 3),
            "reasons_for": [{"question": qid, "text": Q_TEXT[qid], "answer": req.answers[qid],
                             "effect": round(v, 3)} for qid, v in reasons if v > 0][:3],
            "reasons_against": [{"question": qid, "text": Q_TEXT[qid], "answer": req.answers[qid],
                                 "effect": round(v, 3)} for qid, v in reversed(reasons) if v < 0][:2],
        })

    skipped = {qid for q in Q.QUESTIONS for qid in [q["id"]]
               if any(req.answers.get(a) == b for a, b in q.get("skip_if", {}).items())}
    missing = [q["id"] for q in Q.QUESTIONS if q["id"] not in req.answers and q["id"] not in skipped]
    out = {
        "top_fields": top,
        "all_fields": {FIELDS[k]: round(float(proba[k]), 3) for k in order},
        "unanswered_questions": missing,
        "note": "Effects are SHAP contributions (log-odds) of each answer to that field's score. "
                "Recommendations are decision support, not a guarantee.",
    }
    if user is not None:  # logged in -> keep the result in the student's history
        auth.save_assessment(db, user, req.answers, out)
        out["saved_to_account"] = True
    return out


# ---------- career stage: hybrid adaptive questions -> careers -> programs ----------
import careers as C  # noqa: E402
import llm  # noqa: E402
import rag  # noqa: E402
import career_extra  # noqa: E402
from career_bank import BANK  # noqa: E402


class CareerStep(BaseModel):
    field: str = Field(..., examples=["CS & IT"])
    answers: dict[str, str] = Field(default_factory=dict, description="career question id -> chosen option label")
    inter_group: str | None = Field(None, description="the student's intermediate group (from the field questionnaire)")
    profile: dict[str, str] = Field(default_factory=dict, description="field-questionnaire answers (question id -> option)")
    free_text: str | None = Field(None, max_length=600, description="optional: the student describes interests in own words")
    marks: float | None = Field(None, ge=0, le=100, description="intermediate percentage (actual or expected)")
    prefs: dict[str, str] = Field(default_factory=dict, description="program profile answers (GET /programs/questions)")


def _with_skills(careers, profile):
    """Attach the skill-gap checklist (with skills pre-ticked from the questionnaire answers) to each career."""
    return [{**c, "skills": career_extra.skill_gap(c["id"], profile)} for c in careers]


@app.get("/skills")
def list_skills():
    """Every career with its core skills (name, tip, questionnaire evidence) - for the Skill Gap Analysis page."""
    out = []
    for f, b in BANK.items():
        for cid, c in b["careers"].items():
            out.append({"id": cid, "title": c["title"], "field": f, "desc": c["desc"],
                        "skills": [{"name": s["name"], "tip": s["tip"], "evidence": s["evidence"]}
                                   for s in career_extra.SKILLS[cid]]})
    return {"careers": out, "note": "Typical skills per career (curated guidance, not verified). Self-assessed."}


@app.get("/fields")
def list_fields():
    """The 7 fields with their careers and programs (for the Explore Fields page)."""
    out = []
    for f, b in BANK.items():
        out.append({"field": f, "careers": [c["title"] for c in b["careers"].values()],
                    "programs": sorted({C.PROGRAMS[p]["name"] for c in b["careers"].values() for p in c["programs"]}),
                    "n_questions": min(C.MAX_QUESTIONS, len(b["questions"]))})
    return out


@app.post("/career/step")
def career_step(req: CareerStep):
    """Returns the next adaptive question (LLM-chosen when enabled, else rules) or, when done, the result.
    Ranking and programs are always computed by the deterministic rules engine."""
    if req.field not in BANK:
        raise HTTPException(422, f"Unknown field {req.field!r}. Valid: {list(BANK)}")
    try:
        C.validate_answers(req.field, req.answers)
    except ValueError as e:
        raise HTTPException(422, str(e))

    ranked = C.score(req.field, req.answers)
    done = C.is_done(req.field, req.answers)
    resp = {"field": req.field, "done": done, "answered": len(req.answers),
            "max_questions": min(C.MAX_QUESTIONS, len(BANK[req.field]["questions"])),
            "careers": [{k: r[k] for k in ("id", "title", "desc", "match", "points")} for r in ranked],
            "llm": llm.status()}
    if not done:
        cands = C.candidates(req.field, req.answers)
        rules_q = cands[0]
        answered = [{"question": q["text"], "answer": req.answers[q["id"]]}
                    for q in BANK[req.field]["questions"] if q["id"] in req.answers]
        pick = llm.choose(req.field, ranked, answered, cands[:4]) if req.answers else None  # first question: rules
        q = next(c for c in cands if c["id"] == pick["id"]) if pick else rules_q
        resp["question"] = {"id": q["id"], "text": pick["text"] if pick else q["text"], "original_text": q["text"],
                            "options": [o["label"] for o in q["options"]], "source": "llm" if pick else "rules"}
    else:
        # career result only - programs are a separate step (POST /programs/recommend after the program profile)
        resp["result"] = {
            "careers": _with_skills(ranked[:3], req.profile),
            "note": "Careers come from your answers to curated questions (rules-based scoring).",
        }
    return resp


@app.post("/programs/recommend")
def programs_recommend(req: CareerStep):
    """Program recommendation (RAG) for a finished career flow - e.g. re-run with the student's own words."""
    if req.field not in BANK:
        raise HTTPException(422, f"Unknown field {req.field!r}")
    try:
        C.validate_answers(req.field, req.answers)
    except ValueError as e:
        raise HTTPException(422, str(e))
    try:
        rag.validate_prefs(req.prefs)
    except ValueError as e:
        raise HTTPException(422, str(e))
    ranked = C.score(req.field, req.answers)
    return {"careers": _with_skills(ranked[:3], req.profile),
            **rag.recommend(req.field, ranked, req.answers, req.inter_group, req.profile, req.free_text, req.marks,
                            req.prefs),
            "note": "Programs are retrieved from our program knowledge base (RAG) and explained by AI when available. "
                    "Entry requirements are typical, not official - check each university."}


@app.get("/programs/questions")
def program_questions():
    """The program-profile questions asked before recommending programs."""
    return rag.PREF_QUESTIONS


# ---------- website ----------
# Serve the HTML/CSS/JS frontend from the same server, so the whole app runs with one command.
# Mounted LAST so the API routes above take priority over static files.
from fastapi.staticfiles import StaticFiles  # noqa: E402

FRONTEND = ROOT / "frontend"
if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
