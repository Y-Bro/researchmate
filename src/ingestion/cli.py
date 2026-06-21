import argparse, json, logging, sys
from pathlib import Path
from ingestion.loaders import Loader, MarkdownLoader, PdfLoader, HtmlLoader
from ingestion.chunkers import Chunker, FixedSizeChunker, RecursiveChunker
from common.errors import IngestionError, ChunkingError
from ingestion.models import Chunk
logger = logging.getLogger(__name__)

type summary = dict

def build_loader_registery() -> dict[str, Loader]:
    loaders = [MarkdownLoader(), PdfLoader(), HtmlLoader()]
    registry = {}
    for loader in loaders:
        loader_extensions = loader.extensions
        for extension in loader_extensions:
            registry[extension] = loader
    return registry
    


def make_chunker(name, size, overlap) -> Chunker:
    if name == "fixed": 
        return FixedSizeChunker(size, overlap)
    
    if name == "recursive":
        return RecursiveChunker(size, overlap)

    raise ValueError(f"unknown chunker: {name}")


def chunk_to_dict(chunk: Chunk) -> dict:
    return {
        "text" : chunk.text,
        "source": chunk.source,
        "index": chunk.index,
        "metadata": chunk.metadata
    }


def process_file(path: Path, registry: dict[str, Loader], chunker:Chunker) -> list[Chunk]:
    extension = path.suffix.lower()
    loader = registry.get(extension)

    if not loader:
        raise IngestionError(f"No loader for extension: {extension}")

    document = loader.load(path)
    return chunker.chunk(document)


def run(input_dir:str, output_path:str, chunker:Chunker, registery) -> summary:
    in_dir = Path(input_dir)
    out_path = Path(output_path)

    if not in_dir.exists():
        raise ChunkingError(f"Input path does not exist: {in_dir}")

    if not in_dir.is_dir():
        raise ChunkingError(f"Input path is not a directory: {in_dir}")
    
    files = sorted(p for p in in_dir.iterdir() if p.is_file())

    out_path.parent.mkdir(parents=True, exist_ok=True)

    files_ok = 0
    files_failed = 0
    total_chunks = 0

    with out_path.open("w", encoding="utf-8") as f:
        for file in files:
            try:
                chunks = process_file(file, registery, chunker) 
                for chunk in chunks:
                    f.write(json.dumps(chunk_to_dict(chunk)) + "\n")
            
                files_ok += 1
                total_chunks += len(chunks)
            except (IngestionError, ChunkingError) as exc:
                logger.warning("Skipping %s : %s", file.name, exc)
                files_failed += 1

    summary = {
        "files_ok": files_ok,
        "files_failed": files_failed,
        "total_chunks": total_chunks,
    }
    logger.info("ingestion summary: %s", summary)
    return summary

    



def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest files and write chunks as JSONL")

    parser.add_argument(
        "--input",
        default="data/raw",
        help="Input directory containing raw files",
    )

    parser.add_argument(
        "--output",
        default="data/processed/chunks.jsonl",
        help="Output JSONL file path",
    )

    parser.add_argument(
        "--chunker",
        choices=["fixed", "recursive"],
        default="recursive",
        help="Chunking strategy to use",
    )

    parser.add_argument(
        "--size",
        type=int,
        default=1000,
        help="Chunk size",
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=200,
        help="Chunk overlap",
    )

    return parser

def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    try:
        chunker = make_chunker(args.chunker, args.size, args.overlap)
        run(args.input, args.output, chunker, build_loader_registery())
    except (ChunkingError, IngestionError, ValueError) as exc:
        logger.error("ingestion failed: %s", exc)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())