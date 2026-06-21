from dataclasses import dataclass, field

@dataclass(frozen=True)
class Document:
    text: str
    source: str
    metadata: dict = field(default_factory=dict)

@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    index: int
    metadata: dict = field(default_factory=dict)