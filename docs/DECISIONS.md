# Decisions

## 2026-06-04 — Merge Day 0+1 into `main` (supersedes "no move to main")
- **Decision:** merged `feature/scaffold` into `main`; `main` is the trunk from here on.
- **Why:** aligns with the plan's "day branches off `main`" rhythm; the earlier "stay on feature/scaffold" was provisional.

## 2026-06-04 — Load `.env` via python-dotenv (resolves config TODO 1)
- **Decision:** use `python-dotenv` (option b); `config.py` calls `load_dotenv()` at import to populate `os.environ`. Added to `requirements.txt`.
- **Why:** loading is automatic — no need to `export` vars each run.
- **Alternatives:** exporting vars manually (option a) — rejected as error-prone.

## 2026-06-04 — config & errors design choices
- **`validate()` runs inside `load_settings()`** so every caller gets validated settings (fail-fast), rather than trusting callers to validate.
- **Native exception chaining** (`raise XError(...) from e`) instead of a custom `cause` attribute — shows in tracebacks, idiomatic.
- **Error subclasses are docstring-only** (no `__init__`) — they inherit the base; re-declaring added nothing.

## 2026-06-04 — Test harness approach
- **Decision:** pytest with a repo-root `conftest.py` that puts `src/` on `sys.path` and stubs `load_dotenv`; tests set env vars via `monkeypatch`.
- **Why:** no `pyproject`/`pytest.ini` needed yet, and tests never read or depend on the real `.env`. Subclass tests are parametrized to avoid four identical copies.

## 2026-06-04 — Trunk branch & keeping existing config
- **Decision:** keep working on `feature/scaffold` as the trunk (no switch to `main`); keep the existing `.claude/settings.json`, `.claude/settings.local.json`, and `.cursorignore`.
- **Why:** avoid branch churn now; the scaffold permissions (git allow, `.env` deny) are useful and harmless to keep.
- **Trade-off:** diverges slightly from the plan's "day branches off `main`" rhythm and its "config from friction" rule — accepted for simplicity.

## 2026-06-04 — Who fills the project docs (SESSION_LOG / DECISIONS / GAPS)
- **Decision:** Coach (Claude) fills the log docs on **Day 0**. The **user** fills them on **Days 1 and 2**. From **Day 3 onward**, the coach fills them again.
- **Why:** ease into the logging habit — see a worked example first (Day 0), practice it hands-on while it's fresh (Days 1–2), then hand upkeep back to the coach.
- **Alternatives:** user writes all docs from Day 0 (the strict masterplan default — maximizes the reflection habit, more friction up front).
- **Scope:** docs only. The user still writes **all** `src/` implementation code per CLAUDE.md.

## 2026-06-04 — Use Google Gemini as the application LLM
- **Decision:** Gemini via the `google-genai` SDK (e.g. `gemini-2.5-flash`) for both answering and judging; all Gemini code isolated in one module (`llm_client.py`).
- **Why:** the user has a Gemini API key; a Claude Pro/Max subscription does not include API access for the app's own calls. Isolation keeps the rest of the codebase provider-agnostic.
- **Alternatives:** Anthropic/OpenAI APIs — rejected (separate paid API billing).

## 2026-06-04 — No RAG/agent framework (build by hand)
- **Decision:** build chunking, retrieval, the RAG pipeline, and the agent loop on plain SDK code — no LangChain / LlamaIndex / LangGraph.
- **Why:** frameworks hide the exact concepts being learned; building each part once makes every framework transparent later.
- **Alternatives:** use a framework now (faster demo, weaker understanding). Optional Day 10+: rebuild the agent in LangGraph to compare.

## 2026-06-04 — Remove the premature scaffold
- **Decision:** deleted the front-loaded CI workflow and `pyproject.toml` (Ruff/mypy) created earlier in the session.
- **Why:** the plan's rule is "config is born from friction, never upfront" — these belong to later days (lint Day 1+, CI Day 9).
- **Alternatives:** keep them as a head-start — rejected to honor the learning pedagogy.
