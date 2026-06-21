"""Tests for RecursiveChunker.

These assert against the chunker's ACTUAL behavior (verified against source),
not assumptions. Notably, unlike FixedSizeChunker, RecursiveChunker RAISES on
empty/whitespace input, and Chunk metadata carries {"start", "end", **doc.metadata}
with NO "index" key inside metadata (index lives on the Chunk itself).
"""

import pytest

from ingestion.chunkers import RecursiveChunker
from ingestion.models import Document, Chunk
from common.errors import ChunkingError


DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _doc(text: str, source: str = "test.md", metadata: dict | None = None) -> Document:
    return Document(text=text, source=source, metadata=metadata or {})


# 1. defaults construct
def test_defaults_construct():
    chunker = RecursiveChunker()
    assert chunker.chunk_size == 1000
    assert chunker.chunk_overlap == 200
    assert chunker.separators == DEFAULT_SEPARATORS


# 2. validation
def test_overlap_ge_size_raises():
    with pytest.raises(ChunkingError):
        RecursiveChunker(size=100, overlap=100)


@pytest.mark.parametrize("size", [0, -1])
def test_size_le_zero_raises(size):
    with pytest.raises(ChunkingError):
        RecursiveChunker(size=size, overlap=0)


def test_negative_overlap_raises():
    with pytest.raises(ChunkingError):
        RecursiveChunker(size=100, overlap=-1)


# 3. custom separators
def test_custom_separators_stored_as_is():
    custom = ["||", "|", ""]
    chunker = RecursiveChunker(size=100, overlap=0, separators=custom)
    assert chunker.separators == custom


def test_none_separators_falls_back_to_default():
    chunker = RecursiveChunker(size=100, overlap=0, separators=None)
    assert chunker.separators == DEFAULT_SEPARATORS


# 4. paragraph example
def test_paragraph_example_exact():
    text = "Hello world.\n\nSecond paragraph here."
    chunks = RecursiveChunker(size=20, overlap=0).chunk(_doc(text))

    assert [c.text for c in chunks] == [
        "Hello world.",
        "Second paragraph",
        "here.",
    ]
    offsets = [(c.metadata["start"], c.metadata["end"]) for c in chunks]
    assert offsets == [(0, 12), (14, 30), (31, 36)]


# 5. merge-up: tiny lines collapse into far fewer chunks
def test_merge_up_collapses_lines():
    text = "a\nb\nc\nd\ne\nf\ng\nh"  # 8 lines
    chunks = RecursiveChunker(size=20, overlap=0).chunk(_doc(text))

    assert len(chunks) < 8
    assert len(chunks) == 1


# 6. no-separator fallback
def test_no_separator_fallback_lengths():
    text = "x" * 50
    chunks = RecursiveChunker(size=20, overlap=0).chunk(_doc(text))

    assert [len(c.text) for c in chunks] == [20, 20, 10]


# 7. size invariant
def test_every_chunk_within_size():
    size = 30
    text = (
        "Intro sentence here. Another one follows.\n\n"
        "A second paragraph with several words that keeps going for a while.\n"
        "Yet another line with content to split across boundaries."
    )
    chunks = RecursiveChunker(size=size, overlap=0).chunk(_doc(text))

    assert chunks  # non-empty
    for c in chunks:
        assert len(c.text) <= size


# 8. offset citation invariant
def test_offset_citation_invariant():
    text = "Hello world.\n\nSecond paragraph here."
    chunks = RecursiveChunker(size=20, overlap=0).chunk(_doc(text))

    for c in chunks:
        start = c.metadata["start"]
        end = c.metadata["end"]
        assert text[start:end] == c.text


# 9. metadata inheritance + index
def test_metadata_inheritance_and_index():
    text = "First paragraph here.\n\nSecond paragraph also here.\n\nThird one too."
    doc = _doc(text, metadata={"loader": "markdown"})
    chunks = RecursiveChunker(size=25, overlap=0).chunk(doc)

    assert chunks
    assert [c.index for c in chunks] == list(range(len(chunks)))
    for c in chunks:
        assert isinstance(c, Chunk)
        assert c.source == "test.md"
        assert c.metadata["loader"] == "markdown"
        assert "index" not in c.metadata
        assert "start" in c.metadata
        assert "end" in c.metadata


# 10. empty / whitespace raises
@pytest.mark.parametrize("text", ["", "   ", "\n\n", "\t  \n"])
def test_empty_or_whitespace_raises(text):
    with pytest.raises(ChunkingError) as exc_info:
        RecursiveChunker(size=20, overlap=0).chunk(_doc(text))
    assert exc_info.value.message == "No data to chunk"
