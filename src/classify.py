"""Deterministic case classification engine.

Classifies cases into Mode A (routine), Mode B (missing information), or Mode C (escalation).
No Gemini calls. Pure Python logic with configurable thresholds.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.config import (
    SAFE_RETRIEVAL_THRESHOLD,
    STRONG_RETRIEVAL_THRESHOLD,
    WEAK_RETRIEVAL_THRESHOLD,
    MAJOR_INCIDENT_SEVERITIES,
    ACTIVE_INCIDENT_STATUSES,
    CRITICAL_SITE_STATUSES,
    DEGRADED_SITE_STATUSES,
    ENTERPRISE_SEGMENTS,
    HIGH_IMPACT_PRIORITIES,
    REPEAT_COMPLAINT_THRESHOLD,
    SENSITIVE_BILLING_LIMIT_INR,
    CLARIFICATION_MAX_TURNS,
    CATEGORY_KNOWLEDGE_MAP,
    FALLBACK_QUESTIONS,
)


@dataclass
class ClassificationResult:
    mode: str  # "A", "B", or "C"
    reason_codes: list[str] = field(default_factory=list)
    confidence: float = 0.0
    required_information: list[str] = field(default_factory=list)
    escalation_required: bool = False
    escalation_queue: str | None = None
    missing_fields: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    eligible_for_draft: bool = False


# Categories that a front-line telecom agent resolves through normal troubleshooting.
# History, incident, network and account-flag rules do not auto-escalate these; they
# instead fall through to Mode B (gather details) or Mode A (grounded draft).
ROUTINE_CATEGORIES = (
    "connectivity", "network", "voice", "sms", "billing", "device", "roaming",
)

# Risk/infrastructure flags that are genuinely critical even on routine categories.
NON_ROUTINE_SEVERITIES = ("critical", "high")


def is_routine_category(context: dict) -> bool:
    category = (context.get("ticket", {}) or {}).get("category", "").lower()
    return category in ROUTINE_CATEGORIES


def defer_routine_to_triage(context, already_asked, result) -> bool:
    """For routine categories, suppress escalation and let Mode B/A handle it.

    Returns True if the routine case was handled here (caller returns `result`).
    """
    if not is_routine_category(context):
        return False
    missing = detect_missing_information(context, already_asked)
    result.reason_codes.append("ROUTINE: History/incident flag present but category is routine — proceeding with troubleshooting.")
    if missing and len(already_asked or []) < CLARIFICATION_MAX_TURNS:
        result.mode = "B"
        result.required_information = missing
        result.missing_fields = missing
        result.confidence = 0.4
        return True
    result.mode = "A"
    result.eligible_for_draft = True
    result.confidence = 0.4
    return True


# ── Individual check functions ────────────────────────

def check_data_integrity(context: dict) -> tuple[bool, str | None]:
    """Check for missing or conflicting core data."""
    customer = context.get("customer")
    subscription = context.get("subscription")

    if not customer:
        return True, "MISSING-CUSTOMER: Customer record not found."
    if not subscription:
        return True, "MISSING-SUBSCRIPTION: No active subscription found for this customer."

    cust_status = customer.get("status", "").lower()
    if cust_status == "suspended":
        return True, "ACCOUNT-SUSPENDED: Customer account is suspended."

    sub_status = subscription.get("status", "").lower()
    if sub_status == "suspended":
        return True, "SUB-SUSPENDED: Subscription is suspended."

    return False, None


def check_sensitive_case(context: dict) -> tuple[bool, str | None]:
    """Check for sensitive/legal/safety/fraud cases."""
    ticket = context.get("ticket", {})
    description = (ticket.get("description", "") + " " + ticket.get("subject", "")).lower()

    sensitive_keywords = [
        "fraud", "unauthorized", "legal", "lawyer", "attorney", "court",
        "regulatory", "trai", "dot", "safety", "harassment", "abuse",
        "stolen", "identity theft", "sim swap", "data breach",
    ]
    for kw in sensitive_keywords:
        if kw in description:
            return True, f"SENSITIVE-CASE: Sensitive keyword detected: '{kw}'."

    return False, None


def check_conflicting_evidence(context: dict) -> tuple[bool, str | None]:
    """Check for data conflicts between sources."""
    ticket = context.get("ticket", {})
    subscription = context.get("subscription")
    network = context.get("network", {})
    site = network.get("site")

    ticket_status = ticket.get("status", "").lower()
    if ticket_status in ("resolved", "closed"):
        return True, "CONFLICT-TICKET-RESOLVED: Ticket is already resolved/closed but being analyzed."

    if subscription:
        sub_status = subscription.get("status", "").lower()
        if sub_status not in ("active",):
            return True, f"CONFLICT-SUB-STATUS: Subscription status is '{sub_status}' which may conflict with active service request."

    if site:
        site_status = site.get("status", "").lower()
        active_events = [e for e in network.get("events", []) if e.get("status") == "active"]
        if site_status == "operational" and active_events:
            high_sev = [e for e in active_events if e.get("severity") in ("critical", "high")]
            if high_sev:
                return True, "CONFLICT-SITE-EVENTS: Network site shows operational but has high-severity active events."

    incidents = context.get("incidents", [])
    active_incidents = [i for i in incidents if i.get("status") in ACTIVE_INCIDENT_STATUSES]
    if len(active_incidents) > 2:
        return True, "CONFLICT-MULTI-INCIDENT: Multiple active incidents overlap — requires manual disambiguation."

    return False, None


def check_active_incident(context: dict) -> tuple[bool, str | None]:
    """Check for active major incidents affecting the customer."""
    incidents = context.get("incidents", [])
    for inc in incidents:
        status = inc.get("status", "").lower()
        severity = inc.get("severity", "").lower()
        if status in ACTIVE_INCIDENT_STATUSES and severity in MAJOR_INCIDENT_SEVERITIES:
            return True, f"ACTIVE-MAJOR-INCIDENT: Active {severity} incident '{inc.get('incident_number', '')}' in region."

    return False, None


def check_repeat_complaint(context: dict) -> tuple[bool, str | None]:
    """Check for repeated unresolved complaints."""
    investigation = context.get("investigation", {})
    same_cat_count = investigation.get("same_category_previous_tickets", 0)

    if same_cat_count >= REPEAT_COMPLAINT_THRESHOLD:
        return True, f"REPEAT-COMPLAINT: Customer has {same_cat_count} previous tickets in this category."

    return False, None


def has_identifiable_issue(context: dict) -> bool:
    """A greeting or acknowledgement cannot establish a repeat complaint category."""
    ticket = context.get("ticket", {})
    description = f"{ticket.get('subject', '')} {ticket.get('description', '')}".lower()
    return any(
        keyword in description
        for keyword in (
            "wifi", "wi-fi", "broadband", "internet", "slow", "speed", "outage",
            "coverage", "call", "sms", "bill", "charge", "roaming", "router",
            "sim", "device", "network", "connection", "disconnect", "drop", "drops", "dropping", "signal",
        )
    )


def check_enterprise_case(context: dict) -> tuple[bool, str | None]:
    """Check for enterprise/high-impact cases."""
    customer = context.get("customer", {})
    segment = customer.get("segment", "").lower()
    if segment in ENTERPRISE_SEGMENTS:
        return True, f"ENTERPRISE-CASE: Customer segment is '{segment}' — requires specialist handling."

    return False, None


def check_network_degradation(context: dict) -> tuple[bool, str | None]:
    """Check for network site degradation."""
    network = context.get("network", {})
    site = network.get("site")
    if site:
        status = site.get("status", "").lower()
        if status in CRITICAL_SITE_STATUSES:
            return True, f"SITE-OFFLINE: Serving site '{site.get('site_code', '')}' is offline."
        if status in DEGRADED_SITE_STATUSES:
            return True, f"SITE-DEGRADED: Serving site '{site.get('site_code', '')}' is degraded."

    return False, None


def check_retrieval_quality(context: dict) -> tuple[bool, str | None]:
    """Check if retrieval results are sufficient for grounded drafting."""
    retrieval = context.get("retrieval", {})
    total = retrieval.get("total", 0)
    avg_score = retrieval.get("average_score", 0.0)

    if total == 0:
        return True, "NO-RETRIEVAL: No knowledge articles retrieved."
    if avg_score < WEAK_RETRIEVAL_THRESHOLD and total < 2:
        return True, f"WEAK-RETRIEVAL: Retrieval confidence {avg_score:.2f} below threshold."

    return False, None


def check_account_eligibility(context: dict) -> tuple[bool, str | None]:
    """Check if account/service data confirms eligibility."""
    subscription = context.get("subscription")
    if not subscription:
        return True, "NO-SUBSCRIPTION: Cannot confirm service eligibility."

    plan = subscription.get("plan_name", "")
    service_type = subscription.get("service_type", "")
    data_usage = subscription.get("data_usage_gb", 0)
    data_limit = subscription.get("data_limit_gb", 0)

    if data_limit and data_usage and data_usage > data_limit:
        return True, "DATA-OVERAGE: Customer has exceeded data limit — may affect service."

    return False, None


def detect_missing_information(context: dict, already_asked: list[str] | None = None) -> list[str]:
    """Detect what information is missing and would help resolve the case."""
    already_asked = already_asked or []
    missing = []

    ticket = context.get("ticket", {})
    description = (ticket.get("description", "") + " " + ticket.get("subject", "")).lower()
    category = ticket.get("category", "").lower()

    investigation = context.get("investigation", {})
    known_facts = investigation.get("known_facts", [])
    known_text = " ".join(known_facts).lower()
    customer_text = f"{ticket.get('subject', '')} {ticket.get('description', '')}".lower()

    # Any field a customer has already answered is treated as satisfied.
    # The investigation carries these as "Customer confirmed {field}: ...".
    confirmed_fields = {
        m.group(1)
        for m in re.finditer(r"customer confirmed\s+([a-z_]+):", known_text)
    }

    if category in ("network", "connectivity"):
        has_location = (
            "location" in known_text or "area" in known_text or "city" in known_text
            or re.search(r"\b(?:in|at|near)\s+[a-z][a-z -]{2,}", customer_text) is not None
        )
        if not has_location:
            missing.append("location")
        if "time" not in known_text and "when" not in known_text and not re.search(
            r"\b(?:since|started|yesterday|today|morning|evening|week|month|constant|intermittent)\b",
            f"{customer_text} {known_text}",
        ):
            missing.append("timing")
        if "device" not in known_text and "router" not in known_text and not any(
            word in customer_text for word in ("phone", "laptop", "computer", "handset", "modem")
        ):
            missing.append("device")
        if "all devices" not in known_text and "specific device" not in known_text and not re.search(
            r"\b(?:all|one|single)\s+devices?\b", customer_text
        ):
            missing.append("scope")

    elif category == "billing":
        if "charge" not in known_text and "amount" not in known_text and "bill" not in known_text:
            missing.append("symptoms")

    elif category in ("voice", "sms"):
        if "number" not in known_text and "calling" not in known_text:
            missing.append("symptoms")
        if "time" not in known_text and "when" not in known_text:
            missing.append("timing")

    elif category == "device":
        if "device" not in known_text and "model" not in known_text:
            missing.append("device")

    elif category in ("account", "roaming") or not category:
        if "symptoms" not in already_asked:
            missing.append("symptoms")

    # If no missing info detected yet, check if message is a greeting or placeholder
    if not missing:
        greeting_words = ("hello", "hi", "hey", "help", "need help")
        if any(w in description for w in greeting_words) or description in ("new conversation", "customer initiated chat"):
            if "symptoms" not in already_asked:
                missing.append("symptoms")

    return [m for m in missing if m not in already_asked and m not in confirmed_fields]


# ── Main classification function ──────────────────────

def classify_case(context: dict, already_asked: list[str] | None = None) -> ClassificationResult:
    """Classify a case into Mode A, B, or C using deterministic rules.

    Precedence (highest to lowest):
    1. DATA INTEGRITY
    2. SENSITIVE / LEGAL / SAFETY
    3. CONFLICTING EVIDENCE
    4. ACTIVE MAJOR INCIDENT
    5. REPEAT COMPLAINT
    6. ENTERPRISE / HIGH-IMPACT
    7. NETWORK DEGRADATION (escalates if critical)
    8. RETRIEVAL QUALITY
    9. ACCOUNT ELIGIBILITY
    10. MODE SELECTION
    """
    result = ClassificationResult(mode="C")

    # 1. DATA INTEGRITY — always first
    blocked, reason = check_data_integrity(context)
    if blocked:
        result.reason_codes.append(reason)
        if "MISSING-CUSTOMER" in reason:
            result.escalation_required = True
            result.escalation_queue = "Technical Support - L1"
            result.blocking_reasons.append(reason)
            return result
        if "MISSING-SUBSCRIPTION" in reason:
            ticket = context.get("ticket", {})
            if ticket.get("channel") == "web":
                missing = detect_missing_information(context, already_asked)
                if missing:
                    result.mode = "B"
                    result.required_information = missing
                    result.missing_fields = missing
                    result.confidence = 0.4
                    return result
            result.escalation_required = True
            result.escalation_queue = "Technical Support - L1"
            result.blocking_reasons.append(reason)
            return result
        if "SUSPENDED" in reason:
            result.escalation_required = True
            result.escalation_queue = "Customer Retention - L2"
            result.blocking_reasons.append(reason)
            return result

    # 2. SENSITIVE / LEGAL / SAFETY
    is_sensitive, reason = check_sensitive_case(context)
    if is_sensitive:
        result.reason_codes.append(reason)
        result.escalation_required = True
        result.escalation_queue = "Legal & Compliance - Immediate"
        result.blocking_reasons.append(reason)
        return result

    # An unclear message must establish an issue before any history or risk rule applies.
    if not has_identifiable_issue(context):
        missing = detect_missing_information(context, already_asked)
        if missing:
            result.mode = "B"
            result.required_information = missing
            result.missing_fields = missing
            result.confidence = 0.3
            result.reason_codes.append("MISSING-INFO: Customer has not stated an identifiable issue.")
            return result

    missing = detect_missing_information(context, already_asked)
    clarification_attempts = context.get("clarification_attempts", {})
    exhausted_field = next(
        (field for field in missing if clarification_attempts.get(field, 0) >= 2),
        None,
    )
    if exhausted_field:
        result.reason_codes.append(
            f"UNRESOLVED-AFTER-CLARIFICATION: {exhausted_field} was not confirmed after 2 attempts."
        )
        result.escalation_required = True
        result.escalation_queue = "Human Review"
        result.blocking_reasons.append(result.reason_codes[-1])
        return result

    # 3. CONFLICTING EVIDENCE
    has_conflict, reason = check_conflicting_evidence(context)
    if has_conflict:
        result.reason_codes.append(reason)
        if is_routine_category(context):
            result.reason_codes.append(
                "ROUTINE-NO-CONFLICT-ESCALATION: Conflicting evidence present but category is routine — investigating is correct, escalating is not."
            )
        else:
            result.escalation_required = True
            result.escalation_queue = "Billing Operations - Investigation"
            result.blocking_reasons.append(reason)
            return result

    # 4. ACTIVE MAJOR INCIDENT
    has_incident, reason = check_active_incident(context)
    if has_incident:
        result.reason_codes.append(reason)
        if is_routine_category(context):
            if defer_routine_to_triage(context, already_asked, result):
                return result
        else:
            result.escalation_required = True
            result.escalation_queue = "Network Operations - Critical"
            result.blocking_reasons.append(reason)
            return result

    # 5. REPEAT COMPLAINT
    is_repeat, reason = check_repeat_complaint(context) if has_identifiable_issue(context) else (False, None)
    if is_repeat:
        result.reason_codes.append(reason)
        result.escalation_required = True
        result.escalation_queue = "Customer Retention - L2"
        result.blocking_reasons.append(reason)
        return result

    # 6. ENTERPRISE / HIGH-IMPACT
    is_enterprise, reason = check_enterprise_case(context)
    if is_enterprise:
        result.reason_codes.append(reason)
        result.escalation_required = True
        result.escalation_queue = "Enterprise Support - Priority"
        result.blocking_reasons.append(reason)
        return result

    # 7. NETWORK DEGRADATION (critical → escalate, degraded → check further)
    has_degradation, reason = check_network_degradation(context)
    if has_degradation:
        result.reason_codes.append(reason)
        if "OFFLINE" in reason:
            result.escalation_required = True
            result.escalation_queue = "Network Operations - Critical"
            result.blocking_reasons.append(reason)
            return result
        # Degraded site — may still be Mode A with note

    # 8. RETRIEVAL QUALITY
    weak_retrieval, reason = check_retrieval_quality(context)
    if weak_retrieval:
        result.reason_codes.append(reason)
        missing = detect_missing_information(context, already_asked)
        if missing:
            result.mode = "B"
            result.required_information = missing
            result.missing_fields = missing
            result.confidence = 0.3
            return result
        # Don't escalate routine troubleshootable issues just because retrieval is weak
        category = context.get("ticket", {}).get("category", "").lower()
        routine_categories = ("connectivity", "network", "voice", "sms", "billing", "device", "roaming")
        if category in routine_categories:
            result.mode = "A"
            result.eligible_for_draft = True
            result.confidence = 0.4
            result.reason_codes.append("ROUTINE-NO-RETRIEVAL: Weak retrieval but case is routine — drafting with available context.")
            return result
        result.escalation_required = True
        result.escalation_queue = "Technical Support - L1"
        result.blocking_reasons.append(reason)
        return result

    # 9. ACCOUNT ELIGIBILITY
    ineligible, reason = check_account_eligibility(context)
    if ineligible:
        result.reason_codes.append(reason)
        missing = detect_missing_information(context, already_asked)
        if missing:
            result.mode = "B"
            result.required_information = missing
            result.missing_fields = missing
            result.confidence = 0.3
            return result
        result.escalation_required = True
        result.escalation_queue = "Technical Support - L1"
        result.blocking_reasons.append(reason)
        return result

    # 10. MODE SELECTION — if we got here, check if info is sufficient
    missing = detect_missing_information(context, already_asked)
    clarification_attempts = context.get("clarification_attempts", {})
    exhausted_field = next(
        (field for field in missing if clarification_attempts.get(field, 0) >= 2),
        None,
    )
    if exhausted_field:
        result.reason_codes.append(
            f"UNRESOLVED-AFTER-CLARIFICATION: {exhausted_field} was not confirmed after 2 attempts."
        )
        result.escalation_required = True
        result.escalation_queue = "Human Review"
        result.blocking_reasons.append(result.reason_codes[-1])
        return result
    if missing and len(already_asked or []) < CLARIFICATION_MAX_TURNS:
        result.mode = "B"
        result.required_information = missing
        result.missing_fields = missing
        result.confidence = 0.5
        result.reason_codes.append("MISSING-INFO: Required information not yet collected.")
        return result

    # Mode A — all checks passed
    result.mode = "A"
    result.eligible_for_draft = True
    result.confidence = 0.8
    result.reason_codes.append("ROUTINE: Case meets all criteria for grounded resolution draft.")
    if has_degradation:
        result.confidence = 0.6
        result.reason_codes.append("NOTE: Network degradation present — draft should mention monitoring.")
    return result
