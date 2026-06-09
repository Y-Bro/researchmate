# Gaps

Known holes to revisit. The coach appends here as gaps surface.

- [ ] No documents in `data/raw/` yet (needed Day 2 for ingestion)
- [x] ~~No tests yet~~ — 49 passing (config 6, errors 23, llm_client 20)
- [ ] Python version not pinned — plan says 3.11; earlier tooling targeted 3.12 (venv is 3.14)
- [ ] `CLAUDE.md` missing a "what I do first" rule (explain concept + spec before I code)
- [ ] `llm_client` timeout/transient detection is a generic `except Exception` retry, not matched to the SDK's specific timeout type — coarse; could retry non-transient surprises
- [ ] `llm_client` `temperature=0.5` likely too high for grounded RAG — revisit Day 4; consider moving to `Settings`
- [ ] `config` bad-numeric env edge: `int("abc")` raises a raw `ValueError` before `validate()` runs (no typed `ConfigError`)
