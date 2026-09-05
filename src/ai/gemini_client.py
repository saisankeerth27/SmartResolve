"""Gemini client — dedicated module for all Gemini API interactions.

Reads GEMINI_API_KEY from environment. Fails gracefully when key is missing.
Never exposes the key in logs.
"""

import logging
import os
from typing import Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_api_key: str | None = None
_client: genai.Client | None = None


def _get_api_key() -> str | None:
    global _api_key
    if _api_key is None:
        _api_key = os.getenv("GEMINI_API_KEY")
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


def generate_text(prompt: str, system_instruction: str | None = None,
                  temperature: float = 0.3, max_output_tokens: int = 2048) -> str | None:
    """Generate text using Gemini. Returns None on failure."""
    client = get_client()
    if not client:
        return None
    try:
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=config,
        )
        if response.text:
            return response.text
        return None
    except Exception as e:
        logger.error("Gemini generate_text failed: %s", e)
        return None


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float] | None:
    """Embed a single text using gemini-embedding-001. Returns None on failure."""
    client = get_client()
    if not client:
        return None
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        if response.embeddings and len(response.embeddings) > 0:
            return list(response.embeddings[0].values)
        return None
    except Exception as e:
        logger.error("Gemini embed_text failed: %s", e)
        return None


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]] | None:
    """Embed a batch of texts using gemini-embedding-001. Returns None on failure."""
    client = get_client()
    if not client:
        return None
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        if response.embeddings:
            return [list(e.values) for e in response.embeddings]
        return None
    except Exception as e:
        logger.error("Gemini embed_texts failed: %s", e)
        return None
