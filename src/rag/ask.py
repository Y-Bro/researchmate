import argparse
import logging
import sys

from common.config import load_settings
from common.errors import ConfigError, EmbeddingError, RetrievalError, LLMError
from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.retriever import DenseRetriever, Retriever
from rag.llm_client import LLMClient
from rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


def build_retriever(mode: str, settings) -> Retriever:
    if mode == "dense":
        embedder = Embedder(settings)
        store = VectorStore(settings)  # connects to the Chroma container
        return DenseRetriever(embedder, store)

    raise ValueError(f"unsupported retrieval mode (yet): {mode}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask a question against the indexed corpus (RAG)."
    )
    parser.add_argument("question", help="the question to answer")
    parser.add_argument(
        "--k", type=int, default=5, help="number of chunks to retrieve"
    )
    parser.add_argument(
        "--mode",
        choices=["dense", "sparse", "hybrid"],
        default="dense",
        help="retrieval strategy (sparse/hybrid arrive with BM25)",
    )
    return parser


def format_output(result: dict) -> str:
    lines = ["Answer:", result.get("answer", ""), ""]

    citations = result.get("citations") or []
    if citations:
        lines.append("Sources:")
        for c in citations:
            score = c.get("score")
            score_str = f" (score {score:.3f})" if isinstance(score, (int, float)) else ""
            lines.append(f"  [{c.get('n')}] {c.get('source')}{score_str}")
    else:
        lines.append("Sources: none")

    return "\n".join(lines)


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    try:
        settings = load_settings()
        retriever = build_retriever(args.mode, settings)
        llm = LLMClient(settings)
        pipeline = RAGPipeline(retriever, llm)
        result = pipeline.answer(args.question, k=args.k)
        print(format_output(result))
    except (ConfigError, EmbeddingError, RetrievalError, LLMError, ValueError) as exc:
        logger.error("ask failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
