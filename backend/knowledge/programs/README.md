# Program knowledge base (RAG documents)

One file per field. Each `## <program_id>` section is one document that the retrieval step searches
and the LLM reads. Program ids must match `PROGRAMS` in `backend/career_bank.py` (duration, entry
groups and tests live there).

## Status: DRAFT
These texts were drafted as general descriptions so the recommendation pipeline can be built and
tested. They are **not verified**. Before submission, replace each section with text from an official
source (HEC curriculum document or a university program page) and fill in:

```
source: <URL of the official page or PDF>
verified: <YYYY-MM-DD you checked it>
```

Keys per section (one per line, `key: value`):
- `name` - program name as shown to students
- `summary` - 2-3 sentences: what the program is
- `studies` - main subjects/courses, comma separated
- `skills` - skills students build
- `careers` - careers it leads to
- `suits` - what kind of student it suits
- `source`, `verified` - optional per section; otherwise the file header values apply

After editing, restart the backend; the index is rebuilt at startup.
