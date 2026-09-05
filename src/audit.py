"""Audit trail and event logging for case actions."""
from __future__ import annotations

from datetime import datetime, timezone
import json


# ── Event types ───────────────────────────────────────
EVENT_TYPES = (
    "case_created",
    "analysis_started",
    "mode_selected",
    "retrieval_performed",
    "clarification_asked",
    "clarification_answered",
    "escalation_requested",
    "review_started",
    "draft_generated",
    "recommendation_approved",
    "recommendation_dismissed",
    "case_resolved",
    "state_changed",
    "ai_called",
    "ai_failed",
    "conflict_detected",
)


def record_event(
    conn,
    ticket_id: int,
    event_type: str,
    details: dict | None = None,
    actor: str = "system",
) -> None:
    """Record an audit event for a case."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    details_json = json.dumps(details) if details else None

    conn.execute(
        """INSERT INTO audit_events (ticket_id, event_type, details, actor, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (ticket_id, event_type, details_json, actor, now),
    )
    conn.commit()


def record_case_created(conn, ticket_id: int, ticket_number: str, customer_name: str) -> None:
    """Record case creation event."""
    record_event(conn, ticket_id, "case_created", {
        "ticket_number": ticket_number,
        "customer_name": customer_name,
    })


def record_analysis_started(conn, ticket_id: int) -> None:
    """Record that analysis has started."""
    record_event(conn, ticket_id, "analysis_started")


def record_mode_selected(conn, ticket_id: int, mode: str, reason_codes: list[str]) -> None:
    """Record mode selection."""
    record_event(conn, ticket_id, "mode_selected", {
        "mode": mode,
        "reason_codes": reason_codes,
    })


def record_retrieval(conn, ticket_id: int, total: int, avg_score: float, categories: list[str]) -> None:
    """Record retrieval results."""
    record_event(conn, ticket_id, "retrieval_performed", {
        "total_chunks": total,
        "average_score": avg_score,
        "categories": categories,
    })


def record_clarification(conn, ticket_id: int, field: str, question: str = "", turn: int = 1) -> None:
    """Record clarification question."""
    record_event(conn, ticket_id, "clarification_asked", {
        "missing_field": field,
        "question": question,
        "turn_number": turn,
    })


def record_clarification_answer(conn, ticket_id: int, field: str, answer: str) -> None:
    """Record clarification answer."""
    record_event(conn, ticket_id, "clarification_answered", {
        "missing_field": field,
        "answer": answer,
    })


def record_escalation(conn, ticket_id: int, queue: str, reasons: list[str]) -> None:
    """Record escalation request."""
    record_event(conn, ticket_id, "escalation_requested", {
        "queue": queue,
        "reasons": reasons,
    })


def record_draft_generated(conn, ticket_id: int, confidence: float | dict | None = 0.8, limitations: list[str] | None = None) -> None:
    """Record draft generation."""
    if isinstance(confidence, dict):
        record_event(conn, ticket_id, "draft_generated", confidence)
    else:
        record_event(conn, ticket_id, "draft_generated", {
            "confidence": confidence,
            "limitations": limitations or [],
        })


def record_review_started(conn, ticket_id: int, reviewer: str) -> None:
    """Record review started."""
    record_event(conn, ticket_id, "review_started", {"reviewer": reviewer}, actor=reviewer)


def record_recommendation_approved(conn, ticket_id: int, reviewer: str, notes: str = "") -> None:
    """Record recommendation approval."""
    record_event(conn, ticket_id, "recommendation_approved", {
        "reviewer": reviewer,
        "notes": notes,
    }, actor=reviewer)


def record_recommendation_dismissed(conn, ticket_id: int, reviewer: str, reason: str) -> None:
    """Record recommendation dismissal."""
    record_event(conn, ticket_id, "recommendation_dismissed", {
        "reviewer": reviewer,
        "reason": reason,
    }, actor=reviewer)


def record_case_resolved(conn, ticket_id: int, resolution: str) -> None:
    """Record case resolution."""
    record_event(conn, ticket_id, "case_resolved", {"resolution": resolution})


def record_state_changed(conn, ticket_id: int, from_state: str, to_state: str, reason: str = "") -> None:
    """Record state change."""
    record_event(conn, ticket_id, "state_changed", {
        "from_state": from_state,
        "to_state": to_state,
        "reason": reason,
    })


def record_ai_called(conn, ticket_id: int, purpose: str) -> None:
    """Record AI call."""
    record_event(conn, ticket_id, "ai_called", {"purpose": purpose})


def record_ai_failed(conn, ticket_id: int, purpose: str, error: str) -> None:
    """Record AI failure."""
    record_event(conn, ticket_id, "ai_failed", {
        "purpose": purpose,
        "error": error,
    })


def record_conflict_detected(conn, ticket_id: int, conflict_type: str, details: str) -> None:
    """Record conflict detection."""
    record_event(conn, ticket_id, "conflict_detected", {
        "conflict_type": conflict_type,
        "details": details,
    })


def get_audit_trail(conn, ticket_id: int) -> list[dict]:
    """Get full audit trail for a case."""
    cursor = conn.execute(
        """SELECT ticket_id, event_type, details, actor, created_at
           FROM audit_events WHERE ticket_id = ? ORDER BY created_at ASC""",
        (ticket_id,),
    )
    results = []
    for r in cursor.fetchall():
        details = None
        if r[2]:
            try:
                details = json.loads(r[2])
            except (json.JSONDecodeError, TypeError):
                details = r[2]
        results.append({
            "ticket_id": r[0],
            "event_type": r[1],
            "details": details,
            "actor": r[3],
            "created_at": r[4],
        })
    return results
