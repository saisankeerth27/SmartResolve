"""Context builder — creates grounded context for Gemini reasoning.

Separates operational facts from retrieved knowledge so Gemini knows
which information comes from the database and which from knowledge documents.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def build_operational_facts(investigation: dict[str, Any]) -> list[str]:
    """Extract operational facts from investigation context.

    Avoids PII — excludes email, phone, unnecessary identifiers.
    Focuses on operational problem data.
    """
    facts: list[str] = []
    ticket = investigation.get("ticket", {})
    customer = investigation.get("customer")
    subscription = investigation.get("subscription")
    network = investigation.get("network", {})
    incidents = investigation.get("incidents", [])
    previous_tickets = investigation.get("previous_tickets", [])
    inv_result = investigation.get("investigation", {})

    facts.append(f"Ticket category: {ticket.get('category', 'unknown')}")
    facts.append(f"Ticket priority: {ticket.get('priority', 'unknown')}")
    facts.append(f"Ticket subject: {ticket.get('subject', 'unknown')}")
    facts.append(f"Ticket description: {ticket.get('description', 'no description')}")

    if customer:
        facts.append(f"Customer segment: {customer.get('segment', 'unknown')}")
        facts.append(f"Customer account status: {customer.get('status', 'unknown')}")

    if subscription:
        facts.append(f"Service type: {subscription.get('service_type', 'unknown')}")
        facts.append(f"Plan: {subscription.get('plan_name', 'unknown')} ({subscription.get('plan_type', 'unknown')})")
        facts.append(f"Network technology: {subscription.get('technology', 'unknown')}")
        facts.append(f"Region: {subscription.get('region', 'unknown')}, {subscription.get('city', 'unknown')}")
        usage = subscription.get("data_usage_gb", 0)
        limit = subscription.get("data_limit_gb", 0)
        if limit > 0:
            pct = round((usage / limit) * 100, 1)
            facts.append(f"Data usage: {usage} GB / {limit} GB ({pct}%)")

    site = network.get("site")
    if site:
        facts.append(f"Serving network site: {site.get('site_code', 'N/A')} ({site.get('site_name', 'unknown')})")
        facts.append(f"Site technology: {site.get('technology', 'unknown')}")
        facts.append(f"Site status: {site.get('status', 'unknown')}")
        facts.append(f"Site capacity: {site.get('capacity_percent', 0)}%")

    active_events = [e for e in network.get("events", []) if e.get("status") == "active"]
    if active_events:
        facts.append(f"Active network events at serving site: {len(active_events)}")
        for ev in active_events[:3]:
            facts.append(f"  - {ev.get('title', 'Unknown')} (severity: {ev.get('severity', 'Unknown')})")
    else:
        facts.append("No active network events at serving site")

    if incidents:
        inc = incidents[0]
        facts.append(f"Active incident in region: {inc.get('incident_number', 'N/A')} - {inc.get('title', 'unknown')}")
        facts.append(f"  Severity: {inc.get('severity', 'unknown')}, Status: {inc.get('status', 'unknown')}")
        facts.append(f"  Estimated affected customers: {inc.get('affected_customers_estimate', 0):,}")
    else:
        facts.append("No active incident in the customer's region")

    same_cat = inv_result.get("same_category_previous_tickets", 0)
    if same_cat > 0:
        facts.append(f"Previous related tickets: {same_cat} other {ticket.get('category', '')} ticket(s)")

    return facts


def build_retrieved_knowledge(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Format retrieved chunks for the reasoning prompt."""
    knowledge = []
    for chunk in chunks:
        knowledge.append({
            "document_id": chunk.get("document_id", ""),
            "document_title": chunk.get("document_title", ""),
            "section_heading": chunk.get("section_heading", ""),
            "content": chunk.get("content", ""),
            "score": chunk.get("score", 0),
        })
    return knowledge


def build_retrieval_query(investigation: dict[str, Any]) -> str:
    """Build a deterministic query from investigation context.

    Focuses on operational problem. Excludes PII.
    """
    ticket = investigation.get("ticket", {})
    subscription = investigation.get("subscription")
    network = investigation.get("network", {})
    incidents = investigation.get("incidents", [])

    parts = []

    category = ticket.get("category", "")
    if category:
        parts.append(category)

    subject = ticket.get("subject", "")
    if subject:
        parts.append(subject)

    description = ticket.get("description", "")
    if description:
        parts.append(description)

    if subscription:
        parts.append(subscription.get("service_type", ""))
        parts.append(subscription.get("technology", ""))

    site = network.get("site")
    if site:
        parts.append(site.get("status", ""))
        if site.get("status") in ("degraded", "offline"):
            parts.append("network degradation")

    active_events = [e for e in network.get("events", []) if e.get("status") == "active"]
    for ev in active_events[:2]:
        parts.append(ev.get("title", ""))

    if incidents:
        parts.append("active regional incident")

    return " ".join(p for p in parts if p).strip()
