"""
Step 7 - RAG faithfulness + response time (proposal sec 19: RAG Faithfulness, Response Time).

Runs the REAL configured LLM (default: local Ollama) on 50 student profiles:
  - 43 "consistent" students, one per career (same construction as 06_eval_retrieval.py)
  - 7 students who also describe themselves in their own words (one per field)
For every program explanation the LLM writes, automatic checks:
  kept / dropped     - reasons blocked by the grounding rule (claims about the student without citing a real answer)
  cross-program      - the reason names a DIFFERENT program (e.g. "BS AI is more relevant") - off-task
  unsupported facts  - mentions %, fees, Rs or universities that are not in the program document
  support            - share of the reason's content words found in the program document or the cited answer
                       (< 0.6 = weakly supported; a rough lexical proxy, not proof)
Response time: wall time of every LLM call (program explanation; next-question choice), p50 / p95 / max.

Automatic checks are a proxy. True faithfulness needs people: the script writes every AI reason to
reports/07_rag_review.csv with empty 'human_faithful' / 'human_notes' columns - have 2 team members rate a
random 30 independently, then report agreement and the faithful rate.

Usage: (Ollama running with the model pulled)   python scripts/07_eval_rag.py
       other model:  $env:EDUPATH_OLLAMA_MODEL="qwen2.5:7b"; python scripts/07_eval_rag.py
"""
import csv
import re
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import careers as C  # noqa: E402
import llm  # noqa: E402
import rag  # noqa: E402
from career_bank import BANK, PROGRAMS  # noqa: E402

REP = ROOT / "reports"
FREE_TEXT = {
    "Medical & Health": "I want to help people recover from sports injuries",
    "Engineering & Tech": "I like fixing cars and motorbikes",
    "CS & IT": "I want to build mobile apps for small businesses",
    "Business": "I want to open my own clothing brand",
    "Natural Sciences": "I care about climate change and pollution in Lahore",
    "Social Sci/Law/Psych": "I want to help people who are going through depression",
    "Education/Humanities/Arts": "I love making short videos and animations",
}
STOP = set("""the and for with this that your you are from will which into about also more than their them they
have has had been being program programs degree study studies offers offer covers cover covering focus focuses
focused aligns align aligned match matches matching suits suit interest interests career careers well make makes
good great strong would could can may might help helps provide provides including include includes such like
area areas field fields skills skill option options related broader students student""".split())
UNSUPPORTED = re.compile(r"\d+\s*%|\brs\.?\s*\d|\bfees?\b|\btuition|\buniversit", re.I)


def consistent_answers(field, career_id):
    ans = {}
    for q in BANK[field]["questions"]:
        best = max(q["options"], key=lambda o: o["points"].get(career_id, 0))
        if best["points"].get(career_id, 0) > 0:
            ans[q["id"]] = best["label"]
    return ans


def words(text):
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in STOP}


def check(card, fact, doc_text, other_names):
    reason = card["reason"]
    content = words(reason) - words(fact or "")
    support = len(content & words(doc_text)) / len(content) if content else 1.0
    flags = []
    if any(n.lower() in reason.lower() for n in other_names):
        flags.append("cross-program")
    m = UNSUPPORTED.search(reason)
    if m and m.group(0).lower() not in doc_text.lower():
        flags.append("unsupported-fact")
    if support < 0.6:
        flags.append("weak-support")
    return support, flags


def pct(a, q):
    return float(np.percentile(a, q)) if a else float("nan")


def main():
    st = llm.status()
    if not st["enabled"]:
        sys.exit(f"LLM not available ({st}). Start Ollama and pull the model, or set EDUPATH_LLM.")
    print(f"LLM: {st['provider']} / {st['model']} | retrieval: {rag.INDEX.name}")

    cases = []
    for field, bank in BANK.items():
        for cid, career in bank["careers"].items():
            group = PROGRAMS[career["programs"][0]]["accepted"][0]  # a group that can enter the career
            cases.append((f"{field} / {career['title']}", field, consistent_answers(field, cid), group, None))
        cid0 = next(iter(bank["careers"]))
        cases.append((f"{field} / own words", field, consistent_answers(field, cid0),
                      PROGRAMS[bank["careers"][cid0]["programs"][0]]["accepted"][0], FREE_TEXT[field]))

    rows, t_prog, t_q, n_calls_ok, q_llm = [], [], [], 0, 0
    tot = {"proposed": 0, "kept": 0, "dropped_claims": 0, "dropped_offtask": 0, "invalid": 0, "shown": 0}
    for i, (name, field, ans, group, text) in enumerate(cases, 1):
        ranked = C.score(field, ans)
        rec = rag.recommend(field, ranked, ans, group, {}, text)
        L = dict(llm.LAST)
        if L.get("called"):
            t_prog.append(L["seconds"])
            n_calls_ok += bool(L.get("ok"))
            for k in ("proposed", "kept", "dropped_claims", "dropped_offtask", "invalid"):
                tot[k] += L.get(k, 0)
        tot["shown"] += len(rec["programs"])
        names = [p["name"] for p in rec["programs"]]
        for p in rec["programs"]:
            if p["reason_source"] != "llm":
                continue
            doc = rag.DOC_BY_ID[p["id"]]["text"]
            support, flags = check(p, p.get("matches_answer"), doc, [n for n in names if n != p["name"]])
            rows.append({"profile": name, "program": p["name"], "cited_answer": p.get("matches_answer") or "",
                         "reason": p["reason"], "support": round(support, 2), "auto_flags": ";".join(flags),
                         "human_faithful": "", "human_notes": ""})
        # next-question choice latency (second question of the career flow)
        first = next(iter(ans.items()), None)
        if first:
            cands = C.candidates(field, dict([first]))
            if cands:
                pick = llm.choose(field, C.score(field, dict([first])), [], cands[:4])
                if llm.LAST.get("called"):
                    t_q.append(llm.LAST["seconds"])
                    q_llm += pick is not None
        print(f"[{i:2d}/{len(cases)}] {name:55s} prog-call {L.get('seconds', 0):5.1f}s  kept {L.get('kept', 0)}/{L.get('proposed', 0)}")

    n = len(rows)
    flag = lambda f: sum(f in r["auto_flags"] for r in rows)  # noqa: E731
    summary = [
        f"# RAG faithfulness & response time ({date.today()})", "",
        f"LLM: {st['provider']} / {st['model']} · retrieval: {rag.INDEX.name} · profiles: {len(cases)}", "",
        "## Program explanations",
        f"- LLM calls succeeded: {n_calls_ok}/{len(t_prog)}",
        f"- Reasons proposed by the LLM: {tot['proposed']} · kept: {tot['kept']} · blocked for unsupported claims "
        f"about the student: {tot['dropped_claims']} · blocked as off-task: {tot['dropped_offtask']} · invalid (wrong id / duplicate / length): {tot['invalid']}",
        f"- Coverage: {tot['kept']}/{tot['shown']} programs shown ({tot['kept'] / max(tot['shown'], 1):.0%}) got an AI explanation; the rest use rule-based reasons",
        f"- Of the {n} AI reasons shown: cross-program mentions {flag('cross-program')} ({flag('cross-program') / max(n, 1):.0%}), "
        f"unsupported facts {flag('unsupported-fact')} ({flag('unsupported-fact') / max(n, 1):.0%}), "
        f"weak lexical support {flag('weak-support')} ({flag('weak-support') / max(n, 1):.0%})",
        f"- Mean lexical support: {np.mean([r['support'] for r in rows]) if rows else float('nan'):.2f}", "",
        "## Response time (seconds per LLM call)",
        f"- Program explanation: p50 {pct(t_prog, 50):.1f} · p95 {pct(t_prog, 95):.1f} · max {max(t_prog, default=float('nan')):.1f}",
        f"- Next-question choice: p50 {pct(t_q, 50):.1f} · p95 {pct(t_q, 95):.1f} · max {max(t_q, default=float('nan')):.1f} "
        f"· LLM choice accepted {q_llm}/{len(t_q)}", "",
        "Automatic checks are proxies. Human rating sheet: reports/07_rag_review.csv",
    ]
    REP.mkdir(exist_ok=True)
    (REP / "07_rag_eval.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    with open(REP / "07_rag_review.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["profile"])
        w.writeheader(); w.writerows(rows)
    print("\n" + "\n".join(summary))


if __name__ == "__main__":
    main()
