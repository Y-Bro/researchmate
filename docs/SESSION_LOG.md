# Session Log

## Day 1 — 2026-06-04
- **did:** wrote `config.py` (env-based `Settings`, defaults on optional fields, `validate()` wired into `load_settings`, typed `ConfigError`) and `errors.py` (base `ResearchMateError` with message + keyword-only `details`, plus `ConfigError`/`LLMError`/`RetrievalError`/`ChunkingError`); installed `python-dotenv`; set up the pytest harness (`conftest.py` puts `src/` on the path and stubs `load_dotenv` so tests never touch the real `.env`); wrote tests — 6 for config + 23 for errors, **29 passing**; committed everything and merged `feature/scaffold` → `main`.
- **decided:** `validate()` runs inside `load_settings()` (fail-fast); native `raise ... from` chaining instead of a custom `cause` attribute; error subclasses are docstring-only (no `__init__`); subclass tests are parametrized; merged the work into `main` (supersedes the earlier "stay on feature/scaffold"). Coach filled today's logs at the user's request (Day 1 is normally the user's job).
- **next:** finish Day 1 — `src/rag/llm_client.py` (Gemini wrapper: timeout, retry-with-backoff, structured logging of latency + tokens, raises `LLMError`).
- **stuck-on:** none blocking; the bad-numeric env edge in `config.py` (`int("abc")`) is still open — tracked in GAPS.

## Day 0 — 2026-06-04
- **did:** removed premature scaffold (GitHub Actions CI, `pyproject.toml`); kept `.claude/settings.json` + `.cursorignore`; set up `.venv` and `.env` (`GEMINI_API_KEY`); installed `google-genai` + `pytest` and froze `requirements.txt`; wrote `CLAUDE.md` (own, iterated with coach review); created `docs/SESSION_LOG.md`, `docs/DECISIONS.md`, `docs/GAPS.md`, `docs/TODOS.md`.
- **decided:** doc-filling schedule — coach fills logs on Day 0, user fills Days 1–2, coach fills Day 3 onward. Trunk = `feature/scaffold` (no move to `main`). Kept existing `.claude` config. Gemini as the app LLM; no frameworks. (See DECISIONS.md.)
- **next:** Day 1 — `config.py` + `errors.py` + `llm_client.py` (spec-first; I write the code, coach reviews).
- **stuck-on:** nothing open — branch settled (`feature/scaffold` as trunk).
