# Edu Path AI - backend & ML

Final Year Project, Faculty of Computing, Riphah International University.
Recommends an academic **field** (XGBoost), a **career** (adaptive questions: rules + local LLM) and
**degree programs** (RAG over a program knowledge base) for students who have finished intermediate.

> The frontend (HTML/CSS/JS) is kept outside this repository.

## Run the API
```powershell
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```
API docs: http://127.0.0.1:8000/docs  ·  Tests: `python -m pytest backend/test_api.py`

Optional local LLM (explanations / adaptive questions): install [Ollama](https://ollama.com), then
`ollama pull qwen2.5:3b`. Without it the app falls back to rule-based reasons.

## Repository layout
| Folder | Contents |
|---|---|
| `backend/` | FastAPI app (`main.py`), accounts & database (`auth.py`, `db.py`), career engine (`careers.py`, `career_bank.py`, `career_extra.py`), RAG (`rag.py`, `knowledge/programs/`), LLM (`llm.py`) |
| `src/` | `questionnaire.py` - the 12 field questions and their encoding (shared by training and the API) |
| `models/` | trained XGBoost field model + feature spec |
| `scripts/` | data screening, training and evaluation pipeline (`01_...` to `07_...`) |
| `reports/` | evaluation results and cleaning log |

## Data (not in the repo)
The field model is trained on **HSLS:09** (US National Center for Education Statistics, public-use file).
Download `hsls09_16_student_pets_pear_v1_0.csv` from NCES and place it in `datasets/original/`, then run the
scripts in order (`scripts/02_screen.py` builds `datasets/derived/`). Never edit `datasets/original/`.

## Status / handoffs
- Program descriptions, minimum marks and skill lists are **drafts** - to be verified against HEC / university sources.
- Email verification & password reset: see `backend/AUTH_HANDOFF.md`.
- The local database (`backend/data/edupath.db`) is created automatically and is **not** committed.
