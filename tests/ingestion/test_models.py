# =============================================================================
# test_models.py — contract tests for Document and Chunk (the data shapes
# every loader/chunker passes around). These are tiny but they LOCK the
# contract: frozen (immutable) + per-instance metadata (no shared-mutable
# default).
# =============================================================================

import pytest
from dataclasses import FrozenInstanceError
from ingestion.models import Document, Chunk


# -----------------------------------------------------------------------------
# Document
# -----------------------------------------------------------------------------
def test_document_stores_fields():
    doc = Document(text="hi", source="a.md")
    assert doc.text == "hi"
    assert doc.source == "a.md"
    assert doc.metadata == {}


def test_document_is_frozen():
    doc = Document(text="hi", source="a.md")
    with pytest.raises(FrozenInstanceError):
        doc.text = "x"


def test_document_metadata_not_shared():
    d1 = Document("a", "a.md")
    d2 = Document("b", "b.md")
    d1.metadata["k"] = 1
    assert d2.metadata == {}


# -----------------------------------------------------------------------------
# Chunk
# -----------------------------------------------------------------------------
def test_chunk_stores_fields():
    chunk = Chunk(text="t", source="a.md", index=0)
    assert chunk.text == "t"
    assert chunk.source == "a.md"
    assert chunk.index == 0
    assert chunk.metadata == {}


def test_chunk_is_frozen():
    chunk = Chunk(text="t", source="a.md", index=0)
    with pytest.raises(FrozenInstanceError):
        chunk.index = 5


def test_chunk_metadata_not_shared():
    c1 = Chunk("a", "a.md", 0)
    c2 = Chunk("b", "b.md", 1)
    c1.metadata["k"] = 1
    assert c2.metadata == {}
