"""Mode B — Targeted clarification engine.

Determines what information is missing, generates one targeted question per turn.
Does NOT ask all missing information at once. Prevents duplicate questions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass

from src.config import (
    FALLBACK_QUESTIONS,
    CLARIFICATION_MAX_TURNS,
)


@dataclass
class ClarificationRequest:
    question: str
    missing_field: str
    reason: str
    turn_number: int


def get_previously_asked_fields(conn, ticket_id: int) -> list[str]:
    """Get fields already asked about in previous clarification turns."""
    cursor = conn.execute(
        "SELECT missing_field FROM clarification_requests WHERE ticket_id = ? ORDER BY asked_at ASC",
        (ticket_id,),
    )
    return [r[0] for r in cursor.fetchall()]


def get_clarification_count(conn, ticket_id: int) -> int:
    """Count how many clarification turns have occurred."""
    cursor = conn.execute(
        "SELECT COUNT(*) FROM clarification_requests WHERE ticket_id = ?",
        (ticket_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else 0


def store_clarification(
    conn,
    ticket_id: int,
    question: str,
    missing_field: str,
    reason: str,
    turn_number: int,
    answer: str | None = None,
) -> None:
    """Store a clarification request in the database."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute(
        """INSERT INTO clarification_requests
           (ticket_id, question, missing_field, reason, turn_number, answer, asked_at, answered_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (ticket_id, question, missing_field, reason, turn_number, answer, now, None),
    )
    conn.commit()


def record_clarification_answer(conn, ticket_id: int, missing_field: str, answer: str) -> None:
    """Record the customer's answer to a clarification question."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute(
        "UPDATE clarification_requests SET answer = ?, answered_at = ? WHERE ticket_id = ? AND missing_field = ? AND answer IS NULL",
        (answer, now, ticket_id, missing_field),
    )
    conn.commit()


def select_next_question(
    missing_fields: list[str],
    previously_asked: list[str],
) -> str | None:
    """Select the single most important unasked question from missing fields."""
    for field in missing_fields:
        if field not in previously_asked:
            return field
    return None


def get_fallback_question(field: str) -> str:
    """Get a deterministic fallback question when Gemini is unavailable."""
    return FALLBACK_QUESTIONS.get(field, FALLBACK_QUESTIONS["default"])


def generate_clarification(
    conn,
    ticket_id: int,
    missing_fields: list[str],
    gemini_available: bool = True,
    investigation: dict | None = None,
    gemini_client=None,
) -> ClarificationRequest | None:
    """Generate a targeted clarification question.

    Returns None if:
    - No missing fields
    - Max clarification turns reached
    - All missing fields already asked

    Returns a ClarificationRequest with one question.
    """
    previously_asked = get_previously_asked_fields(conn, ticket_id)
    turn_count = get_clarification_count(conn, ticket_id)

    if turn_count >= CLARIFICATION_MAX_TURNS:
        return None

    next_field = select_next_question(missing_fields, previously_asked)
    if not next_field:
        return None

    # Try Gemini for natural wording
    question = None
    if gemini_available and gemini_client:
        try:
            question = _generate_with_gemini(
                next_field, investigation or {}, gemini_client
            )
        except Exception:
            question = None

    # Fallback to deterministic question
    if not question:
        question = get_fallback_question(next_field)

    reason = f"Required field '{next_field}' not yet confirmed from customer."
    new_turn = turn_count + 1

    # Persist the clarification question
    store_clarification(conn, ticket_id, question, next_field, reason, new_turn)

    return ClarificationRequest(
        question=question,
        missing_field=next_field,
        reason=reason,
        turn_number=new_turn,
    )


def _generate_with_gemini(
    field: str,
    investigation: dict,
    gemini_client,
) -> str | None:
    """Use Gemini to generate natural wording for clarification question."""
    ticket = investigation.get("ticket", {})
    category = ticket.get("category", "general")
    subject = ticket.get("subject", "")

    prompt = f"""Generate ONE short, professional clarification question for a telecom support agent to ask a customer.

Category: {category}
Issue: {subject}
Missing information: {field}

Requirements:
- Ask ONLY about the missing field
- Be polite and professional
- Reference the specific issue
- Return ONLY the question text, nothing else
- Maximum 2 sentences
"""

    try:
        from src.ai.gemini_client import generate_text as gemini_generate
        response = gemini_generate(
            prompt,
            system_instruction="You are a telecom support assistant. Generate only the clarification question.",
            temperature=0.3,
            max_output_tokens=150,
        )

        if response and isinstance(response, str):
            question = response.strip().strip('"').strip("'")
            if question and len(question) > 10 and "?" in question:
                return question
    except Exception:
        pass

    return None
