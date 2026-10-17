"""
Step 2 - Screening + documented cleaning for the two surviving datasets (HSLS:09, UCI).
READ-ONLY on datasets/original. Writes derived files to datasets/derived/ and logs to reports/.

  - HSLS: keep only columns collected BEFORE the field choice (9th grade 2009, 11th grade 2012,
          high-school transcript), drop post-high-school columns (leakage), map target to 7 fields.
  - UCI:  keep only pre-enrolment columns, map Course -> 7 fields.
  - Both: drop constant columns, drop students without a valid field, remove duplicate students.

Usage:  python scripts/02_screen.py        (HSLS read takes a few minutes: 1 GB file)
"""
import re, sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from field_map import FIELDS, CIP2_TO_FIELD, UCI_COURSE_TO_FIELD

ORIG, DER, REP = ROOT / "datasets" / "original", ROOT / "datasets" / "derived", ROOT / "reports"
DER.mkdir(parents=True, exist_ok=True)
LOG = []


def log(msg):
    LOG.append(f"- {msg}")
    print(msg)


def field_table(s, name):
    vc = s.value_counts()
    t = pd.DataFrame({"n": vc, "share": (vc / vc.sum()).round(3)}).reindex(FIELDS).fillna(0)
    print(f"\n{name}: n={int(vc.sum())}\n{t.to_string()}")
    return t


# =============================== HSLS:09 ===============================
def hsls():
    f = ORIG / "hsls09_16_student_pets_pear_v1_0.csv"
    print(f"\n{'='*30} HSLS:09 {'='*30}")
    cols = pd.read_csv(f, nrows=0).columns.tolist()

    # Column naming: <source letter><wave digit>... ; source X=composite, S=student, P=parent,
    # M/N=math/science teacher, A=administrator, C=counselor, W=weights. Wave 1=2009 (9th grade),
    # 2=2012 (11th grade), 3=2013 update (after HS) except X3T* = HS transcript, 4=2016, 5/6=PETS/PEAR.
    TARGETS = ["S3FIELD2", "S4FIELD2"]
    rows = []
    for c in cols:
        m = re.match(r"^([A-Z])(\d)", c)
        src, wave = (m.group(1), int(m.group(2))) if m else (None, None)
        if c == "STU_ID":
            g, why = "id", "student id"
        elif c in TARGETS:
            g, why = "target", "field of study (CIP-2)"
        elif src in ("X", "S") and wave in (1, 2):
            g, why = "allowed", "student/composite, 9th or 11th grade (before choice)"
        elif src == "X" and wave == 3 and c.startswith("X3T"):
            g, why = "allowed", "high-school transcript (before choice)"
        elif wave is not None and wave >= 3:
            g, why = "LEAKAGE", "collected after high school"
        elif src in ("P", "M", "N", "A", "C"):
            g, why = "excluded", "parent/teacher/school questionnaire - student cannot answer it"
        elif src == "W" or c.startswith("PSU") or c.startswith("STRAT"):
            g, why = "excluded", "survey design / weight"
        else:
            g, why = "excluded", "unclassified"
        rows.append((c, g, why))
    cmap = pd.DataFrame(rows, columns=["column", "group", "reason"])
    cmap.to_csv(REP / "02_hsls_columns.csv", index=False)
    print(cmap.group.value_counts().to_string())

    keep = cmap.loc[cmap.group.isin(["id", "target", "allowed"]), "column"].tolist()
    print(f"Reading {len(keep)} of {len(cols)} columns ... (this takes a while)")
    df = pd.read_csv(f, usecols=keep, low_memory=False)
    n0 = len(df)
    log(f"HSLS: read {n0} students; {len(keep)-3} pre-choice columns kept of {len(cols)} "
        f"(post-HS columns = leakage, parent/teacher/school + weights excluded; list in reports/02_hsls_columns.csv)")

    # constant columns (mostly -5 = suppressed in public-use file)
    feats = [c for c in keep if c not in TARGETS + ["STU_ID"]]
    const = [c for c in feats if df[c].nunique(dropna=False) <= 1]
    df = df.drop(columns=const)
    feats = [c for c in feats if c not in const]
    log(f"HSLS: dropped {len(const)} constant columns (public-use suppression -5 etc.) -> {len(feats)} features")

    # non-numeric columns (should be none in HSLS)
    obj = [c for c in feats if not pd.api.types.is_numeric_dtype(df[c])]
    if obj:
        log(f"HSLS: non-numeric columns found and dropped: {obj[:20]}")
        df = df.drop(columns=obj); feats = [c for c in feats if c not in obj]

    # targets: raw code distribution + mapping
    for t in TARGETS:
        raw = df[t].value_counts().sort_index()
        mapped = raw.index.map(lambda k: CIP2_TO_FIELD.get(k, "UNMAPPED" if k > 0 else "MISSING"))
        tab = pd.DataFrame({"code": raw.index, "n": raw.values, "field": [m if m else "DROPPED" for m in mapped]})
        tab.to_csv(REP / f"02_hsls_{t}_codes.csv", index=False)
        print(f"\n{t} code -> field:")
        print(tab.groupby("field")["n"].sum().sort_values(ascending=False).to_string())
        unm = tab[tab.field == "UNMAPPED"]
        if len(unm):
            print(f"!! UNMAPPED positive codes in {t}: {unm.code.tolist()} -> add to src/field_map.py")
        df[t + "_field"] = df[t].map(CIP2_TO_FIELD)

    # agreement 2013 vs 2016 (is the choice stable?)
    both = df.dropna(subset=["S3FIELD2_field", "S4FIELD2_field"])
    agree = (both.S3FIELD2_field == both.S4FIELD2_field).mean()
    print(f"\nS3 (2013) vs S4 (2016) field agreement, n={len(both)}: {agree:.3f}")
    pd.crosstab(both.S3FIELD2_field, both.S4FIELD2_field).to_csv(REP / "02_hsls_S3_vs_S4.csv")

    # primary target = S3FIELD2 (field right after high school, closest to the Pakistani use case)
    y = "S3FIELD2_field"
    miss = int((df.S3FIELD2 <= 0).sum())
    drop_code = int(((df.S3FIELD2 > 0) & df[y].isna()).sum())
    d = df[df[y].notna()].copy()
    log(f"HSLS: target = S3FIELD2 (2013, year after HS). Dropped {miss} with no field (not enrolled / "
        f"skip / nonresponse) and {drop_code} with undeclared/general/vocational codes -> {len(d)} students")

    # duplicates on features + target (ID excluded)
    dup = int(d.duplicated(subset=feats + [y]).sum())
    dupx = int(d.duplicated(subset=feats).sum())
    d = d.drop_duplicates(subset=feats + [y])
    log(f"HSLS: removed {dup} duplicate students (identical features+target); "
        f"{dupx} had identical features (incl. conflicting targets)")

    # missing-code share per feature (informative only)
    neg = (d[feats] < 0).mean().sort_values()
    print(f"\nFeatures by share of negative (missing/skip) codes: <10%: {(neg<.1).sum()}, "
          f"10-50%: {((neg>=.1)&(neg<.5)).sum()}, >=50%: {(neg>=.5).sum()}")

    out = d[["STU_ID"] + feats + [y, "S4FIELD2_field"]].rename(columns={y: "field", "S4FIELD2_field": "field_2016"})
    out.to_csv(DER / "hsls_prechoice.csv.gz", index=False)
    log(f"HSLS: wrote datasets/derived/hsls_prechoice.csv.gz ({len(out)} rows x {len(feats)} features)")
    t = field_table(out.field, "HSLS final field distribution")
    t.to_csv(REP / "02_hsls_field_counts.csv")


# =============================== UCI ===============================
def uci():
    print(f"\n{'='*30} UCI Dropout {'='*30}")
    df = pd.read_csv(ORIG / "uci_dropout_academic_success.csv", sep=None, engine="python", encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    log(f"UCI: read {len(df)} students; column names stripped of BOM/tab characters")
    PRE = ["Marital status", "Application mode", "Application order", "Previous qualification",
           "Previous qualification (grade)", "Nacionality", "Mother's qualification", "Father's qualification",
           "Mother's occupation", "Father's occupation", "Admission grade", "Displaced",
           "Educational special needs", "Gender", "Age at enrollment", "International"]
    LEAK = [c for c in df.columns if c not in PRE + ["Course"]]
    log(f"UCI: kept {len(PRE)} pre-enrolment columns; excluded {len(LEAK)}: {LEAK} "
        f"(post-enrolment, day/evening identifies course, macro = year, Target = dropout outcome)")
    unm = sorted(set(df.Course) - set(UCI_COURSE_TO_FIELD))
    if unm:
        print(f"!! UNMAPPED course codes: {unm}")
    df["field"] = df.Course.map(UCI_COURSE_TO_FIELD)
    d = df.dropna(subset=["field"])[PRE + ["field"]]
    dup = int(d.duplicated().sum())
    d = d.drop_duplicates()
    log(f"UCI: removed {dup} duplicate students (identical features+field) -> {len(d)}")
    d.to_csv(DER / "uci_prechoice.csv", index=False)
    log("UCI: wrote datasets/derived/uci_prechoice.csv")
    t = field_table(d.field, "UCI final field distribution")
    t.to_csv(REP / "02_uci_field_counts.csv")


if __name__ == "__main__":
    which = sys.argv[1:] or ["uci", "hsls"]
    if "uci" in which: uci()
    if "hsls" in which: hsls()
    with open(REP / "cleaning_log.md", "a", encoding="utf-8") as fh:
        fh.write(f"\n## Step 2 run {date.today()} (scripts/02_screen.py, mappings in src/field_map.py)\n")
        fh.write("\n".join(LOG) + "\n")
    print("\nLog appended to reports/cleaning_log.md")
