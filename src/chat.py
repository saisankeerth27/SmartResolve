"""Customer chat service — manages conversations, messages, and Mode A/B/C integration."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field

from src.database.db import get_connection
from src.tickets import transition_case, get_current_state, InvalidTransitionError
from src.audit import (
    record_case_created, record_analysis_started, record_mode_selected,
    record_clarification, record_clarification_answer, record_escalation,
    record_draft_generated, record_event,
)
from src.services.analysis_service import analyze_ticket

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    id: int
    conversation_id: int
    sender: str
    content: str
    mode: str | None
    created_at: str


@dataclass
class ConversationInfo:
    id: int
    ticket_id: int
    customer_id: int
    ticket_number: str
    customer_name: str
    subject: str
    status: str
    created_at: str
    updated_at: str


def get_or_create_conversation(customer_id: int) -> ConversationInfo:
    """Get an active conversation for a customer, or create a new one."""
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        cursor = conn.execute(
            "SELECT c.id, c.ticket_id, t.ticket_number, t.status, c.created_at, c.updated_at "
            "FROM conversations c JOIN tickets t ON c.ticket_id = t.id "
            "WHERE c.customer_id = ? AND c.status = 'active' ORDER BY c.created_at DESC LIMIT 1",
            (customer_id,),
        )
        row = cursor.fetchone()
        if row:
            conv_id, ticket_id, ticket_number, status, created_at, updated_at = row
            cust = conn.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
            return ConversationInfo(
                id=conv_id, ticket_id=ticket_id, customer_id=customer_id,
                ticket_number=ticket_number, customer_name=cust[0] if cust else "Unknown",
                subject="", status=status, created_at=created_at, updated_at=updated_at,
            )

        ticket_number = _generate_ticket_number(conn)
        cursor.execute(
            "INSERT INTO tickets (ticket_number, customer_id, category, priority, subject, description, status, channel, created_at, updated_at) VALUES (?, ?, 'account', 'medium', 'New conversation', 'Customer initiated chat', 'open', 'web', ?, ?)",
            (ticket_number, customer_id, now, now),
        )
        ticket_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO conversations (ticket_id, customer_id, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
            (ticket_id, customer_id, now, now),
        )
        conv_id = cursor.lastrowid

        cust = conn.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        conn.commit()

        record_case_created(conn, ticket_id, customer_id, "web")
        conn.commit()

        return ConversationInfo(
            id=conv_id, ticket_id=ticket_id, customer_id=customer_id,
            ticket_number=ticket_number, customer_name=cust[0] if cust else "Unknown",
            subject="New conversation", status="open", created_at=now, updated_at=now,
        )
    finally:
        conn.close()


def send_customer_message(conversation_id: int, customer_id: int, content: str) -> dict:
    """Process a customer message through the full pipeline. Returns the assistant response."""
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        conv = conn.execute(
            "SELECT c.id, c.ticket_id, c.customer_id FROM conversations c WHERE c.id = ? AND c.status = 'active'",
            (conversation_id,),
        ).fetchone()
        if not conv:
            return {"error": "Conversation not found or closed"}

        conv_id, ticket_id, _ = conv

        conn.execute(
            "INSERT INTO conversation_messages (conversation_id, sender, content, mode, created_at) VALUES (?, 'customer', ?, NULL, ?)",
            (conv_id, content, now),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))

        record_event(conn, ticket_id, "customer_reply", {"message": content[:200]}, "customer")
        conn.commit()

        analysis = analyze_ticket(conn, ticket_id)
        mode = analysis.mode
        result_msg = ""
        mode_label = None

        if mode == "A":
            if analysis.draft:
                result_msg = _build_mode_a_response(analysis.draft, analysis.classification)
            else:
                inv_ctx = analysis.investigation or {}
                result_msg = _build_deterministic_mode_a(inv_ctx)
            mode_label = "A"
            record_draft_generated(conn, ticket_id, {"mode": "A"})
            conn.commit()

        elif mode == "B":
            if analysis.clarification:
                result_msg = analysis.clarification.question
            else:
                result_msg = _build_deterministic_mode_b(analysis.classification)
            mode_label = "B"
            missing = (analysis.classification.missing_fields or analysis.classification.required_information or ["unknown"])[0]
            record_clarification(conn, ticket_id, missing, result_msg)
            conn.commit()

        elif mode == "C":
            result_msg = "I'm connecting you with a specialist who has your full context, so you won't need to repeat the issue."
            mode_label = "C"
            if analysis.handover:
                from src.escalate import store_escalation
                store_escalation(conn, ticket_id, analysis.handover)
                record_escalation(conn, ticket_id, analysis.handover.escalation_queue, analysis.handover.escalation_reasons)
                conn.commit()
            else:
                record_escalation(conn, ticket_id, "human_review", analysis.classification.reason_codes)
                conn.commit()
        else:
            result_msg = "I've noted your message. A support specialist will review your case shortly."
            mode_label = None

        conn.execute(
            "INSERT INTO conversation_messages (conversation_id, sender, content, mode, created_at) VALUES (?, 'assistant', ?, ?, ?)",
            (conv_id, result_msg, mode_label, now),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
        conn.commit()

        return {
            "message": result_msg,
            "mode": mode_label,
            "ticket_id": ticket_id,
            "conversation_id": conv_id,
        }
    finally:
        conn.close()


def get_conversation_messages(conversation_id: int) -> list[ChatMessage]:
    """Get all messages for a conversation."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, conversation_id, sender, content, mode, created_at "
            "FROM conversation_messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        return [
            ChatMessage(id=r[0], conversation_id=r[1], sender=r[2], content=r[3], mode=r[4], created_at=r[5])
            for r in rows
        ]
    finally:
        conn.close()


def get_customer_conversations(customer_id: int) -> list[ConversationInfo]:
    """Get all conversations for a customer."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT c.id, c.ticket_id, c.customer_id, t.ticket_number, cust.name, t.subject, t.status, c.created_at, c.updated_at "
            "FROM conversations c "
            "JOIN tickets t ON c.ticket_id = t.id "
            "JOIN customers cust ON c.customer_id = cust.id "
            "WHERE c.customer_id = ? ORDER BY c.created_at DESC",
            (customer_id,),
        ).fetchall()
        return [
            ConversationInfo(
                id=r[0], ticket_id=r[1], customer_id=r[2], ticket_number=r[3],
                customer_name=r[4], subject=r[5], status=r[6], created_at=r[7], updated_at=r[8],
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_ticket_conversation(ticket_id: int) -> list[ChatMessage]:
    """Get the conversation messages for a ticket (used by AgentConsole)."""
    conn = get_connection()
    try:
        conv = conn.execute(
            "SELECT id FROM conversations WHERE ticket_id = ? ORDER BY created_at DESC LIMIT 1",
            (ticket_id,),
        ).fetchone()
        if not conv:
            return []
        return get_conversation_messages(conv[0])
    finally:
        conn.close()


def _generate_ticket_number(conn) -> str:
    cursor = conn.execute("SELECT MAX(CAST(SUBSTR(ticket_number, 5) AS INTEGER)) FROM tickets")
    row = cursor.fetchone()
    max_num = row[0] if row and row[0] else 300000
    return f"TKT-{max_num + 1}"


def _build_mode_a_response(draft, classification) -> str:
    parts = []

    if hasattr(draft, 'draft_response') and draft.draft_response:
        parts.append(draft.draft_response)
    elif hasattr(draft, 'reasoning_summary') and draft.reasoning_summary:
        parts.append(draft.reasoning_summary)

    if hasattr(draft, 'citations') and draft.citations:
        refs = ", ".join(draft.citations[:2]) if isinstance(draft.citations, list) else str(draft.citations)
        parts.append(f"Reference: {refs}")

    if hasattr(draft, 'limitations') and draft.limitations:
        parts.append("A resolution draft has been prepared for a support agent to review before anything is finalized.")

    if not parts:
        parts.append("I found information that may help with your issue. A support agent will review and follow up shortly.")

    return " ".join(parts)


def _build_deterministic_mode_a(investigation: dict) -> str:
    """Build a Mode A response without Gemini — uses investigation context directly."""
    ticket = investigation.get("ticket", {})
    customer = investigation.get("customer", {})
    subscription = investigation.get("subscription", {})
    network = investigation.get("network", {})
    incidents = investigation.get("incidents", [])
    inv = investigation.get("investigation", {})
    category = ticket.get("category", "general")
    subject = ticket.get("subject", "your issue")

    parts = []
    parts.append(f"Regarding your {category} concern about '{subject}':")

    if subscription:
        parts.append(f"Your plan is {subscription.get('plan_name', 'unknown')} ({subscription.get('service_type', 'N/A')}) at ₹{subscription.get('monthly_price', 'N/A')}/month.")
        if subscription.get("data_usage_gb") and subscription.get("data_limit_gb"):
            usage_pct = (subscription["data_usage_gb"] / subscription["data_limit_gb"]) * 100
            if usage_pct > 90:
                parts.append(f"Your data usage is at {usage_pct:.0f}% of your {subscription['data_limit_gb']}GB limit, which may be affecting service.")

    if network.get("site"):
        site = network["site"]
        parts.append(f"Serving site {site.get('site_code', 'N/A')} ({site.get('technology', 'N/A')}) is {site.get('status', 'unknown')} with {site.get('capacity_percent', 0)}% capacity.")
        if site.get("capacity_percent", 0) > 85:
            parts.append("High capacity at your serving site may cause slower speeds during peak hours.")

    if incidents:
        active = [i for i in incidents if i.get("status") != "resolved"]
        if active:
            parts.append(f"There {('is' if len(active) == 1 else 'are')} {len(active)} active incident(s) in your region that may be affecting service.")

    if inv.get("same_category_previous_tickets", 0) > 0:
        parts.append(f"We found {inv['same_category_previous_tickets']} previous ticket(s) in the same category. A specialist will review the pattern.")

    parts.append("A support agent will review this case and follow up shortly. You can also check the case status in your account.")
    return " ".join(parts)


def _build_deterministic_mode_b(classification) -> str:
    """Build a Mode B clarification question without Gemini."""
    missing = classification.missing_fields or classification.required_information
    if not missing:
        missing = ["issue_details"]

    from src.config import FALLBACK_QUESTIONS
    field_name = missing[0]
    question = FALLBACK_QUESTIONS.get(field_name, f"Could you provide more details about your {field_name.replace('_', ' ')}?")

    return f"To help resolve your case, I need some additional information: {question}"
