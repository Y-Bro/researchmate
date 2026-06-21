import pytest

from google.genai import errors

from common.config import Settings
from common.errors import EmbeddingError
from rag.embedder import Embedder


# ---------------------------------------------------------------------------
# Test doubles — a hand-built fake that mimics the google-genai surface the
# embedder touches: `client.models.embed_content(...)` returning an object
# with `.embeddings`, each item exposing `.values` (a list[float]).
# No network, no real SDK call.
# ---------------------------------------------------------------------------


class FakeEmbedding:
    def __init__(self, values):
        self.values = values


class FakeEmbedResponse:
    """Wraps N embedding vectors. `dim` controls vector length."""

    def __init__(self, n, dim=4):
        self.embeddings = [FakeEmbedding([0.1] * dim) for _ in range(n)]


class FakeEmptyResponse:
    """Model returns no embeddings at all."""

    embeddings = []


class FakeAPIError(errors.APIError):
    """A real APIError subclass with a trivial constructor.

    The production code catches `errors.APIError` and reads `.code`; this is
    an instance of that class, so the `except` branch fires, without dragging
    in the SDK's complex APIError signature.
    """

    def __init__(self, code):
        self.code = code
        self.message = f"fake api error {code}"
        Exception.__init__(self, self.message)


class FakeModels:
    """Scripts successive embed_content calls from a queue.

    Each queue item is either an Exception (raised) or a response (returned).
    Records how many times it was called and the last kwargs it saw.
    """

    def __init__(self, side_effect):
        self._queue = list(side_effect)
        self.calls = 0
        self.last_kwargs = None

    def embed_content(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        item = self._queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class FakeClient:
    def __init__(self, side_effect):
        self.models = FakeModels(side_effect)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def settings():
    """Settings built directly — never touches load_settings() or the real .env."""
    return Settings(
        gemini_api_key="test-key",
        gemini_model="fake-model",
        embedding_model="text-embedding-004",
        request_timeout=30,
        max_retries=3,
    )


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Record backoff sleeps and make them instant — retry tests must not wait."""
    sleeps = []
    monkeypatch.setattr("rag.embedder.time.sleep", lambda s: sleeps.append(s))
    return sleeps


def make_embedder(settings, side_effect):
    fake = FakeClient(side_effect)
    return Embedder(settings, client=fake), fake


# ---------------------------------------------------------------------------
# embed_texts — happy path & validation
# ---------------------------------------------------------------------------


def test_embed_texts_batch_returns_one_vector_per_input(settings):
    embedder, fake = make_embedder(settings, [FakeEmbedResponse(3, dim=4)])

    result = embedder.embed_texts(["a", "b", "c"])

    assert len(result) == 3
    assert all(isinstance(v, list) for v in result)
    assert all(len(v) == 4 for v in result)
    assert fake.models.calls == 1
    assert fake.models.last_kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"


def test_embed_texts_empty_list_returns_empty_without_calling_api(settings):
    embedder, fake = make_embedder(settings, [FakeEmbedResponse(1)])

    result = embedder.embed_texts([])

    assert result == []
    assert fake.models.calls == 0


@pytest.mark.parametrize("bad_item", ["", "   "])
def test_embed_texts_blank_item_raises_without_calling_api(settings, bad_item):
    embedder, fake = make_embedder(settings, [FakeEmbedResponse(2)])

    with pytest.raises(EmbeddingError):
        embedder.embed_texts(["good", bad_item])

    assert fake.models.calls == 0


# ---------------------------------------------------------------------------
# embed_query — happy path & validation
# ---------------------------------------------------------------------------


def test_embed_query_returns_single_flat_vector(settings):
    embedder, fake = make_embedder(settings, [FakeEmbedResponse(1, dim=5)])

    result = embedder.embed_query("a real query")

    assert isinstance(result, list)
    assert len(result) == 5
    assert all(isinstance(x, float) for x in result)  # flat, not nested
    assert fake.models.calls == 1
    assert fake.models.last_kwargs["config"].task_type == "RETRIEVAL_QUERY"


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_embed_query_blank_raises_without_calling_api(settings, blank):
    embedder, fake = make_embedder(settings, [FakeEmbedResponse(1)])

    with pytest.raises(EmbeddingError):
        embedder.embed_query(blank)

    assert fake.models.calls == 0


# ---------------------------------------------------------------------------
# Retry behaviour (shared _embed helper)
# ---------------------------------------------------------------------------


def test_transient_error_retries_then_succeeds(settings, _no_sleep):
    embedder, fake = make_embedder(
        settings, [FakeAPIError(503), FakeEmbedResponse(1)]
    )

    result = embedder.embed_texts(["q"])

    assert len(result) == 1
    assert fake.models.calls == 2
    assert _no_sleep == [1]  # backoff happened, but instant


def test_transient_error_exhausts_retries_then_raises(settings, _no_sleep):
    # max_retries=3 -> 1 initial + 3 retries = 4 calls, attempt hits 4 > 3.
    embedder, fake = make_embedder(
        settings, [FakeAPIError(503)] * 4
    )

    with pytest.raises(EmbeddingError) as exc:
        embedder.embed_texts(["q"])

    assert fake.models.calls == 4
    assert exc.value.details["attempts"] == 4
    assert _no_sleep == [1, 2, 4]


def test_non_transient_error_raises_immediately_no_retry(settings):
    original = FakeAPIError(400)
    embedder, fake = make_embedder(settings, [original])

    with pytest.raises(EmbeddingError) as exc:
        embedder.embed_texts(["q"])

    assert fake.models.calls == 1  # no retry
    assert exc.value.__cause__ is original


def test_generic_exception_retried_then_raises(settings, _no_sleep):
    embedder, fake = make_embedder(
        settings, [RuntimeError("boom")] * 4
    )

    with pytest.raises(EmbeddingError) as exc:
        embedder.embed_texts(["q"])

    assert fake.models.calls == 4
    assert exc.value.details["attempts"] == 4
    assert exc.value.details["error_type"] == "RuntimeError"


def test_empty_embeddings_raises_immediately_no_retry(settings):
    embedder, fake = make_embedder(settings, [FakeEmptyResponse()])

    with pytest.raises(EmbeddingError, match="did not generate"):
        embedder.embed_texts(["q"])

    assert fake.models.calls == 1  # guard fires inside try, not retried


# ---------------------------------------------------------------------------
# DRY: both public methods route through the same _embed retry helper.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda e: e.embed_texts(["q"]),
        lambda e: e.embed_query("q"),
    ],
)
def test_both_public_methods_share_retry_helper(settings, _no_sleep, call):
    embedder, fake = make_embedder(
        settings, [FakeAPIError(503), FakeEmbedResponse(1)]
    )

    call(embedder)

    assert fake.models.calls == 2  # retried via the shared helper
    assert _no_sleep == [1]
