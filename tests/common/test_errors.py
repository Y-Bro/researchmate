import pytest

from common.errors import (
    ChunkingError,
    ConfigError,
    LLMError,
    ResearchMateError,
    RetrievalError,
)

SUBCLASSES = [ConfigError, LLMError, RetrievalError, ChunkingError]


def test_base_stores_message():
    err = ResearchMateError("something broke")
    assert err.message == "something broke"


def test_str_returns_message():
    err = ResearchMateError("something broke")
    assert str(err) == "something broke"


def test_details_defaults_to_empty_dict():
    err = ResearchMateError("oops")
    assert err.details == {}


def test_details_stored_when_provided():
    err = ResearchMateError("oops", details={"key": "value"})
    assert err.details == {"key": "value"}


def test_details_is_keyword_only():
    # details comes after `*`, so passing it positionally must fail.
    with pytest.raises(TypeError):
        ResearchMateError("oops", {"key": "value"})


@pytest.mark.parametrize("exc_cls", SUBCLASSES)
def test_subclass_of_base(exc_cls):
    assert issubclass(exc_cls, ResearchMateError)


@pytest.mark.parametrize("exc_cls", SUBCLASSES)
def test_subclass_inherits_base_init(exc_cls):
    err = exc_cls("boom", details={"x": 1})
    assert err.message == "boom"
    assert err.details == {"x": 1}


@pytest.mark.parametrize("exc_cls", SUBCLASSES)
def test_base_catches_subclass(exc_cls):
    with pytest.raises(ResearchMateError):
        raise exc_cls("caught as base")


def test_exception_chaining_sets_cause():
    original = ValueError("root cause")
    try:
        raise LLMError("wrapper failed") from original
    except LLMError as exc:
        assert exc.__cause__ is original


def test_base_is_exception_subclass():
    assert issubclass(ResearchMateError, Exception)


def test_message_is_required():
    with pytest.raises(TypeError):
        ResearchMateError()  # message has no default


def test_details_not_shared_between_instances():
    a = ResearchMateError("a")
    b = ResearchMateError("b")
    a.details["k"] = "v"
    assert b.details == {}  # each instance must get its own dict


def test_subclasses_are_distinct():
    for cls in SUBCLASSES:
        for other in SUBCLASSES:
            if cls is not other:
                assert not issubclass(cls, other)


def test_specific_except_does_not_catch_sibling():
    # `except LLMError` must NOT swallow a ConfigError — it should propagate.
    with pytest.raises(ConfigError):
        try:
            raise ConfigError("boom")
        except LLMError:
            pytest.fail("LLMError wrongly caught a ConfigError")
