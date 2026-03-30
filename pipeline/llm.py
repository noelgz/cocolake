from __future__ import annotations

import asyncio
import json
import logging
import time

from pipeline.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

_client = None
_last_call = 0.0

_MIN_DELAY = 4.0
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 10.0


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


async def ask_json(prompt: str) -> dict | list:
    """Send a prompt to Gemini and parse the JSON reply"""
    global _last_call

    wait = _MIN_DELAY - (time.time() - _last_call)
    if wait > 0:
        await asyncio.sleep(wait)

    from google.genai import types

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            _last_call = time.time()
            client = _get_client()
            response = await client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            text = response.text.strip()
            return json.loads(text)

        except json.JSONDecodeError:
            logger.error("Gemini returned invalid JSON")
            raise

        except Exception as exc:
            is_rate_limit = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)
            if is_rate_limit and attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning("Rate limited, retry %d/%d in %.0fs…", attempt, _MAX_RETRIES, delay)
                await asyncio.sleep(delay)
                continue
            raise

    raise RuntimeError("Gemini: max retries exceeded")
