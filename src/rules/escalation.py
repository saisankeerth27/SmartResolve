"""Explicit escalation matrix for case routing.

CRITICAL: Immediate human escalation
HIGH: Human review required
MEDIUM: Clarification first, escalation if unresolved
LOW: Routine grounded draft
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import (
    MAJOR_INCIDENT_SEVERITIES,
    ACTIVE_INCIDENT_STATUSES,
    ENTERPRISE_SEGMENTS,
    HIGH_IMPACT_PRIORITIES,
    REPEAT_COMPLAINT_THRESHOLD,
    SENSITIVE_BILLING_LIMIT_INR,
    ESCALATION_QUEUES,
)


# ── Escalation severity levels ────────────────────────
CRITICAL = "critical"
HIGH = "high"
MEDIUM = "medium"
LOW = "low"


@dataclass
class EscalationDecision:
    severity: str
    queue: str
    reasons: list[str]
    requires_immediate_action: bool
    can_attempt_clarification: bool


def check_critical_escalation(context: dict) -> EscalationDecision | None:
    """Check for CRITICAL escalation triggers.

    CRITICAL triggers:
    - Safety/legal/regulatory/suspected fraud
    - Major active outage
    - Site offline
    """
    ticket = context.get("ticket", {})
    description = (ticket.get("description", "") + " " + ticket.get("subject", "")).lower()

    # Safety / legal / regulatory / fraud
    critical_keywords = ["fraud", "legal", "lawyer", "court", "safety", "harassment", "sim swap", "data breach"]
    for kw in critical_keywords:
        if kw in description:
            return EscalationDecision(
                severity=CRITICAL,
                queue=ESCALATION_QUEUES["legal_safety"],
                reasons=[f"Sensitive keyword detected: '{kw}'"],
                requires_immediate_action=True,
                can_attempt_clarification=False,
            )

    # Major active outage / site offline
    network = context.get("network", {})
    site = network.get("site")
    if site and site.get("status", "").lower() == "offline":
        return EscalationDecision(
            severity=CRITICAL,
            queue=ESCALATION_QUEUES["critical"],
            reasons=[f"Network site '{site.get('site_code', '')}' is offline"],
            requires_immediate_action=True,
            can_attempt_clarification=False,
        )

    # Active major incident
    incidents = context.get("incidents", [])
    for inc in incidents:
        status = inc.get("status", "").lower()
        severity = inc.get("severity", "").lower()
        if status in ACTIVE_INCIDENT_STATUSES and severity in MAJOR_INCIDENT_SEVERITIES:
            return EscalationDecision(
                severity=CRITICAL,
                queue=ESCALATION_QUEUES["critical"],
                reasons=[f"Active {severity} incident '{inc.get('incident_number', '')}'"],
                requires_immediate_action=True,
                can_attempt_clarification=False,
            )

    return None


def check_high_escalation(context: dict) -> EscalationDecision | None:
    """Check for HIGH escalation triggers.

    HIGH triggers:
    - Enterprise/high-impact service
    - Repeated unresolved complaints
    - Severe service disruption
    - Conflicting account data
    """
    customer = context.get("customer", {})
    segment = customer.get("segment", "").lower()

    # Enterprise case
    if segment in ENTERPRISE_SEGMENTS:
        return EscalationDecision(
            severity=HIGH,
            queue=ESCALATION_QUEUES["enterprise"],
            reasons=[f"Enterprise segment customer"],
            requires_immediate_action=False,
            can_attempt_clarification=False,
        )

    # Repeated unresolved complaints
    investigation = context.get("investigation", {})
    same_cat_count = investigation.get("same_category_previous_tickets", 0)
    if same_cat_count >= REPEAT_COMPLAINT_THRESHOLD:
        return EscalationDecision(
            severity=HIGH,
            queue=ESCALATION_QUEUES["repeat"],
            reasons=[f"Repeat complaint ({same_cat_count} previous tickets in category)"],
            requires_immediate_action=False,
            can_attempt_clarification=False,
        )

    # Conflicting account data
    ticket = context.get("ticket", {})
    subscription = context.get("subscription")
    if subscription:
        sub_status = subscription.get("status", "").lower()
        ticket_status = ticket.get("status", "").lower()
        if sub_status not in ("active",) and ticket_status in ("open", "in_progress"):
            return EscalationDecision(
                severity=HIGH,
                queue=ESCALATION_QUEUES["conflict"],
                reasons=[f"Subscription status '{sub_status}' conflicts with active ticket"],
                requires_immediate_action=False,
                can_attempt_clarification=False,
            )

    # High priority ticket
    priority = ticket.get("priority", "").lower()
    if priority in ("critical",):
        return EscalationDecision(
            severity=HIGH,
            queue=ESCALATION_QUEUES["general"],
            reasons=[f"Ticket priority is '{priority}'"],
            requires_immediate_action=False,
            can_attempt_clarification=False,
        )

    return None


def check_medium_escalation(context: dict) -> EscalationDecision | None:
    """Check for MEDIUM escalation triggers.

    MEDIUM triggers:
    - Insufficient evidence
    - Ambiguous retrieval
    - Missing required information
    """
    retrieval = context.get("retrieval", {})
    total = retrieval.get("total", 0)
    avg_score = retrieval.get("average_score", 0.0)

    if total == 0:
        return EscalationDecision(
            severity=MEDIUM,
            queue=ESCALATION_QUEUES["insufficient"],
            reasons=["No knowledge articles retrieved"],
            requires_immediate_action=False,
            can_attempt_clarification=True,
        )

    if avg_score < 0.25 and total < 2:
        return EscalationDecision(
            severity=MEDIUM,
            queue=ESCALATION_QUEUES["insufficient"],
            reasons=[f"Weak retrieval confidence ({avg_score:.2f})"],
            requires_immediate_action=False,
            can_attempt_clarification=True,
        )

    return None


def evaluate_escalation(context: dict) -> EscalationDecision | None:
    """Evaluate the full escalation matrix.

    Returns the highest severity escalation required, or None if routine.
    Priority: CRITICAL > HIGH > MEDIUM
    """
    # Check CRITICAL first
    result = check_critical_escalation(context)
    if result:
        return result

    # Check HIGH
    result = check_high_escalation(context)
    if result:
        return result

    # Check MEDIUM
    result = check_medium_escalation(context)
    if result:
        return result

    return None
