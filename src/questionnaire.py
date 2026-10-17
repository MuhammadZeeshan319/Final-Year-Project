"""
Edu Path field questionnaire: the FIXED questions the XGBoost field model was trained on.
Single source of truth - used by scripts/05_final_model.py (training) AND the FastAPI backend
(prediction), so a Pakistani answer is converted to HSLS codes identically in both places.

Each option maps to HSLS:09 codes (see reports/hsls_codebook_extract.md).
Conversions marked [ASSUMPTION] cannot be validated without Pakistani data and must be reported.
To change a question later: edit here, re-run scripts/05_final_model.py.
"""
import numpy as np
import pandas as pd

AGREE = [("Strongly agree", 1), ("Agree", 2), ("Disagree", 3), ("Strongly disagree", 4)]

SUBJECTS = [  # HSLS S2FAVSUBJ / S1LEASTSUBJ codes
    ("Biology", 3), ("Chemistry", 3), ("Physics", 3),           # HSLS has one "Science" code [loses detail]
    ("Mathematics", 6), ("Computer Science", 10),
    ("English", 1), ("Urdu", 1),                                 # language & literature = HSLS "English" [ASSUMPTION]
    ("Islamiat", 8), ("Pakistan Studies / History", 11), ("Economics / Civics", 11),
    ("Accounting / Commerce / Business", 12),                    # HSLS "Career preparation class" [ASSUMPTION]
    ("Art / Fine Arts", 4), ("Physical Education", 7), ("Other", 13),
]

QUESTIONS = [
    {"id": "career", "group": "goals",
     "text": "Which job would you most like to have at age 30?",
     "options": [  # X2STU30OCC2 = O*NET major group; X2STU30OCC_STEM1 = STEM sub-domain (as coded in HSLS data)
         ("Doctor, dentist, pharmacist, nurse or other health professional", {"X2STU30OCC2": 29, "X2STU30OCC_STEM1": 4}),
         ("Engineer", {"X2STU30OCC2": 17, "X2STU30OCC_STEM1": 1}),
         ("Architect", {"X2STU30OCC2": 17, "X2STU30OCC_STEM1": 5}),
         ("Software developer, IT or data scientist", {"X2STU30OCC2": 15, "X2STU30OCC_STEM1": 1}),
         ("Scientist (biology, chemistry, physics, environment)", {"X2STU30OCC2": 19, "X2STU30OCC_STEM1": 1}),
         ("Psychologist, economist or social scientist", {"X2STU30OCC2": 19, "X2STU30OCC_STEM1": 5}),
         ("Accountant, banker or finance professional", {"X2STU30OCC2": 13, "X2STU30OCC_STEM1": 0}),
         ("Manager or business owner", {"X2STU30OCC2": 11, "X2STU30OCC_STEM1": 0}),
         ("Lawyer or judge", {"X2STU30OCC2": 23, "X2STU30OCC_STEM1": 0}),
         ("Teacher or lecturer", {"X2STU30OCC2": 25, "X2STU30OCC_STEM1": 0}),
         ("Artist, designer, media, journalist or sports", {"X2STU30OCC2": 27, "X2STU30OCC_STEM1": 0}),
         ("Social worker or counsellor", {"X2STU30OCC2": 21, "X2STU30OCC_STEM1": 0}),
         ("Army, police or security services", {"X2STU30OCC2": 33, "X2STU30OCC_STEM1": 0}),
         ("I don't know yet", {"X2STU30OCC2": 98, "X2STU30OCC_STEM1": 0}),
     ]},
    {"id": "career_certain", "group": "goals", "skip_if": {"career": "I don't know yet"},
     "text": "How sure are you about that job?",
     "options": [("Very sure", {"S2OCC30CERTAIN": 1}), ("Fairly sure", {"S2OCC30CERTAIN": 2}),
                 ("Not sure", {"S2OCC30CERTAIN": 3})]},
    {"id": "career_thought", "group": "goals", "skip_if": {"career": "I don't know yet"},  # HSLS skipped it too
     "text": "How much have you thought about which job you want at age 30?",
     "options": [("Not at all", {"S2OCC30THINK": 1}), ("A little", {"S2OCC30THINK": 2}),
                 ("Somewhat", {"S2OCC30THINK": 3}), ("A lot", {"S2OCC30THINK": 4})]},
    {"id": "education_plan", "group": "goals",
     "text": "What is the highest level of education you plan to complete?",
     "options": [("Intermediate only", {"S2EDUEXP": 2}),
                 ("Diploma or certificate (e.g. DAE)", {"S2EDUEXP": 4}),
                 ("Bachelor's degree (BS, BBA, BE, BSc)", {"S2EDUEXP": 8}),
                 ("Master's degree (MS, MBA, MPhil)", {"S2EDUEXP": 10}),
                 ("Professional degree (MBBS, BDS, Pharm-D, LLB) or PhD", {"S2EDUEXP": 12}),  # US MD/law/PhD [ASSUMPTION]
                 ("I don't know", {"S2EDUEXP": 13})]},
    {"id": "fav_subject", "group": "interests", "text": "What is your favourite subject?",
     "options": [(s, {"S2FAVSUBJ": c}) for s, c in SUBJECTS]},
    {"id": "least_subject", "group": "interests", "text": "What is your least favourite subject?",
     "options": [(s, {"S1LEASTSUBJ": c}) for s, c in SUBJECTS]},
    {"id": "science_person", "group": "interests", "text": "I see myself as a science person.",
     "options": [(a, {"S2SPERSON1": c}) for a, c in AGREE]},
    {"id": "math_person", "group": "interests", "text": "I see myself as a maths person.",
     "options": [(a, {"S2MPERSON1": c}) for a, c in AGREE]},
    {"id": "science_useful", "group": "interests", "text": "Science will be useful for my future career.",
     "options": [(a, {"S2SUSEJOB": c}) for a, c in AGREE]},
    {"id": "math_useful", "group": "interests", "text": "Maths will be useful for my future career.",
     "options": [(a, {"S2MUSEJOB": c}) for a, c in AGREE]},
    {"id": "math_confident", "group": "skills", "text": "I am confident I can do an excellent job on maths tests.",
     "options": [(a, {"S2MTESTS": c}) for a, c in AGREE]},
    {"id": "inter_group", "group": "grades",
     "text": "Which intermediate group did you study? (A-Level: choose the closest)",
     # [ASSUMPTION] Pakistani group -> US transcript profile (Carnegie credits over grades 9-12 = matric + inter).
     # Values placed relative to the US distribution (science credits: median 4, 90th pct 5, max 8;
     # STEM median 8.5, 90th pct 11; computer science 0-1 typical; business 0 typical).
     "options": [
         ("FSc Pre-Medical", {"X3THIMATH": 7, "X3TCREDSCI": 6, "X3TCREDSTEM": 10, "X3TCREDCOMPSCI": 0, "X3TCREDART": 0, "X3TCREDBUS": 0}),
         ("FSc Pre-Engineering", {"X3THIMATH": 12, "X3TCREDSCI": 5, "X3TCREDSTEM": 11, "X3TCREDCOMPSCI": 0, "X3TCREDART": 0, "X3TCREDBUS": 0}),
         ("ICS (Computer Science)", {"X3THIMATH": 12, "X3TCREDSCI": 3, "X3TCREDSTEM": 11, "X3TCREDCOMPSCI": 2, "X3TCREDART": 0, "X3TCREDBUS": 0}),
         ("I.Com (Commerce)", {"X3THIMATH": 9, "X3TCREDSCI": 2, "X3TCREDSTEM": 5, "X3TCREDCOMPSCI": 0, "X3TCREDART": 0, "X3TCREDBUS": 4}),
         ("FA / Humanities / Arts", {"X3THIMATH": 7, "X3TCREDSCI": 2, "X3TCREDSTEM": 4, "X3TCREDCOMPSCI": 0, "X3TCREDART": 2, "X3TCREDBUS": 0}),
     ]},
]

NOMINAL = ["X2STU30OCC2", "X2STU30OCC_STEM1", "S2FAVSUBJ", "S1LEASTSUBJ"]  # categories, one-hot encoded
NCES_MISSING = [-9, -8, -7, -6, -5, -4, -3]
TRANSCRIPT_COLS = ["X3THIMATH", "X3TCREDSCI", "X3TCREDSTEM", "X3TCREDCOMPSCI", "X3TCREDART", "X3TCREDBUS"]


def model_columns(include_group=True):
    cols = []
    for q in QUESTIONS:
        if q["id"] == "inter_group" and not include_group:
            continue
        for _, m in q["options"]:
            cols += [c for c in m if c not in cols]
    return cols


def make_spec(cols):
    """Feature specification: column order + fixed category list per nominal column (from the options)."""
    cats = {}
    for q in QUESTIONS:
        for _, m in q["options"]:
            for c, v in m.items():
                if c in NOMINAL and c in cols:
                    cats.setdefault(c, set()).add(v)
    cats = {c: sorted(v) for c, v in cats.items()}
    names = []
    for c in cols:
        names += [f"{c}__{v}" for v in cats[c]] if c in cats else [c]
    return {"columns": cols, "nominal": cats, "features": names}


def design_matrix(df, spec):
    """HSLS-coded DataFrame -> numeric matrix in spec order. Missing codes -> NaN; nominal -> one-hot
    (an unseen/missing category gives all zeros). Identical function for training and prediction."""
    out = {}
    for c in spec["columns"]:
        s = pd.to_numeric(df[c], errors="coerce").replace(NCES_MISSING, np.nan)
        if c in spec["nominal"]:
            for v in spec["nominal"][c]:
                out[f"{c}__{v}"] = (s == v).astype(float)
        else:
            out[c] = s.astype(float)
    return pd.DataFrame(out, index=df.index)[spec["features"]].values


def answers_to_hsls(answers):
    """{question_id: option label} -> {HSLS column: code}. Skipped / unanswered questions -> NaN."""
    row = {}
    for q in QUESTIONS:
        skip = q.get("skip_if", {})
        skipped = any(answers.get(k) == v for k, v in skip.items())
        label = None if skipped else answers.get(q["id"])
        opts = dict(q["options"])
        if label is not None and label not in opts:
            raise ValueError(f"{q['id']}: unknown option {label!r}")
        for c in {c for _, m in q["options"] for c in m}:
            row[c] = opts[label][c] if label is not None else np.nan
    return row


def questions_json():
    """Front-end friendly question bank (no HSLS codes)."""
    return [{"id": q["id"], "group": q["group"], "text": q["text"],
             "options": [o for o, _ in q["options"]], **({"skip_if": q["skip_if"]} if "skip_if" in q else {})}
            for q in QUESTIONS]
