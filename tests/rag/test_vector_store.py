import uuid

import chromadb
import pytest

from types import SimpleNamespace

from common.errors import RetrievalError
from ingestion.models import Chunk
from rag.vector_store import VectorStore, _clean_metadata


# ---------------------------------------------------------------------------
# Fixture — a fresh in-memory Chroma collection injected into VectorStore via
# the DI seam (collection=). Each test gets its own EphemeralClient so no two
# tests share data. No container, no real settings, no HttpClient.
# ---------------------------------------------------------------------------


@pytest.fixture
def store_and_collection():
    name = "testcol-" + uuid.uuid4().hex
    collection = chromadb.EphemeralClient().get_or_create_collection(
        name=name, configuration={"hnsw": {"space": "cosine"}}
    )
    store = VectorStore(SimpleNamespace(), collection=collection)
    return store, collection


def _chunk(text="hello", source="doc.txt", index=0, metadata=None):
    # Chroma rejects empty metadata dicts on upsert, so the default is a
    # non-empty marker. Tests that care about metadata pass their own.
    return Chunk(
        text=text,
        source=source,
        index=index,
        metadata={"loader": "test"} if metadata is None else metadata,
    )


# ---------------------------------------------------------------------------
# _clean_metadata
# ---------------------------------------------------------------------------


def test_clean_metadata_drops_none_valued_keys():
    # Arrange
    md = {"loader": "html", "title": None, "start": 0}

    # Act
    cleaned = _clean_metadata(md)

    # Assert
    assert cleaned == {"loader": "html", "start": 0}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_injected_collection_builds_without_container(store_and_collection):
    store, collection = store_and_collection

    assert store.collection is collection


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


def test_add_stores_chunks(store_and_collection):
    store, collection = store_and_collection
    chunks = [_chunk(text="a", index=0), _chunk(text="b", index=1)]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

    store.add(chunks, embeddings)

    assert collection.count() == 2


def test_add_empty_list_is_noop(store_and_collection):
    store, collection = store_and_collection

    result = store.add([], [])

    assert result is None
    assert collection.count() == 0


def test_add_length_mismatch_raises_and_stores_nothing(store_and_collection):
    store, collection = store_and_collection
    chunks = [_chunk(index=0), _chunk(index=1)]
    embeddings = [[1.0, 0.0, 0.0]]

    with pytest.raises(RetrievalError):
        store.add(chunks, embeddings)

    assert collection.count() == 0


def test_add_is_idempotent_via_upsert(store_and_collection):
    store, collection = store_and_collection
    chunks = [_chunk(text="a", index=0), _chunk(text="b", index=1)]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

    store.add(chunks, embeddings)
    store.add(chunks, embeddings)

    assert collection.count() == 2


def test_add_overwrites_on_same_id(store_and_collection):
    store, collection = store_and_collection
    cid = "doc.txt:0"

    store.add([_chunk(text="original", index=0)], [[1.0, 0.0, 0.0]])
    store.add([_chunk(text="updated", index=0)], [[0.0, 1.0, 0.0]])

    assert collection.count() == 1
    stored = collection.get(ids=[cid])
    assert stored["documents"] == ["updated"]


def test_add_drops_none_metadata(store_and_collection):
    store, collection = store_and_collection
    cid = "doc.txt:0"
    chunk = _chunk(index=0, metadata={"loader": "html", "title": None})

    store.add([chunk], [[1.0, 0.0, 0.0]])

    stored = collection.get(ids=[cid], include=["metadatas"])
    metadata = stored["metadatas"][0]
    assert "title" not in metadata
    assert metadata["loader"] == "html"


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


def test_query_ranking_closest_first(store_and_collection):
    store, collection = store_and_collection
    chunks = [
        _chunk(text="x-axis", source="x", index=0),
        _chunk(text="y-axis", source="y", index=0),
    ]
    embeddings = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    store.add(chunks, embeddings)

    results = store.query([0.9, 0.1, 0.0], k=2)

    assert results[0]["text"] == "x-axis"
    assert results[0]["score"] > results[1]["score"]
    assert isinstance(results[0]["score"], float)
    assert -1.0 <= results[0]["score"] <= 1.0


def test_query_record_shape(store_and_collection):
    store, collection = store_and_collection
    store.add([_chunk(text="a", index=0)], [[1.0, 0.0, 0.0]])

    results = store.query([1.0, 0.0, 0.0], k=1)

    assert len(results) == 1
    assert set(results[0].keys()) == {"id", "text", "metadata", "score"}


def test_query_empty_collection_returns_empty(store_and_collection):
    store, _ = store_and_collection

    results = store.query([1.0, 0.0, 0.0], k=5)

    assert results == []


@pytest.mark.parametrize(
    "embedding, k",
    [
        ([], 5),
        ([1.0, 0.0, 0.0], 0),
        ([1.0, 0.0, 0.0], -1),
    ],
)
def test_query_validation_raises(store_and_collection, embedding, k):
    store, _ = store_and_collection

    with pytest.raises(RetrievalError):
        store.query(embedding, k=k)
