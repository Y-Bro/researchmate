from __future__ import annotations


class ResearchMateError(Exception):
    """Base class for all ResearchMate errors."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict = details or {}


class ConfigError(ResearchMateError):
    """Raised when configuration is missing or invalid."""


class LLMError(ResearchMateError):
    """Raised when a Gemini / LLM call failed."""


class RetrievalError(ResearchMateError):
    """Raised when retrieval (vector or BM25 search) failed."""


class ChunkingError(ResearchMateError):
    """Raised when document chunking failed."""

