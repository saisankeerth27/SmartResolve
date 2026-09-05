import logging
from datetime import datetime, timezone

from src.rules.resolution_rules import (
    evaluate_rules,
    get_triggered_rules,
    requires_human_review,
)
from src.services.case_investigation_service import get_case_investigation
from src.services.ai_reasoning_service import analyze_case
from src.retrieval.retriever import retrieve_relevant_chunks
from src.retrieval.context_builder import build_retrieval_query

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "network": "network_investigation",
    "connectivity": "network_investigation",
    "voice": "customer_troubleshooting",
    "sms": "customer_troubleshooting",
    "billing": "billing_review",
    "roaming": "service_configuration_review",
    "device": "device_diagnostics",
    "account": "service_configuration_review",
}

ACTION_MAP = {
    "network_investigation": "Review active incident and serving site status. Confirm whether the customer's impact window overlaps with any known network event.",
    "incident_review": "Review the active regional incident and confirm whether the customer's impact window overlaps the incident period.",
    "customer_troubleshooting": "Perform standard device and connectivity troubleshooting. Verify signal quality, APN settings, and device compatibility.",
    "billing_review": "Review billing transaction details. Verify promotional pricing, usage charges, and plan terms.",
    "device_diagnostics": "Verify device compatibility and SIM card status. Check for hardware or provisioning issues.",
    "service_configuration_review": "Review service configuration, provisioning status, and account settings.",
    "monitoring": "Monitor network site status and customer impact. Escalate if conditions worsen.",
    "human_escalation": "Escalate to specialist team for manual review and resolution.",
    "insufficient_evidence": "Collect additional information from customer. Investigation context is incomplete.",
}


def _build_evidence(context: dict, triggered_rules: list) -> list[dict]:
    evidence = []

    network = context.get("network", {})
    site = network.get("site")
    if site:
        status = site.get("status", "unknown")
        evidence.append({
            "type": "operational",
            "source": "network_site",
            "reference": site.get("site_code", "?"),
            "statement": f"Serving site {site.get('site_code', '?')} is {status}.",
        })

    events = network.get("events", [])
    active_events = [e for e in events if e.get("status") == "active"]
    high_sev = [e for e in active_events if e.get("severity") in ("high", "critical")]
    for ev in high_sev[:2]:
        evidence.append({
            "type": "operational",
            "source": "network_event",
            "reference": ev.get("site_code", "?"),
            "statement": f"{ev.get('event_type', '?')} ({ev.get('severity', '?')}) at {ev.get('site_code', '?')}: {ev.get('title', '?')}.",
        })

    incidents = context.get("incidents", [])
    active_incidents = [i for i in incidents if i.get("status") in ("investigating", "identified", "monitoring")]
    for inc in active_incidents[:2]:
        evidence.append({
            "type": "operational",
            "source": "incident",
            "reference": inc.get("incident_number", "?"),
            "statement": f"Active incident {inc.get('incident_number', '?')} ({inc.get('severity', '?')}) in {inc.get('region', '?')} region.",
        })

    prev = context.get("previous_tickets", [])
    same_cat = context.get("investigation", {}).get("same_category_previous_tickets", 0)
    if same_cat >= 2:
        evidence.append({
            "type": "operational",
            "source": "ticket_history",
            "reference": "customer_tickets",
            "statement": f"Customer has {same_cat} previous related ticket(s) in this category.",
        })

    for r in triggered_rules:
        if r.rule_id.startswith("MISSING"):
            evidence.append({
                "type": "operational",
                "source": "data_completeness",
                "reference": r.rule_id,
                "statement": r.reason,
            })

    return evidence


def _build_knowledge_sources(ai_result: dict) -> list[dict]:
    sources = []
    reasoning = ai_result.get("reasoning", {})
    citations = reasoning.get("knowledge_citations", [])
    for cit in citations:
        sources.append({
            "document_id": cit.get("document_id", ""),
            "section": cit.get("section", ""),
        })
    return sources


def _determine_confidence(
    evidence: list[dict],
    ai_confidence: str | None,
    triggered_rules: list,
    retrieval_count: int,
    ai_unavailable: bool,
) -> tuple[str, list[str]]:
    reasons = []
    score = 0

    op_evidence = [e for e in evidence if e["type"] == "operational"]
    if len(op_evidence) >= 3:
        score += 3
        reasons.append("Strong operational evidence available.")
    elif len(op_evidence) >= 1:
        score += 1
        reasons.append("Some operational evidence available.")
    else:
        reasons.append("Limited operational evidence.")

    if retrieval_count >= 3:
        score += 2
        reasons.append("Relevant knowledge procedures retrieved.")
    elif retrieval_count >= 1:
        score += 1
        reasons.append("Some relevant knowledge found.")
    else:
        reasons.append("No relevant knowledge retrieved.")

    if ai_confidence == "high":
        score += 2
        reasons.append("AI confidence is high.")
    elif ai_confidence == "medium":
        score += 1
        reasons.append("AI confidence is medium.")
    elif ai_confidence == "low":
        reasons.append("AI confidence is low.")
    elif ai_unavailable:
        reasons.append("AI service unavailable.")

    conflict_rules = [r for r in triggered_rules if r.rule_id == "AI-CONFLICT"]
    if conflict_rules:
        score -= 2
        reasons.append("AI assessment conflicts with operational data.")

    if score >= 5:
        return "high", reasons
    elif score >= 2:
        return "medium", reasons
    else:
        return "low", reasons


def _build_recommendation(
    triggered_rules: list,
    ticket: dict,
    context: dict,
) -> tuple[str, str, list[dict]]:
    rule_ids = {r.rule_id for r in triggered_rules}
    category = ticket.get("category", "network")
    segment = context.get("customer", {}).get("segment", "")

    if "MISSING-CUSTOMER" in rule_ids or "MISSING-SUBSCRIPTION" in rule_ids:
        return "insufficient_evidence", ACTION_MAP["insufficient_evidence"], []

    if "AI-CONFLICT" in rule_ids:
        return "human_escalation", ACTION_MAP["human_escalation"], []

    if category == "billing":
        return "billing_review", ACTION_MAP["billing_review"], []

    if category in ("voice", "sms"):
        return "customer_troubleshooting", ACTION_MAP["customer_troubleshooting"], []

    if category == "device":
        return "device_diagnostics", ACTION_MAP["device_diagnostics"], []

    if category == "roaming" or category == "account":
        return "service_configuration_review", ACTION_MAP["service_configuration_review"], []

    if "INC-ACTIVE-MATCH" in rule_ids:
        return "incident_review", ACTION_MAP["incident_review"], [
            {"category": "network_investigation", "action": ACTION_MAP["network_investigation"]},
        ]

    if "NET-DEGRADED-SITE" in rule_ids or "NET-ACTIVE-EVENTS" in rule_ids:
        primary = "network_investigation"
        alt = []
        if "CASE-REPEATED" in rule_ids:
            alt.append({"category": "customer_troubleshooting", "action": ACTION_MAP["customer_troubleshooting"]})
        return primary, ACTION_MAP["network_investigation"], alt

    if "NET-NO-INCIDENT" in rule_ids:
        return "customer_troubleshooting", ACTION_MAP["customer_troubleshooting"], [
            {"category": "monitoring", "action": ACTION_MAP["monitoring"]},
        ]

    if "CASE-REPEATED" in rule_ids:
        return "customer_troubleshooting", ACTION_MAP["customer_troubleshooting"], [
            {"category": "human_escalation", "action": ACTION_MAP["human_escalation"]},
        ]

    if segment == "enterprise":
        return "human_escalation", ACTION_MAP["human_escalation"], []

    return "monitoring", ACTION_MAP["monitoring"], []


def _store_review_state(
    conn,
    ticket_id: int,
    ticket_number: str,
    category: str,
    action: str,
    confidence: str,
    requires_review: bool,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    decision = "pending_review" if requires_review else "approved"
    try:
        conn.execute(
            "INSERT INTO review_states (ticket_id, recommendation_category, recommendation_action, confidence, reviewer_decision, reason, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, category, action, confidence, decision, "", now, now),
        )
        conn.commit()
    except Exception as e:
        logger.warning("Failed to store review state: %s", e)


def resolve_case(conn, ticket_id: int, question: str | None = None) -> dict:
    investigation = get_case_investigation(conn, ticket_id)
    if not investigation:
        return {
            "case_id": str(ticket_id),
            "decision_status": "insufficient_evidence",
            "primary_recommendation": {
                "category": "insufficient_evidence",
                "action": "Unable to build investigation context.",
            },
            "alternative_actions": [],
            "deterministic_findings": [],
            "ai_assessment": None,
            "evidence": [],
            "knowledge_sources": [],
            "confidence": "low",
            "confidence_reasons": ["Investigation context could not be built."],
            "limitations": ["Investigation context is unavailable."],
            "conflicts": [],
            "requires_human_review": True,
        }

    ticket = investigation.get("ticket", {})

    rule_results = evaluate_rules(investigation)
    triggered = get_triggered_rules(rule_results)

    ai_result = None
    ai_confidence = None
    ai_unavailable = False
    retrieval_count = 0
    try:
        ai_result = analyze_case(investigation, question=question or "What is the recommended next action for this case?")
        reasoning = ai_result.get("reasoning", {})
        ai_confidence = reasoning.get("confidence")
        retrieval = ai_result.get("retrieval", {})
        retrieval_count = retrieval.get("total", 0)
    except Exception as e:
        logger.warning("AI reasoning failed: %s", e)
        ai_unavailable = True

    if ai_result:
        investigation_with_ai = dict(investigation)
        investigation_with_ai["ai_result"] = ai_result
        rule_results = evaluate_rules(investigation_with_ai)
        triggered = get_triggered_rules(rule_results)

    evidence = _build_evidence(investigation, triggered)
    knowledge_sources = _build_knowledge_sources(ai_result) if ai_result else []

    confidence, confidence_reasons = _determine_confidence(
        evidence, ai_confidence, triggered, retrieval_count, ai_unavailable
    )

    primary_cat, primary_action, alternatives = _build_recommendation(triggered, ticket, investigation)

    review_required, review_reasons = requires_human_review(rule_results, ai_confidence)

    conflicts = []
    conflict_rules = [r for r in triggered if r.rule_id == "AI-CONFLICT"]
    for cr in conflict_rules:
        conflicts.append(cr.reason)

    limitations = []
    if ai_unavailable:
        limitations.append("AI reasoning service is unavailable.")
    if not knowledge_sources:
        limitations.append("No relevant knowledge procedures were retrieved.")
    missing = [r for r in triggered if r.rule_id.startswith("MISSING")]
    for m in missing:
        limitations.append(m.reason)

    deterministic_findings = []
    for r in triggered:
        deterministic_findings.append(r.reason)

    ticket_number = ticket.get("ticket_number", str(ticket_id))
    _store_review_state(conn, ticket_id, ticket_number, primary_cat, primary_action, confidence, review_required)

    return {
        "case_id": ticket_number,
        "decision_status": "recommended",
        "primary_recommendation": {
            "category": primary_cat,
            "action": primary_action,
        },
        "alternative_actions": alternatives,
        "deterministic_findings": deterministic_findings,
        "ai_assessment": {
            "summary": ai_result["reasoning"]["summary"] if ai_result and "reasoning" in ai_result else None,
            "confidence": ai_confidence,
            "status": ai_result["reasoning"].get("status") if ai_result and "reasoning" in ai_result else None,
        } if ai_result else None,
        "evidence": evidence,
        "knowledge_sources": knowledge_sources,
        "confidence": confidence,
        "confidence_reasons": confidence_reasons,
        "limitations": limitations,
        "conflicts": conflicts,
        "requires_human_review": review_required,
        "review_reasons": review_reasons,
    }
