import logging
from abc import ABC, abstractmethod
from rag.embedder import Embedder
from rag.vector_store import VectorStore
logger = logging.getLogger(__name__)


class Retriever(ABC):

    @abstractmethod
    def retrieve(self, query:str, k: int = 5) -> list[dict]:
        ...


class DenseRetriever(Retriever):

    def __init__(self, embedder : Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        vector = self.embedder.embed_query(query)
        return self.vector_store.query(vector, k)



#
# -----------------------------------------------------------------------------
# TODO R3 — (LATER, after BM25) make_retriever(mode, *, embedder, vector_store,
#            bm25=None) -> Retriever   — the factory the toggle uses
# -----------------------------------------------------------------------------
#   Sketch only for now (don't implement until BM25 exists):
#       if mode == "dense":  return DenseRetriever(embedder, vector_store)
#       if mode == "sparse": return BM25Retriever(bm25)
#       if mode == "hybrid": return HybridRetriever(DenseRetriever(...), BM25Retriever(...))
#       raise ValueError(f"unknown retrieval mode: {mode}")
#   This is what Settings.retrieval_mode / the ask CLI's --mode will call. Leaving
#   it as a comment now keeps the seam visible without premature code (YAGNI).
#
#
# -----------------------------------------------------------------------------
# Write R1 + R2. They're tiny — the value is the INTERFACE, not the lines. Test
# DenseRetriever with a FAKE embedder + in-memory VectorStore (or a fake store):
# assert retrieve("q", k=3) embeds the query and returns the store's records.
# Say "check" when R1+R2 are done.
# -----------------------------------------------------------------------------
