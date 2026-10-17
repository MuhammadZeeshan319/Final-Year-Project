"""
LLM part of Edu Path's hybrid design. The LLM never decides alone:
  - choose():        picks the next career question from candidates the rules engine offers, and rephrases it
  - rank_programs(): ranks programs that RAG retrieved (and eligibility kept) and explains each from its document
Every output is validated (ids must be among the candidates, text length limits). On any problem -
LLM off, server not running, model not downloaded, timeout, refusal, invalid output - the callers use
the rules / retrieval result instead, so the app always works.

Providers (env EDUPATH_LLM):
  ollama  (default) local model on this computer via Ollama - free, offline, private
          install https://ollama.com, then:  ollama pull qwen2.5:3b
          EDUPATH_OLLAMA_MODEL (default qwen2.5:3b), OLLAMA_URL (default http://127.0.0.1:11434)
  claude  Anthropic API via the official SDK (pip install anthropic; ANTHROPIC_API_KEY)
          EDUPATH_CLAUDE_MODEL (default claude-opus-5-5)
  off     rules only
EDUPATH_LLM_TIMEOUT seconds (default 60; local models on a GPU usually answer in a few seconds).
"""
import json
import re
import logging
import os
import time

import httpx
from pydantic import BaseModel

log = logging.getLogger("edupath.llm")

PROVIDER = os.getenv("EDUPATH_LLM", "ollama").strip().lower()
TIMEOUT = float(os.getenv("EDUPATH_LLM_TIMEOUT", "60"))


# ---------------- providers ----------------
class _Ollama:
    name = "ollama"

    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        self.model = os.getenv("EDUPATH_OLLAMA_MODEL", "qwen2.5:3b")
        self._checked, self._ok, self._why = 0.0, False, "not checked"

    def available(self):
        if time.time() - self._checked < 30:  # cache the check; it runs on every request otherwise
            return self._ok
        self._checked = time.time()
        try:
            tags = httpx.get(f"{self.url}/api/tags", timeout=1.5).json()
            names = {m.get("name", "") for m in tags.get("models", [])}
            self._ok = self.model in names or f"{self.model}:latest" in names
            self._why = "ready" if self._ok else f"model not downloaded - run: ollama pull {self.model}"
        except Exception:
            self._ok, self._why = False, "Ollama is not running"
        return self._ok

    def structured(self, system, user, schema):
        r = httpx.post(f"{self.url}/api/chat", timeout=TIMEOUT, json={
            "model": self.model, "stream": False, "format": schema.model_json_schema(),
            "options": {"temperature": 0.2},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return schema.model_validate_json(r.json()["message"]["content"])


class _Claude:
    name = "claude"

    def __init__(self):
        import anthropic  # optional dependency
        self.model = os.getenv("EDUPATH_CLAUDE_MODEL", "claude-opus-5-5")
        self.client = anthropic.Anthropic(timeout=TIMEOUT, max_retries=1)
        self._why = "ready"

    def available(self):
        return True

    def structured(self, system, user, schema):
        resp = self.client.messages.parse(model=self.model, max_tokens=4000, system=system,
                                          messages=[{"role": "user", "content": user}], output_format=schema)
        if resp.stop_reason == "refusal":
            raise RuntimeError("refusal")
        return resp.parsed_output


def _make():
    try:
        if PROVIDER == "ollama":
            return _Ollama()
        if PROVIDER == "claude":
            return _Claude()
    except Exception as e:
        log.warning("LLM provider %s unavailable: %s", PROVIDER, e)
    return None


_provider = _make()


def status():
    if _provider is None:
        return {"provider": PROVIDER, "enabled": False, "model": None, "detail": "off"}
    ok = _provider.available()
    return {"provider": _provider.name, "enabled": ok, "model": _provider.model, "detail": _provider._why}


# measurement hook for scripts/07_eval_rag.py: details of the most recent LLM call
LAST = {}


def _ask(system, user, schema):
    LAST.clear()
    if _provider is None or not _provider.available():
        LAST.update(called=False)
        return None
    t = time.time()
    try:
        out = _provider.structured(system, user, schema)
        LAST.update(called=True, ok=True, seconds=time.time() - t)
        return out
    except Exception as e:  # connection, timeout, refusal, invalid JSON ...
        LAST.update(called=True, ok=False, seconds=time.time() - t, error=f"{type(e).__name__}: {e}"[:200])
        log.warning("LLM call failed (%s); using rules", e)
        return None


# ---------------- task 1: next career question ----------------
class NextQuestion(BaseModel):
    question_id: str
    question_text: str


SYSTEM_QUESTION = (
    "You are a friendly academic counsellor for Pakistani students who have just finished intermediate "
    "(FSc, ICS, I.Com, FA). Choose the ONE candidate question that best helps tell the leading careers apart "
    "for this student, and rephrase it in warm, simple English (at most 25 words). Keep the meaning identical: "
    "the student answers with the bank's original options, so do not add, remove or hint at options. "
    "Return question_id exactly as given."
)


def choose(field, ranked, answered, candidates):
    if not candidates:
        return None
    lines = [f"Field: {field}", "", "Careers still in contention (rules-engine scores):"]
    lines += [f"- {r['title']}: {r['points']:.0f} points, {round(r['match'] * 100)}% match" for r in ranked[:4]]
    lines += ["", "Already answered:"] + ([f"- {a['question']} -> {a['answer']}" for a in answered] or ["- (nothing yet)"])
    lines += ["", "Candidate questions (choose one):"]
    lines += [f"- id={q['id']}: {q['text']} | options: " + " / ".join(o["label"] for o in q["options"]) for q in candidates]
    out = _ask(SYSTEM_QUESTION, "\n".join(lines), NextQuestion)
    if out is None:
        return None
    text = " ".join((out.question_text or "").split())
    if out.question_id not in {q["id"] for q in candidates} or not (5 <= len(text) <= 220):
        log.info("LLM question rejected (id=%r)", out.question_id)
        return None
    return {"id": out.question_id, "text": text}


# ---------------- task 2: rank + explain retrieved programs (the "G" in RAG) ----------------
class ProgramPick(BaseModel):
    program_id: str
    profile_fact: int  # number of the STUDENT FACT the reason relies on, 0 = none
    reason: str


# phrases that assert something about the student - only allowed when the reason cites a real profile fact
_CLAIM = re.compile(r"\byou(?:'re| are)?(?: not)? (?:enjoy|love|like|prefer|want|are interested|have a passion|"
                    r"comfortable|good at)|\byour (?:strong )?(?:interest|passion|preference|love|enjoyment|background)",
                    re.I)
# reasons that argue AGAINST the program they are attached to are off-task for a recommendation list
_OFFTASK = re.compile(r"does not (?:match|align|fit|focus)|not (?:aligned|a good fit|suitable|relevant)|"
                      r"ranked (?:last|lower)|better fit|less (?:relevant|suitable)|is more relevant", re.I)


class ProgramRanking(BaseModel):
    ranking: list[ProgramPick]


SYSTEM_PROGRAMS = (
    "You are an academic counsellor for Pakistani students who have just finished intermediate. "
    "You are given a student profile and a list of degree program documents retrieved from a knowledge base. "
    "Rank the programs from best to worst fit for THIS student and give each a reason of 1-2 short sentences "
    "written to the student ('you'). Facts about the PROGRAM may come only from its document. Facts about the "
    "STUDENT may come only from the numbered STUDENT FACTS. For each program set profile_fact to the number of "
    "the one fact your reason relies on, or 0 if none of the facts fits. If profile_fact is 0, do NOT say what "
    "the student likes, enjoys, prefers or is interested in - just describe the program as a related or broader "
    "option and what it covers. A document's 'suits' line describes typical students, not this student. "
    "Use only program_id values from the list. Do not mention programs that are not listed, and do not state "
    "fees, admission marks, universities or anything that is not in the documents."
)


def rank_programs(facts, inter_group, candidates):
    """facts: the student's real profile statements (strings). candidates: [{id, name, text}] (retrieved +
    eligible). Returns [{id, reason, fact}] or None. Reasons that claim student preferences without citing
    a real fact are dropped (the caller then uses its rule-based reason for that program)."""
    if not candidates:
        return None
    lines = ["STUDENT FACTS (the only things you may say about the student)"]
    lines += [f"{i}. {f}" for i, f in enumerate(facts, start=1)] or ["(none)"]
    lines += [f"Intermediate group: {inter_group or 'not given'}", "", "RETRIEVED PROGRAM DOCUMENTS"]
    lines += [f"[{c['id']}] {c['text']}" for c in candidates]
    out = _ask(SYSTEM_PROGRAMS, "\n".join(lines), ProgramRanking)
    if out is None:
        return None
    valid, seen, dropped, offtask = [], set(), 0, 0
    ids = {c["id"] for c in candidates}
    for p in out.ranking:
        reason = " ".join((p.reason or "").split())
        if p.program_id not in ids or p.program_id in seen or not (10 <= len(reason) <= 400):
            continue
        fact = facts[p.profile_fact - 1] if 1 <= p.profile_fact <= len(facts) else None
        if fact is None and _CLAIM.search(reason):
            dropped += 1  # unsupported claim about the student -> not shown
            continue
        others = [c["name"] for c in candidates if c["id"] != p.program_id]
        if _OFFTASK.search(reason) or any(o.lower() in reason.lower() for o in others):
            offtask += 1  # argues against the program, or talks about another one -> not shown
            continue
        valid.append({"id": p.program_id, "reason": reason, "fact": fact})
        seen.add(p.program_id)
    if dropped:
        log.info("LLM: %d reason(s) dropped for unsupported claims about the student", dropped)
    LAST.update(proposed=len(out.ranking), kept=len(valid), dropped_claims=dropped, dropped_offtask=offtask,
                invalid=len(out.ranking) - len(valid) - dropped - offtask)
    return valid or None
