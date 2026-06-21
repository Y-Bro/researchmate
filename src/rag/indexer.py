
import argparse, json, logging, sys
from pathlib import Path
from ingestion.models import Chunk
from common.config import load_settings
from common.errors import RetrievalError, EmbeddingError, ConfigError
from rag.embedder import Embedder
from rag.vector_store import VectorStore
logger = logging.getLogger(__name__)


def read_chunks(path: Path) -> list[Chunk]:
    if not path.exists():
        raise RetrievalError(f"Chunks file does not exist: {path}")

    chunks: list[Chunk] = []
    skipped = 0

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                rec = json.loads(line)

                chunk = Chunk(
                    text=rec["text"],
                    source=rec["source"],
                    index=rec["index"],
                    metadata=rec.get("metadata", {}),
                )

                chunks.append(chunk)

            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                skipped += 1
                logger.warning(
                    "Skipping malformed chunk line %s in %s: %s",
                    line_no,
                    path,
                    exc,
                )

    if skipped:
        logger.warning("Skipped %s malformed chunk lines from %s", skipped, path)

    return chunks
    

class Indexer:

    def __init__(self, embedder: Embedder, vector_store : VectorStore, *, batch_size=100):
        self.embedder = embedder
        self.vector_store = vector_store
        self.batch_size = batch_size

    def index(self, chunks: list[Chunk]) -> dict:
        if not chunks:
            return {
                "indexed" : 0,
                "batches" : 0
            }
        
        indexed = 0
        batches = 0

        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start: start + self.batch_size]
            texts = [c.text for c in batch]
            vectors = self.embedder.embed_texts(texts)
            self.vector_store.add(batch, vectors)

            indexed += len(batch)
            batches += 1
        
        return {
            "indexed" : indexed,
            "batches" : batches
        }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
    "--input",
    default="data/processed/chunks.jsonl",
    help="Path to chunks JSONL file",
    )

    parser.add_argument(
    "--batch-size",
    type=int,
    default=100,
    help="Number of chunks to embed/store per batch",
    )

    return parser

def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)

    try:
        settings = load_settings()
        embedder = Embedder(settings)
        store = VectorStore(settings)

        chunks = read_chunks(Path(args.input))

        summary = Indexer(
            embedder,
            store,
            batch_size=args.batch_size,
        ).index(chunks)

        logger.info("index summary: %s", summary)

    except (ConfigError, EmbeddingError, RetrievalError) as exc:
        logger.error("indexing failed: %s", exc)
        return 1

    return 0



if __name__ == "__main__":
    sys.exit(main())
