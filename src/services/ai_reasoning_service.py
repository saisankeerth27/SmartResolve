"""AI Reasoning Service — orchestrates case analysis using RAG + Gemini.

Receives Case Investigation Context, builds retrieval query,
retrieves relevant knowledge, builds grounded context, calls Gemini,
validates structured response, and returns typed AI result.
"""

import json
import logging
from typing import Any

from src.ai.gemini_client import generate_text, is_available
from src.ai.prompts import SYSTEM_INSTRUCTION, build_reasoning_prompt
from src.ai.models import AIReasoningResult
from src.retrieval.retriever import retrieve_relevant_chunks
from src.retrieval.context_builder import (
    build_operational_facts,
    build_retrieved_knowledge,
    build_retrieval_query,
)
from src.retrieval.vector_store import get_vector_store
from src.services.knowledge_service import route_ticket_to_categories

logger = logging.getLogger(__name__)


def analyze_case(
    investigation: dict[str, Any],
    question: str = "What is the most likely explanation for this case?",
) -> dict[str, Any]:
    """Analyze a case using RAG + Gemini reasoning.

    Returns a dict with retrieval info and structured reasoning result.
    """
    if not is_available():
        return {
            "retrieval": {
                "status": "unavailable",
                "query": "",
                "results": [],
                "total": 0,
            },
            "reasoning": {
                "status": "insufficient_evidence",
                "summary": "AI service unavailable — GEMINI_API_KEY not configured.",
                "possible_causes": [],
                "recommended_next_steps": ["Configure GEMINI_API_KEY to enable AI analysis."],
                "knowledge_citations": [],
                "limitations": ["Gemini API key is not set in the environment."],
                "confidence": "low",
            },
        }

    store = get_vector_store()
    if not store.is_loaded():
        return {
            "retrieval": {
                "status": "unavailable",
                "query": "",
                "results": [],
                "total": 0,
            },
            "reasoning": {
                "status": "insufficient_evidence",
                "summary": "Knowledge retrieval unavailable — FAISS index not found.",
                "possible_causes": [],
                "recommended_next_steps": ["Run 'python scripts/build_index.py' to generate the FAISS index."],
                "knowledge_citations": [],
                "limitations": ["FAISS index is missing. Knowledge retrieval is not possible."],
                "confidence": "low",
            },
        }

    query = build_retrieval_query(investigation)
    ticket = investigation.get("ticket", {})
    category = ticket.get("category", "")
    candidate_categories = route_ticket_to_categories(category)

    chunks = retrieve_relevant_chunks(
        query=query,
        candidate_categories=candidate_categories,
        top_k=5,
    )

    retrieval_results = []
    for c in chunks:
        retrieval_results.append({
            "chunk_id": c.get("chunk_id", ""),
            "document_id": c.get("document_id", ""),
            "document_title": c.get("document_title", ""),
            "section_heading": c.get("section_heading", ""),
            "content": c.get("content", "")[:300] + "..." if len(c.get("content", "")) > 300 else c.get("content", ""),
            "score": round(c.get("score", 0), 4),
        })

    retrieval_info = {
        "status": "success" if chunks else "no_results",
        "query": query,
        "results": retrieval_results,
        "total": len(chunks),
    }

    if not chunks:
        return {
            "retrieval": retrieval_info,
            "reasoning": {
                "status": "insufficient_evidence",
                "summary": "No sufficiently relevant knowledge was retrieved for this case.",
                "possible_causes": [],
                "recommended_next_steps": [
                    "Review the case manually using operational data.",
                    "Consider whether additional knowledge documents are needed.",
                ],
                "knowledge_citations": [],
                "limitations": [
                    "No relevant knowledge chunks retrieved above the relevance threshold.",
                    "AI analysis cannot be grounded in telecom procedures without relevant knowledge.",
                ],
                "confidence": "low",
            },
        }

    operational_facts = build_operational_facts(investigation)
    retrieved_knowledge = build_retrieved_knowledge(chunks)

    prompt = build_reasoning_prompt(question, operational_facts, retrieved_knowledge)

    raw_response = generate_text(
        prompt=prompt,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.3,
        max_output_tokens=4096,
    )

    if raw_response is None:
        return {
            "retrieval": retrieval_info,
            "reasoning": {
                "status": "insufficient_evidence",
                "summary": "AI service temporarily unavailable.",
                "possible_causes": [],
                "recommended_next_steps": ["Retry the analysis."],
                "knowledge_citations": [],
                "limitations": ["Gemini API call failed."],
                "confidence": "low",
            },
        }

    logger.debug("Raw Gemini response (first 500): %s", raw_response[:500])
    reasoning = _parse_reasoning_response(raw_response, chunks)

    return {
        "retrieval": retrieval_info,
        "reasoning": reasoning,
    }


def _parse_reasoning_response(raw: str, chunks: list[dict]) -> dict[str, Any]:
    """Parse and validate Gemini's structured response."""
    import re

    try:
        cleaned = raw.strip()

        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        else:
            # Remove any standalone ``` lines
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        # Find JSON object boundaries
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start:end + 1]

        # Try to fix common JSON issues from Gemini
        # Remove trailing commas before } or ]
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

        data = json.loads(cleaned)

        # Validate and fill defaults
        if "status" not in data:
            data["status"] = "insufficient_evidence"
        if "summary" not in data:
            data["summary"] = "Response could not be parsed."
        if "possible_causes" not in data:
            data["possible_causes"] = []
        if "recommended_next_steps" not in data:
            data["recommended_next_steps"] = []
        if "knowledge_citations" not in data:
            data["knowledge_citations"] = []
        if "limitations" not in data:
            data["limitations"] = []
        if "confidence" not in data:
            data["confidence"] = "low"

        if data["status"] not in ("grounded", "insufficient_evidence"):
            data["status"] = "insufficient_evidence"
        if data["confidence"] not in ("high", "medium", "low"):
            data["confidence"] = "low"

        # Validate citations against retrieved chunks
        valid_citations = []
        retrieved_ids = {c.get("document_id") for c in chunks}
        for cit in data.get("knowledge_citations", []):
            if isinstance(cit, dict) and cit.get("document_id") in retrieved_ids:
                valid_citations.append(cit)
        data["knowledge_citations"] = valid_citations

        # Normalize possible_causes to ensure they have the right structure
        normalized_causes = []
        for cause in data.get("possible_causes", []):
            if isinstance(cause, str):
                normalized_causes.append({"cause": cause, "evidence": []})
            elif isinstance(cause, dict):
                normalized_causes.append({
                    "cause": cause.get("cause", str(cause)),
                    "evidence": cause.get("evidence", []),
                })
        data["possible_causes"] = normalized_causes

        # Normalize recommended_next_steps
        if not isinstance(data.get("recommended_next_steps"), list):
            data["recommended_next_steps"] = []

        # Normalize limitations
        if not isinstance(data.get("limitations"), list):
            data["limitations"] = []

        return data

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Failed to parse Gemini response (type=%s): %s", type(e).__name__, e)
        logger.debug("Raw response (first 800): %s", raw[:800])
        return {
            "status": "insufficient_evidence",
            "summary": "AI response could not be validated.",
            "possible_causes": [],
            "recommended_next_steps": ["Retry the analysis."],
            "knowledge_citations": [],
            "limitations": [f"Gemini response parsing failed: {type(e).__name__}"],
            "confidence": "low",
        }
