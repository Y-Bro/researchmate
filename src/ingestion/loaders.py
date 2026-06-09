# =============================================================================
# loaders.py  —  turn a raw file on disk into a Document.
# =============================================================================
# One loader per format (markdown, PDF, HTML). They all produce the SAME thing:
# a `Document` (text + source + metadata). That uniform output is what lets the
# chunker stay format-blind. This is the Strategy pattern — interchangeable
# algorithms behind one interface.
#
# Build order: base interface -> MarkdownLoader (trivial, proves the shape)
# -> PdfLoader (pypdf) -> HtmlLoader (beautifulsoup4) -> a dispatcher that picks
# the loader by file extension. Today: just the base + Markdown.
#
# -----------------------------------------------------------------------------
# TODO 1 — imports
# -----------------------------------------------------------------------------
#   from abc import ABC, abstractmethod
#   from pathlib import Path
#   from ingestion.models import Document
#   (you will likely want a typed error too — see the DESIGN NOTE below)


# -----------------------------------------------------------------------------
# DESIGN NOTE — errors (a friction point, your call)
# -----------------------------------------------------------------------------
# errors.py has ConfigError / LLMError / RetrievalError / ChunkingError — but
# NO error for "loading a file failed." Loading can fail many ways: file
# missing, unreadable, bad encoding, empty. Two options:
#   a) add `IngestionError(ResearchMateError)` to errors.py (consistent with the
#      hierarchy — recommended; this is the "born from friction" moment)
#   b) reuse an existing one (ChunkingError is the closest, but semantically
#      wrong — loading isn't chunking)
# Decide and record it in DECISIONS.md. Cover the UNHAPPY paths, not just read.


# -----------------------------------------------------------------------------
# TODO 2 — class Loader(ABC)  (the interface every loader implements)
# -----------------------------------------------------------------------------
# An abstract base class with:
#   - an abstract method `load(self, path: Path) -> Document`
#   - optionally a class attribute listing the extensions it handles
#     (e.g. `extensions = (".md", ".markdown")`) — the dispatcher will use this
#     later to route a file to the right loader.
# No __init__ needed yet (these loaders are stateless). DI comes in when the
# dispatcher is GIVEN a list of loaders rather than hardcoding them.


# -----------------------------------------------------------------------------
# TODO 3 — class MarkdownLoader(Loader)
# -----------------------------------------------------------------------------
# Implement load(path):
#   - read the file's text. Use pathlib: `path.read_text(encoding="utf-8")`.
#     DECISION: what about weird unicode / bad bytes? `encoding="utf-8"` with
#     the default errors="strict" will RAISE on bad bytes — is that what you
#     want, or errors="replace"? (The "done when" requires handling weird
#     unicode, so think about this now.) Wrap failures in your typed error.
#   - handle the unhappy paths: file doesn't exist, is a directory, is empty.
#     What should an empty file do — return Document(text="") or raise? Pick one
#     and be consistent (downstream chunker must agree).
#   - return Document(text=<contents>, source=<the filename>, metadata={...})
#     For source, prefer `path.name` (just the filename — cleaner citations)
#     unless you need the path. Put anything extra (e.g. "loader": "markdown")
#     in metadata.
#
# -----------------------------------------------------------------------------
# Write the base + MarkdownLoader. Markdown is plain text, so load() is short —
# the real work is the error handling and the encoding decision. When done,
# say "check" and I'll review before we add pypdf/bs4 loaders.
# -----------------------------------------------------------------------------
