# =============================================================================
# llm_client.py  —  the ONLY place Gemini code is allowed to live.
# =============================================================================
# WHY this rule: every other module (retrieval, chunking, the RAG pipeline)
# should ask "give me an answer for this prompt" without knowing or caring that
# Gemini is behind it. If you ever swap to OpenAI/Claude/local, you edit THIS
# FILE ONLY. That is the whole point of isolating the provider.
#
# GOAL of this module: a small class that wraps one Gemini call and makes it
# production-safe — timeout, retries with backoff, structured logging, and a
# typed error on failure.
#
# -----------------------------------------------------------------------------
# CONCEPTS you are exercising here (Day 1 LLM fundamentals)
# -----------------------------------------------------------------------------
# - tokens          : the unit Gemini bills + limits on. You will LOG how many
#                     a call used (prompt tokens + completion tokens).
# - temperature     : 0.0 = deterministic/factual, higher = more creative.
#                     For RAG you want LOW. Make it configurable, default low.
# - system prompt   : the "who you are / rules" instruction, separate from the
#                     user prompt. Gemini calls this `system_instruction`.
# - retry + backoff : networks and LLM APIs fail transiently (429, 5xx,
#                     timeouts). Retry a FEW times with GROWING waits
#                     (1s -> 2s -> 4s) so you don't hammer a struggling API.
# - timeout         : never let one call hang forever. Bound every request.
# - structured log  : log latency_ms + token counts so you can see cost/speed.
#
# -----------------------------------------------------------------------------
# DESIGN (your CLAUDE.md rules: DI + OOP, cover all paths)
# -----------------------------------------------------------------------------
# A class `LLMClient` that takes its dependencies via the constructor (DI):
#   - `settings: Settings`  -> api key, model, timeout, max_retries
#   - `client=None`         -> the Gemini SDK client. Inject it so tests can
#                              pass a fake; if None, build a real one from
#                              settings inside __init__. This is what makes the
#                              class testable WITHOUT calling the real API.
#
# =============================================================================


# -----------------------------------------------------------------------------
# TODO 1 — Imports
# -----------------------------------------------------------------------------
# You will need:
#   - `time`     (for backoff sleeps and measuring latency)
#   - `logging`  (module-level logger: `logger = logging.getLogger(__name__)`)
#   - the Gemini SDK: `from google import genai` and likely
#     `from google.genai import types` (for GenerateContentConfig)
#   - `from common.config import Settings`
#   - `from common.errors import LLMError`
# Verify the exact google-genai import/call shape from its docs — don't trust
# memory, the SDK changed names recently.

import time
import logging
from google import genai
from common.config import Settings
from common.errors import LLMError
from google.genai import types





logger = logging.getLogger(__name__)

logger.info(msg="Test")

# -----------------------------------------------------------------------------
# TODO 2 — module-level logger
# -----------------------------------------------------------------------------
#   logger = logging.getLogger(__name__)
# (Don't configure logging here — libraries log, applications configure.)


# -----------------------------------------------------------------------------
# TODO 3 — class LLMClient  (constructor / dependency injection)
# -----------------------------------------------------------------------------
# class LLMClient:
#     def __init__(self, settings, *, client=None):
#         # store settings
#         # if client is None: build the real Gemini client from
#         #   settings.gemini_api_key  (this is the ONE place a client is made)
#         # else: use the injected client  (tests pass a fake here)
#         #
#         # Think: should you also store the model name now, or read it from
#         # settings each call? Pick one and be consistent.


# -----------------------------------------------------------------------------
# TODO 4 — the public method: generate(prompt, system=None) -> str
# -----------------------------------------------------------------------------
# This is the only method the rest of the app calls. Pseudocode:
#
#   def generate(self, prompt, system=None):
#       # validate input early — empty/blank prompt is a programming error,
#       #   raise LLMError (don't waste an API call). Cover the unhappy path.
#
#       attempt = 0
#       while True:
#           try:
#               start = time.monotonic()
#
#               response = <call Gemini>:
#                   model            = self.settings.gemini_model
#                   contents         = prompt
#                   system_instruction = system          (only if provided)
#                   temperature      = <low, e.g. 0.0>
#                   timeout          = self.settings.request_timeout
#                   # ^ where the timeout goes depends on the SDK — find it.
#
#               latency_ms = (time.monotonic() - start) * 1000
#
#               # pull token counts from the response usage metadata
#               #   (prompt tokens, completion tokens, total)
#               # LOG structured: model, latency_ms, the three token counts
#               logger.info(...)
#
#               # extract and return the text. Guard: what if the response has
#               #   NO text (safety block / empty candidates)? That's a real
#               #   case — decide: raise LLMError or return ""? (Recommend
#               #   raise, so callers never silently get nothing.)
#               return <text>
#
#           except <transient error> as e:
#               attempt += 1
#               if attempt > self.settings.max_retries:
#                   raise LLMError("Gemini call failed after retries",
#                                  details={...}) from e
#               sleep = 2 ** (attempt - 1)        # 1, 2, 4 seconds
#               logger.warning("retry %d after %ss: %s", attempt, sleep, e)
#               time.sleep(sleep)
#               continue
#
#           except <permanent error> as e:
#               # bad api key (401), bad request (400) -> retrying is pointless
#               raise LLMError("Gemini call failed", details={...}) from e
#
# KEY DECISIONS for you to make (this is the real learning):
#   a) WHICH exceptions are transient (retry) vs permanent (fail fast)?
#      Look at what the SDK raises. Common transient: timeouts, 429, 500/503.
#      Common permanent: 401 auth, 400 invalid arg. If unsure which class an
#      error is, lean toward NOT retrying (fail fast beats hammering).
#   b) Always use `raise LLMError(...) from e` — keep the original cause in the
#      traceback (you built this into errors.py already).
#   c) Put useful stuff in `details=` (model, attempt count) — that dict you
#      designed in ResearchMateError pays off here.


# -----------------------------------------------------------------------------
# DONE WHEN (Day 1 finish line)
# -----------------------------------------------------------------------------
# A tiny throwaway script (NOT committed in src/, or put it in main.py) does:
#   settings = load_settings()
#   client = LLMClient(settings)
#   print(client.generate("Say hello in one sentence."))
# ...and you SEE a real answer + a log line with latency_ms and token counts.
#
# Then tests (next /goal): inject a FAKE client to assert
#   - happy path returns text
#   - transient error retries then succeeds / then raises after max_retries
#   - permanent error raises LLMError immediately (no retry)
#   - empty prompt raises LLMError before any call
# All without touching the real API.
