from abc import ABC, abstractmethod
from pathlib import Path
from ingestion.models import Document
from common.errors import IngestionError

class Loader(ABC):

    extensions: tuple[str, ...] = ()

    @abstractmethod
    def load(self, path: Path) -> Document:
        ...


class MarkdownLoader(Loader):   
    extensions = (".md", ".markdown")

    def load(self, path: Path) -> Document:
        if not path.exists():
            raise IngestionError("File not found", details={
                "path" : path.name
            })

        if not path.is_file():
            raise IngestionError("Path is not a file", details={
                "path": path.name
            })

        try:
            read_text = path.read_text(encoding="utf-8")
            if not read_text.strip():
                raise IngestionError("File is empty")

            return Document(text=read_text, source=path.name, metadata={
                "loader": "markdown"
            })

        except UnicodeDecodeError as exc:
            raise IngestionError("Path is not a valide UTF-8") from exc
        except OSError as exc:
            raise IngestionError("Could not read file") from exc