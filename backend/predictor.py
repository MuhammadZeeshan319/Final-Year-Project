"""
Pure-Python inference (no numpy / pandas / scikit-learn needed at runtime).
Reads model_lr.json written by train_model.py and mirrors features.row_from_answers().
"""
import json, math

_M = json.load(open("model_lr.json"))
CLASSES, FEATURES = _M["classes"], _M["features"]
OCC_CODES = [11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 39, 41, 45, 47, 49, 51, 53, 55, 98]
NAN = float("nan")

def _num(v):
    return float(v) if v not in (None, "") else NAN

def build_row(a):
    """Web-form answers -> feature vector in the exact order saved at training time."""
    occ = a.get("occupation")
    occ = int(occ) if occ not in (None, "") else -1
    row = []
    for f in FEATURES:
        if f.startswith(("gpa_", "lvl_")):
            row.append(_num(a.get(f)))                     # blank -> NaN -> training median
        elif f.startswith("act_"):
            row.append(1.0 if a.get(f) else 0.0)
        elif f == "occ_other":
            row.append(0.0 if occ in OCC_CODES else 1.0)
        else:                                              # occ_<code>
            row.append(1.0 if f == f"occ_{occ}" else 0.0)
    return row

def predict_proba(answers):
    x = build_row(answers)
    z = []
    for v, med, mu, sd in zip(x, _M["medians"], _M["mean"], _M["scale"]):
        v = med if v != v else v          # NaN -> training median
        z.append((v - mu) / sd)
    logits = [sum(w * zi for w, zi in zip(ws, z)) + b for ws, b in zip(_M["coef"], _M["intercept"])]
    m = max(logits); e = [math.exp(l - m) for l in logits]; t = sum(e)
    return [v / t for v in e]
