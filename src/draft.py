"""Mode A — Grounded resolution draft generator.

Uses Gemini + retrieval evidence to create an approvable draft for the human agent.
The draft must reference customer/account facts, operational facts, and knowledge citations.
The agent NEVER automatically sends the response to the customer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.retrieval.retriever import retrieve_relevant_chunks
from src.retrieval.context_builder import (
    build_operational_facts,
    build_retrieved_knowledge,
    build_retrieval_query,
)
from src.config import CATEGORY_KNOWLEDGE_MAP


@dataclass
class DraftResult:
    draft_response: str
    reasoning_summary: str
    citations: list[dict[str, str]]
    confidence: float
    limitations: list[str]
    account_evidence: list[str]
    operational_evidence: list[str]
    knowledge_evidence: list[str]


def build_grounding_context(context: dict) -> dict:
    """Build the grounded context that Gemini receives.

    Before calling Gemini, Python must already have:
    - Mode A confirmed
    - Relevant retrieved evidence
    - Account facts
    - Operational facts
    - Eligibility confirmed
    - No blocking escalation condition
    """
    ticket = context.get("ticket", {})
    customer = context.get("customer", {})
    subscription = context.get("subscription", {})
    network = context.get("network", {})
    incidents = context.get("incidents", [])
    investigation = context.get("investigation", {})

    # Account evidence
    account_evidence = []
    if customer:
        account_evidence.append(f"Customer: {customer.get('name', 'N/A')} ({customer.get('segment', 'N/A')})")
    if subscription:
        account_evidence.append(f"Plan: {subscription.get('plan_name', 'N/A')} ({subscription.get('service_type', 'N/A')})")
        account_evidence.append(f"Status: {subscription.get('status', 'N/A')}")
        if subscription.get("data_limit_gb"):
            account_evidence.append(f"Data limit: {subscription['data_limit_gb']}GB")
        if subscription.get("monthly_price"):
            account_evidence.append(f"Monthly price: ₹{subscription['monthly_price']}")

    # Operational evidence
    operational_evidence = []
    site = network.get("site")
    if site:
        operational_evidence.append(f"Serving site: {site.get('site_code', 'N/A')} ({site.get('status', 'N/A')})")
    active_events = [e for e in network.get("events", []) if e.get("status") == "active"]
    for ev in active_events[:3]:
        operational_evidence.append(
            f"Active event: {ev.get('event_type', 'N/A')} ({ev.get('severity', 'N/A')}) at {ev.get('site_code', 'N/A')}"
        )
    active_incidents = [i for i in incidents if i.get("status") in ("investigating", "identified", "monitoring")]
    for inc in active_incidents[:2]:
        operational_evidence.append(
            f"Active incident: {inc.get('incident_number', 'N/A')} ({inc.get('severity', 'N/A')}) in {inc.get('region', 'N/A')}"
        )

    # Known facts from investigation
    known_facts = investigation.get("known_facts", [])

    # Retrieval context
    retrieval = context.get("retrieval", {})
    knowledge_chunks = retrieval.get("chunks", [])
    knowledge_evidence = [chunk.get("content", "")[:200] for chunk in knowledge_chunks[:3]]

    return {
        "ticket": {
            "number": ticket.get("ticket_number", ""),
            "category": ticket.get("category", ""),
            "subject": ticket.get("subject", ""),
            "description": ticket.get("description", ""),
            "priority": ticket.get("priority", ""),
        },
        "account_evidence": account_evidence,
        "operational_evidence": operational_evidence,
        "known_facts": known_facts,
        "knowledge_evidence": knowledge_evidence,
        "knowledge_citations": [
            {"document_id": c.get("document_id", ""), "section": c.get("section_heading", "")}
            for c in knowledge_chunks[:3]
        ],
    }


def build_draft_prompt(grounding: dict) -> str:
    """Build the prompt for Gemini to generate a grounded draft response."""
    ticket = grounding["ticket"]

    prompt_parts = [
        "You are a telecom support resolution assistant. Generate a grounded draft response for the human agent.",
        "",
        "CASE INFORMATION:",
        f"Ticket: {ticket['number']}",
        f"Category: {ticket['category']}",
        f"Subject: {ticket['subject']}",
        f"Description: {ticket['description']}",
        f"Priority: {ticket['priority']}",
        "",
        "ACCOUNT EVIDENCE:",
    ]
    for ev in grounding["account_evidence"]:
        prompt_parts.append(f"- {ev}")

    prompt_parts.append("")
    prompt_parts.append("OPERATIONAL EVIDENCE:")
    for ev in grounding["operational_evidence"]:
        prompt_parts.append(f"- {ev}")

    prompt_parts.append("")
    prompt_parts.append("KNOWN FACTS:")
    for fact in grounding["known_facts"]:
        prompt_parts.append(f"- {fact}")

    prompt_parts.append("")
    prompt_parts.append("RETRIEVED KNOWLEDGE:")
    for ev in grounding["knowledge_evidence"]:
        prompt_parts.append(f"- {ev[:200]}")

    prompt_parts.extend([
        "",
        "INSTRUCTIONS:",
        "1. Generate a professional, empathetic draft response to send to the customer.",
        "2. The draft must be grounded in the evidence above — do NOT fabricate facts.",
        "3. Reference specific account details, plan terms, or operational status.",
        "4. If a knowledge article applies, reference it naturally.",
        "5. Be clear about what the agent should communicate and what needs verification.",
        "6. If evidence is insufficient for a complete response, note what is missing.",
        "7. Return JSON with: draft_response, reasoning_summary, confidence (0.0-1.0), limitations.",
        "",
        "IMPORTANT: This is a DRAFT for agent review. Do NOT generate a final customer response.",
        "The agent must review and approve before any customer communication.",
    ])

    return "\n".join(prompt_parts)


def generate_draft(
    context: dict,
    gemini_client,
) -> DraftResult | None:
    """Generate a grounded Mode A draft using Gemini.

    Returns None if Gemini fails — the system must NOT produce a fake draft.
    """
    grounding = build_grounding_context(context)
    prompt = build_draft_prompt(grounding)

    system_instruction = (
        "You are SmartResolve, a telecom operations resolution assistant. "
        "Generate grounded draft responses for human agents. "
        "Never fabricate information. Always cite evidence. "
        "Return valid JSON only."
    )

    try:
        from src.ai.gemini_client import generate_text as gemini_generate
        response = gemini_generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.2,
        )

        if not response:
            return None

        # Parse response
        parsed = _parse_draft_response(response)
        if not parsed:
            return None

        return DraftResult(
            draft_response=parsed.get("draft_response", ""),
            reasoning_summary=parsed.get("reasoning_summary", ""),
            citations=parsed.get("citations", grounding["knowledge_citations"]),
            confidence=min(1.0, max(0.0, parsed.get("confidence", 0.5))),
            limitations=parsed.get("limitations", []),
            account_evidence=grounding["account_evidence"],
            operational_evidence=grounding["operational_evidence"],
            knowledge_evidence=grounding["knowledge_evidence"],
        )

    except Exception:
        return None


def _parse_draft_response(response: str) -> dict | None:
    """Parse Gemini response into structured draft."""
    import json
    import re

    text = response.strip()

    # Strip markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in response
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None
