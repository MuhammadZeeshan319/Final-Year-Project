"""
Step 3 - Train + evaluate ML models on each surviving dataset with ONE identical protocol.
  - repeated stratified k-fold CV (default 5 folds x 5 repeats), duplicates already removed in step 2
  - metrics: top-1, top-3, macro-F1, mean [2.5-97.5 percentile across folds]
  - always next to baselines: largest class (top-1), 3 biggest classes (top-3)
  - shuffled-label control (must fall to baseline, otherwise something leaks)
  - all preprocessing inside the CV pipeline (fit on training folds only)
Datasets are evaluated SEPARATELY, never merged.

Usage:  python scripts/03_evaluate.py               (full run, can take 30+ min)
        python scripts/03_evaluate.py --quick       (3 folds x 1 repeat, to test it works)
Output: console + reports/03_results.csv + reports/03_results.md (the proof table)
        reports/03_confusion_<set>.csv, reports/03_per_field_<set>.csv
"""
import re, sys, time
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import f1_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DER, REP = ROOT / "datasets" / "derived", ROOT / "reports"
QUICK = "--quick" in sys.argv
FOLDS, REPEATS = (3, 1) if QUICK else (5, 5)
RNG = 42
NCES_MISSING = [-9, -8, -7, -6, -5, -4, -3]  # -1 "don't know" is kept as an answer

# HSLS columns a student can actually answer in the Edu Path questionnaire, by question group
QGROUPS = {
    "grades":    r"^X3TGPA|^X3TCRED|^X3THIMATH$|^X3THISCI$|^X3TACADTRCK$|^S1[MS]8GRADE$",
    "interests": r"FAVSUBJ$|LEASTSUBJ$|^X[12](MTH|SCI)(INT|INT_R|UTI|ID)$|^S2(FFA|HOSA|MUSIC|ART|DRAMA|SPORTS|CLUB|ACADEMIC)$"
                 r"|^S1[MS](CLUB|COMPETE|CAMP|TUTOR)$|^S1(SBOOKS|WEBINFO|SMUSEUM)$",
    "skills":    r"^X[12]TXM|^X[12](MTH|SCI)EFF$",
    "goals":     r"STU30OCC2$|STU30OCC_STEM1$|EDUEXPCT$|EDUEXPECT$|^S2EDUEXP$|OCC30THINK$|OCC30CERTAIN$",
}
NOMINAL = r"FAVSUBJ$|LEASTSUBJ$|STU30OCC2$"  # codes are categories, not amounts -> one-hot
UCI_NOMINAL = ["Marital status", "Application mode", "Previous qualification", "Nacionality",
               "Mother's qualification", "Father's qualification", "Mother's occupation", "Father's occupation"]


def qgroup(c):
    for g, pat in QGROUPS.items():
        if re.search(pat, c):
            return g
    return None


def models():
    return {
        "LogReg": lambda: make_pipeline(SimpleImputer(strategy="median", add_indicator=True),
                                        StandardScaler(), LogisticRegression(max_iter=3000, C=0.1)),
        "GradBoost": lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                                            early_stopping=True, random_state=RNG),
    }


def pct(a):
    a = np.asarray(a)
    return f"{a.mean():.3f} [{np.percentile(a, 2.5):.3f}-{np.percentile(a, 97.5):.3f}]"


def run_cv(X, y, make, repeats):
    cv = RepeatedStratifiedKFold(n_splits=FOLDS, n_repeats=repeats, random_state=RNG)
    t1, t3, f1 = [], [], []
    oof = np.empty(len(y), dtype=object)
    for i, (tr, te) in enumerate(cv.split(X, y)):
        m = make().fit(X[tr], y[tr])
        P = m.predict_proba(X[te])
        top = m.classes_[np.argsort(-P, axis=1)[:, :3]]
        t1.append((top[:, 0] == y[te]).mean())
        t3.append((top == y[te][:, None]).any(axis=1).mean())
        f1.append(f1_score(y[te], top[:, 0], average="macro"))
        if i < FOLDS:  # first repeat -> out-of-fold predictions for confusion matrix
            oof[te] = top[:, 0]
    return t1, t3, f1, oof


def evaluate(set_name, X, y, results):
    X = X.astype(float).values
    y = np.array(pd.Series(y).astype(str).tolist(), dtype=object)
    cls, cnt = np.unique(y, return_counts=True)
    o = np.argsort(-cnt)
    b1, b3 = cnt[o[0]] / len(y), cnt[o[:3]].sum() / len(y)
    bf1 = f1_score(y, np.full(len(y), cls[o[0]]), average="macro")
    print(f"\n=== {set_name} === n={len(y)} features={X.shape[1]} fields={len(cls)}")
    print(f"Baseline: largest class ({cls[o[0]]}) top1={b1:.3f} | 3 biggest {list(cls[o[:3]])} top3={b3:.3f}")
    results.append(dict(dataset=set_name, model="Baseline (largest / 3 biggest)", n=len(y),
                        features=X.shape[1], top1=f"{b1:.3f}", top3=f"{b3:.3f}", macroF1=f"{bf1:.3f}"))
    best, best_t1 = None, -1
    for name, make in models().items():
        t0 = time.time()
        t1, t3, f1, oof = run_cv(X, y, make, REPEATS)
        print(f"  {name:10s} top1={pct(t1)} top3={pct(t3)} macroF1={pct(f1)}  ({time.time()-t0:.0f}s)")
        results.append(dict(dataset=set_name, model=name, n=len(y), features=X.shape[1],
                            top1=pct(t1), top3=pct(t3), macroF1=pct(f1)))
        if np.mean(t1) > best_t1:
            best, best_t1, best_oof = name, np.mean(t1), oof
    # shuffled-label control with the best model (1 repeat)
    ys = np.random.default_rng(RNG).permutation(y)
    t1, t3, f1, _ = run_cv(X, ys, models()[best], 1)
    print(f"  {best} SHUFFLED labels: top1={pct(t1)} top3={pct(t3)}  (must be ~baseline)")
    results.append(dict(dataset=set_name, model=f"{best} - SHUFFLED labels (control)", n=len(y),
                        features=X.shape[1], top1=pct(t1), top3=pct(t3), macroF1=pct(f1)))
    # confusion matrix + per-field recall (first repeat, out-of-fold)
    safe = re.sub(r"\W+", "_", set_name)
    cm = pd.DataFrame(confusion_matrix(y, best_oof, labels=cls), index=cls, columns=cls)
    cm.to_csv(REP / f"03_confusion_{safe}.csv")
    rec = pd.DataFrame({"n": cnt, "recall": np.diag(cm) / cnt}, index=cls).round(3)
    rec.to_csv(REP / f"03_per_field_{safe}.csv")
    print(f"  per-field recall ({best}):\n" + rec.to_string().replace("\n", "\n    "))


def main():
    results = []
    # ---------- UCI ----------
    u = pd.read_csv(DER / "uci_prechoice.csv")
    Xu = pd.get_dummies(u.drop(columns="field"), columns=UCI_NOMINAL)
    evaluate("UCI (Portugal, 16 pre-enrolment cols)", Xu, u.field, results)

    # ---------- HSLS ----------
    h = pd.read_csv(DER / "hsls_prechoice.csv.gz", low_memory=False)
    feats = [c for c in h.columns if c not in ("STU_ID", "field", "field_2016")]
    H = h[feats].replace(NCES_MISSING, np.nan)
    qcols = [c for c in feats if qgroup(c)]
    pd.DataFrame({"column": qcols, "group": [qgroup(c) for c in qcols]}).to_csv(REP / "03_hsls_questionnaire_cols.csv", index=False)
    print(f"\nHSLS questionnaire columns by group: {pd.Series([qgroup(c) for c in qcols]).value_counts().to_dict()}")
    nom = [c for c in qcols if re.search(NOMINAL, c)]
    Xq = pd.get_dummies(H[qcols], columns=nom, dummy_na=False)  # missing answer -> all-zero dummies
    evaluate("HSLS questionnaire set (what Edu Path can ask)", Xq, h.field, results)
    evaluate("HSLS all pre-choice cols (ceiling, not askable)", H, h.field, results)

    # ---------- save ----------
    res = pd.DataFrame(results)
    res.to_csv(REP / "03_results.csv", index=False)
    with open(REP / "03_results.md", "w", encoding="utf-8") as fh:
        fh.write(f"# Edu Path - model evaluation ({date.today()})\n\n")
        fh.write(f"Protocol: repeated stratified {FOLDS}-fold CV x {REPEATS} repeats; duplicates removed before CV; "
                 "preprocessing fitted inside each training fold; values = mean [2.5-97.5 percentile over folds]. "
                 "Datasets evaluated separately (never merged). Shuffled-label control must equal baseline.\n\n")
        try:
            fh.write(res.to_markdown(index=False))  # needs `pip install tabulate`
        except ImportError:
            fh.write("```\n" + res.to_string(index=False) + "\n```")
        fh.write("\n")
    print("\n" + res.to_string(index=False))
    print("\nSaved reports/03_results.csv and reports/03_results.md")


if __name__ == "__main__":
    main()
