import pytest

from google.genai import errors

from common.config import Settings
from common.errors import LLMError
from rag.llm_client import LLMClient


# ---------------------------------------------------------------------------
# Test doubles — a hand-built fake that mimics the google-genai surface the
# client touches: `client.models.generate_content(...)` returning an object
# with `.text`, `.usage_metadata`, `.candidates`. No network, no real SDK call.
# ---------------------------------------------------------------------------


class FakeUsage:
    total_token_count = 10
    cached_content_token_count = 0
    prompt_token_count = 6
    candidates_token_count = 4


class FakeCandidate:
    finish_reason = "STOP"


class FakeResponse:
    def __init__(self, text="hello"):
        self.text = text
        self.usage_metadata = FakeUsage()
        self.candidates = [FakeCandidate()]


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
    """Scripts successive generate_content calls from a queue.

    Each queue item is either an Exception (raised) or a response (returned).
    Records how many times it was called and the last kwargs it saw.
    """

    def __init__(self, side_effect):
        self._queue = list(side_effect)
        self.calls = 0
        self.last_kwargs = None

    def generate_content(self, **kwargs):
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
        request_timeout=30,
        max_retries=2,
    )


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Record backoff sleeps and make them instant — retry tests must not wait."""
    sleeps = []
    monkeypatch.setattr("rag.llm_client.time.sleep", lambda s: sleeps.append(s))
    return sleeps


def make_client(settings, side_effect):
    fake = FakeClient(side_effect)
    return LLMClient(settings, client=fake), fake


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_returns_text(settings):
    client, fake = make_client(settings, [FakeResponse("the answer")])

    result = client.generate("a real prompt")

    assert result == "the answer"
    assert fake.models.calls == 1


def test_system_instruction_is_forwarded(settings):
    client, fake = make_client(settings, [FakeResponse()])

    client.generate("prompt", system="you are terse")

    config = fake.models.last_kwargs["config"]
    assert config.system_instruction == "you are terse"


# ---------------------------------------------------------------------------
# Input validation — empty prompt must fail before any API call
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_prompt", ["", "   ", None])
def test_empty_prompt_raises_without_calling_api(settings, bad_prompt):
    client, fake = make_client(settings, [FakeResponse()])

    with pytest.raises(LLMError):
        client.generate(bad_prompt)

    assert fake.models.calls == 0


# ---------------------------------------------------------------------------
# Empty / blank response from the model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("empty_text", ["", "   ", None])
def test_empty_response_raises_llmerror(settings, empty_text):
    client, fake = make_client(settings, [FakeResponse(empty_text)])

    with pytest.raises(LLMError):
        client.generate("a real prompt")

    assert fake.models.calls == 1


# ---------------------------------------------------------------------------
# Permanent errors — raise immediately, never retry
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_permanent_error_raises_immediately(settings, code):
    client, fake = make_client(settings, [FakeAPIError(code)])

    with pytest.raises(LLMError) as exc:
        client.generate("a real prompt")

    assert fake.models.calls == 1  # no retry
    assert exc.value.details["status_code"] == code


def test_permanent_error_chains_original_cause(settings):
    original = FakeAPIError(400)
    client, _ = make_client(settings, [original])

    with pytest.raises(LLMError) as exc:
        client.generate("a real prompt")

    assert exc.value.__cause__ is original


# ---------------------------------------------------------------------------
# Transient errors — retry with backoff
# ---------------------------------------------------------------------------


def test_transient_error_retries_then_succeeds(settings):
    client, fake = make_client(
        settings, [FakeAPIError(503), FakeResponse("recovered")]
    )

    result = client.generate("a real prompt")

    assert result == "recovered"
    assert fake.models.calls == 2


def test_transient_error_exhausts_retries_then_raises(settings, _no_sleep):
    # max_retries=2 -> 1 initial + 2 retries = 3 calls, then give up.
    client, fake = make_client(
        settings, [FakeAPIError(503), FakeAPIError(503), FakeAPIError(503)]
    )

    with pytest.raises(LLMError) as exc:
        client.generate("a real prompt")

    assert fake.models.calls == 3
    assert exc.value.details["attempts"] == 3


def test_backoff_schedule_grows_exponentially(settings, _no_sleep):
    client, _ = make_client(
        settings, [FakeAPIError(503), FakeAPIError(503), FakeAPIError(503)]
    )

    with pytest.raises(LLMError):
        client.generate("a real prompt")

    # sleeps fire before each retry continue: 2**0, 2**1 (none before final raise)
    assert _no_sleep == [1, 2]


@pytest.mark.parametrize("code", [429, 500, 502, 503])
def test_all_transient_codes_are_retried(settings, code):
    client, fake = make_client(settings, [FakeAPIError(code), FakeResponse("ok")])

    assert client.generate("a real prompt") == "ok"
    assert fake.models.calls == 2
