"""
Shared feature logic for EduPath.
Used by BOTH train_model.py (raw HSLS columns) and app.py (web-form answers),
so the model sees identical features at training time and prediction time.
"""
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- target ----
# 2-digit CIP codes (HSLS S4FIELD2 / S3FIELD2) grouped into the 7 study fields.
# Edit this dict to change the grouping; everything else adapts.
# Not mapped (dropped from training): CIP 30 (multi/interdisciplinary), 60, 99 (other).
# NOTE: 2-digit CIP cannot separate veterinary medicine (inside 51) or geology (inside 40).
FIELDS = {
    "Computer Science & Information Technology": [11],
    "Engineering & Technology":         [14, 15, 47, 48, 49],
    "Medical & Health Sciences":        [51],
    "Business & Management":            [52],
    "Natural & Physical Sciences":      [26, 40],
    "Social Sciences":                  [42, 45, 44, 19],
    "Arts, Design & Humanities":        [50, 24, 23, 54, 16, 38, 39, 5],
    "Law & Legal Studies":              [22, 43],
    "Education & Teaching":             [13],
    "Agriculture & Veterinary Sciences":[1],
    "Architecture & Built Environment": [4, 46],
    "Media & Communication":            [9, 10],
    "Mathematics & Statistics":         [27],
    "Environmental & Earth Sciences":   [3],
    "Hospitality, Tourism & Sports":    [12, 31],
}
CODE2FIELD = {c: f for f, cs in FIELDS.items() for c in cs}

def build_target(df: pd.DataFrame) -> pd.Series:
    """Latest known field of study: S4FIELD2, falling back to S3FIELD2."""
    t = df["S4FIELD2"].where(df["S4FIELD2"] > 0)
    t = t.fillna(df["S3FIELD2"].where(df["S3FIELD2"] > 0))
    return t.map(CODE2FIELD)

# -------------------------------------------------------------- features ----
GPA = {  # feature name -> HSLS column
    "gpa_english": "X3TGPAENG", "gpa_math": "X3TGPAMAT", "gpa_science": "X3TGPASCI",
    "gpa_social":  "X3TGPASOCST", "gpa_overall": "X3TGPATOT",
}
ELECTIVES = {  # feature name -> HSLS credits column (Carnegie units over high school)
    "lvl_cs": "X3TCREDCOMPSCI", "lvl_engineering": "X3TCREDENGIN", "lvl_art": "X3TCREDART",
    "lvl_business": "X3TCREDBUS", "lvl_health": "X3TCREDHELSCI", "lvl_media": "X3TCREDCOM",
    "lvl_agriculture": "X3TCREDAG", "lvl_language": "X3TCREDLANG",
    "lvl_architecture": "X3TCREDARCH", "lvl_publicservice": "X3TCREDPUBSER", "lvl_humanservices": "X3TCREDHUMSER",
}
ACTIVITIES = {
    "act_ffa": "S2FFA", "act_hosa": "S2HOSA", "act_music": "S2MUSIC", "act_art": "S2ART",
    "act_drama": "S2DRAMA", "act_sports": "S2SPORTS", "act_club": "S2CLUB", "act_academic": "S2ACADEMIC",
}
# Career area a student imagines at age 30 (X1STU30OCC2 = 2-digit SOC major group)
OCC_CODES = [11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 39, 41, 45, 47, 49, 51, 53, 55, 98]
OCC_FEATURES = [f"occ_{c}" for c in OCC_CODES] + ["occ_other"]

FEATURES = list(GPA) + list(ELECTIVES) + list(ACTIVITIES) + OCC_FEATURES

def _level(credits):
    """0 = none, 1 = up to 1.5 years, 2 = more than 1.5 years (NaN stays NaN)."""
    return np.select([credits == 0, credits <= 1.5, credits > 1.5], [0, 1, 2], default=np.nan)

def _occ_onehot(occ: pd.Series) -> pd.DataFrame:
    out = {f"occ_{c}": (occ == c).astype(int) for c in OCC_CODES}
    out["occ_other"] = (~occ.isin(OCC_CODES)).astype(int)
    return pd.DataFrame(out)

def training_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Raw HSLS dataframe -> model features. HSLS negative codes (-1,-5,-7,-8,-9) = missing."""
    X = pd.DataFrame(index=df.index)
    for f, c in GPA.items():
        X[f] = df[c].where(df[c] >= 0)
    for f, c in ELECTIVES.items():
        X[f] = _level(df[c].where(df[c] >= 0))
    for f, c in ACTIVITIES.items():
        X[f] = df[c].where(df[c] >= 0)
    X = pd.concat([X, _occ_onehot(df["X1STU30OCC2"])], axis=1)
    return X[FEATURES]

def row_from_answers(a: dict) -> pd.DataFrame:
    """Web-form answers (dict) -> one-row feature frame in the exact training column order."""
    row = {}
    for f in GPA:
        v = a.get(f)
        row[f] = float(v) if v not in (None, "") else np.nan
    for f in ELECTIVES:
        v = a.get(f)
        row[f] = float(v) if v not in (None, "") else np.nan
    for f in ACTIVITIES:
        row[f] = 1.0 if a.get(f) else 0.0
    occ = a.get("occupation")
    occ = int(occ) if occ not in (None, "") else -1
    for c in OCC_CODES:
        row[f"occ_{c}"] = 1 if occ == c else 0
    row["occ_other"] = 0 if occ in OCC_CODES else 1
    return pd.DataFrame([row])[FEATURES]
