"""Gemini client — dedicated module for all Gemini API interactions.

Reads GEMINI_API_KEY from environment. Fails gracefully when key is missing.
Never exposes the key in logs.

Features: retry with exponential backoff on 429/503, in-memory cache for generate_text.
"""

import hashlib
import logging
import os
import re
import time
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

from src.core.config import GEMINI_API_KEY as _CONFIG_GEMINI_API_KEY
from src.core.config import GEMINI_MODEL as _GEMINI_MODEL
from src.core.config import GEMINI_EMBEDDING_MODEL as _GEMINI_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_api_key: str | None = None
_client: genai.Client | None = None

_generate_cache: dict[str, str | None] = {}
_MAX_CACHE = 256

_THINKING_BUDGET = 8

_rate_limited_until: float = 0.0


def _set_throttle(seconds: float) -> None:
    """Remember we are rate-limited so future calls fail fast instead of blocking."""
    global _rate_limited_until
    _rate_limited_until = time.monotonic() + max(seconds, 10.0)
    logger.warning("Gemini throttled for %.0fs (free-tier rate limit)", max(seconds, 10.0))


def _is_throttled() -> bool:
    return time.monotonic() < _rate_limited_until


def _get_api_key() -> str | None:
    global _api_key
    if _api_key is None:
        _api_key = os.getenv("GEMINI_API_KEY") or _CONFIG_GEMINI_API_KEY
        if not _api_key:
            logger.warning("GEMINI_API_KEY not set — AI features unavailable")
    return _api_key


def get_client() -> genai.Client | None:
    """Return a configured Gemini client, or None if unavailable."""
    global _client
    if _client is not None:
        return _client
    key = _get_api_key()
    if not key:
        return None
    try:
        _client = genai.Client(api_key=key)
        return _client
    except Exception as e:
        logger.error("Failed to create Gemini client: %s", e)
        return None


def is_available() -> bool:
    """Check if Gemini API is configured and accessible."""
    return _get_api_key() is not None


def _cache_key(prompt: str, system_instruction: str | None, temperature: float, max_output_tokens: int | None) -> str:
    raw = f"{prompt}|{system_instruction or ''}|{temperature}|{max_output_tokens}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_retry_after(err_str: str) -> float | None:
    """Parse 'Please retry in NNs' from a rate-limit error message."""
    match = re.search(r"retry in ([\d.]+)s", err_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def generate_text(prompt: str, system_instruction: str | None = None,
                  temperature: float = 0.3, max_output_tokens: int | None = None) -> str | None:
    """Generate text using Gemini with cache and fast throttling. Returns None on failure."""
    client = get_client()
    if not client:
        return None

    key = _cache_key(prompt, system_instruction, temperature, max_output_tokens)
    if key in _generate_cache:
        return _generate_cache[key]

    if _is_throttled():
        return None

    for attempt in range(3):
        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                thinking_config=types.ThinkingConfig(thinking_budget=_THINKING_BUDGET),
            )
            if max_output_tokens is not None:
                config.max_output_tokens = max_output_tokens
            if system_instruction:
                config.system_instruction = system_instruction
            response = client.models.generate_content(
                model=_GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
            result = response.text if response.text else None
            if len(_generate_cache) >= _MAX_CACHE:
                _generate_cache.clear()
            _generate_cache[key] = result
            return result
        except Exception as e:
            err_str = str(e)
            retry_after = _parse_retry_after(err_str)
            if retry_after is not None or "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                _set_throttle(retry_after if retry_after is not None else 30.0)
                return None
            if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < 2:
                time.sleep(1.0)
                continue
            logger.error("Gemini generate_text failed: %s", e)
            return None
    return None


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float] | None:
    """Embed a single text using gemini-embedding-001. Returns None on failure."""
    if _is_throttled():
        return None
    client = get_client()
    if not client:
        return None
    for attempt in range(3):
        try:
            response = client.models.embed_content(
                model=_GEMINI_EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            if response.embeddings and len(response.embeddings) > 0:
                return list(response.embeddings[0].values)
            return None
        except Exception as e:
            err_str = str(e)
            retry_after = _parse_retry_after(err_str)
            if retry_after is not None or "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                _set_throttle(retry_after if retry_after is not None else 30.0)
                return None
            if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < 2:
                time.sleep(1.0)
                continue
            logger.error("Gemini embed_text failed: %s", e)
            return None
    return None


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]] | None:
    """Embed a batch of texts using gemini-embedding-001. Returns None on failure."""
    if texts and _is_throttled():
        return None
    client = get_client()
    if not client:
        return None
    for attempt in range(3):
        try:
            response = client.models.embed_content(
                model=_GEMINI_EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            if response.embeddings:
                return [list(e.values) for e in response.embeddings]
            return None
        except Exception as e:
            err_str = str(e)
            retry_after = _parse_retry_after(err_str)
            if retry_after is not None or "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                _set_throttle(retry_after if retry_after is not None else 30.0)
                return None
            if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < 2:
                time.sleep(1.0)
                continue
            logger.error("Gemini embed_texts failed: %s", e)
            return None
    return None
