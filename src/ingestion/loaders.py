from abc import ABC, abstractmethod
from pathlib import Path
from ingestion.models import Document
from common.errors import IngestionError
from pypdf import PdfReader
from bs4 import BeautifulSoup

class Loader(ABC):

    extensions: tuple[str, ...] = ()

    def _validate(self, path:Path) -> None:
        if not path.exists():
            raise IngestionError("File not found", details={
                "path" : path.name
            })

        if not path.is_file():
            raise IngestionError("Path is not a file", details={
                "path": path.name
            })

    @abstractmethod
    def load(self, path: Path) -> Document:
        ...


class MarkdownLoader(Loader):   
    extensions = (".md", ".markdown")

    def load(self, path: Path) -> Document:
        
        self._validate(path)

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



class PdfLoader(Loader):
    extensions = (".pdf",)

    def load(self, path: Path) -> Document:

        self._validate(path)

        try:
            reader = PdfReader(path)
            pages = []
            for p in reader.pages:
                pages.append(p.extract_text() or "")
            text = "\n".join(pages)

            if not text.strip():
                raise IngestionError(
                    "File is empty / no extractable text",
                    details={"path": path.name},
                )

            return Document(
                text=text,
                source=path.name,
                metadata={"loader": "pdf", "pages": len(reader.pages)},
            )

        except IngestionError:
            raise
        except Exception as exc:
            raise IngestionError(
                "Could not read PDF",
                details={"path": path.name},
            ) from exc



class HtmlLoader(Loader):

    extensions = (".html", ".htm")

    def load(self, path: Path) -> Document:

        self._validate(path)

        try:
            read_html = path.read_text(encoding="utf-8")
            if not read_html.strip():
                raise IngestionError("No content exists")
            
            soup = BeautifulSoup(read_html, "html.parser")

            for tag in soup(["script","style"]):
                tag.decompose()
            
            text = soup.get_text(separator="\n", strip=True)

            title = soup.title.get_text(strip=True) if soup.title else None

            if not text.strip():
                raise IngestionError("No html content exists")

            return Document(text=text, source=path.name, metadata={"loader": "html", "title" : title or None})
        except UnicodeDecodeError as exc:
            raise IngestionError("Not a valide UTF-8") from exc
        except OSError as exc:
            raise IngestionError("Not a valid file") from exc
        

# -----------------------------------------------------------------------------
# TODO 5 — class HtmlLoader(Loader)   (deps: `beautifulsoup4` — installed)
# -----------------------------------------------------------------------------
#   extensions = (".html", ".htm")
#
#   load(path):
#     1. self._validate(path)              -> existence / is_file (reuse, same as others)
#     2. READ the text exactly like MarkdownLoader does:
#          path.read_text(encoding="utf-8"); wrap UnicodeDecodeError -> IngestionError
#          and OSError -> IngestionError (HTML is just text — identical decode path).
#          DON'T duplicate logic carelessly; mirror MarkdownLoader's try/except shape.
#     3. PARSE: from bs4 import BeautifulSoup
#          soup = BeautifulSoup(html, "html.parser")
#          -> USE "html.parser" (stdlib). `lxml` is NOT in requirements; importing it
#             would crash. Stick with the built-in parser.
#     4. STRIP non-content BEFORE extracting (order matters):
#          for tag in soup(["script", "style"]): tag.decompose()
#          (else JS/CSS text lands in your chunks — a real retrieval killer)
#     5. text = soup.get_text(separator="\n", strip=True)
#     6. EMPTY rule (consistent with markdown/pdf): if not text.strip(): raise IngestionError
#          -> this raise must sit so it is NOT swallowed by a broad catch (same trap
#             you handled in PdfLoader: `except IngestionError: raise` first).
#     7. metadata: {"loader": "html", "title": <title>}
#          GOTCHA: `soup.title.string` can be None even when <title> exists (nested
#          tags inside it). Safer:
#             title = soup.title.get_text(strip=True) if soup.title else None
#             ... and treat "" as None  ->  title or None
#
#   STRUCTURE HINT — you now have TWO failure surfaces (file read + parse). Decide:
#     - one try around read, a separate try around parse, OR
#     - one try with `except IngestionError: raise` first, then targeted excepts.
#     Match whichever reads cleanest against your other two loaders. Cover all paths,
#     not just the happy one (CLAUDE.md).
#
# When done, say "check" — then we write the full ingestion test suite
# (models + Markdown + Pdf + Html) in one pass.
# -----------------------------------------------------------------------------