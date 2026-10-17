"""
Program recommendation - Retrieval-Augmented Generation.

  1. PROFILE   field + top career + career answers + questionnaire answers (+ optional free text)
  2. RETRIEVE  semantic search over the program knowledge base (backend/knowledge/programs/*.md)
               embeddings: Sentence Transformers if installed (all-MiniLM-L6-v2), else TF-IDF
               hybrid score = cosine similarity + small documented priors (same field, leads to top career)
  3. FILTER    eligibility rules (intermediate group) - programs not usual for the group move to "other options"
  4. GENERATE  LLM ranks ONLY the retrieved, eligible programs and explains each from its document
               (llm.rank_programs). Invalid / missing LLM output -> retrieval order + rule-based reasons.

Nothing here invents programs: every recommendation is a document in the knowledge base.
"""
import os
import re
from pathlib import Path

import numpy as np

from career_bank import BANK, PROGRAMS
import careers as C
import llm

KB_DIR = Path(__file__).resolve().parent / "knowledge" / "programs"
PRIOR_SAME_FIELD, PRIOR_TOP_CAREER, PRIOR_OTHER_CAREER = 0.10, 0.15, 0.05
N_CANDIDATES, N_SHOW = 8, 6


# ---------------- knowledge base ----------------
def load_docs(kb_dir=KB_DIR):
    docs = []
    for path in sorted(kb_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        head, *sections = re.split(r"^## +", text, flags=re.M)
        header = dict(re.findall(r"^(\w+):[ \t]*(.*)$", head, flags=re.M))
        for sec in sections:
            pid, _, body = sec.partition("\n")
            d = {"id": pid.strip(), "field": header.get("field", ""),
                 "source": header.get("source", ""), "verified": header.get("verified", "") or None}
            d.update({k: v.strip() for k, v in re.findall(r"^(\w+):[ \t]*(.*)$", body, flags=re.M)})
            if d["id"] not in PROGRAMS:
                raise ValueError(f"{path.name}: program id {d['id']!r} is not in career_bank.PROGRAMS")
            d["text"] = ". ".join(d.get(k, "") for k in ("name", "summary", "studies", "skills", "careers", "suits"))
            docs.append(d)
    missing = set(PROGRAMS) - {d["id"] for d in docs}
    if missing:
        raise ValueError(f"knowledge base is missing documents for: {sorted(missing)}")
    return docs


DOCS = load_docs()
DOC_BY_ID = {d["id"]: d for d in DOCS}


# ---------------- embeddings ----------------
class _Tfidf:
    name = "TF-IDF (word + bigram)"

    def __init__(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        self.M = self.vec.fit_transform(texts)

    def sims(self, query):
        q = self.vec.transform([query])
        return (self.M @ q.T).toarray().ravel()  # rows are L2-normalised -> cosine


class _SentenceTransformer:
    name = "Sentence Transformers (all-MiniLM-L6-v2)"

    def __init__(self, texts):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(os.getenv("EDUPATH_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
        self.M = self.model.encode(texts, normalize_embeddings=True)

    def sims(self, query):
        return self.M @ self.model.encode([query], normalize_embeddings=True)[0]


def _make_index(texts):
    choice = os.getenv("EDUPATH_EMBEDDINGS", "auto").lower()  # auto | st | tfidf
    if choice in ("auto", "st"):
        try:
            return _SentenceTransformer(texts)
        except Exception as e:  # not installed / no model download -> TF-IDF
            if choice == "st":
                raise
            print(f"[rag] Sentence Transformers unavailable ({type(e).__name__}); using TF-IDF")
    return _Tfidf(texts)


INDEX = _make_index([d["text"] for d in DOCS])


# ---------------- program profile (asked on the Program Recommendation page) ----------------
# Each option may add search words (query expansion), a ranking penalty for clashing programs, and a fact the
# LLM may cite. Effects are deliberately small and documented so the ranking stays explainable.
PREF_QUESTIONS = [
    {"id": "years", "text": "How many years are you willing to study for your first degree?",
     "options": ["4 years", "5 years is fine", "Either is fine"]},
    {"id": "entry_test", "text": "Are you willing to take an entry test such as MDCAT, ECAT or LAT?",
     "options": ["Yes", "I'd rather not", "Not sure yet"]},
    {"id": "style", "text": "How do you like to learn?",
     "options": ["Theory and ideas", "Hands-on and practical", "A mix of both"]},
    {"id": "priority", "text": "What matters most to you in a degree?",
     "options": ["Good job opportunities", "Research and higher study", "Creativity and design", "Helping people"]},
    {"id": "after", "text": "What do you want to do after graduating?",
     "options": ["Get a job", "Continue to MS / MPhil", "Start my own business", "Not sure yet"]},
]
PREF_WORDS = {  # query expansion
    "Theory and ideas": "theory research analysis",
    "Hands-on and practical": "practical hands-on lab projects studio clinical practice",
    "Good job opportunities": "careers jobs industry",
    "Research and higher study": "research further study PhD",
    "Creativity and design": "creative creativity design",
    "Helping people": "helping people patients community care",
    "Continue to MS / MPhil": "research further study",
    "Start my own business": "business entrepreneur",
}
PREF_PENALTY = 0.08
PREF_IDS = {q["id"]: set(q["options"]) for q in PREF_QUESTIONS}


def validate_prefs(prefs):
    for k, v in (prefs or {}).items():
        if k not in PREF_IDS or v not in PREF_IDS[k]:
            raise ValueError(f"program preference {k!r}: unknown value {v!r}")


def _pref_effects(doc_id, prefs):
    """(penalty, notes) for one program given the student's program profile."""
    p, prefs, pen, notes = PROGRAMS[doc_id], prefs or {}, 0.0, []
    if prefs.get("years") == "4 years" and p["years"] > 4:
        pen += PREF_PENALTY
        notes.append(f"{p['years']}-year program - longer than the 4 years you prefer")
    if p["test"]:
        if prefs.get("entry_test") == "I'd rather not":
            pen += PREF_PENALTY
            notes.append(f"Needs an entry test ({p['test']}) - you said you'd rather not take one")
        elif prefs.get("entry_test") == "Not sure yet":
            notes.append(f"Needs an entry test ({p['test']})")
    return pen, notes


# ---------------- profile -> query ----------------
SKIP = {"I don't know yet", "I don't know", "Other"}


def build_query(field, ranked_careers, career_answers, profile=None, free_text=None, prefs=None):
    profile = profile or {}
    parts = [field]
    if ranked_careers:
        top = ranked_careers[0]
        parts += [top["title"], top["title"], top["desc"]]  # top career weighted twice
        parts += [c["title"] for c in ranked_careers[1:3]]
    parts += list(career_answers.values())
    for k in ("fav_subject", "career"):
        v = profile.get(k)
        if v and v not in SKIP:
            parts.append(v)
    parts += [PREF_WORDS[v] for v in (prefs or {}).values() if v in PREF_WORDS]
    if free_text:
        parts += [free_text.strip()[:500]] * 2  # the student's own words weigh more
    return ". ".join(p for p in parts if p)


def student_facts(field, ranked_careers, career_answers, profile=None, free_text=None, prefs=None):
    """The ONLY statements the LLM may make about the student: their real answers, in plain words."""
    profile = profile or {}
    facts = []
    if ranked_careers and ranked_careers[0]["points"] > 0:
        facts.append(f"Top career match from your answers: {ranked_careers[0]['title']}")
    qtext = {q["id"]: q["text"] for q in BANK.get(field, {}).get("questions", [])}
    facts += [f"{qtext.get(qid, qid)} -> {ans}" for qid, ans in career_answers.items()]
    if profile.get("fav_subject") and profile["fav_subject"] not in SKIP:
        facts.append(f"Favourite subject: {profile['fav_subject']}")
    if profile.get("career") and profile["career"] not in SKIP:
        facts.append(f"Job wanted at age 30: {profile['career']}")
    ptext = {q["id"]: q["text"] for q in PREF_QUESTIONS}
    facts += [f"{ptext[k]} -> {v}" for k, v in (prefs or {}).items() if k in ptext]
    if free_text and free_text.strip():
        facts.append(f"In your own words: {free_text.strip()[:300]}")
    return facts


# ---------------- retrieve + filter + generate ----------------
def retrieve(query, field=None, ranked_careers=None, k=N_CANDIDATES):
    sims = INDEX.sims(query)
    career_progs = {}
    if field in BANK and ranked_careers:
        for i, r in enumerate(ranked_careers[:3]):
            for pid in BANK[field]["careers"][r["id"]]["programs"]:
                career_progs.setdefault(pid, (i, r["title"]))
    out = []
    for d, s in zip(DOCS, sims):
        prior = PRIOR_SAME_FIELD if d["field"] == field else 0.0
        link = career_progs.get(d["id"])
        if link:
            prior += PRIOR_TOP_CAREER if link[0] == 0 else PRIOR_OTHER_CAREER
        out.append({"doc": d, "similarity": float(s), "score": float(s) + prior,
                    "for_career": link[1] if link else None})
    out.sort(key=lambda x: -x["score"])
    return out[:k]


def _rule_reason(hit, top_career):
    d = hit["doc"]
    studies = ", ".join(d.get("studies", "").split(", ")[:3])
    if hit.get("from_words"):
        return f"Matches what you wrote about yourself. You would study {studies}."
    if hit["for_career"] and hit["for_career"] == top_career:
        return f"Leads directly to your top career ({top_career}). You would study {studies}."
    if hit["for_career"]:
        return f"Leads to {hit['for_career']}, one of your matching careers. You would study {studies}."
    return f"Close match to your interests and answers. You would study {studies}."


def _card(hit, inter_group, rank, reason, reason_source, marks=None):
    d, p = hit["doc"], PROGRAMS[hit["doc"]["id"]]
    return {"id": d["id"], "rank": rank, "name": p["name"], "field": d["field"], "years": p["years"],
            "test": p["test"], "note": p["note"], "accepted": p["accepted"], "conditional": p["conditional"],
            "eligibility": C.eligibility(d["id"], inter_group, marks), "min_pct": p["min_pct"], "for_career": hit["for_career"],
            "similarity": round(hit["similarity"], 3), "score": round(hit["score"], 3),
            "reason": reason, "reason_source": reason_source, "pref_notes": hit.get("pref_notes", []),
            "doc": {"summary": d.get("summary"), "studies": d.get("studies"), "careers": d.get("careers"),
                    "source": d.get("source"), "verified": d.get("verified")}}


REL_MIN = 0.35   # a program is "relevant" if its similarity is >= 35% of the best match (or it leads to a top career)
ALT_MIN = 0.02   # alternatives open to the student's group need at least this similarity


def recommend(field, ranked_careers, career_answers, inter_group=None, profile=None, free_text=None, marks=None,
              prefs=None):
    validate_prefs(prefs)
    query = build_query(field, ranked_careers, career_answers, profile, free_text, prefs)
    hits = retrieve(query, field, ranked_careers, k=12)
    for h in hits:  # program-profile effects: small penalty + a visible note
        pen, notes = _pref_effects(h["doc"]["id"], prefs)
        h["score"] -= pen
        h["pref_notes"] = notes
    hits.sort(key=lambda h: -h["score"])
    best = max((h["similarity"] for h in hits), default=0.0)
    elig = lambda h: C.eligibility(h["doc"]["id"], inter_group, marks)  # noqa: E731
    blocked = ("not_usual", "below_marks")

    # Main list: RELEVANT programs only, whatever the eligibility (shown as a badge). Unrelated programs are
    # never promoted just because the student can enter them - that produced absurd matches before.
    # Programs the student can't normally enter stay only if they lead to one of the student's careers
    # (so the student sees why their goal is blocked); unrelated blocked programs are dropped entirely.
    ok = [h for h in hits if h["for_career"] or (h["similarity"] >= REL_MIN * best and elig(h) not in blocked)][:N_SHOW]
    top_career = ranked_careers[0]["title"] if ranked_careers else None

    # If the programs for the student's top career are not usually open to their group, say so plainly and
    # offer related programs they CAN apply to - as a separate, clearly labelled list.
    notice, alternatives = None, []
    top_progs = [h for h in ok if top_career and h["for_career"] == top_career]
    if inter_group and top_progs and all(elig(h) in blocked for h in top_progs):
        if all(elig(h) == "not_usual" for h in top_progs):
            need = sorted({g for h in top_progs for g in PROGRAMS[h["doc"]["id"]]["accepted"]})
            notice = (f"Programs for {top_career} usually require {' or '.join(need)}. With {inter_group}, check "
                      f"whether a university accepts you with extra courses, or look at related programs open to you.")
        else:
            need = min(PROGRAMS[h["doc"]["id"]]["min_pct"] for h in top_progs)
            notice = (f"Programs for {top_career} usually ask for at least {need}% in intermediate; you entered "
                      f"{marks:g}%. Some universities differ, and improvement exams can help - or look at related "
                      f"programs open to you.")
        shown = {h["doc"]["id"] for h in ok}
        alternatives = [h for h in hits if h["doc"]["id"] not in shown and elig(h) not in blocked
                        and h["similarity"] >= ALT_MIN][:3]

    # The student's own words get a guaranteed say: the best match to the free text alone (if not already
    # shown, eligible and actually similar) takes the last slot, so typing something always matters.
    if free_text and free_text.strip():
        ft = INDEX.sims(free_text.strip())
        shown = {h["doc"]["id"] for h in ok}
        for i in np.argsort(-ft):
            d = DOCS[i]
            if ft[i] < 0.05:
                break
            if d["id"] not in shown and C.eligibility(d["id"], inter_group, marks) not in ("not_usual", "below_marks"):
                pick = {"doc": d, "similarity": float(ft[i]), "score": float(ft[i]), "for_career": None,
                        "from_words": True}
                ok = (ok[:N_SHOW - 1] if len(ok) >= N_SHOW else ok) + [pick]
                break

    llm_out = llm.rank_programs(
        facts=student_facts(field, ranked_careers, career_answers, profile, free_text, prefs),
        inter_group=inter_group,
        candidates=[{"id": h["doc"]["id"], "name": h["doc"]["name"], "text": h["doc"]["text"]} for h in ok],
    ) if ok else None

    by_id = {h["doc"]["id"]: h for h in ok}
    programs = []
    if llm_out:
        for i, pick in enumerate(llm_out, start=1):
            card = _card(by_id[pick["id"]], inter_group, i, pick["reason"], "llm", marks)
            card["matches_answer"] = pick["fact"]
            programs.append(card)
        ranked_ids = {p["id"] for p in programs}
        for h in ok:  # anything the LLM left out keeps retrieval order, with a rule-based reason
            if h["doc"]["id"] not in ranked_ids:
                programs.append(_card(h, inter_group, len(programs) + 1, _rule_reason(h, top_career), "rules", marks))
    else:
        programs = [_card(h, inter_group, i, _rule_reason(h, top_career), "rules", marks) for i, h in enumerate(ok, start=1)]

    return {
        "programs": programs,
        "notice": notice,
        "alternatives": [_card(h, inter_group, 0, "Open to your group and related to your answers. "
                               f"You would study {', '.join(h['doc'].get('studies', '').split(', ')[:3])}.", "rules", marks)
                         for h in alternatives],
        "retrieval": {"method": INDEX.name, "query": query, "n_documents": len(DOCS),
                      "candidates_retrieved": len(hits)},
        "llm": llm.status(),
        "knowledge_base": "DRAFT descriptions - not yet verified against official sources",
    }
