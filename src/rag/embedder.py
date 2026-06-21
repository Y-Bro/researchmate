import time, logging
from google import genai
from google.genai import types, errors
from common.config import Settings
from common.errors import EmbeddingError
logger = logging.getLogger(__name__)


class Embedder:

    def __init__(self, settings : Settings, *, client=None, model_name=None):
        self.settings = settings
        self.client= client if client is not None else genai.Client(api_key=self.settings.gemini_api_key
        , http_options={"timeout": self.settings.request_timeout * 1000})
        self.model_name = model_name if model_name else self.settings.embedding_model

    def _embed(self, contents: list[str], task_type: str) -> list[list[float]]:
        attempt = 0

        while True:
            try:
                start = time.monotonic()
                embedding_response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.EmbedContentConfig(
                        task_type=task_type
                    )
                )
                latency_ms = (time.monotonic() - start) * 1000
                vals = [e.values for e in embedding_response.embeddings]

                if not vals or not len(vals):
                    raise EmbeddingError("Model did not generate any embeddings")

                logger.info(
                    "Embedding Model OK | latency=%.0fms vectors=%d dim=%d",
                    latency_ms, len(vals), len(vals[0]),
                )
                return vals

            except EmbeddingError:
                raise
            except errors.APIError as e:
                if e.code not in {429, 500, 502, 503}:
                    raise EmbeddingError("Embedding model call failed", details= {
                        "error_type": type(e).__name__
                    }) from e
                attempt += 1
                if attempt > self.settings.max_retries:
                    raise EmbeddingError("Max retries reached", details = {
                        "attempts" : attempt
                    }) from e
                sleep = 2 ** (attempt - 1)
                logger.warning("Sleeping before retry")
                time.sleep(sleep)
                continue
            except Exception as e:
                attempt += 1
                if attempt > self.settings.max_retries:
                    raise EmbeddingError(
                        "Gemini call failed after retries",
                        details={"error_type": type(e).__name__, "attempts": attempt},
                    ) from e
                sleep = 2 ** (attempt - 1)
                logger.warning("Retry %d after %ss (%s)", attempt, sleep, type(e).__name__)
                time.sleep(sleep)
                continue

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not len(texts):
            return []

        for text in texts:
            if not text.strip():
                raise EmbeddingError("Empty")

        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise EmbeddingError("No query provided")

        return self._embed([text], "RETRIEVAL_QUERY")[0]
