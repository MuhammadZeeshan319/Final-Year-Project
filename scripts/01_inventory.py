"""
Step 1 - Inventory + structural screening (checklist items 1, 2, 4, 5, 6 - first pass).
READ-ONLY: never writes to datasets/original. Records SHA-256 of every original file
so later steps can prove the originals were never modified.

Usage (from project root):
    python scripts/01_inventory.py
Output:
    console summary (paste this back)
    reports/01_inventory/<file>__<sheet>.txt   full per-table profile
    reports/original_hashes.csv                file fingerprints
"""
import hashlib, re, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "datasets" / "original"
OUT = ROOT / "reports" / "01_inventory"
OUT.mkdir(parents=True, exist_ok=True)

TARGET_HINTS = r"field|major|course|stream|career|degree|program|faculty|department|discipline|subject|study|job|profession|occupation|recommend|label|target|class"
ID_HINTS = r"(^id$|_id$|^id_|index|serial|^sr|^s\.?no|roll|timestamp|email|name|phone|cnic)"
FAKE_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "test.com")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_tables(p):
    ext = p.suffix.lower()
    if ext in (".csv", ".txt", ".tsv"):
        sep = "\t" if ext == ".tsv" else None
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return {"csv": pd.read_csv(p, sep=sep, engine="python", encoding=enc)}
            except UnicodeDecodeError:
                continue
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(p, sheet_name=None)
    if ext == ".json":
        return {"json": pd.read_json(p)}
    if ext == ".parquet":
        return {"parquet": pd.read_parquet(p)}
    return {}


def uniformity_flag(s):
    """Generated scores are often perfectly uniform. KS test vs uniform on [min,max]."""
    s = pd.to_numeric(s, errors="coerce").dropna()
    if len(s) < 50 or s.nunique() < 5:
        return None
    try:
        from scipy.stats import kstest
        lo, hi = s.min(), s.max()
        if hi == lo:
            return None
        p = kstest((s - lo) / (hi - lo), "uniform").pvalue
        return round(p, 4)
    except ImportError:
        return None


def profile(name, df):
    L = []
    w = L.append
    n, m = df.shape
    w(f"===== {name} =====")
    w(f"rows={n}  cols={m}")

    id_cols = [c for c in df.columns if re.search(ID_HINTS, str(c), re.I)]
    feat_cols = [c for c in df.columns if c not in id_cols]
    dup_exact = int(df.duplicated().sum())
    dup_noid = int(df[feat_cols].duplicated().sum()) if feat_cols else 0
    w(f"exact duplicate rows: {dup_exact} ({dup_exact/max(n,1):.1%})")
    w(f"duplicate rows ignoring ID/name/time cols {id_cols}: {dup_noid} ({dup_noid/max(n,1):.1%})")

    w("\n-- columns --")
    w(f"{'column':40s} {'dtype':10s} {'missing%':>8s} {'nuniq':>7s}  example / range  [uniform-p]")
    for c in df.columns:
        s = df[c]
        miss = s.isna().mean()
        nu = s.nunique(dropna=True)
        if pd.api.types.is_numeric_dtype(s):
            ex = f"[{s.min()} .. {s.max()}] mean={s.mean():.2f} sd={s.std():.2f}"
            up = uniformity_flag(s)
            if up is not None:
                ex += f"  [uniform-p={up}{' <-- looks UNIFORM' if up > 0.05 else ''}]"
        else:
            top = s.astype(str).value_counts().head(3).index.tolist()
            ex = " | ".join(t[:25] for t in top)
        w(f"{str(c)[:40]:40s} {str(s.dtype)[:10]:10s} {miss:8.1%} {nu:7d}  {ex}")

    w("\n-- candidate TARGET columns (name matches field/major/career/...) --")
    tcols = [c for c in df.columns if re.search(TARGET_HINTS, str(c), re.I)]
    for c in tcols:
        vc = df[c].astype(str).value_counts()
        w(f"\n[{c}]  {len(vc)} classes; largest = {vc.iloc[0]/n:.1%}")
        for k, v in vc.head(40).items():
            w(f"    {v:6d}  {k[:70]}")
        if len(vc) > 40:
            w(f"    ... {len(vc)-40} more classes")

    w("\n-- generated-data signals --")
    for c in df.columns:
        if re.search("email", str(c), re.I):
            dom = df[c].astype(str).str.split("@").str[-1].str.lower()
            fake = dom.isin(FAKE_EMAIL_DOMAINS).mean()
            w(f"email col {c}: top domains {dom.value_counts().head(5).to_dict()}  fake-domain share={fake:.1%}")
        if re.search("name", str(c), re.I) and df[c].dtype == object:
            w(f"name col {c}: {df[c].nunique()} unique of {n}; sample {df[c].dropna().astype(str).head(5).tolist()}")
    const = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
    w(f"constant columns: {const}")
    near_unique = [c for c in df.columns if df[c].nunique() > 0.95 * n and c not in id_cols]
    w(f"near-unique non-ID columns (possible IDs / free text): {near_unique}")

    w("\n-- first 5 rows --")
    with pd.option_context("display.max_columns", 50, "display.width", 250):
        w(df.head().to_string())

    summary = dict(table=name, rows=n, cols=m, dup_exact=dup_exact, dup_noid=dup_noid,
                   target_candidates=";".join(map(str, tcols))[:80])
    return "\n".join(L), summary


def compact(text):
    """Short version for pasting: header, target candidates (top 15 classes), generated-data signals."""
    keep, out, n_cls = True, [], 0
    for line in text.splitlines():
        if line.startswith("-- columns --") or line.startswith("-- first 5 rows"):
            keep = False
        elif line.startswith("-- candidate TARGET") or line.startswith("-- generated-data"):
            keep = True
        if not keep:
            continue
        if line.startswith("["):
            n_cls = 0
        elif line.startswith("    ") and not line.strip().startswith("..."):
            n_cls += 1
            if n_cls > 15:
                continue
        out.append(line[:300])
    return "\n".join(out)


def main():
    if not ORIG.exists():
        sys.exit(f"Put datasets in {ORIG}")
    only = set(sys.argv[1:])  # optional: python scripts/01_inventory.py newfile.csv other.xlsx
    all_files = sorted(p for p in ORIG.rglob("*") if p.is_file())
    if "--new" in only:  # only files not yet fingerprinted in reports/original_hashes.csv
        hp0 = ROOT / "reports" / "original_hashes.csv"
        seen = set(pd.read_csv(hp0)["file"]) if hp0.exists() else set()
        files = [p for p in all_files if p.relative_to(ORIG).as_posix() not in seen]
        only = {"--new"}
    else:
        files = [p for p in all_files
                 if not only or {p.name, p.stem, p.relative_to(ORIG).as_posix()} & only]
    if not files:
        sys.exit(f"No files matched {sorted(only)} in {ORIG}. Available: "
                 f"{sorted(p.name for p in ORIG.rglob('*') if p.is_file())}")
    hashes, summaries = [], []
    for p in files:
        rel = p.relative_to(ORIG).as_posix()
        hashes.append(dict(file=rel, bytes=p.stat().st_size, sha256=sha256(p)))
        try:
            tables = load_tables(p)
        except Exception as e:
            print(f"!! could not read {rel}: {e}")
            continue
        if not tables:
            print(f"-- skipped (unsupported type): {rel}")
            continue
        for sheet, df in tables.items():
            name = f"{rel}::{sheet}"
            text, s = profile(name, df)
            safe = re.sub(r"[^\w.-]+", "_", name)
            (OUT / f"{safe}.txt").write_text(text, encoding="utf-8")
            summaries.append(s)
            print(compact(text))  # full profile is in the .txt file
            print("\n" + "#" * 100 + "\n")

    hp = ROOT / "reports" / "original_hashes.csv"
    new = pd.DataFrame(hashes)
    if hp.exists():  # verify originals unchanged since first run; keep hashes of files not re-scanned
        old_df = pd.read_csv(hp)
        old = old_df.set_index("file")["sha256"]
        for h in hashes:
            if h["file"] in old and old[h["file"]] != h["sha256"]:
                print(f"!!! ORIGINAL FILE CHANGED: {h['file']}")
        new = pd.concat([old_df[~old_df.file.isin(new.file)], new])
    new.to_csv(hp, index=False)

    print("=" * 30, "SUMMARY", "=" * 30)
    with pd.option_context("display.width", 250, "display.max_colwidth", 80):
        print(pd.DataFrame(summaries).to_string(index=False))


if __name__ == "__main__":
    main()
