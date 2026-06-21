from dotenv import load_dotenv
from dataclasses import dataclass
import os

from common.errors import ConfigError

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    request_timeout: int = 30
    max_retries: int = 3
    embedding_model: str = "text-embedding-004"


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"{name} is required but not set")
    return value

def load_settings() -> Settings:
    settings = Settings(
        gemini_api_key=_require("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
        embedding_model=os.getenv("EMBEDDING_MODEL","text-embedding-004")
    )

    validate(settings)
    return settings


def validate(s: Settings) -> None:
    if not s.gemini_api_key.strip():
        raise ConfigError("GEMINI_API_KEY is empty — set it in your .env")
    if s.request_timeout <= 0:
        raise ConfigError(f"REQUEST_TIMEOUT must be > 0, got {s.request_timeout}")
    if s.max_retries < 0:
        raise ConfigError(f"MAX_RETRIES must be >= 0, got {s.max_retries}")



