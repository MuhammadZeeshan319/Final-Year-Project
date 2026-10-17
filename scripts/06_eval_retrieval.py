"""
Step 6 - Retrieval evaluation for program recommendation (proposal sec 19: Retrieval Accuracy, Recall@K).

Test cases: for every career in the curated bank (43), simulate a CONSISTENT student - for each career question
pick the option that gives that career the most points. The query is built exactly as the app builds it.
Ground truth = the programs the curated bank links to that career (written independently of the documents).

Reported for (a) pure semantic similarity and (b) the app's hybrid score (similarity + priors):
  Hit@1, Hit@3   - a correct program is ranked 1st / in the top 3
  Recall@5       - share of the career's programs found in the top 5
  MRR            - mean reciprocal rank of the first correct program
  (c) answers only: the query has NO career names - just the field and the chosen answer texts.
      This is the most honest test of the retriever; (a) and (b) contain the career title, and the draft
      documents list careers by name, so they are easy by construction.
Caveat: (b) uses the rules' career ranking as a prior, and that ranking comes from the same curated bank,
so (b) is optimistic; (a) is the honest measure of the retriever itself.

Usage:  python scripts/06_eval_retrieval.py
        set EDUPATH_EMBEDDINGS=st   to evaluate Sentence Transformers instead of TF-IDF
"""
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("EDUPATH_LLM", "off")
import careers as C  # noqa: E402
import rag  # noqa: E402
from career_bank import BANK  # noqa: E402


def consistent_answers(field, career_id):
    ans = {}
    for q in BANK[field]["questions"]:
        best = max(q["options"], key=lambda o: o["points"].get(career_id, 0))
        if best["points"].get(career_id, 0) > 0:
            ans[q["id"]] = best["label"]
    return ans


def metrics(ranked_ids, truth):
    first = next((i for i, pid in enumerate(ranked_ids) if pid in truth), None)
    return {"hit1": float(first == 0), "hit3": float(first is not None and first < 3),
            "recall5": len(set(ranked_ids[:5]) & truth) / len(truth),
            "mrr": 0.0 if first is None else 1.0 / (first + 1)}


def main():
    rows = {"similarity only": [], "hybrid (app)": [], "answers only (hard)": []}
    per_field = {}
    for field, bank in BANK.items():
        for cid, career in bank["careers"].items():
            ans = consistent_answers(field, cid)
            ranked = C.score(field, ans)
            truth = set(career["programs"])
            query = rag.build_query(field, ranked, ans)
            sims = rag.INDEX.sims(query)
            by_sim = [rag.DOCS[i]["id"] for i in np.argsort(-sims)]
            hybrid = [h["doc"]["id"] for h in rag.retrieve(query, field, ranked, k=len(rag.DOCS))]
            m = metrics(by_sim, truth)
            rows["similarity only"].append(m)
            rows["hybrid (app)"].append(metrics(hybrid, truth))
            # hard setting: no career names in the query - only the field and the student's answer texts
            hard_q = ". ".join([field] + list(ans.values()))
            hard = [rag.DOCS[i]["id"] for i in np.argsort(-rag.INDEX.sims(hard_q))]
            rows["answers only (hard)"].append(metrics(hard, truth))
            per_field.setdefault(field, []).append(m)

    n = len(rows["similarity only"])
    print(f"Retriever: {rag.INDEX.name} | documents: {len(rag.DOCS)} | test careers: {n}\n")
    print(f"{'setting':18s} {'Hit@1':>7s} {'Hit@3':>7s} {'Recall@5':>9s} {'MRR':>6s}")
    for name, ms in rows.items():
        avg = {k: np.mean([m[k] for m in ms]) for k in ms[0]}
        print(f"{name:18s} {avg['hit1']:7.3f} {avg['hit3']:7.3f} {avg['recall5']:9.3f} {avg['mrr']:6.3f}")
    print("\nSimilarity-only Hit@3 by field:")
    for f, ms in per_field.items():
        print(f"  {f:28s} {np.mean([m['hit3'] for m in ms]):.2f}  ({len(ms)} careers)")
    print(f"\nRandom baseline Hit@3 (3 of {len(rag.DOCS)} documents, ~1.4 correct each): "
          f"~{1 - np.prod([(len(rag.DOCS) - 1.4 - i) / (len(rag.DOCS) - i) for i in range(3)]):.3f}")


if __name__ == "__main__":
    main()
