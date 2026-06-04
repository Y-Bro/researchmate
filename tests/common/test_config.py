import pytest

from common.config import load_settings
from common.errors import ConfigError

ENV_VARS = ["GEMINI_API_KEY", "GEMINI_MODEL", "REQUEST_TIMEOUT", "MAX_RETRIES"]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Start every test from a blank slate — no leakage from the real env."""
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_loads_all_values_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("REQUEST_TIMEOUT", "45")
    monkeypatch.setenv("MAX_RETRIES", "5")

    s = load_settings()

    assert s.gemini_api_key == "test-key"
    assert s.gemini_model == "gemini-2.5-flash"
    assert s.request_timeout == 45
    assert isinstance(s.request_timeout, int)
    assert s.max_retries == 5
    assert isinstance(s.max_retries, int)


def test_optional_fields_fall_back_to_defaults(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    s = load_settings()

    assert s.gemini_model == "gemini-2.5-flash"
    assert s.request_timeout == 30
    assert s.max_retries == 3


def test_missing_api_key_raises_config_error():
    with pytest.raises(ConfigError):
        load_settings()


def test_whitespace_api_key_raises_config_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    with pytest.raises(ConfigError):
        load_settings()


def test_non_positive_timeout_raises_config_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("REQUEST_TIMEOUT", "0")
    with pytest.raises(ConfigError):
        load_settings()


def test_negative_retries_raises_config_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("MAX_RETRIES", "-1")
    with pytest.raises(ConfigError):
        load_settings()
