"""
Career stage - deterministic rules engine (the "rules" half of the hybrid).

  scores      : each answered option adds its points to careers (career_bank.py)
  match %     : points earned / points that career could have earned on the questions asked
  next question (rules): the unanswered question that best separates the current top careers
  stop        : after MAX_QUESTIONS, or once MIN_QUESTIONS are answered and the leader is clear
  programs    : from the top careers, with the usual entry requirement checked against the
                student's intermediate group

The LLM (llm.py) may only choose among the candidate questions this module offers and rephrase
the chosen one; it never touches scores, rankings or programs.
"""
from statistics import pstdev

from career_bank import BANK, PROGRAMS
import career_extra  # noqa: F401  (adds min_pct to PROGRAMS; skill lists)

MIN_QUESTIONS, MAX_QUESTIONS, CLEAR_LEAD = 3, 5, 0.25


def fields():
    return list(BANK)


def _bank(field):
    if field not in BANK:
        raise KeyError(field)
    return BANK[field]


def validate_answers(field, answers):
    """answers: {question_id: option label}. Raises ValueError on unknown ids/labels."""
    qs = {q["id"]: q for q in _bank(field)["questions"]}
    for qid, label in answers.items():
        if qid not in qs:
            raise ValueError(f"unknown question {qid!r}")
        if label not in [o["label"] for o in qs[qid]["options"]]:
            raise ValueError(f"{qid}: unknown option {label!r}")


def score(field, answers):
    bank = _bank(field)
    careers = bank["careers"]
    got = {c: 0.0 for c in careers}
    possible = {c: 0.0 for c in careers}
    why = {c: [] for c in careers}
    for q in bank["questions"]:
        if q["id"] not in answers:
            continue
        for c in careers:
            possible[c] += max(o["points"].get(c, 0) for o in q["options"])
        chosen = next(o for o in q["options"] if o["label"] == answers[q["id"]])
        for c, pts in chosen["points"].items():
            got[c] += pts
            why[c].append({"question": q["text"], "answer": chosen["label"], "points": pts})
    ranked = []
    for c, meta in careers.items():
        match = got[c] / possible[c] if possible[c] else 0.0
        ranked.append({"id": c, "title": meta["title"], "desc": meta["desc"], "points": got[c],
                       "match": round(match, 3), "reasons": sorted(why[c], key=lambda r: -r["points"])})
    # rank by points earned, then by match (ties broken by bank order)
    ranked.sort(key=lambda r: (-r["points"], -r["match"]))
    return ranked


def candidates(field, answers, k=3):
    """Unanswered questions, ordered by how well they separate the current top-k careers (rules choice first)."""
    bank = _bank(field)
    ranked = score(field, answers)
    top = [r["id"] for r in ranked[:k]] if answers else list(bank["careers"])
    out = []
    for i, q in enumerate(bank["questions"]):
        if q["id"] in answers:
            continue
        # spread of points across the top careers, averaged over the options
        spread = sum(pstdev([o["points"].get(c, 0) for c in top]) for o in q["options"]) / len(q["options"])
        out.append((round(spread, 4), -i, q))
    out.sort(key=lambda t: (-t[0], -t[1]))
    return [q for _, _, q in out]


def is_done(field, answers):
    n = len(answers)
    if n >= MAX_QUESTIONS or n >= len(_bank(field)["questions"]):
        return True
    if n < MIN_QUESTIONS:
        return False
    r = score(field, answers)
    return len(r) > 1 and (r[0]["match"] - r[1]["match"]) >= CLEAR_LEAD and r[0]["points"] > r[1]["points"]


def eligibility(program_id, inter_group, marks=None):
    """eligible | conditional (extra courses) | not_usual (group) | below_marks | unknown (no group given).
    Group comes first: a program not open to the group is not_usual whatever the marks."""
    p = PROGRAMS[program_id]
    if not inter_group:
        status = "unknown"
    elif inter_group in p["accepted"]:
        status = "eligible"
    elif inter_group in p["conditional"]:
        status = "conditional"
    else:
        return "not_usual"
    if marks is not None and marks < p["min_pct"]:
        return "below_marks"
    return status


def programs(field, ranked, inter_group=None, top_n=3):
    """Programs for the top careers; a program's score is the best match of any career that leads to it."""
    bank = _bank(field)
    seen = {}
    for r in ranked[:top_n]:
        for pid in bank["careers"][r["id"]]["programs"]:
            if pid not in seen or r["match"] > seen[pid]["match"]:
                p = PROGRAMS[pid]
                seen[pid] = {"id": pid, "name": p["name"], "years": p["years"], "test": p["test"],
                             "note": p["note"], "accepted": p["accepted"], "conditional": p["conditional"],
                             "match": r["match"], "for_career": r["title"],
                             "eligibility": eligibility(pid, inter_group)}
    order = {"eligible": 0, "conditional": 1, "unknown": 1, "not_usual": 2, "below_marks": 2}
    return sorted(seen.values(), key=lambda p: (order[p["eligibility"]], -p["match"]))
