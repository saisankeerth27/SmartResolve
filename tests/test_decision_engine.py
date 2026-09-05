"""Decision engine tests for SmartResolve.

Tests deterministic Mode A/B/C classification without requiring Gemini.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.classify import (
    classify_case,
    check_data_integrity,
    check_sensitive_case,
    check_conflicting_evidence,
    check_active_incident,
    check_repeat_complaint,
    check_enterprise_case,
    check_network_degradation,
    check_retrieval_quality,
    detect_missing_information,
)
from src.rules.escalation import (
    evaluate_escalation,
    check_critical_escalation,
    check_high_escalation,
    check_medium_escalation,
)
from src.rules.conflict import detect_conflicts
from src.tickets import validate_transition, VALID_TRANSITIONS, VALID_STATES
from src.clarify import select_next_question, get_fallback_question


# ── Test: Classification ──────────────────────────────

def test_missing_customer_escalates():
    """Missing customer → Mode C (escalation)."""
    context = {"customer": None, "subscription": None, "ticket": {"category": "network", "description": "test"}}
    result = classify_case(context)
    assert result.mode == "C", f"Expected Mode C, got {result.mode}"
    assert result.escalation_required


def test_missing_subscription_escalates():
    """Missing subscription → Mode C."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": None,
        "ticket": {"category": "network", "description": "test"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": []},
    }
    result = classify_case(context)
    assert result.mode == "C", f"Expected Mode C, got {result.mode}"


def test_sensitive_case_escalates():
    """Fraud keyword → Mode C (escalation)."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "billing", "description": "I think there is fraud on my account"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": []},
    }
    result = classify_case(context)
    assert result.mode == "C"
    assert any("SENSITIVE" in code for code in result.reason_codes)


def test_active_major_incident_escalates():
    """Active critical incident → Mode C."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "network", "description": "no internet"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": []},
        "incidents": [{"incident_number": "INC-001", "severity": "critical", "status": "investigating", "region": "South"}],
        "retrieval": {"total": 3, "average_score": 0.6},
    }
    result = classify_case(context)
    assert result.mode == "C"
    assert any("MAJOR-INCIDENT" in code for code in result.reason_codes)


def test_repeat_complaint_escalates():
    """2+ previous tickets → Mode C."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "network", "description": "internet down again"},
        "investigation": {"same_category_previous_tickets": 3, "known_facts": [], "missing_information": []},
        "retrieval": {"total": 3, "average_score": 0.5},
    }
    result = classify_case(context)
    assert result.mode == "C"
    assert any("REPEAT" in code for code in result.reason_codes)


def test_enterprise_case_escalates():
    """Enterprise segment → Mode C."""
    context = {
        "customer": {"name": "Corp", "segment": "enterprise", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "billing", "description": "billing issue"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": []},
        "retrieval": {"total": 3, "average_score": 0.6},
    }
    result = classify_case(context)
    assert result.mode == "C"
    assert any("ENTERPRISE" in code for code in result.reason_codes)


def test_routine_request_mode_a():
    """Clear request with good retrieval → Mode A."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active", "plan_name": "Jio Prime", "service_type": "mobile", "data_limit_gb": 50, "monthly_price": 299},
        "ticket": {"category": "billing", "description": "I was charged ₹599 instead of ₹299"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": ["Customer charged ₹599", "Plan price is ₹299", "Bill shows duplicate charge of ₹599", "Amount dispute is clear"], "missing_information": []},
        "incidents": [],
        "retrieval": {"total": 5, "average_score": 0.65},
    }
    result = classify_case(context)
    assert result.mode == "A", f"Expected Mode A, got {result.mode}. Reasons: {result.reason_codes}"
    assert result.eligible_for_draft


def test_missing_information_mode_b():
    """Network issue without location → Mode B."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "network", "description": "internet is slow"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": ["location", "timing"]},
        "incidents": [],
        "network": {"site": {"status": "operational"}},
        "retrieval": {"total": 3, "average_score": 0.45},
    }
    result = classify_case(context)
    assert result.mode == "B", f"Expected Mode B, got {result.mode}. Reasons: {result.reason_codes}"
    assert len(result.missing_fields) > 0


def test_no_retrieval_mode_b_or_c():
    """No retrieval results → Mode B (if info missing) or Mode C."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "network", "description": "connection drops"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": []},
        "incidents": [],
        "retrieval": {"total": 0, "average_score": 0.0},
    }
    result = classify_case(context)
    # With no retrieval and no missing info, should escalate
    assert result.mode in ("B", "C"), f"Expected Mode B or C, got {result.mode}"


def test_site_offline_escalates():
    """Offline site → Mode C."""
    context = {
        "customer": {"name": "Test", "segment": "consumer", "status": "active"},
        "subscription": {"status": "active"},
        "ticket": {"category": "network", "description": "no internet"},
        "investigation": {"same_category_previous_tickets": 0, "known_facts": [], "missing_information": []},
        "network": {"site": {"status": "offline", "site_code": "SITE-001"}, "events": []},
        "incidents": [],
        "retrieval": {"total": 3, "average_score": 0.5},
    }
    result = classify_case(context)
    assert result.mode == "C"
    assert any("OFFLINE" in code for code in result.reason_codes)


# ── Test: Escalation Matrix ───────────────────────────

def test_critical_escalation_fraud():
    """Fraud keyword triggers critical escalation."""
    context = {
        "ticket": {"description": "suspected fraud on my account", "subject": "Fraud"},
        "network": {"site": None, "events": []},
        "incidents": [],
    }
    result = check_critical_escalation(context)
    assert result is not None
    assert result.severity == "critical"


def test_critical_escalation_site_offline():
    """Site offline triggers critical escalation."""
    context = {
        "ticket": {"description": "no internet", "subject": "Connection issue"},
        "network": {"site": {"status": "offline", "site_code": "SITE-001"}, "events": []},
        "incidents": [],
    }
    result = check_critical_escalation(context)
    assert result is not None
    assert result.severity == "critical"


def test_high_escalation_enterprise():
    """Enterprise customer triggers high escalation."""
    context = {
        "customer": {"segment": "enterprise"},
        "ticket": {"priority": "medium", "description": "issue", "subject": "Issue"},
        "investigation": {"same_category_previous_tickets": 0},
    }
    result = check_high_escalation(context)
    assert result is not None
    assert result.severity == "high"


def test_high_escalation_repeat():
    """Repeat complaints trigger high escalation."""
    context = {
        "customer": {"segment": "consumer"},
        "ticket": {"priority": "medium", "description": "issue", "subject": "Issue"},
        "investigation": {"same_category_previous_tickets": 3},
    }
    result = check_high_escalation(context)
    assert result is not None
    assert result.severity == "high"


def test_medium_escalation_no_retrieval():
    """No retrieval results trigger medium escalation."""
    context = {"retrieval": {"total": 0, "average_score": 0.0}}
    result = check_medium_escalation(context)
    assert result is not None
    assert result.severity == "medium"


def test_no_escalation_for_routine():
    """Routine case with good data → no escalation."""
    context = {
        "customer": {"segment": "consumer"},
        "ticket": {"priority": "medium", "description": "billing question", "subject": "Billing"},
        "investigation": {"same_category_previous_tickets": 0},
        "network": {"site": {"status": "operational"}, "events": []},
        "incidents": [],
        "retrieval": {"total": 5, "average_score": 0.6},
    }
    result = evaluate_escalation(context)
    assert result is None


# ── Test: Conflict Detection ──────────────────────────

def test_ticket_sub_status_conflict():
    """Ticket active but subscription suspended → conflict."""
    context = {
        "ticket": {"status": "open", "category": "network", "description": "issue"},
        "subscription": {"status": "suspended", "plan_name": "Test", "service_type": "mobile"},
        "customer": {"name": "Test"},
        "network": {"site": None, "events": []},
        "incidents": [],
        "previous_tickets": [],
        "interactions": [],
        "investigation": {"same_category_previous_tickets": 0, "known_facts": []},
    }
    conflicts = detect_conflicts(context)
    assert len(conflicts) > 0
    assert any(c.conflict_type == "ticket_sub_status" for c in conflicts)


def test_site_vs_events_conflict():
    """Site operational but has high-severity events → conflict."""
    context = {
        "ticket": {"status": "open", "category": "network", "description": "issue"},
        "subscription": {"status": "active"},
        "customer": {"name": "Test"},
        "network": {
            "site": {"status": "operational", "site_code": "SITE-001"},
            "events": [
                {"status": "active", "severity": "critical", "event_type": "congestion", "title": "High congestion"}
            ],
        },
        "incidents": [],
        "previous_tickets": [],
        "interactions": [],
        "investigation": {"same_category_previous_tickets": 0, "known_facts": []},
    }
    conflicts = detect_conflicts(context)
    assert any(c.conflict_type == "site_vs_events" for c in conflicts)


def test_no_conflict_for_clean_data():
    """Clean data → no conflicts."""
    context = {
        "ticket": {"status": "open", "category": "billing", "description": "billing question"},
        "subscription": {"status": "active"},
        "customer": {"name": "Test"},
        "network": {"site": {"status": "operational"}, "events": []},
        "incidents": [],
        "previous_tickets": [],
        "interactions": [],
        "investigation": {"same_category_previous_tickets": 0, "known_facts": []},
    }
    conflicts = detect_conflicts(context)
    assert len(conflicts) == 0


# ── Test: State Machine ───────────────────────────────

def test_valid_transition():
    """new → analyzing is valid."""
    assert validate_transition("new", "analyzing")


def test_valid_transition_analyzing_to_info():
    """analyzing → needs_information is valid."""
    assert validate_transition("analyzing", "needs_information")


def test_valid_transition_analyzing_to_approval():
    """analyzing → pending_agent_approval is valid."""
    assert validate_transition("analyzing", "pending_agent_approval")


def test_valid_transition_analyzing_to_escalation():
    """analyzing → escalation_requested is valid."""
    assert validate_transition("analyzing", "escalation_requested")


def test_invalid_transition():
    """new → resolved is invalid."""
    assert not validate_transition("new", "resolved")


def test_invalid_transition_resolved_to_anything():
    """resolved → anything is invalid."""
    assert not validate_transition("resolved", "analyzing")
    assert not validate_transition("resolved", "new")


def test_invalid_transition_dismissed_to_anything():
    """dismissed → anything is invalid."""
    assert not validate_transition("dismissed", "analyzing")


def test_all_states_valid():
    """All defined states should be in VALID_STATES."""
    expected = {"open", "new", "analyzing", "needs_information", "pending_agent_approval",
                "escalation_requested", "human_review", "approved", "dismissed", "resolved"}
    assert set(VALID_STATES) == expected


def test_all_transitions_from_valid_states():
    """All transition keys should reference valid states."""
    for from_state, to_states in VALID_TRANSITIONS.items():
        assert from_state in VALID_STATES, f"Invalid from_state: {from_state}"
        for to_state in to_states:
            assert to_state in VALID_STATES, f"Invalid to_state: {to_state}"


# ── Test: Clarification ───────────────────────────────

def test_select_next_question():
    """Should select first unasked field."""
    missing = ["location", "timing", "device"]
    asked = ["location"]
    result = select_next_question(missing, asked)
    assert result == "timing"


def test_select_next_question_all_asked():
    """Should return None if all fields asked."""
    missing = ["location", "timing"]
    asked = ["location", "timing"]
    result = select_next_question(missing, asked)
    assert result is None


def test_fallback_questions():
    """All fallback questions should be strings."""
    for field in ["location", "timing", "device", "scope", "symptoms", "account", "default"]:
        q = get_fallback_question(field)
        assert isinstance(q, str)
        assert len(q) > 10


# ── Test: Missing Information Detection ───────────────

def test_missing_info_network():
    """Network category should detect missing location."""
    context = {
        "ticket": {"category": "network", "description": "slow internet", "subject": "Slow"},
        "investigation": {"known_facts": [], "missing_information": []},
    }
    missing = detect_missing_information(context)
    assert "location" in missing


def test_missing_info_already_asked():
    """Should not suggest already-asked fields."""
    context = {
        "ticket": {"category": "network", "description": "slow internet", "subject": "Slow"},
        "investigation": {"known_facts": [], "missing_information": []},
    }
    missing = detect_missing_information(context, already_asked=["location", "timing", "device", "scope"])
    assert "location" not in missing
    assert "timing" not in missing


# ── Test Matrix ────────────────────────────────────────

TEST_MATRIX = [
    ("missing_customer", "Mode C", test_missing_customer_escalates),
    ("missing_subscription", "Mode C", test_missing_subscription_escalates),
    ("sensitive_fraud", "Mode C", test_sensitive_case_escalates),
    ("active_major_incident", "Mode C", test_active_major_incident_escalates),
    ("repeat_complaint", "Mode C", test_repeat_complaint_escalates),
    ("enterprise_case", "Mode C", test_enterprise_case_escalates),
    ("site_offline", "Mode C", test_site_offline_escalates),
    ("routine_billing", "Mode A", test_routine_request_mode_a),
    ("missing_info_network", "Mode B", test_missing_information_mode_b),
    ("no_retrieval", "Mode B/C", test_no_retrieval_mode_b_or_c),
    ("ticket_sub_conflict", "Conflict", test_ticket_sub_status_conflict),
    ("site_events_conflict", "Conflict", test_site_vs_events_conflict),
    ("clean_data", "No Conflict", test_no_conflict_for_clean_data),
    ("valid_transition", "OK", test_valid_transition),
    ("invalid_transition", "Rejected", test_invalid_transition),
    ("select_question", "OK", test_select_next_question),
    ("fallback_questions", "OK", test_fallback_questions),
]


def run_all_tests():
    """Run all tests and report results."""
    passed = 0
    failed = 0
    errors = []

    tests = [
        test_missing_customer_escalates,
        test_missing_subscription_escalates,
        test_sensitive_case_escalates,
        test_active_major_incident_escalates,
        test_repeat_complaint_escalates,
        test_enterprise_case_escalates,
        test_routine_request_mode_a,
        test_missing_information_mode_b,
        test_no_retrieval_mode_b_or_c,
        test_site_offline_escalates,
        test_critical_escalation_fraud,
        test_critical_escalation_site_offline,
        test_high_escalation_enterprise,
        test_high_escalation_repeat,
        test_medium_escalation_no_retrieval,
        test_no_escalation_for_routine,
        test_ticket_sub_status_conflict,
        test_site_vs_events_conflict,
        test_no_conflict_for_clean_data,
        test_valid_transition,
        test_valid_transition_analyzing_to_info,
        test_valid_transition_analyzing_to_approval,
        test_valid_transition_analyzing_to_escalation,
        test_invalid_transition,
        test_invalid_transition_resolved_to_anything,
        test_invalid_transition_dismissed_to_anything,
        test_all_states_valid,
        test_all_transitions_from_valid_states,
        test_select_next_question,
        test_select_next_question_all_asked,
        test_fallback_questions,
        test_missing_info_network,
        test_missing_info_already_asked,
    ]

    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS {test.__name__}")
        except AssertionError as e:
            failed += 1
            errors.append((test.__name__, str(e)))
            print(f"  FAIL {test.__name__}: {e}")
        except Exception as e:
            failed += 1
            errors.append((test.__name__, str(e)))
            print(f"  FAIL {test.__name__}: ERROR: {e}")

    print(f"\nResults: {passed} passed, {failed} failed out of {len(tests)} tests")
    return failed == 0


if __name__ == "__main__":
    print("Running SmartResolve decision engine tests...\n")
    success = run_all_tests()
    sys.exit(0 if success else 1)
