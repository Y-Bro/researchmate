import time, logging
import chromadb
from ingestion.models import Chunk
from common.config import Settings
from common.errors import RetrievalError
logger = logging.getLogger(__name__)

def _clean_metadata(md: dict) -> dict:
      return {k: v for k, v in md.items() if v is not None}

class VectorStore:

    def __init__(self, settings: Settings, *, client=None, collection=None):
        self.settings = settings
        if collection is not None:
            self.collection = collection
        else:
            client = client or chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            self.collection = client.get_or_create_collection(name=settings.chroma_collection_name, configuration={"hnsw": {"space": "cosine"}})

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        
        if len(chunks) != len(embeddings):
            raise RetrievalError("Mismatch, silent corruption")

        ids = [f"{chunk.source}:{chunk.index}" for chunk in chunks]
        documents = [c.text for c in chunks]
        metadatas = [_clean_metadata(c.metadata) for c in chunks]

        self.collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    

    def query(self, embedding: list[float], k: int = 5) -> list[dict]:
        if not embedding or not len(embedding):
            raise RetrievalError("No embedding")
        
        if k <= 0:
            raise RetrievalError("K value cannot be lower than 0")
        
        res = self.collection.query(query_embeddings=[embedding], n_results=k)

        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]

        return [
            {"id" : i, "text": d, "metadata": m, "score": 1 - dist} for i, d, m, dist in zip(ids, docs, metas, dists)
        ]

    def count(self) -> int:
        return self.collection.count()
