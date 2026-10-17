"""
Step 4 - How much does each question help? (XGBoost, HSLS questionnaire set)

  A. Group ablation under CV: accuracy with ONLY each question group, and WITHOUT each group.
     Extra config: without US standardized test scores (a Pakistani student cannot supply them).
  B. Nested top-N selection: in every training fold, rank questions by SHAP on the TRAINING data only,
     keep the top N, refit, test on the held-out fold. -> honest accuracy of a short questionnaire.
     (Selecting on all data and then cross-validating would leak and inflate accuracy.)
  C. Final XGBoost on all students + SHAP: importance per question, per group and per field.
     Saved to models/ (full questionnaire model; the compact model is built in step 5).

Usage: python scripts/04_explain_select.py            (5-fold x 3 repeats, ~20-30 min)
       python scripts/04_explain_select.py --quick    (3-fold x 1)
Output: reports/04_group_ablation.csv, reports/04_topN_curve.csv, reports/04_topN_selection_freq.csv,
        reports/04_shap_importance.csv, reports/04_shap_by_group.csv, reports/04_shap_by_field.csv,
        reports/04_summary.md, models/xgb_hsls_questionnaire.json (+ _features.json)
"""
import json, re, sys, time
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import f1_score
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
DER, REP, MOD = ROOT / "datasets" / "derived", ROOT / "reports", ROOT / "models"
MOD.mkdir(exist_ok=True)
QUICK = "--quick" in sys.argv
FOLDS, REPEATS = (3, 1) if QUICK else (5, 3)
RNG = 42
NCES_MISSING = [-9, -8, -7, -6, -5, -4, -3]
NOMINAL = r"FAVSUBJ$|LEASTSUBJ$|STU30OCC2$"
TESTSCORE = r"^X[12]TXM"
TOP_N = [5, 10, 15, 20, 30, 50]
SHAP_ROWS = 1500  # SHAP computed on a sample of training rows (speed); same seed each fold


def xgb():  # identical settings to step 3b
    return XGBClassifier(n_estimators=400, learning_rate=0.05, max_depth=4, subsample=0.8,
                         colsample_bytree=0.5, tree_method="hist", eval_metric="mlogloss",
                         random_state=RNG, n_jobs=-1)


def design(H, cols):
    """One-hot nominal columns; dummy names 'COL__value' so they map back to the question."""
    nom = [c for c in cols if re.search(NOMINAL, c)]
    X = pd.get_dummies(H[cols], columns=nom, prefix=nom, prefix_sep="__", dummy_na=False).astype(float)
    return X


def orig(name):
    return name.split("__")[0]


def metrics(P, classes, yte):
    top = np.asarray(classes)[np.argsort(-P, axis=1)[:, :3]]
    hit = top == yte[:, None]
    return dict(top1=hit[:, 0].mean(), top3=hit.any(axis=1).mean(),
                macroF1=f1_score(yte, top[:, 0], average="macro"),
                NDCG3=(hit / np.log2(np.arange(2, 5))).sum(axis=1).mean())


def pct(a):
    a = np.asarray(a)
    return f"{a.mean():.3f} [{np.percentile(a, 2.5):.3f}-{np.percentile(a, 97.5):.3f}]"


def shap_abs(model, X, K):
    """mean |SHAP| per feature (averaged over rows and classes); handles old/new shap output shapes."""
    sv = shap.TreeExplainer(model).shap_values(X)
    arr = np.stack(sv, axis=-1) if isinstance(sv, list) else np.asarray(sv)
    if arr.ndim == 3 and arr.shape[0] == K and arr.shape[-1] != K:
        arr = np.moveaxis(arr, 0, -1)
    return np.abs(arr)  # (rows, features, classes)


def main():
    h = pd.read_csv(DER / "hsls_prechoice.csv.gz", low_memory=False)
    qmap = pd.read_csv(REP / "03_hsls_questionnaire_cols.csv")  # column, group (from step 3)
    qcols, group = qmap.column.tolist(), dict(zip(qmap.column, qmap.group))
    H = h[qcols].replace(NCES_MISSING, np.nan)
    fields = sorted(h.field.unique())
    y = h.field.map({f: i for i, f in enumerate(fields)}).values
    K = len(fields)
    cv = list(RepeatedStratifiedKFold(n_splits=FOLDS, n_repeats=REPEATS, random_state=RNG).split(H, y))
    print(f"n={len(y)}, questions={len(qcols)}, CV={FOLDS}-fold x {REPEATS} ({len(cv)} fits per config)")

    # ---------------- A. group ablation ----------------
    groups = sorted(set(group.values()))
    configs = {"ALL questions": qcols}
    for g in groups:
        configs[f"ONLY {g}"] = [c for c in qcols if group[c] == g]
    for g in groups:
        configs[f"WITHOUT {g}"] = [c for c in qcols if group[c] != g]
    configs["WITHOUT US test scores (Pakistan-askable)"] = [c for c in qcols if not re.search(TESTSCORE, c)]
    rows = []
    print("\n--- A. group ablation (XGBoost) ---")
    for name, cols in configs.items():
        t0 = time.time()
        X = design(H, cols).values
        res = {k: [] for k in ("top1", "top3", "macroF1", "NDCG3")}
        for tr, te in cv:
            m = xgb().fit(X[tr], y[tr])
            for k, v in metrics(m.predict_proba(X[te]), m.classes_, y[te]).items():
                res[k].append(v)
        rows.append(dict(config=name, questions=len(cols), **{k: pct(v) for k, v in res.items()},
                         top1_mean=np.mean(res["top1"]), top3_mean=np.mean(res["top3"])))
        print(f"  {name:45s} q={len(cols):3d} top1={pct(res['top1'])} top3={pct(res['top3'])} ({time.time()-t0:.0f}s)")
    abl = pd.DataFrame(rows)
    ref1, ref3 = abl.top1_mean[0], abl.top3_mean[0]
    abl["delta_top1_vs_ALL"] = (abl.top1_mean - ref1).round(3)
    abl["delta_top3_vs_ALL"] = (abl.top3_mean - ref3).round(3)
    abl.drop(columns=["top1_mean", "top3_mean"]).to_csv(REP / "04_group_ablation.csv", index=False)

    # ---------------- B. nested top-N selection ----------------
    print("\n--- B. nested top-N question selection (selection inside each training fold) ---")
    Xall = design(H, qcols)
    names = Xall.columns.tolist()
    Xv = Xall.values
    owner = np.array([orig(n) for n in names])
    curve = {n: {k: [] for k in ("top1", "top3", "macroF1", "NDCG3")} for n in TOP_N}
    sel_count = pd.Series(0, index=qcols)
    rng = np.random.default_rng(RNG)
    t0 = time.time()
    for i, (tr, te) in enumerate(cv):
        m = xgb().fit(Xv[tr], y[tr])
        samp = rng.choice(tr, size=min(SHAP_ROWS, len(tr)), replace=False)
        imp = pd.Series(shap_abs(m, Xv[samp], K).mean(axis=(0, 2)), index=owner).groupby(level=0).sum()
        ranked = imp.sort_values(ascending=False).index.tolist()
        sel_count[ranked[:20]] += 1
        for n in TOP_N:
            keep = np.isin(owner, ranked[:n])
            mm = xgb().fit(Xv[tr][:, keep], y[tr])
            for k, v in metrics(mm.predict_proba(Xv[te][:, keep]), mm.classes_, y[te]).items():
                curve[n][k].append(v)
        print(f"  fold {i+1}/{len(cv)} done ({time.time()-t0:.0f}s)")
    cur = pd.DataFrame([dict(top_N_questions=n, **{k: pct(v) for k, v in curve[n].items()}) for n in TOP_N])
    cur = pd.concat([cur, pd.DataFrame([dict(top_N_questions=f"ALL ({len(qcols)})",
                                             **{k: abl.loc[0, k] for k in ("top1", "top3", "macroF1", "NDCG3")})])],
                    ignore_index=True)
    cur.to_csv(REP / "04_topN_curve.csv", index=False)
    freq = (sel_count / len(cv)).sort_values(ascending=False)
    freq = freq[freq > 0].rename("share_of_folds_in_top20").to_frame()
    freq["group"] = [group[c] for c in freq.index]
    freq.to_csv(REP / "04_topN_selection_freq.csv")
    print(cur.to_string(index=False))

    # ---------------- C. final model on all students + SHAP ----------------
    print("\n--- C. final XGBoost on all students + SHAP ---")
    final = xgb().fit(Xv, y)
    final.save_model(MOD / "xgb_hsls_questionnaire.json")
    json.dump({"features": names, "fields": fields, "nces_missing_to_nan": NCES_MISSING,
               "trained_on": f"HSLS:09 n={len(y)}", "date": str(date.today())},
              open(MOD / "xgb_hsls_questionnaire_features.json", "w"), indent=1)
    samp = rng.choice(len(y), size=min(3000, len(y)), replace=False)
    A = shap_abs(final, Xv[samp], K)  # rows x features x classes
    per_feat = pd.DataFrame(A.mean(axis=0), index=owner, columns=fields).groupby(level=0).sum()
    per_feat["overall"] = per_feat[fields].mean(axis=1)
    per_feat["group"] = [group[c] for c in per_feat.index]
    per_feat = per_feat.sort_values("overall", ascending=False)
    per_feat["share_%"] = (100 * per_feat.overall / per_feat.overall.sum()).round(2)
    per_feat.round(4).to_csv(REP / "04_shap_importance.csv")
    by_group = per_feat.groupby("group")[["overall"] + fields].sum()
    by_group["share_%"] = (100 * by_group.overall / by_group.overall.sum()).round(1)
    by_group.round(4).to_csv(REP / "04_shap_by_group.csv")
    top_field = {f: per_feat[f].sort_values(ascending=False).head(5).index.tolist() for f in fields}
    pd.DataFrame(top_field).to_csv(REP / "04_shap_by_field.csv", index=False)

    print("\nSHAP share by question group:\n" + by_group[["share_%"]].sort_values("share_%", ascending=False).to_string())
    print("\nTop 30 questions by SHAP:\n" + per_feat[["group", "share_%"]].head(30).to_string())
    print("\nTop 5 questions per field:\n" + pd.DataFrame(top_field).to_string(index=False))
    print("\nGroup ablation:\n" + abl.drop(columns=["top1_mean", "top3_mean", "macroF1", "NDCG3"]).to_string(index=False))
    print("\nMost stable top-20 questions across folds:\n" + freq.head(30).to_string())

    with open(REP / "04_summary.md", "w", encoding="utf-8") as fh:
        fh.write(f"# Edu Path - question contribution (XGBoost) ({date.today()})\n\n"
                 f"n={len(y)} HSLS:09 students, CV {FOLDS}-fold x {REPEATS}. Ablation and top-N use the "
                 "same folds. Top-N selection is nested (SHAP ranking on training folds only).\n\n")
        for title, d in (("Group ablation", abl.drop(columns=["top1_mean", "top3_mean"])),
                         ("Accuracy vs number of questions (nested)", cur),
                         ("SHAP share by group (final model)", by_group[["share_%"]].reset_index()),
                         ("Top 30 questions by SHAP (final model)", per_feat[["group", "share_%"]].head(30).reset_index(names="question"))):
            fh.write(f"## {title}\n\n```\n{d.to_string(index=False)}\n```\n\n")
    print("\nSaved reports/04_*.csv, reports/04_summary.md, models/xgb_hsls_questionnaire.json")


if __name__ == "__main__":
    main()
