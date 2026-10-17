"""
Smoke tests for the Edu Path API.  Run from project root:  python -m pytest backend/test_api.py -q
(or simply: python backend/test_api.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os, tempfile  # noqa: E401,E402
from pathlib import Path as _P  # noqa: E402
os.environ["DATABASE_URL"] = f"sqlite:///{(_P(tempfile.mkdtemp()) / 'test.db').as_posix()}"  # never the real DB
from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

client = TestClient(app)

DOCTOR = {"career": "Doctor, dentist, pharmacist, nurse or other health professional",
          "career_certain": "Very sure", "career_thought": "A lot",
          "education_plan": "Professional degree (MBBS, BDS, Pharm-D, LLB) or PhD",
          "fav_subject": "Biology", "least_subject": "Mathematics", "science_person": "Strongly agree",
          "math_person": "Disagree", "science_useful": "Strongly agree", "math_useful": "Disagree",
          "math_confident": "Disagree", "inter_group": "FSc Pre-Medical"}


def test_health_and_questions():
    assert client.get("/health").json()["status"] == "ok"
    qs = client.get("/questions").json()
    assert len(qs) == 12 and all(q["options"] for q in qs)


def test_doctor_gets_medical_first():
    r = client.post("/predict-field", json={"answers": DOCTOR}).json()
    assert r["top_fields"][0]["field"] == "Medical & Health"
    assert abs(sum(r["all_fields"].values()) - 1) < 0.01
    assert r["unanswered_questions"] == []
    assert r["top_fields"][0]["reasons_for"], "expected at least one reason"


def test_undecided_skips_follow_up_questions():
    r = client.post("/predict-field", json={"answers": {"career": "I don't know yet",
                                                        "inter_group": "ICS (Computer Science)"}}).json()
    assert "career_certain" not in r["unanswered_questions"]
    assert "career_thought" not in r["unanswered_questions"]


def test_bad_input_rejected():
    assert client.post("/predict-field", json={"answers": {"career": "Astronaut"}}).status_code == 422
    assert client.post("/predict-field", json={"answers": {"shoe_size": "42"}}).status_code == 422


# ---------- career stage (hybrid adaptive questions) ----------
from types import SimpleNamespace  # noqa: E402
import llm  # noqa: E402  (importable because backend.main put backend/ on sys.path)
import rag  # noqa: E402

llm._provider = None  # tests never call a real model (Ollama/Claude); AI paths use _FakeLLM below


def _walk(field, prefer, inter_group="ICS (Computer Science)"):
    answers = {}
    for _ in range(8):
        r = client.post("/career/step", json={"field": field, "answers": answers, "inter_group": inter_group}).json()
        if r["done"]:
            return r
        q = r["question"]
        answers[q["id"]] = prefer.get(q["id"], q["options"][0])
    raise AssertionError("career flow did not finish")


def test_career_flow_rules_only():
    r = _walk("CS & IT", {"cs_excite": "Working with data and AI", "cs_maths": "I love it",
                          "cs_puzzle": "Making a program that learns", "cs_work": "Research and experiments",
                          "cs_side": "The logic behind the program"})
    assert r["result"]["careers"][0]["title"].startswith("AI")
    assert "programs" not in r["result"]          # programs are a separate step now
    assert 3 <= r["answered"] <= 5


def test_career_bad_input():
    assert client.post("/career/step", json={"field": "Astrology", "answers": {}}).status_code == 422
    assert client.post("/career/step", json={"field": "CS & IT", "answers": {"cs_maths": "meh"}}).status_code == 422


class _FakeLLM:
    """Stands in for the local/Claude provider so the hybrid paths are tested without a real model."""
    name, model, _why = "fake", "fake-model", "ready"

    def __init__(self, reply=None, boom=False):
        self.reply, self.boom = reply, boom

    def available(self):
        return True

    def structured(self, system, user, schema):
        if self.boom:
            raise RuntimeError("model crashed")
        return schema.model_validate(self.reply)


def _with_llm(fake, fn):
    old = llm._provider
    llm._provider = fake
    try:
        return fn()
    finally:
        llm._provider = old


def _second_question(fake):
    return _with_llm(fake, lambda: client.post("/career/step", json={
        "field": "CS & IT", "answers": {"cs_puzzle": "Making a program that learns"}}).json()["question"])


def test_llm_choice_used_when_valid():
    q = _second_question(_FakeLLM({"question_id": "cs_side",
                                   "question_text": "Do you care more about how apps look, or the logic inside them?"}))
    assert q["source"] == "llm" and q["id"] == "cs_side" and q["text"].startswith("Do you care")
    assert q["options"] == ["How an app looks and feels", "The logic behind the program", "How systems connect and stay safe"]


def test_llm_question_falls_back_to_rules():
    for fake in (_FakeLLM({"question_id": "cs_puzzle", "question_text": "Already answered question"}),
                 _FakeLLM({"question_id": "made_up", "question_text": "Invented question"}),
                 _FakeLLM(boom=True)):
        assert _second_question(fake)["source"] == "rules"


# ---------- program recommendation (RAG) ----------
AI_ANSWERS = {"cs_puzzle": "Making a program that learns", "cs_maths": "I love it", "cs_work": "Research and experiments"}


def _recommend(**kw):
    body = {"field": "CS & IT", "answers": AI_ANSWERS, "inter_group": "ICS (Computer Science)", **kw}
    return client.post("/programs/recommend", json=body).json()


def test_rag_retrieves_relevant_programs():
    r = _recommend()
    names = [p["name"] for p in r["programs"]]
    assert names[0] == "BS Artificial Intelligence"
    assert {"BS Computer Science", "BS Data Science"} <= set(names[:4])
    assert all(p["reason_source"] == "rules" for p in r["programs"])  # no LLM in tests by default
    assert r["retrieval"]["n_documents"] == len(rag.DOCS)


def test_rag_eligibility_filter():
    # ICS student who wants to treat patients: MBBS stays visible but is flagged, and a notice explains why
    r = client.post("/programs/recommend", json={"field": "Medical & Health", "inter_group": "ICS (Computer Science)",
                                                 "answers": {"med_part": "Diagnosing and treating patients"}}).json()
    mbbs = next(p for p in r["programs"] if p["name"] == "MBBS")
    assert mbbs["eligibility"] == "not_usual"
    assert r["notice"] and "FSc Pre-Medical" in r["notice"]


def test_unrelated_programs_never_recommended():
    # Pre-Medical student who loves architecture: engineering programs are flagged, NOT replaced by
    # unrelated programs (the bug that showed Pharm-D/Nursing to an architecture lover)
    r = client.post("/programs/recommend", json={"field": "Engineering & Tech", "inter_group": "FSc Pre-Medical",
                    "answers": {"eng_excite": "Buildings, bridges and roads", "eng_style": "Design beautiful spaces",
                                "eng_place": "In a design studio"}}).json()
    names = [p["name"] for p in r["programs"]]
    assert names[0] == "B.Arch (Architecture)" and r["programs"][0]["eligibility"] == "not_usual"
    assert not {"Pharm-D", "BS Nursing", "MBBS"} & set(names)
    assert r["notice"] and "Architect" in r["notice"]
    assert all(a["eligibility"] != "not_usual" for a in r["alternatives"])


def test_rag_free_text_changes_retrieval():
    r = _recommend(inter_group="FSc Pre-Medical", free_text="I love drawing cartoons and want to make video games")
    assert "BS Animation / Multimedia" in [p["name"] for p in r["programs"]]


def test_free_text_always_counts():
    # ICS student whose answers point to AI: CS programs fill the list, but their own words must still show up
    r = _recommend(free_text="I love drawing cartoons and want to make video games")
    last = r["programs"][-1]
    assert last["name"] in {"BS Animation / Multimedia", "BFA Fine Arts", "BS Graphic Design"}
    assert last["field"] == "Education/Humanities/Arts" and "what you wrote" in last["reason"]


def test_marks_eligibility():
    body = {"field": "Medical & Health", "inter_group": "FSc Pre-Medical",
            "answers": {"med_part": "Diagnosing and treating patients", "med_length": "I'm ready for it"}}
    ok = client.post("/programs/recommend", json={**body, "marks": 82}).json()
    low = client.post("/programs/recommend", json={**body, "marks": 55}).json()
    mbbs_ok = next(p for p in ok["programs"] if p["name"] == "MBBS")
    mbbs_low = next(p for p in low["programs"] if p["name"] == "MBBS")
    assert mbbs_ok["eligibility"] == "eligible" and mbbs_ok["min_pct"] == 60
    assert mbbs_low["eligibility"] == "below_marks"
    assert low["notice"] and "60%" in low["notice"] and "55%" in low["notice"]
    assert all(a["eligibility"] not in ("not_usual", "below_marks") for a in low["alternatives"])
    assert client.post("/programs/recommend", json={**body, "marks": 140}).status_code == 422


def test_skill_gap_prefilled_from_answers():
    r = client.post("/programs/recommend", json={"field": "CS & IT", "answers": AI_ANSWERS,
                    "profile": {"math_confident": "Agree", "fav_subject": "Computer Science"}}).json()
    skills = {s["name"]: s for s in r["careers"][0]["skills"]}
    assert r["careers"][0]["title"].startswith("AI") and len(skills) == 4
    assert skills["Maths"]["suggested"] and skills["Programming"]["suggested"]
    assert not skills["Statistics & probability"]["suggested"] and skills["Statistics & probability"]["tip"]


def test_skills_endpoint_covers_every_career():
    r = client.get("/skills").json()
    assert len(r["careers"]) == 43 and all(len(c["skills"]) == 4 and all(s["tip"] for s in c["skills"]) for c in r["careers"])


def test_program_questions_and_prefs():
    qs = client.get("/programs/questions").json()
    assert [q["id"] for q in qs] == ["years", "entry_test", "style", "priority", "after"]
    body = {"field": "Medical & Health", "inter_group": "FSc Pre-Medical",
            "answers": {"med_part": "Diagnosing and treating patients", "med_length": "I'm ready for it"}}
    base = {p["name"]: p for p in client.post("/programs/recommend", json=body).json()["programs"]}
    pref = client.post("/programs/recommend", json={**body, "prefs": {"years": "4 years", "entry_test": "I'd rather not"}}).json()
    by = {p["name"]: p for p in pref["programs"]}
    assert any("MDCAT" in n for n in by["MBBS"]["pref_notes"]) and any("5-year" in n for n in by["MBBS"]["pref_notes"])
    assert by["MBBS"]["score"] < base["MBBS"]["score"]                      # clashes lower the ranking
    assert by["BS Nursing"]["pref_notes"] == []                            # 4 years, no entry test
    bad = client.post("/programs/recommend", json={**body, "prefs": {"years": "10 years"}})
    assert bad.status_code == 422


def test_blocked_unrelated_programs_dropped():
    # FA student who wants to be a lawyer and wants to "help people": no Pre-Medical-only programs in the list
    r = client.post("/programs/recommend", json={"field": "Social Sci/Law/Psych", "inter_group": "FA / Humanities / Arts",
                    "answers": {"soc_interest": "Justice and people's rights", "soc_goal": "Practising law in court"},
                    "prefs": {"priority": "Helping people"}, "free_text": "I want to help women get justice"}).json()
    assert r["programs"][0]["name"] == "LLB (5 years)"
    assert all(p["eligibility"] not in ("not_usual", "below_marks") or p["for_career"] for p in r["programs"])


def test_llm_ranks_only_retrieved_programs():
    reply = {"ranking": [{"program_id": "bsds", "profile_fact": 3, "reason": "You love maths, and this program is all about data."},
                         {"program_id": "mbbs", "profile_fact": 0, "reason": "Not retrieved, must be dropped by validation."},
                         {"program_id": "bsai", "profile_fact": 1, "reason": "It teaches machine learning, matching your top career."}]}
    r = _with_llm(_FakeLLM(reply), _recommend)
    progs = r["programs"]
    assert [p["id"] for p in progs[:2]] == ["bsds", "bsai"] and progs[0]["reason_source"] == "llm"
    assert progs[1]["matches_answer"].startswith("Top career match")
    assert "mbbs" not in [p["id"] for p in progs]
    assert all(p["reason_source"] == "rules" for p in progs[2:])      # rest keep retrieval order


def test_llm_unsupported_claims_are_dropped():
    reply = {"ranking": [{"program_id": "bsse", "profile_fact": 0,   # cites no fact but invents a preference
                          "reason": "Your preference for building software in teams fits this program."},
                         {"program_id": "bscs", "profile_fact": 0,   # cites no fact, makes no claim -> allowed
                          "reason": "A broader option covering programming, algorithms and computer systems."}]}
    progs = {p["id"]: p for p in _with_llm(_FakeLLM(reply), _recommend)["programs"]}
    assert progs["bsse"]["reason_source"] == "rules"
    assert progs["bscs"]["reason_source"] == "llm" and progs["bscs"]["matches_answer"] is None


def test_llm_offtask_reasons_are_dropped():
    reply = {"ranking": [{"program_id": "bsds", "profile_fact": 1,
                          "reason": "BS Data Science does not match your career; BS Artificial Intelligence is more relevant."},
                         {"program_id": "bscs", "profile_fact": 0,
                          "reason": "You are not comfortable with maths, which this program needs."}]}
    progs = {p["id"]: p for p in _with_llm(_FakeLLM(reply), _recommend)["programs"]}
    assert progs["bsds"]["reason_source"] == "rules" and progs["bscs"]["reason_source"] == "rules"


def test_llm_ranking_failure_falls_back():
    r = _with_llm(_FakeLLM(boom=True), _recommend)
    assert r["programs"][0]["name"] == "BS Artificial Intelligence" and r["programs"][0]["reason_source"] == "rules"


# ---------- accounts & database ----------
def _signup(email="ali@example.com", password="Secret#123", name="Ali Khan"):
    return client.post("/auth/signup", json={"name": name, "email": email, "password": password})


def test_signup_login_me_logout():
    r = _signup()
    assert r.status_code == 200 and r.json()["user"]["email"] == "ali@example.com"
    tok = client.post("/auth/login", json={"email": "ALI@example.com ", "password": "Secret#123"}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    assert client.get("/auth/me", headers=h).json()["name"] == "Ali Khan"
    client.post("/auth/logout", headers=h)
    assert client.get("/auth/me", headers=h).status_code == 401


def test_signup_validation_and_duplicates():
    assert _signup(email="dup@example.com").status_code == 200
    assert _signup(email="dup@example.com").status_code == 409
    assert _signup(email="not-an-email").status_code == 422
    assert _signup(email="weak@example.com", password="password1").status_code == 422  # no upper case / symbol
    assert _signup(email="weak2@example.com", password="Password1").status_code == 422  # no symbol
    assert _signup(email="short@example.com", password="A1#a").status_code == 422      # too short
    r = client.post("/auth/signup", json={"email": "noname@example.com", "password": "Secret#123"})  # email only
    assert r.status_code == 200 and r.json()["user"]["name"] == "noname"


def test_wrong_password_and_throttling():
    _signup(email="sara@example.com")
    for _ in range(5):
        assert client.post("/auth/login", json={"email": "sara@example.com", "password": "Wrong#999"}).status_code == 401
    assert client.post("/auth/login", json={"email": "sara@example.com", "password": "Secret#123"}).status_code == 429


def test_passwords_are_hashed_not_stored():
    import db as DB
    _signup(email="hash@example.com", password="Secret#123")
    with DB.SessionLocal() as s:
        u = s.query(DB.User).filter_by(email="hash@example.com").one()
        assert "Secret#123" not in u.password_hash and u.password_hash.startswith("pbkdf2_sha256$")


def test_state_saved_per_user_and_protected():
    h1 = {"Authorization": f"Bearer {_signup(email='u1@example.com').json()['token']}"}
    h2 = {"Authorization": f"Bearer {_signup(email='u2@example.com').json()['token']}"}
    assert client.put("/me/state", headers=h1, json={"items": {"ep_marks": 78, "ep_shortlist": ["BBA"]}}).status_code == 200
    assert client.get("/me/state", headers=h1).json() == {"ep_marks": 78, "ep_shortlist": ["BBA"]}
    assert client.get("/me/state", headers=h2).json() == {}                       # other users can't see it
    assert client.put("/me/state", headers=h1, json={"items": {"ep_token": "x"}}).status_code == 422
    client.put("/me/state", headers=h1, json={"items": {"ep_marks": None}})
    assert "ep_marks" not in client.get("/me/state", headers=h1).json()
    assert client.get("/me/state").status_code == 401


def test_predict_saves_history_only_when_logged_in():
    h = {"Authorization": f"Bearer {_signup(email='hist@example.com').json()['token']}"}
    assert "saved_to_account" not in client.post("/predict-field", json={"answers": DOCTOR}).json()
    assert client.post("/predict-field", headers=h, json={"answers": DOCTOR}).json()["saved_to_account"]
    hist = client.get("/me/assessments", headers=h).json()
    assert len(hist) == 1 and hist[0]["top_fields"][0]["field"] == "Medical & Health"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
    import json
    print(json.dumps(client.post("/predict-field", json={"answers": DOCTOR}).json()["top_fields"][0], indent=1))
