# Gaps

Known holes to revisit. The coach appends here as gaps surface.

- [ ] No documents in `data/raw/` yet (needed Day 2 for ingestion)
- [x] ~~No tests yet~~ — 49 passing (config 6, errors 23, llm_client 20)
- [ ] Python version not pinned — plan says 3.11; earlier tooling targeted 3.12 (venv is 3.14)
- [ ] `CLAUDE.md` missing a "what I do first" rule (explain concept + spec before I code)
- [ ] `llm_client` timeout/transient detection is a generic `except Exception` retry, not matched to the SDK's specific timeout type — coarse; could retry non-transient surprises
- [ ] `llm_client` `temperature=0.5` likely too high for grounded RAG — revisit Day 4; consider moving to `Settings`
- [ ] `config` bad-numeric env edge: `int("abc")` raises a raw `ValueError` before `validate()` runs (no typed `ConfigError`)
- [ ] Chunker empty-text behavior is inconsistent by choice: `FixedSizeChunker.chunk("")` returns `[]`, `RecursiveChunker.chunk("")` raises `ChunkingError("No data to chunk")`. CLI's per-file try/except tolerates both (raise → counted as `files_failed`; `[]` → `files_ok` with 0 chunks). Considered aligning both on `[]` but deferred to avoid src/test churn — revisit if a caller relies on uniform behavior.
- [ ] `VectorStore.add` crashes with a raw chroma `ValueError` ("Expected metadata to be a non-empty dict") if a chunk's metadata cleans to `{}` (all-`None` values, or empty). Doesn't fire in the normal pipeline (chunkers always set `loader`/`start`/`end`), but it's an unguarded edge + a raw error instead of typed `RetrievalError`. Fix options: have `_clean_metadata` guarantee a non-empty dict, or wrap `add`'s `upsert` in try/except → `RetrievalError`. Also `add`/`query` don't wrap chroma failures in `RetrievalError` (raw exceptions bubble) and have no logging — deferred.
