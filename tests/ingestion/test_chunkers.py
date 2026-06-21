# =============================================================================
# test_chunkers.py — behaviour tests for FixedSizeChunker.
#
# No I/O here — chunkers are pure functions over a Document, so build Documents
# in-memory and assert on the returned list[Chunk]. Cover the overlap math, the
# fail-fast guards, and the boundary cases (short/empty text).
# =============================================================================

import pytest

from ingestion.chunkers import FixedSizeChunker
from ingestion.models import Document, Chunk
from common.errors import ChunkingError


# -----------------------------------------------------------------------------
# Construction / validation (fail-fast guards)
# -----------------------------------------------------------------------------
def test_defaults_construct():
    # K1 — FixedSizeChunker() with no args constructs fine (size=1000, overlap=200).
    chunker = FixedSizeChunker()

    assert chunker.chunk_size == 1000
    assert chunker.chunk_overlap == 200


def test_overlap_ge_size_raises():
    # K2 — the loop-forever guard: overlap == size and overlap > size both raise.
    with pytest.raises(ChunkingError):
        FixedSizeChunker(size=10, overlap=10)

    with pytest.raises(ChunkingError):
        FixedSizeChunker(size=10, overlap=20)


@pytest.mark.parametrize("size", [0, -1])
def test_bad_size_raises(size):
    # K3 — size=0 and size=-1 -> ChunkingError.
    with pytest.raises(ChunkingError):
        FixedSizeChunker(size=size, overlap=0)


def test_negative_overlap_raises():
    # K4 — overlap=-1 -> ChunkingError.
    with pytest.raises(ChunkingError):
        FixedSizeChunker(size=10, overlap=-1)


# -----------------------------------------------------------------------------
# Chunking behaviour
# -----------------------------------------------------------------------------
TEXT = "abcdefghijklmnopqrstuvwxyz"  # len 26
EXPECTED_TEXTS = ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]
EXPECTED_STARTS = [0, 7, 14, 21]


def test_chunks_cover_text_with_overlap():
    # K5 — size=10, overlap=3, step=7 over a len-26 string.
    chunker = FixedSizeChunker(size=10, overlap=3)
    document = Document(text=TEXT, source="x.md")

    chunks = chunker.chunk(document)

    assert len(chunks) == 4
    assert [c.text for c in chunks] == EXPECTED_TEXTS
    # each non-first chunk repeats the 3-char overlap from the previous window
    assert chunks[1].text[:3] == TEXT[7:10] == "hij"


def test_index_increments():
    # K6 — c.index for the 4 chunks == [0, 1, 2, 3].
    chunker = FixedSizeChunker(size=10, overlap=3)
    document = Document(text=TEXT, source="x.md")

    chunks = chunker.chunk(document)

    assert [c.index for c in chunks] == [0, 1, 2, 3]


def test_offsets_and_metadata_inherited():
    # K7 — char offsets point at the chunk and loader metadata is inherited.
    chunker = FixedSizeChunker(size=10, overlap=3)
    document = Document(text=TEXT, source="x.md", metadata={"loader": "markdown"})

    chunks = chunker.chunk(document)

    for chunk, expected_start in zip(chunks, EXPECTED_STARTS):
        assert chunk.source == "x.md"
        assert chunk.metadata["start"] == expected_start
        assert chunk.metadata["end"] == expected_start + len(chunk.text)
        assert chunk.metadata["loader"] == "markdown"
        # offsets actually point at the chunk -> valid Day-4 citations
        assert TEXT[chunk.metadata["start"]:chunk.metadata["end"]] == chunk.text


def test_short_text_single_chunk():
    # K8 — text shorter than size -> exactly one chunk holding the whole string.
    chunker = FixedSizeChunker(size=10, overlap=3)
    document = Document(text="hi", source="x.md")

    chunks = chunker.chunk(document)

    assert len(chunks) == 1
    assert chunks[0].text == "hi"
    assert chunks[0].index == 0
    assert chunks[0].metadata["start"] == 0
    assert chunks[0].metadata["end"] == 2


def test_empty_text_returns_empty_list():
    # K9 — empty in, empty out.
    chunker = FixedSizeChunker(size=10, overlap=3)
    document = Document(text="", source="x.md")

    chunks = chunker.chunk(document)

    assert chunks == []


def test_no_overlap_tiles_exactly():
    # K10 — overlap=0, size=5 over a len-10 string -> 2 adjacent chunks, step==size.
    chunker = FixedSizeChunker(size=5, overlap=0)
    document = Document(text="abcdefghij", source="x.md")

    chunks = chunker.chunk(document)

    assert len(chunks) == 2
    assert [c.text for c in chunks] == ["abcde", "fghij"]
    assert "".join(c.text for c in chunks) == "abcdefghij"
