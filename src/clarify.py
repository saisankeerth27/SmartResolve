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


def answer_satisfies_field(field: str, answer: str) -> bool:
    """Reject acknowledgements that do not provide the requested telecom fact."""
    text = answer.strip().lower()
    if not text:
        return False
    if field == "device":
        return any(token in text for token in (
            "phone", "mobile", "router", "modem", "laptop", "computer", "tablet",
            "iphone", "android", "samsung", "pixel", "handset", "broadband",
        )) or any(char.isdigit() for char in text) and len(text) > 2
    if field == "scope":
        return any(phrase in text for phrase in (
            "all device", "every device", "one device", "single device", "just my",
            "only my", "two device", "2 device", "multiple device", "specific device",
        ))
    if field == "timing":
        return any(token in text for token in (
            "today", "yesterday", "morning", "afternoon", "evening", "night", "hour",
            "day", "week", "month", "since", "started", "constant", "intermittent",
            "always", "sometimes", "occasionally", "come and go", "recently",
        ))
    if field == "location":
        return len(text.split()) >= 2 or any(city in text for city in (
            "bengaluru", "bangalore", "chennai", "mumbai", "delhi", "pune", "hyderabad",
            "vijayawada", "kochi", "indiranagar", "area", "locality", "near",
        ))
    if field == "symptoms":
        return len(text.split()) >= 3 and text not in {"yes", "no", "ok", "okay", "thanks"}
    return len(text.split()) >= 2


def get_latest_unanswered_field(conn, ticket_id: int) -> str | None:
    row = conn.execute(
        "SELECT missing_field FROM clarification_requests WHERE ticket_id = ? AND answer IS NULL ORDER BY id DESC LIMIT 1",
        (ticket_id,),
    ).fetchone()
    return row[0] if row else None


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


def get_field_attempt_count(conn, ticket_id: int, missing_field: str) -> int:
    """Count clarification requests for one field, including unanswered retries."""
    row = conn.execute(
        "SELECT COUNT(*) FROM clarification_requests WHERE ticket_id = ? AND missing_field = ?",
        (ticket_id, missing_field),
    ).fetchone()
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
    field_attempts: dict[str, int] | None = None,
) -> str | None:
    """Select the first missing field that has not reached the retry cap."""
    for field in missing_fields:
        if field_attempts is None and field in previously_asked:
            continue
        if (field_attempts or {}).get(field, 0) < 2:
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

    field_attempts = {
        field: get_field_attempt_count(conn, ticket_id, field)
        for field in missing_fields
    }
    next_field = select_next_question(missing_fields, previously_asked, field_attempts)
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

    # Fallback to deterministic question, with a distinct acknowledgement on retries.
    if not question:
        question = get_fallback_question(next_field)
    if field_attempts.get(next_field, 0) > 0:
        question = _rephrase_retry(next_field, question, field_attempts[next_field])

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


def _rephrase_retry(field: str, question: str, attempt: int) -> str:
    """Ensure a non-answer never produces the same assistant text twice."""
    prefixes = {
        "location": "I still need your location or area to check network status. ",
        "timing": "Thanks. To narrow this down, I still need to know when it started. ",
        "device": "Thanks. I still need the affected device or router model. ",
        "scope": "Thanks. Is this affecting all devices or just one specific device? ",
    }
    prefix = prefixes.get(field, "I still need this detail to continue. ")
    return prefix + question[0].lower() + question[1:]


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
