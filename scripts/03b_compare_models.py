"""
Step 3b - Compare the algorithms named in the project documents, on the selected dataset
(HSLS:09 questionnaire set), with the SAME protocol as step 3:
  - repeated stratified 5-fold x 5 repeats, duplicates removed (step 2), preprocessing inside each fold
  - fixed, documented hyperparameters (no tuning on test folds -> no optimistic bias)
  - metrics: top-1, top-3, macro-F1, Precision@3, Recall@3, NDCG@3 ; mean [2.5-97.5 pct over folds]
  - baselines (largest class / 3 biggest classes) + shuffled-label control for the best model

Algorithms and where they are required:
  XGBoost            - proposal "AI Powered...Decision Support System" sec 6.5, 10.4, 16
  Random Forest      - presentation slide 7 (Kumar et al. 2022)
  Decision Tree C4.5 - presentation slide 7 (Kumar et al. 2022)  [sklearn CART with entropy = C4.5-style]
  Naive Bayes        - presentation slide 7 (Rances et al. 2026; Arcinas et al. 2025)
  KNN                - presentation slide 7 (Arcinas et al. 2025)
  AdaBoost           - presentation slide 7 (Arcinas et al. 2025)
  SVM                - presentation slide 7 (Kumar et al. 2022, "Fuzzy SVM"; standard linear SVM used,
                       fuzzy SVM has no maintained Python implementation)
  LogReg, HistGradBoost - reference models from step 3

Needs: pip install xgboost
Usage: python scripts/03b_compare_models.py            (XGBoost + 2 reference models, ~10 min)
       python scripts/03b_compare_models.py --quick    (3 folds x 1 repeat)
       python scripts/03b_compare_models.py --all      (also the literature-review algorithms, ~30 min)
Output: reports/03b_model_comparison.csv / .md, reports/03b_per_field_recall.csv
"""
import sys, time
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (HistGradientBoostingClassifier, RandomForestClassifier, AdaBoostClassifier)
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import f1_score
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
DER, REP = ROOT / "datasets" / "derived", ROOT / "reports"
QUICK = "--quick" in sys.argv
FOLDS, REPEATS = (3, 1) if QUICK else (5, 5)
RNG = 42
NCES_MISSING = [-9, -8, -7, -6, -5, -4, -3]
NOMINAL = r"FAVSUBJ$|LEASTSUBJ$|STU30OCC2$"


def imp(*steps):  # impute missing (median + missing-indicator) inside the fold, then the model
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), *steps)


MODELS = {
    "XGBoost":             lambda: XGBClassifier(n_estimators=400, learning_rate=0.05, max_depth=4,
                                                 subsample=0.8, colsample_bytree=0.5, tree_method="hist",
                                                 eval_metric="mlogloss", random_state=RNG, n_jobs=-1),
    "Random Forest":       lambda: imp(RandomForestClassifier(n_estimators=400, min_samples_leaf=3,
                                                              max_features="sqrt", n_jobs=-1, random_state=RNG)),
    "Decision Tree (C4.5-style)": lambda: imp(DecisionTreeClassifier(criterion="entropy", max_depth=8,
                                                                    min_samples_leaf=20, random_state=RNG)),
    "Naive Bayes":         lambda: imp(StandardScaler(), GaussianNB()),
    "KNN":                 lambda: imp(StandardScaler(), KNeighborsClassifier(n_neighbors=50, weights="distance")),
    "AdaBoost":            lambda: imp(AdaBoostClassifier(DecisionTreeClassifier(max_depth=3), n_estimators=200,
                                                          learning_rate=0.5, random_state=RNG)),
    "SVM (linear)":        lambda: imp(StandardScaler(), CalibratedClassifierCV(LinearSVC(C=0.01, max_iter=5000), cv=3)),
    "Logistic Regression": lambda: imp(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1)),
    "HistGradBoost":       lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                                                  early_stopping=True, random_state=RNG),
}
# Project algorithm = XGBoost (proposal sec 6.5 / 10.4). Step-3 models kept as reference.
# Literature-review algorithms (RF, DT, NB, KNN, AdaBoost, SVM) only with --all (optional comparison).
if "--all" not in sys.argv:
    MODELS = {k: MODELS[k] for k in ("XGBoost", "HistGradBoost", "Logistic Regression")}


def pct(a):
    a = np.asarray(a)
    return f"{a.mean():.3f} [{np.percentile(a, 2.5):.3f}-{np.percentile(a, 97.5):.3f}]"


def run_cv(X, y, make, repeats):
    """y = integer codes 0..K-1. Returns per-fold metric lists + out-of-fold top-1 (first repeat)."""
    cv = RepeatedStratifiedKFold(n_splits=FOLDS, n_repeats=repeats, random_state=RNG)
    m_ = {k: [] for k in ("top1", "top3", "macroF1", "P@3", "R@3", "NDCG@3")}
    oof = np.full(len(y), -1)
    for i, (tr, te) in enumerate(cv.split(X, y)):
        m = make().fit(X[tr], y[tr])
        P = m.predict_proba(X[te])
        top = np.asarray(m.classes_)[np.argsort(-P, axis=1)[:, :3]]
        hit = top == y[te][:, None]                       # one relevant field per student
        rank_gain = (hit / np.log2(np.arange(2, 5))).sum(axis=1)  # DCG@3; ideal DCG = 1
        m_["top1"].append(hit[:, 0].mean())
        m_["top3"].append(hit.any(axis=1).mean())
        m_["macroF1"].append(f1_score(y[te], top[:, 0], average="macro"))
        m_["P@3"].append(hit.sum(axis=1).mean() / 3)      # max 0.333 with a single relevant item
        m_["R@3"].append(hit.any(axis=1).mean())          # = top-3 accuracy
        m_["NDCG@3"].append(rank_gain.mean())
        if i < FOLDS:
            oof[te] = top[:, 0]
    return m_, oof


def main():
    h = pd.read_csv(DER / "hsls_prechoice.csv.gz", low_memory=False)
    qcols = pd.read_csv(REP / "03_hsls_questionnaire_cols.csv")["column"].tolist()  # written by step 3
    H = h[qcols].replace(NCES_MISSING, np.nan)
    nom = [c for c in qcols if pd.Series([c]).str.contains(NOMINAL).iloc[0]]
    X = pd.get_dummies(H, columns=nom, dummy_na=False).astype(float).values
    fields = sorted(h.field.unique())
    y = h.field.map({f: i for i, f in enumerate(fields)}).values
    cnt = np.bincount(y)
    o = np.argsort(-cnt)
    print(f"HSLS questionnaire set: n={len(y)} features={X.shape[1]} fields={len(fields)}  "
          f"CV={FOLDS}-fold x {REPEATS}")

    b1, b3 = cnt[o[0]] / len(y), cnt[o[:3]].sum() / len(y)
    rows = [dict(model="Baseline (largest / 3 biggest)", top1=f"{b1:.3f}", top3=f"{b3:.3f}",
                 macroF1=f"{f1_score(y, np.full(len(y), o[0]), average='macro'):.3f}",
                 **{"P@3": f"{b3/3:.3f}", "R@3": f"{b3:.3f}",
                    "NDCG@3": f"{(cnt[o[0]] + cnt[o[1]]/np.log2(3) + cnt[o[2]]/2) / len(y):.3f}"}, seconds="")]
    recall, best, best_t1 = {}, None, -1
    for name, make in MODELS.items():
        t0 = time.time()
        res, oof = run_cv(X, y, make, REPEATS)
        secs = time.time() - t0
        rows.append(dict(model=name, **{k: pct(v) for k, v in res.items()}, seconds=f"{secs:.0f}"))
        recall[name] = [((oof == k) & (y == k)).sum() / cnt[k] for k in range(len(fields))]
        print(f"  {name:28s} top1={pct(res['top1'])} top3={pct(res['top3'])} "
              f"F1={pct(res['macroF1'])} NDCG@3={pct(res['NDCG@3'])} ({secs:.0f}s)")
        if np.mean(res["top1"]) > best_t1:
            best, best_t1 = name, np.mean(res["top1"])

    ys = np.random.default_rng(RNG).permutation(y)
    res, _ = run_cv(X, ys, MODELS[best], 1)
    rows.append(dict(model=f"{best} - SHUFFLED labels (control)", **{k: pct(v) for k, v in res.items()}, seconds=""))
    print(f"  {best} SHUFFLED: top1={pct(res['top1'])} top3={pct(res['top3'])} (must be ~baseline)")

    df = pd.DataFrame(rows)
    df.to_csv(REP / "03b_model_comparison.csv", index=False)
    rec = pd.DataFrame(recall, index=fields).round(3)
    rec.insert(0, "n", cnt)
    rec.to_csv(REP / "03b_per_field_recall.csv")
    with open(REP / "03b_model_comparison.md", "w", encoding="utf-8") as fh:
        fh.write(f"# Edu Path - algorithm comparison ({date.today()})\n\n"
                 f"Dataset: HSLS:09 questionnaire set, n={len(y)} students, {X.shape[1]} features, 7 fields. "
                 f"Protocol: repeated stratified {FOLDS}-fold CV x {REPEATS}; duplicates removed before CV; "
                 "imputation/scaling fitted inside each training fold; fixed hyperparameters (listed in "
                 "scripts/03b_compare_models.py), no tuning on test folds. Values = mean [2.5-97.5 percentile "
                 "over folds]. P@3 max = 0.333 because each student has one true field. R@3 = top-3 accuracy.\n\n")
        for d, name in ((df, "Results"), (rec.reset_index(names="field"), "Recall per field (first repeat, out-of-fold)")):
            fh.write(f"## {name}\n\n")
            try:
                fh.write(d.to_markdown(index=False))
            except ImportError:
                fh.write("```\n" + d.to_string(index=False) + "\n```")
            fh.write("\n\n")
    print("\n" + df.to_string(index=False))
    print("\nRecall per field:\n" + rec.to_string())
    print(f"\nBest by top-1: {best}. Saved reports/03b_model_comparison.md / .csv, reports/03b_per_field_recall.csv")


if __name__ == "__main__":
    main()
