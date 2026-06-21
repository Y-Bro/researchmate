from abc import ABC, abstractmethod
from ingestion.models import Document, Chunk
from common.errors import ChunkingError

class Chunker(ABC):

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]: 
        ...


class FixedSizeChunker(Chunker):

    def __init__(self, size:int = 1000, overlap: int = 200):
        self.chunk_size = size
        self.chunk_overlap = overlap

        if size <= 0 or overlap < 0 or overlap >= size:
            raise ChunkingError("Wrong chunking args provided")

    def chunk(self, document: Document) -> list[Chunk]:
        step = self.chunk_size - self.chunk_overlap
        text = document.text
        chunks = []
        i = 0
        index = 0
        while i < len(text):
            piece = text[i : i + self.chunk_size]
            chunks.append(Chunk(text = piece, source = document.source, index = index, metadata={
                "start" : i,
                "end": i + len(piece),
                **document.metadata
            }))
            index = index + 1
            i = i + step
        return chunks


class RecursiveChunker(Chunker):
    def __init__(self, size : int = 1000, overlap: int = 200, separators : list[str] | None = None):
        self.chunk_size = size
        self.chunk_overlap = overlap
        self.separators = separators if separators is not None else ["\n\n", "\n", ". ", " ", ""]


        if size <= 0 or overlap >= size or overlap < 0:
            raise ChunkingError("Not valide chunking configs")
        
        self.step = size - overlap

        
    def _split(self, text: str, separators: list[str]) -> list[str]:
        sep = separators[0]
        rest = separators[1:]

        if sep == "":
            return [
                text[i : i + self.chunk_size]
                for i in range(0, len(text), self.chunk_size)
            ]

        parts = text.split(sep)

        out: list[str] = []
        buf = ""  

        for part in parts:
            candidate = (buf + sep + part) if buf else part

            if len(candidate) <= self.chunk_size:
                buf = candidate
            else:
                if buf:
                    out.append(buf)
                if len(part) <= self.chunk_size:
                    buf = part
                else:
                    out.extend(self._split(part, rest))
                    buf = ""
        if buf:
            out.append(buf)

        return out

    def chunk(self, document: Document) -> list[Chunk]:
        text = document.text

        if not text.strip():
            raise ChunkingError("No data to chunk")

        pieces = self._split(text, self.separators)
        chunks: list[Chunk] = []
        cursor = 0
        for index, piece in enumerate(pieces):
            start = text.find(piece, cursor)
            if start == -1:  
                start = cursor
            end = start + len(piece)
            cursor = end

            chunks.append(
                Chunk(
                    text=piece,
                    source=document.source,
                    index=index,
                    metadata={
                        "start": start,
                        "end": end,
                        **document.metadata,
                    },
                )
            )

        return chunks


