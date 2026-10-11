"""
Train the EduPath field-ranking model on HSLS:09.
Run:  python train_model.py path/to/hsls.csv
Outputs: model_lr.json (used by the web app), model_meta.json (metrics), confusion_matrix.png
Model: multinomial logistic regression with mild class weighting (so rare fields can still appear
in the ranking). Gradient boosting is trained only as a comparison.
"""
import sys, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, top_k_accuracy_score, confusion_matrix, classification_report
import features as F

CW_POWER = 0.5   # 0 = no class weighting, 1 = fully balanced

path = sys.argv[1] if len(sys.argv) > 1 else "hsls_slim.csv"
raw = pd.read_csv(path, low_memory=False)
y_all = F.build_target(raw)
keep = y_all.notna()
X, y = F.training_frame(raw[keep]).reset_index(drop=True), y_all[keep].reset_index(drop=True)
K = y.nunique()
print(f"rows in file: {len(raw):,} | rows with a usable field label: {len(X):,} | fields: {K}")
print(y.value_counts().to_string(), "\n")

def class_weights(labels):
    vc = labels.value_counts()
    return {c: (len(labels) / (len(vc) * n)) ** CW_POWER for c, n in vc.items()}

def make_lr(labels):
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                         LogisticRegression(max_iter=4000, C=0.3, class_weight=class_weights(labels)))

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

def scores(p, cls, truth):
    return {"top1": accuracy_score(truth, cls[p.argmax(1)]),
            "top3": top_k_accuracy_score(truth, p, k=3, labels=cls),
            "top5": top_k_accuracy_score(truth, p, k=5, labels=cls)}
def show(name, m): print(f"{name:26s} top-1 {m['top1']:.3f} | top-3 {m['top3']:.3f} | top-5 {m['top5']:.3f}")

majority = yte.value_counts(normalize=True).max()
print(f"{'random guess':26s} top-1 {1/K:.3f} | top-3 {3/K:.3f} | top-5 {5/K:.3f}")
print(f"{'always biggest field':26s} top-1 {majority:.3f}")
lr = make_lr(ytr).fit(Xtr, ytr); p = lr.predict_proba(Xte); cls = lr.classes_
m_lr = scores(p, cls, yte); show("logistic regression", m_lr)
gb = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.05, max_depth=3,
                                    l2_regularization=1.0, random_state=42).fit(Xtr, ytr)
m_gb = scores(gb.predict_proba(Xte), gb.classes_, yte); show("gradient boosting (compare)", m_gb)

skf = StratifiedKFold(5, shuffle=True, random_state=42)
# cross_val_predict label-encodes y internally, so give it integer labels (same sorted order as class names)
names = np.array(sorted(y.unique())); yi = pd.Series(np.searchsorted(names, y.values))
pcv = cross_val_predict(make_lr(yi), X, yi, cv=skf, method="predict_proba")
m_cv = scores(pcv, np.arange(K), yi); show("5-fold CV (logistic reg.)", m_cv)
print()
print(classification_report(yte, cls[p.argmax(1)]))

cm = confusion_matrix(yte, cls[p.argmax(1)], labels=cls)
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 10)); cmn = cm / cm.sum(1, keepdims=True)
    ax.imshow(cmn, cmap="Blues"); ax.set_xticks(range(K)); ax.set_yticks(range(K))
    short = [c if len(c) < 24 else c[:22] + "…" for c in cls]
    ax.set_xticklabels(short, rotation=60, ha="right", fontsize=8); ax.set_yticklabels(short, fontsize=8)
    for i in range(K):
        for j in range(K): ax.text(j, i, f"{cmn[i,j]:.0%}", ha="center", va="center", fontsize=6)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title("Confusion matrix (row-normalised)")
    plt.tight_layout(); plt.savefig("confusion_matrix.png", dpi=150)
except Exception as e:
    print("skipping plot:", e)

# final model: refit on ALL labelled rows and export as plain JSON (no scikit-learn needed at runtime)
final = make_lr(y).fit(X, y)
imp_, sc_, clf_ = final.named_steps["simpleimputer"], final.named_steps["standardscaler"], final.named_steps["logisticregression"]
json.dump({"classes": list(clf_.classes_), "features": F.FEATURES, "medians": imp_.statistics_.tolist(),
           "mean": sc_.mean_.tolist(), "scale": sc_.scale_.tolist(),
           "coef": clf_.coef_.tolist(), "intercept": clf_.intercept_.tolist()}, open("model_lr.json", "w"))
json.dump({"n_fields": K, "classes": list(clf_.classes_), "holdout_logreg": m_lr, "holdout_gradient_boosting": m_gb,
           "cv5_logreg": m_cv, "biggest_class_rate": float(majority), "n_train_rows": int(len(X)),
           "class_counts": {k: int(v) for k, v in y.value_counts().items()}},
          open("model_meta.json", "w"), indent=2)
print("saved model_lr.json, model_meta.json, confusion_matrix.png")
