import logging
from rag.retriever import Retriever
from rag.llm_client import LLMClient
from common.errors import LLMError
logger = logging.getLogger(__name__)



class RAGPipeline:

    def __init__(self, retreiver: Retriever, llm_client: LLMClient):
        self.retreiver = retreiver
        self.llm_client = llm_client

    @staticmethod
    def _build_context(records: list[dict]) -> str:
        blocks: list[str] = []

        for i, record in enumerate(records, start=1):
            metadata = record.get("metadata") or {}

            source = metadata.get("source")
            if not source:
                record_id = record.get("id", "")
                source = record_id.rsplit(":", 1)[0] if ":" in record_id else record_id

            text = record.get("text", "")
            blocks.append(f"[{i}] (source: {source}) {text}")

        return "\n\n".join(blocks)


    def answer(self, question: str, k: int = 5) -> dict:
        if not question:
            raise LLMError("Question not provided")
        
        records = self.retreiver.retrieve(question, k)

        if not records:
            return {
                "answer" : "no relevant context found",
                "citations" : [],
                "questions" : question
            }

        context = self._build_context(records)

        system = (
        "You are a research assistant. Answer the question USING ONLY the "
        "context below. If the answer is not in the context, say you don't "
        "know. Cite sources by their [n] number."
        )

        prompt = f"Context:\n{context}\n\nQuestion: {question}"

        text = self.llm_client.generate(prompt, system)

        return {
        "answer": text,
        "citations": [
          {"n": i+1, "id": r["id"],
           "source": (r["metadata"].get("source") or r["id"].rsplit(":", 1)[0]),
           "score": r["score"]}
          for i, r in enumerate(records)
        ],
        "question": question,
      }
