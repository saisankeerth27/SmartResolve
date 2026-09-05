"""End-to-end API tests for SmartResolve workflows."""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timezone
from src.database.db import init_database, get_connection
from src.core.config import DATABASE_PATH
from src.tickets import transition_case, get_current_state, VALID_STATES, VALID_TRANSITIONS
from src.classify import classify_case
from src.clarify import store_clarification, get_previously_asked_fields, get_clarification_count, record_clarification_answer
from src.audit import record_event, get_audit_trail

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _cleanup(conn, ticket_number):
    tid = conn.execute("SELECT id FROM tickets WHERE ticket_number = ?", (ticket_number,)).fetchone()
    if tid:
        tid = tid[0]
        conn.execute("DELETE FROM case_state_history WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM audit_events WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM clarification_requests WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM escalation_records WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM review_states WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM tickets WHERE ticket_number = ?", (ticket_number,))
        conn.commit()


def setup():
    """Initialize database."""
    init_database(DATABASE_PATH)
    conn = get_connection()
    for i in range(1, 10):
        _cleanup(conn, f"TKT-E2E-{i:03d}")
    conn.close()


def _insert_ticket(conn, ticket_number, category="billing", priority="medium", subject="Test", description="Test", status="open"):
    conn.execute(
        "INSERT INTO tickets (ticket_number, customer_id, category, priority, subject, description, status, channel, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (ticket_number, 1, category, priority, subject, description, status, "web", NOW, NOW),
    )
    conn.commit()
    return conn.execute("SELECT id FROM tickets WHERE ticket_number = ?", (ticket_number,)).fetchone()[0]


def _cleanup(conn, ticket_number):
    tid = conn.execute("SELECT id FROM tickets WHERE ticket_number = ?", (ticket_number,)).fetchone()
    if tid:
        tid = tid[0]
        conn.execute("DELETE FROM case_state_history WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM audit_events WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM clarification_requests WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM escalation_records WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM review_states WHERE ticket_id = ?", (tid,))
        conn.execute("DELETE FROM tickets WHERE ticket_number = ?", (ticket_number,))
        conn.commit()


def test_mode_a_workflow():
    """Test complete Mode A: open → analyzing → pending_agent_approval → approved → resolved."""
    conn = get_connection()
    try:
        ticket_id = _insert_ticket(conn, "TKT-E2E-001")

        assert get_current_state(conn, ticket_id) == "open"
        transition_case(conn, ticket_id, "open", "analyzing", "system", "Analysis started")
        assert get_current_state(conn, ticket_id) == "analyzing"

        transition_case(conn, ticket_id, "analyzing", "pending_agent_approval", "system", "Mode A selected")
        assert get_current_state(conn, ticket_id) == "pending_agent_approval"

        transition_case(conn, ticket_id, "pending_agent_approval", "approved", "agent", "Recommendation approved")
        assert get_current_state(conn, ticket_id) == "approved"

        transition_case(conn, ticket_id, "approved", "resolved", "agent", "Case resolved")
        assert get_current_state(conn, ticket_id) == "resolved"

        cursor = conn.execute("SELECT COUNT(*) FROM case_state_history WHERE ticket_id = ?", (ticket_id,))
        assert cursor.fetchone()[0] >= 4

        _cleanup(conn, "TKT-E2E-001")
        print("PASS test_mode_a_workflow")
    finally:
        conn.close()


def test_mode_b_clarification_workflow():
    """Test Mode B clarification: store question, record answer, re-analyze."""
    conn = get_connection()
    try:
        ticket_id = _insert_ticket(conn, "TKT-E2E-002", category="network", subject="Slow internet", description="My internet is slow")

        store_clarification(conn, ticket_id, "What area are you in?", "location", "Need location", 1)
        assert get_clarification_count(conn, ticket_id) == 1

        asked = get_previously_asked_fields(conn, ticket_id)
        assert "location" in asked

        record_clarification_answer(conn, ticket_id, "location", "Mumbai, Andheri West")

        cursor = conn.execute("SELECT answer FROM clarification_requests WHERE ticket_id = ? AND missing_field = 'location'", (ticket_id,))
        row = cursor.fetchone()
        assert row and row[0] == "Mumbai, Andheri West"

        _cleanup(conn, "TKT-E2E-002")
        print("PASS test_mode_b_clarification_workflow")
    finally:
        conn.close()


def test_mode_c_escalation_workflow():
    """Test Mode C escalation: open → analyzing → escalation_requested → human_review → approved → resolved."""
    conn = get_connection()
    try:
        ticket_id = _insert_ticket(conn, "TKT-E2E-003", category="connectivity", priority="critical", subject="Repeated drops", description="Connection keeps dropping")

        transition_case(conn, ticket_id, "open", "analyzing", "system", "Analysis started")
        transition_case(conn, ticket_id, "analyzing", "escalation_requested", "system", "Mode C - escalation required")
        transition_case(conn, ticket_id, "escalation_requested", "human_review", "system", "Routed to human review")
        assert get_current_state(conn, ticket_id) == "human_review"

        transition_case(conn, ticket_id, "human_review", "approved", "agent", "Human review approved")
        assert get_current_state(conn, ticket_id) == "approved"

        transition_case(conn, ticket_id, "approved", "resolved", "agent", "Resolved after human review")
        assert get_current_state(conn, ticket_id) == "resolved"

        _cleanup(conn, "TKT-E2E-003")
        print("PASS test_mode_c_escalation_workflow")
    finally:
        conn.close()


def test_reopen_workflow():
    """Test reopen: dismissed → open → analyzing."""
    conn = get_connection()
    try:
        ticket_id = _insert_ticket(conn, "TKT-E2E-004", subject="Dismissed case", description="Was dismissed")

        transition_case(conn, ticket_id, "open", "analyzing", "system", "Analysis")
        transition_case(conn, ticket_id, "analyzing", "pending_agent_approval", "system", "Mode A")
        transition_case(conn, ticket_id, "pending_agent_approval", "dismissed", "agent", "Not appropriate")
        assert get_current_state(conn, ticket_id) == "dismissed"

        transition_case(conn, ticket_id, "dismissed", "open", "agent", "Case reopened")
        assert get_current_state(conn, ticket_id) == "open"

        transition_case(conn, ticket_id, "open", "analyzing", "system", "Re-analysis")
        assert get_current_state(conn, ticket_id) == "analyzing"

        _cleanup(conn, "TKT-E2E-004")
        print("PASS test_reopen_workflow")
    finally:
        conn.close()


def test_invalid_transitions():
    """Test that invalid transitions raise errors."""
    from src.tickets import InvalidTransitionError
    conn = get_connection()
    try:
        ticket_id = _insert_ticket(conn, "TKT-E2E-005", subject="Invalid transitions", description="Test")

        transition_case(conn, ticket_id, "open", "analyzing", "system", "")
        transition_case(conn, ticket_id, "analyzing", "pending_agent_approval", "system", "")
        transition_case(conn, ticket_id, "pending_agent_approval", "approved", "agent", "")
        transition_case(conn, ticket_id, "approved", "resolved", "agent", "")

        try:
            transition_case(conn, ticket_id, "resolved", "analyzing", "system", "")
            assert False, "Should have raised InvalidTransitionError"
        except InvalidTransitionError:
            pass

        transition_case(conn, ticket_id, "resolved", "open", "agent", "reopen")
        transition_case(conn, ticket_id, "open", "analyzing", "system", "")
        transition_case(conn, ticket_id, "analyzing", "pending_agent_approval", "system", "")
        transition_case(conn, ticket_id, "pending_agent_approval", "dismissed", "agent", "")

        try:
            transition_case(conn, ticket_id, "dismissed", "analyzing", "system", "")
            assert False, "Should have raised InvalidTransitionError"
        except InvalidTransitionError:
            pass

        _cleanup(conn, "TKT-E2E-005")
        print("PASS test_invalid_transitions")
    finally:
        conn.close()


def test_audit_trail():
    """Test audit trail recording and retrieval."""
    conn = get_connection()
    try:
        ticket_id = _insert_ticket(conn, "TKT-E2E-006", subject="Audit test", description="Test audit")

        record_event(conn, ticket_id, "analysis_started", {"mode": "A"}, "system")
        record_event(conn, ticket_id, "recommendation_approved", {"agent": "test"}, "agent")
        record_event(conn, ticket_id, "case_resolved", {"resolution": "test"}, "agent")

        trail = get_audit_trail(conn, ticket_id)
        assert len(trail) >= 3

        event_types = [e["event_type"] for e in trail]
        assert "analysis_started" in event_types
        assert "recommendation_approved" in event_types
        assert "case_resolved" in event_types

        _cleanup(conn, "TKT-E2E-006")
        print("PASS test_audit_trail")
    finally:
        conn.close()


def test_classification_modes():
    """Test that classification returns correct modes for different contexts."""
    # Mode A: routine billing with good retrieval
    context_a = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active", "plan_name": "Jio Prime", "service_type": "mobile", "data_limit_gb": 50, "monthly_price": 299},
        "ticket": {"category": "billing", "description": "duplicate charge", "subject": "Billing issue"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": ["Bill shows duplicate charge of 599"], "missing_information": []},
        "incidents": [],
        "retrieval": {"total": 5, "average_score": 0.65},
    }
    result_a = classify_case(context_a)
    assert result_a.mode == "A", f"Expected A, got {result_a.mode}"

    # Mode B: missing information
    context_b = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "network", "description": "slow internet", "subject": "Slow"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": []},
        "incidents": [],
        "network": {"site": {"status": "operational"}, "events": []},
        "retrieval": {"total": 3, "average_score": 0.45},
    }
    result_b = classify_case(context_b)
    assert result_b.mode == "B", f"Expected B, got {result_b.mode}"

    # Mode C: enterprise with repeat complaints
    context_c = {
        "customer": {"name": "Corp", "segment": "enterprise", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "connectivity", "description": "connection drops", "subject": "Repeated drops"},
        "investigation": {"same_category_previous_tickets": 3, "known_facts": [], "missing_information": []},
        "incidents": [],
        "retrieval": {"total": 3, "average_score": 0.4},
    }
    result_c = classify_case(context_c)
    assert result_c.mode == "C", f"Expected C, got {result_c.mode}"
    assert result_c.escalation_required

    print("PASS test_classification_modes")


if __name__ == "__main__":
    setup()
    test_classification_modes()
    test_mode_a_workflow()
    test_mode_b_clarification_workflow()
    test_mode_c_escalation_workflow()
    test_reopen_workflow()
    test_invalid_transitions()
    test_audit_trail()
    print("\nAll E2E tests passed!")
