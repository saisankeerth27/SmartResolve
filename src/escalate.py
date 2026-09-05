"""Mode C — Escalation and handover generation.

Creates a complete handover package so specialists understand the full problem
without asking the customer to repeat everything.
"""
from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass, field

from src.config import ESCALATION_QUEUES


@dataclass
class HandoverPackage:
    case_id: str
    ticket_number: str
    customer_name: str
    customer_segment: str
    customer_phone: str
    account_service: str
    plan_name: str
    plan_type: str
    operator: str
    issue_summary: str
    original_message: str
    confirmed_facts: list[str]
    missing_information: list[str]
    previous_tickets: list[dict]
    previous_troubleshooting: list[str]
    network_context: dict
    retrieval_result: str
    retrieval_confidence: float
    escalation_reasons: list[str]
    escalation_queue: str
    severity: str
    timestamp: str
    current_status: str
    recommendations: list[str]
    evidence_summary: list[str]


def build_handover(
    context: dict,
    classification_result,
    retrieval_info: dict | None = None,
) -> HandoverPackage:
    """Build a complete handover package for human review.

    The specialist should be able to understand the entire problem
    WITHOUT asking the customer to repeat everything.
    """
    ticket = context.get("ticket", {})
    customer = context.get("customer", {})
    subscription = context.get("subscription", {})
    network = context.get("network", {})
    incidents = context.get("incidents", [])
    investigation = context.get("investigation", {})
    previous_tickets = context.get("previous_tickets", [])
    interactions = context.get("interactions", [])

    # Build confirmed facts
    confirmed_facts = investigation.get("known_facts", [])

    # Build missing information
    missing_info = investigation.get("missing_information", [])

    # Build previous troubleshooting from interactions
    previous_troubleshooting = []
    for inter in interactions:
        if inter.get("interaction_type") in ("call", "chat", "email"):
            previous_troubleshooting.append(inter.get("summary", ""))

    # Network context
    site = network.get("site")
    network_context = {}
    if site:
        network_context = {
            "site_code": site.get("site_code", ""),
            "status": site.get("status", ""),
            "technology": site.get("technology", ""),
            "region": site.get("region", ""),
            "city": site.get("city", ""),
        }
    active_events = [e for e in network.get("events", []) if e.get("status") == "active"]
    if active_events:
        network_context["active_events"] = [
            {"type": e.get("event_type", ""), "severity": e.get("severity", ""), "title": e.get("title", "")}
            for e in active_events[:5]
        ]

    # Retrieval info
    retrieval_result = "No knowledge articles retrieved."
    retrieval_confidence = 0.0
    if retrieval_info:
        total = retrieval_info.get("total", 0)
        avg = retrieval_info.get("average_score", 0.0)
        retrieval_result = f"{total} articles retrieved (avg score: {avg:.2f})"
        retrieval_confidence = avg

    # Determine severity from classification
    reason_codes = classification_result.reason_codes if classification_result else []
    severity = "medium"
    for code in reason_codes:
        if any(s in code.upper() for s in ["CRITICAL", "OFFLINE", "FRAUD", "LEGAL", "SAFETY"]):
            severity = "critical"
            break
        if any(s in code.upper() for s in ["HIGH", "ENTERPRISE", "REPEAT", "MAJOR"]):
            severity = "high"
            break

    # Get escalation queue
    queue = "Technical Support - L1"
    if classification_result and classification_result.escalation_queue:
        queue = classification_result.escalation_queue

    # Build recommendations
    recommendations = _build_recommendations(context, classification_result)

    # Evidence summary
    evidence_summary = _build_evidence_summary(context)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    return HandoverPackage(
        case_id=str(ticket.get("id", "")),
        ticket_number=ticket.get("ticket_number", ""),
        customer_name=customer.get("name", "Unknown"),
        customer_segment=customer.get("segment", "N/A"),
        customer_phone=customer.get("phone", "N/A"),
        account_service=subscription.get("service_number", "N/A") if subscription else "N/A",
        plan_name=subscription.get("plan_name", "N/A") if subscription else "N/A",
        plan_type=subscription.get("service_type", "N/A") if subscription else "N/A",
        operator=subscription.get("provider_name", "N/A") if subscription else "N/A",
        issue_summary=ticket.get("subject", ""),
        original_message=ticket.get("description", ""),
        confirmed_facts=confirmed_facts,
        missing_information=missing_info,
        previous_tickets=[
            {"ticket_number": pt.get("ticket_number", ""), "subject": pt.get("subject", ""), "status": pt.get("status", "")}
            for pt in previous_tickets[:5]
        ],
        previous_troubleshooting=previous_troubleshooting[:5],
        network_context=network_context,
        retrieval_result=retrieval_result,
        retrieval_confidence=retrieval_confidence,
        escalation_reasons=reason_codes,
        escalation_queue=queue,
        severity=severity,
        timestamp=now,
        current_status="escalation_requested",
        recommendations=recommendations,
        evidence_summary=evidence_summary,
    )


def _build_recommendations(context: dict, classification_result) -> list[str]:
    """Build recommendations for the specialist."""
    recommendations = []
    reason_codes = classification_result.reason_codes if classification_result else []

    for code in reason_codes:
        if "REPEAT" in code:
            recommendations.append("Review previous ticket history for unresolved patterns.")
        if "ENTERPRISE" in code:
            recommendations.append("Prioritize — enterprise SLA requirements apply.")
        if "CONFLICT" in code:
            recommendations.append("Investigate data source conflict before resolution.")
        if "INCIDENT" in code:
            recommendations.append("Check if customer is affected by active incident.")
        if "OFFLINE" in code:
            recommendations.append("Network site requires immediate attention.")
        if "SENSITIVE" in code:
            recommendations.append("Handle with care — legal/compliance review may be needed.")
        if "DATA-OVERAGE" in code:
            recommendations.append("Review data usage and plan terms.")
        if "NO-RETRIEVAL" in code:
            recommendations.append("No matching knowledge articles — manual resolution required.")

    if not recommendations:
        recommendations.append("Review case details and determine appropriate resolution.")

    return recommendations


def _build_evidence_summary(context: dict) -> list[str]:
    """Build a summary of all evidence available."""
    evidence = []

    investigation = context.get("investigation", {})
    known_facts = investigation.get("known_facts", [])
    for fact in known_facts[:5]:
        evidence.append(f"Fact: {fact}")

    network = context.get("network", {})
    site = network.get("site")
    if site:
        evidence.append(f"Site: {site.get('site_code', '')} ({site.get('status', '')})")

    incidents = context.get("incidents", [])
    active = [i for i in incidents if i.get("status") in ("investigating", "identified", "monitoring")]
    for inc in active[:3]:
        evidence.append(f"Incident: {inc.get('incident_number', '')} ({inc.get('severity', '')})")

    return evidence


def store_escalation(
    conn,
    ticket_id: int,
    handover: HandoverPackage,
) -> None:
    """Store escalation record in the database."""
    import json
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    handover_dict = {
        "case_id": handover.case_id,
        "ticket_number": handover.ticket_number,
        "customer_name": handover.customer_name,
        "issue_summary": handover.issue_summary,
        "confirmed_facts": handover.confirmed_facts,
        "missing_information": handover.missing_information,
        "previous_tickets": handover.previous_tickets,
        "network_context": handover.network_context,
        "retrieval_result": handover.retrieval_result,
        "escalation_reasons": handover.escalation_reasons,
        "escalation_queue": handover.escalation_queue,
        "severity": handover.severity,
        "recommendations": handover.recommendations,
        "evidence_summary": handover.evidence_summary,
    }

    conn.execute(
        """INSERT INTO escalation_records
           (ticket_id, escalation_queue, severity, escalation_reasons, handover_summary, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ticket_id,
            handover.escalation_queue,
            handover.severity,
            json.dumps(handover.escalation_reasons),
            json.dumps(handover_dict),
            "open",
            now,
            now,
        ),
    )
    conn.commit()
