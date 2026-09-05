"""Case state machine and ticket lifecycle management."""
from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass


# ── Valid states ──────────────────────────────────────
VALID_STATES = (
    "open",
    "new",
    "analyzing",
    "needs_information",
    "pending_agent_approval",
    "escalation_requested",
    "human_review",
    "approved",
    "dismissed",
    "resolved",
)

# ── Valid transitions ─────────────────────────────────
VALID_TRANSITIONS: dict[str, list[str]] = {
    "open": ["analyzing"],
    "new": ["analyzing"],
    "analyzing": ["needs_information", "pending_agent_approval", "escalation_requested"],
    "needs_information": ["analyzing", "escalation_requested", "dismissed", "open"],
    "pending_agent_approval": ["approved", "dismissed", "escalation_requested", "needs_information"],
    "escalation_requested": ["human_review", "dismissed", "needs_information", "approved"],
    "human_review": ["approved", "dismissed", "needs_information"],
    "approved": ["resolved", "needs_information"],
    "dismissed": ["open"],
    "resolved": ["open"],
}


@dataclass
class StateTransition:
    from_state: str
    to_state: str
    timestamp: str
    actor: str
    reason: str


class InvalidTransitionError(Exception):
    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid transition: '{from_state}' → '{to_state}'. "
            f"Valid transitions from '{from_state}': {VALID_TRANSITIONS.get(from_state, [])}"
        )


def validate_transition(from_state: str, to_state: str) -> bool:
    """Check if a state transition is valid."""
    if from_state not in VALID_STATES:
        raise ValueError(f"Unknown state: '{from_state}'")
    if to_state not in VALID_STATES:
        raise ValueError(f"Unknown state: '{to_state}'")
    allowed = VALID_TRANSITIONS.get(from_state, [])
    if to_state not in allowed:
        return False
    return True


def transition_case(
    conn,
    ticket_id: int,
    from_state: str,
    to_state: str,
    actor: str = "system",
    reason: str = "",
) -> dict:
    """Attempt a state transition. Records in case_state_history. Raises on invalid."""
    if not validate_transition(from_state, to_state):
        raise InvalidTransitionError(from_state, to_state)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    conn.execute(
        """INSERT INTO case_state_history (ticket_id, from_state, to_state, actor, reason, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (ticket_id, from_state, to_state, actor, reason, now),
    )
    conn.execute(
        "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
        (to_state, now, ticket_id),
    )
    conn.commit()

    return {
        "ticket_id": ticket_id,
        "from_state": from_state,
        "to_state": to_state,
        "actor": actor,
        "reason": reason,
        "timestamp": now,
    }


def get_state_history(conn, ticket_id: int) -> list[dict]:
    """Get full state transition history for a case."""
    cursor = conn.execute(
        """SELECT ticket_id, from_state, to_state, actor, reason, created_at
           FROM case_state_history WHERE ticket_id = ? ORDER BY created_at ASC""",
        (ticket_id,),
    )
    return [
        {
            "ticket_id": r[0],
            "from_state": r[1],
            "to_state": r[2],
            "actor": r[3],
            "reason": r[4],
            "created_at": r[5],
        }
        for r in cursor.fetchall()
    ]


def get_current_state(conn, ticket_id: int) -> str:
    """Get current state of a case from the tickets table."""
    cursor = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Ticket {ticket_id} not found")
    return row[0]
