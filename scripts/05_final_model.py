"""
Step 5 - Final compact questionnaire model (XGBoost), evaluated with the step-3 protocol.

Configs (same 5x5 folds):
  A. 12 questions incl. intermediate group (-> US transcript profile, [ASSUMPTION] conversion)
  B. 11 questions, WITHOUT the intermediate-group question (no unverifiable conversion)
  REF. all 179 HSLS questionnaire columns (step 4 reference)
Each config reported for: all students, DECIDED students (named a job), UNDECIDED ("don't know" job).
Then trains final models A and B on all students -> models/, plus models/questions.json for the front end,
and runs example students through the SAME encoding the backend will use (src/questionnaire.py).

Usage: python scripts/05_final_model.py           (~10 min)
       python scripts/05_final_model.py --quick
Output: reports/05_final_eval.csv/.md, models/edupath_xgb_{A,B}.json, models/edupath_spec_{A,B}.json,
        models/questions.json
"""
import json, sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import f1_score
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import questionnaire as Q

DER, REP, MOD = ROOT / "datasets" / "derived", ROOT / "reports", ROOT / "models"
MOD.mkdir(exist_ok=True)
QUICK = "--quick" in sys.argv
FOLDS, REPEATS = (3, 1) if QUICK else (5, 5)
RNG = 42


def xgb():  # identical settings to steps 3b/4
    return XGBClassifier(n_estimators=400, learning_rate=0.05, max_depth=4, subsample=0.8,
                         colsample_bytree=0.5, tree_method="hist", eval_metric="mlogloss",
                         random_state=RNG, n_jobs=-1)


def pct(a):
    a = np.asarray(a)
    return f"{a.mean():.3f} [{np.percentile(a, 2.5):.3f}-{np.percentile(a, 97.5):.3f}]"


def scores(P, classes, y):
    top = np.asarray(classes)[np.argsort(-P, axis=1)[:, :3]]
    hit = top == y[:, None]
    return dict(top1=hit[:, 0].mean(), top3=hit.any(axis=1).mean(),
                macroF1=f1_score(y, top[:, 0], average="macro"),
                NDCG3=(hit / np.log2(np.arange(2, 5))).sum(axis=1).mean())


def baseline(y_train, y_test):
    """Largest class / 3 biggest classes learned from the TRAINING fold, applied to the test subset."""
    cnt = np.bincount(y_train, minlength=7)
    o = np.argsort(-cnt)
    return dict(top1=(y_test == o[0]).mean(), top3=np.isin(y_test, o[:3]).mean())


def main():
    h = pd.read_csv(DER / "hsls_prechoice.csv.gz", low_memory=False)
    fields = sorted(h.field.unique())
    y = h.field.map({f: i for i, f in enumerate(fields)}).values
    undecided = (h.X2STU30OCC2 == 98).values
    decided = (h.X2STU30OCC2 > 0).values & ~undecided
    print(f"n={len(y)}  decided={decided.sum()}  undecided(don't know job)={undecided.sum()}  "
          f"CV={FOLDS}x{REPEATS}")

    specs = {"A": Q.make_spec(Q.model_columns(True)), "B": Q.make_spec(Q.model_columns(False))}
    qcols = pd.read_csv(REP / "03_hsls_questionnaire_cols.csv").column.tolist()
    ref = h[qcols].replace(Q.NCES_MISSING, np.nan)
    nom = [c for c in qcols if c.endswith(("FAVSUBJ", "LEASTSUBJ", "STU30OCC2"))]
    X = {"A": Q.design_matrix(h, specs["A"]), "B": Q.design_matrix(h, specs["B"]),
         "REF": pd.get_dummies(ref, columns=nom).astype(float).values}
    names = {"A": "A: 12 questions (with intermediate group)", "B": "B: 11 questions (no group question)",
             "REF": f"REF: all {len(qcols)} HSLS questionnaire columns"}

    cv = list(RepeatedStratifiedKFold(n_splits=FOLDS, n_repeats=REPEATS, random_state=RNG).split(X["B"], y))
    subsets = {"all": np.ones(len(y), bool), "decided": decided, "undecided": undecided}
    res = {(k, s): {m: [] for m in ("top1", "top3", "macroF1", "NDCG3")} for k in X for s in subsets}
    base = {s: {"top1": [], "top3": []} for s in subsets}
    for i, (tr, te) in enumerate(cv):
        for s, mask in subsets.items():
            for m, v in baseline(y[tr], y[te][mask[te]]).items():
                base[s][m].append(v)
        for k, Xk in X.items():
            mdl = xgb().fit(Xk[tr], y[tr])
            P = mdl.predict_proba(Xk[te])
            for s, mask in subsets.items():
                sel = mask[te]
                for m, v in scores(P[sel], mdl.classes_, y[te][sel]).items():
                    res[(k, s)][m].append(v)
        print(f"  fold {i+1}/{len(cv)}")

    rows = []
    for s in subsets:
        rows.append(dict(students=s, n=int(subsets[s].sum()), model="Baseline (largest / 3 biggest)",
                         features="", top1=pct(base[s]["top1"]), top3=pct(base[s]["top3"]), macroF1="", NDCG3=""))
        for k in X:
            rows.append(dict(students=s, n=int(subsets[s].sum()), model=names[k], features=X[k].shape[1],
                             **{m: pct(v) for m, v in res[(k, s)].items()}))
    df = pd.DataFrame(rows)
    df.to_csv(REP / "05_final_eval.csv", index=False)
    print("\n" + df.to_string(index=False))

    # ---------- final models on all students ----------
    for k in ("A", "B"):
        mdl = xgb().fit(X[k], y)
        mdl.save_model(MOD / f"edupath_xgb_{k}.json")
        json.dump({**specs[k], "fields": fields, "nces_missing_to_nan": Q.NCES_MISSING,
                   "trained_on": f"HSLS:09 n={len(y)}", "date": str(date.today())},
                  open(MOD / f"edupath_spec_{k}.json", "w"), indent=1)
    json.dump(Q.questions_json(), open(MOD / "questions.json", "w"), indent=1)

    # ---------- example students through the backend encoding path ----------
    examples = {
        "Pre-Med, wants doctor": {"career": "Doctor, dentist, pharmacist, nurse or other health professional",
                                  "career_certain": "Very sure", "career_thought": "A lot",
                                  "education_plan": "Professional degree (MBBS, BDS, Pharm-D, LLB) or PhD",
                                  "fav_subject": "Biology", "least_subject": "Mathematics",
                                  "science_person": "Strongly agree", "math_person": "Disagree",
                                  "science_useful": "Strongly agree", "math_useful": "Disagree",
                                  "math_confident": "Disagree", "inter_group": "FSc Pre-Medical"},
        "ICS, undecided, likes computers": {"career": "I don't know yet",
                                            "education_plan": "Bachelor's degree (BS, BBA, BE, BSc)",
                                            "fav_subject": "Computer Science", "least_subject": "Biology",
                                            "science_person": "Disagree", "math_person": "Agree",
                                            "science_useful": "Disagree", "math_useful": "Agree",
                                            "math_confident": "Agree", "inter_group": "ICS (Computer Science)"},
        "I.Com, wants accountant": {"career": "Accountant, banker or finance professional",
                                    "career_certain": "Fairly sure", "career_thought": "Somewhat",
                                    "education_plan": "Master's degree (MS, MBA, MPhil)",
                                    "fav_subject": "Accounting / Commerce / Business", "least_subject": "Physics",
                                    "science_person": "Strongly disagree", "math_person": "Agree",
                                    "science_useful": "Disagree", "math_useful": "Agree",
                                    "math_confident": "Agree", "inter_group": "I.Com (Commerce)"},
    }
    print("\nExample students (model A, same encoding path as the backend):")
    mdl = XGBClassifier(); mdl.load_model(MOD / "edupath_xgb_A.json")
    for name, ans in examples.items():
        row = pd.DataFrame([Q.answers_to_hsls(ans)])
        p = mdl.predict_proba(Q.design_matrix(row, specs["A"]))[0]
        top = np.argsort(-p)[:3]
        print(f"  {name:32s} -> " + " | ".join(f"{fields[j]} {p[j]:.0%}" for j in top))

    with open(REP / "05_final_eval.md", "w", encoding="utf-8") as fh:
        fh.write(f"# Edu Path - final compact questionnaire ({date.today()})\n\nXGBoost, HSLS:09 n={len(y)}, "
                 f"repeated stratified {FOLDS}-fold x {REPEATS}; baselines learned on each training fold. "
                 "Undecided = answered 'don't know' for job at 30. Questions and Pakistani->HSLS conversions: "
                 "src/questionnaire.py. Model A's intermediate-group conversion is an untested assumption.\n\n")
        fh.write("```\n" + df.to_string(index=False) + "\n```\n")
    print("\nSaved reports/05_final_eval.*, models/edupath_xgb_{A,B}.json, models/edupath_spec_{A,B}.json, models/questions.json")


if __name__ == "__main__":
    main()
