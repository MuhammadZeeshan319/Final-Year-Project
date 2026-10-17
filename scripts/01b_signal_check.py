"""
Checklist item 7 - signal check: can an ML model learn anything real from these datasets?
Protocol: repeated stratified k-fold CV (5 folds x 5 repeats), duplicates removed first,
metrics next to baselines, plus a shuffled-label control (must be ~ baseline).

Usage:  python scripts/01b_signal_check.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "datasets" / "original"
RNG = 42


def ci(a):
    a = np.asarray(a)
    return f"{a.mean():.3f} [{np.percentile(a, 2.5):.3f}-{np.percentile(a, 97.5):.3f}]"


def evaluate(name, X, y, n_splits=5, n_repeats=5):
    X = pd.get_dummies(X, drop_first=False).astype(float).values
    y = np.array(pd.Series(y).astype(str).tolist(), dtype=object)  # plain numpy (pandas 3 returns StringArray)
    classes, counts = np.unique(y, return_counts=True)
    order = np.argsort(-counts)
    # baselines: always predict largest class / always show the 3 biggest classes
    base_top1 = counts[order[0]] / len(y)
    base_top3 = counts[order[:3]].sum() / len(y)
    base_f1 = f1_score(y, np.full(len(y), classes[order[0]]), average="macro")

    models = {
        "LogReg": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "RandomForest": lambda: RandomForestClassifier(300, min_samples_leaf=3, n_jobs=-1, random_state=RNG),
    }
    rows = []
    for shuffled in (False, True):
        yy = np.random.default_rng(RNG).permutation(y) if shuffled else y
        for mname, make in models.items():
            t1, t3, f1 = [], [], []
            cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=RNG)
            for tr, te in cv.split(X, yy):
                m = make().fit(X[tr], yy[tr])
                P = m.predict_proba(X[te])
                cls = m.classes_ if not hasattr(m, "steps") else m.steps[-1][1].classes_
                top = cls[np.argsort(-P, axis=1)[:, :3]]
                t1.append((top[:, 0] == yy[te]).mean())
                t3.append((top == yy[te][:, None]).any(axis=1).mean())
                f1.append(f1_score(yy[te], top[:, 0], average="macro"))
            rows.append(dict(model=mname + (" (SHUFFLED labels)" if shuffled else ""),
                             top1=ci(t1), top3=ci(t3), macroF1=ci(f1)))
    print(f"\n=== {name} ===  n={len(y)}  classes={len(classes)}")
    print(f"Baseline: largest class top1={base_top1:.3f} | 3 biggest classes top3={base_top3:.3f} | macroF1={base_f1:.3f}")
    print(f"Chance (uniform guess): top1={1/len(classes):.3f}  top3={min(3/len(classes),1):.3f}")
    print(pd.DataFrame(rows).to_string(index=False))


# ---------- career_path_in_all_field: target = Field ----------
cp = pd.read_csv(ORIG / "career_path_in_all_field.csv")
# Career is chosen AFTER the field -> leakage, excluded from features
evaluate("career_path: Field from skills/GPA (Career excluded)", cp.drop(columns=["Field", "Career"]), cp["Field"])
# Sanity: if data were real, Career would almost determine Field
evaluate("career_path: Field from Career only (should be ~100% if real)", cp[["Career"]], cp["Field"])

# ---------- student-scores-6k: target = career_aspiration ----------
ss = pd.read_csv(ORIG / "student-scores-6k.csv")
feats = [c for c in ss.columns if c not in ("id", "first_name", "last_name", "email", "career_aspiration")]
print(f"\nstudent-scores: {len(ss)} rows, {len(ss.drop_duplicates(feats + ['career_aspiration']))} unique students")
evaluate("student-scores WITH duplicates (WRONG - copies leak across folds)", ss[feats], ss["career_aspiration"])
ssd = ss.drop_duplicates(feats + ["career_aspiration"])
evaluate("student-scores duplicates REMOVED (honest)", ssd[feats], ssd["career_aspiration"])
