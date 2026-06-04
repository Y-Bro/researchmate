# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

This repository is currently a skeleton — it contains only `README.md`, `LICENSE`, and `.gitignore`. There is no source code, dependency manifest, build configuration, or test suite yet. **Update this file as the codebase takes shape** (add real build/lint/test commands and an architecture overview once they exist).

## Project

**researchmate** — a personal research agent that operates on custom (user-supplied) knowledge. See `README.md`.

## Intended tooling

No tooling is configured yet, but `.gitignore` is set up for a **Python** project and points at the intended toolchain:

- **Linting/formatting:** Ruff (`.ruff_cache/` is ignored)
- **Type checking:** mypy (`.mypy_cache/` is ignored)
- **Testing:** pytest (`.pytest_cache/` is ignored)
- **Environments:** virtualenv-based (`.venv/`, `venv/`, `env/` ignored); secrets in `.env` (ignored)
- **Packaging:** standard build/dist layout (`build/`, `dist/`, `*.egg-info/`, `wheels/` ignored)

None of these are wired up — there is no `pyproject.toml`, `setup.py`, or config for any of them. Confirm the actual setup before running commands once code is added.
