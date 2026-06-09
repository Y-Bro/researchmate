# =============================================================================
# models.py  —  the shared data structures the ingestion pipeline passes around.
# =============================================================================
# WHY a dedicated models file: loaders produce `Document`s, chunkers turn those
# into `Chunk`s. If both sides agree on these two shapes, you can swap any
# loader or chunker without touching the other. Define the contract first.
#
# Your CLAUDE.md says frozen dataclasses + carry metadata. Both of these are
# frozen (immutable — a chunk shouldn't mutate after creation) and carry the
# metadata you'll need for CITATIONS on Day 4. Decide what metadata you need
# NOW, because retro-fitting source/position later is painful.
#
# -----------------------------------------------------------------------------
# TODO 1 — imports
# -----------------------------------------------------------------------------
#   from dataclasses import dataclass, field
#   (you may want `field(default_factory=dict)` for a metadata dict)

from dataclasses import dataclass, field


# -----------------------------------------------------------------------------
# TODO 2 — class Document  (what a LOADER returns: one whole source file)
# -----------------------------------------------------------------------------
# A frozen dataclass holding:
#   - text: str                  -> the full extracted plain text of the file
#   - source: str                -> the filename it came from (e.g. "paper.pdf")
#                                    you NEED this for citations later
#   - metadata: dict             -> open bag for extras (page count, mime type…)
#                                    use field(default_factory=dict) — never a
#                                    bare {} default (shared-mutable-default trap,
#                                    same lesson as ResearchMateError.details)
#
# Question to settle: does a loader return ONE Document per file, or could a
# PDF return one-per-page? Pick one and be consistent. (Recommend one per file;
# page numbers go in metadata.)

@dataclass(frozen=True)
class Document:
    text: str
    source: str
    metadata: dict = field(default_factory=dict)

# -----------------------------------------------------------------------------
# TODO 3 — class Chunk  (what a CHUNKER returns: a slice of a Document)
# -----------------------------------------------------------------------------
# A frozen dataclass holding:
#   - text: str                  -> the chunk's text
#   - source: str                -> carried through from the Document
#   - index: int                 -> this chunk's position in the doc (0, 1, 2…)
#                                    so you can cite "chunk 3 of paper.pdf" and
#                                    reassemble order later
#   - metadata: dict             -> default_factory=dict (char offsets, page, …)
#
# Think ahead: on Day 3 each Chunk gets embedded + stored in ChromaDB, and on
# Day 4 answers cite chunks by id. `source` + `index` are the minimum that makes
# a citation meaningful. Add char start/end to metadata if it's cheap now.
#
# -----------------------------------------------------------------------------
# Write Document first, then Chunk. They're tiny — the value is deciding the
# FIELDS, not the syntax. When done, say "check" and I'll review the contract
# before you build loaders on top of it.
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    index: int
    metadata: dict = field(default_factory=dict)