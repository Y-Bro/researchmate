# Session Log

## Day 0 — 2026-06-04
- **did:** removed premature scaffold (GitHub Actions CI, `pyproject.toml`); kept `.claude/settings.json` + `.cursorignore`; set up `.venv` and `.env` (`GEMINI_API_KEY`); installed `google-genai` + `pytest` and froze `requirements.txt`; wrote `CLAUDE.md` (own, iterated with coach review); created `docs/SESSION_LOG.md`, `docs/DECISIONS.md`, `docs/GAPS.md`, `docs/TODOS.md`.
- **decided:** doc-filling schedule — coach fills logs on Day 0, user fills Days 1–2, coach fills Day 3 onward. Trunk = `feature/scaffold` (no move to `main`). Kept existing `.claude` config. Gemini as the app LLM; no frameworks. (See DECISIONS.md.)
- **next:** Day 1 — `config.py` + `errors.py` + `llm_client.py` (spec-first; I write the code, coach reviews).
- **stuck-on:** nothing open — branch settled (`feature/scaffold` as trunk).
