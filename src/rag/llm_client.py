from math import nan  # TODO(fix #3): unused — delete this import
import time
import logging
from google import genai
from common.config import Settings
from common.errors import LLMError
from google.genai import types
from google.genai import errors


# TODO(fix #3): a library must not call basicConfig — it reconfigures the ROOT
# logger for the whole app as a side effect of import. Move logging setup to
# main.py (the application entry point) and delete these three lines.
logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(__name__)
logger.info(msg="Test HAHAHH")  # TODO(fix #3): delete — debug log that fires on import


class LLMClient:
    
    def __init__(self, settings : Settings, *, client=None, model_name: str | None = None):
        self.settings = settings
        self.client = client if client is not None else genai.Client(api_key=settings.gemini_api_key, http_options={"timeout": self.settings.request_timeout * 1000})
        self.model_name = model_name or settings.gemini_model


    def generate(self, prompt, system=None):
        if not prompt or not prompt.strip():
            raise LLMError("Empty prompt", details={"prompt": prompt})

        attempt = 0

        while True:
            try:
                start = time.monotonic()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config = types.GenerateContentConfig(
                        system_instruction=system,
                        temperature=0.5
                    )
                )

                latency_ms = (time.monotonic() - start) * 1000

                response_metadata = response.usage_metadata

                total_token_count = response_metadata.total_token_count
                cached_token_count = response_metadata.cached_content_token_count
                prompt_token_count = response_metadata.prompt_token_count
                completion_token_count = response_metadata.candidates_token_count

                logger.info(
                    "LLM ok | model=%s latency=%.0fms tokens: total=%s prompt=%s completion=%s cached=%s",
                    self.model_name, latency_ms,
                    total_token_count, prompt_token_count, completion_token_count, cached_token_count,
                  )
                

                text = getattr(response, "text", None)

                if not text or not text.strip():
                    raise LLMError("LLM Did not return a response", 
                    details={
                        "finish_reason": getattr(
                            response.candidates[0], "finish_reason", None
                        ) if getattr(response, "candidates", None) else None,
                    },
                )

                return text

            except LLMError:
                raise
            
            except errors.APIError as e:

                if e.code not in {429, 500, 502, 503}:
                    raise LLMError(
                        "Gemini call failed",
                        details={
                            "model": self.model_name,
                            "status_code": e.code,
                            "error_type": type(e).__name__,
                        },
                    ) from e

                attempt += 1
                if attempt > self.settings.max_retries:
                    raise LLMError(
                        "Gemini call failed after retries",
                        details={
                            "model": self.model_name,
                            "status_code": e.code,
                            "attempts": attempt,
                            "error_type": type(e).__name__,
                        },
                    ) from e
                sleep = 2 ** (attempt - 1)
                logger.warning("Sleeping before retry")
                time.sleep(sleep)
                continue

            except Exception as e:
                  attempt += 1
                  if attempt > self.settings.max_retries:
                      raise LLMError(
                          "Gemini call failed after retries",
                          details={"error_type": type(e).__name__, "attempts": attempt},
                      ) from e
                  sleep = 2 ** (attempt - 1)
                  logger.warning("Retry %d after %ss (%s)", attempt, sleep, type(e).__name__)
                  time.sleep(sleep)
                  continue
