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
from src.clarify import answer_satisfies_field, get_latest_unanswered_field, record_clarification_answer

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
            tkt = conn.execute("SELECT subject, subscription_id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
            tkt_subject = tkt[0] if tkt else ""
            if tkt and not tkt[1]:
                sub_row = conn.execute(
                    "SELECT id FROM subscriptions WHERE customer_id = ? AND status = 'active' ORDER BY id ASC LIMIT 1",
                    (customer_id,),
                ).fetchone()
                if not sub_row:
                    sub_row = conn.execute(
                        "SELECT id FROM subscriptions WHERE customer_id = ? ORDER BY id ASC LIMIT 1",
                        (customer_id,),
                    ).fetchone()
                if sub_row:
                    conn.execute("UPDATE tickets SET subscription_id = ? WHERE id = ?", (sub_row[0], ticket_id))
                    conn.commit()

            return ConversationInfo(
                id=conv_id, ticket_id=ticket_id, customer_id=customer_id,
                ticket_number=ticket_number, customer_name=cust[0] if cust else "Unknown",
                subject=tkt_subject, status=status, created_at=created_at, updated_at=updated_at,
            )

        # Look up active subscription for customer
        sub_row = conn.execute(
            "SELECT id FROM subscriptions WHERE customer_id = ? AND status = 'active' ORDER BY id ASC LIMIT 1",
            (customer_id,),
        ).fetchone()
        if not sub_row:
            sub_row = conn.execute(
                "SELECT id FROM subscriptions WHERE customer_id = ? ORDER BY id ASC LIMIT 1",
                (customer_id,),
            ).fetchone()
        sub_id = sub_row[0] if sub_row else None

        ticket_number = _generate_ticket_number(conn)
        cursor.execute(
            "INSERT INTO tickets (ticket_number, customer_id, subscription_id, category, priority, subject, description, status, channel, created_at, updated_at) VALUES (?, ?, ?, 'account', 'medium', 'New conversation', 'Customer initiated chat', 'open', 'web', ?, ?)",
            (ticket_number, customer_id, sub_id, now, now),
        )
        ticket_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO conversations (ticket_id, customer_id, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
            (ticket_id, customer_id, now, now),
        )
        conv_id = cursor.lastrowid

        cust = conn.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        conn.commit()

        record_case_created(conn, ticket_id, ticket_number, cust[0] if cust else "Unknown")
        conn.commit()

        return ConversationInfo(
            id=conv_id, ticket_id=ticket_id, customer_id=customer_id,
            ticket_number=ticket_number, customer_name=cust[0] if cust else "Unknown",
            subject="New conversation", status="open", created_at=now, updated_at=now,
        )
    finally:
        conn.close()


def create_new_conversation(customer_id: int) -> ConversationInfo:
    """Explicitly create a new conversation and ticket for a customer, closing any prior active conversation."""
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        conn.execute(
            "UPDATE conversations SET status = 'closed', updated_at = ? WHERE customer_id = ? AND status = 'active'",
            (now, customer_id),
        )
        conn.execute(
            """UPDATE tickets SET status = 'dismissed', updated_at = ?
               WHERE customer_id = ? AND channel = 'web'
                 AND subject = 'New conversation' AND description = 'Customer initiated chat'""",
            (now, customer_id),
        )

        sub_row = conn.execute(
            "SELECT id FROM subscriptions WHERE customer_id = ? AND status = 'active' ORDER BY id ASC LIMIT 1",
            (customer_id,),
        ).fetchone()
        if not sub_row:
            sub_row = conn.execute(
                "SELECT id FROM subscriptions WHERE customer_id = ? ORDER BY id ASC LIMIT 1",
                (customer_id,),
            ).fetchone()
        sub_id = sub_row[0] if sub_row else None

        ticket_number = _generate_ticket_number(conn)
        cursor = conn.execute(
            "INSERT INTO tickets (ticket_number, customer_id, subscription_id, category, priority, subject, description, status, channel, created_at, updated_at) VALUES (?, ?, ?, 'account', 'medium', 'New conversation', 'Customer initiated chat', 'open', 'web', ?, ?)",
            (ticket_number, customer_id, sub_id, now, now),
        )
        ticket_id = cursor.lastrowid

        cursor = conn.execute(
            "INSERT INTO conversations (ticket_id, customer_id, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
            (ticket_id, customer_id, now, now),
        )
        conv_id = cursor.lastrowid

        cust = conn.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()
        conn.commit()

        record_case_created(conn, ticket_id, ticket_number, cust[0] if cust else "Unknown")
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
            "SELECT c.id, c.ticket_id, c.customer_id, c.status, t.status "
            "FROM conversations c JOIN tickets t ON t.id = c.ticket_id WHERE c.id = ?",
            (conversation_id,),
        ).fetchone()
        if not conv:
            return {"error": "Conversation not found or closed"}

        conv_id, ticket_id, _, conversation_status, ticket_status = conv

        conn.execute(
            "INSERT INTO conversation_messages (conversation_id, sender, content, mode, created_at) VALUES (?, 'customer', ?, NULL, ?)",
            (conv_id, content, now),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))

        pending_field = get_latest_unanswered_field(conn, ticket_id)
        if pending_field:
            record_clarification_answer(conn, ticket_id, pending_field, content)
            conn.commit()

        if conversation_status == "closed" or ticket_status in ("escalated", "escalation_requested", "human_review"):
            conn.commit()
            return {
                "message": None,
                "mode": None,
                "ticket_id": ticket_id,
                "conversation_id": conv_id,
                "transcript_only": True,
            }

        # Update ticket details based on customer message
        ticket_row = conn.execute(
            "SELECT subject, description, category, subscription_id FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()
        if ticket_row:
            curr_subject, curr_desc, curr_category, curr_sub_id = ticket_row

            if not curr_sub_id:
                sub_row = conn.execute(
                    "SELECT id FROM subscriptions WHERE customer_id = ? AND status = 'active' ORDER BY id ASC LIMIT 1",
                    (customer_id,),
                ).fetchone()
                if not sub_row:
                    sub_row = conn.execute(
                        "SELECT id FROM subscriptions WHERE customer_id = ? ORDER BY id ASC LIMIT 1",
                        (customer_id,),
                    ).fetchone()
                if sub_row:
                    conn.execute("UPDATE tickets SET subscription_id = ? WHERE id = ?", (sub_row[0], ticket_id))

            from src.category_detector import detect_category
            detected_cat = detect_category(content)

            updates = []
            params = []
            if curr_subject in ("New conversation", "Customer initiated chat", "") or curr_desc in ("Customer initiated chat", "New conversation", ""):
                first_line = content.strip().split("\n")[0][:80]
                updates.append("subject = ?")
                params.append(first_line)
                updates.append("description = ?")
                params.append(content.strip())
            elif curr_subject in ("Hello", "Hello i need help", "Hello, I need help") or curr_category == "account":
                # Promote the first real issue into the ticket summary; transcript owns later turns.
                if detected_cat != "account":
                    updates.append("subject = ?")
                    params.append(content.strip().split("\n")[0][:120])
                    updates.append("description = ?")
                    params.append(content.strip()[:500])

            if detected_cat != "account" or curr_category == "account":
                updates.append("category = ?")
                params.append(detected_cat)

            if updates:
                params.append(now)
                params.append(ticket_id)
                conn.execute(f"UPDATE tickets SET {', '.join(updates)}, updated_at = ? WHERE id = ?", params)

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
            conn.execute("UPDATE conversations SET status = 'closed', updated_at = ? WHERE id = ?", (now, conv_id))

        last_assistant = conn.execute(
            "SELECT content FROM conversation_messages WHERE conversation_id = ? AND sender = 'assistant' ORDER BY id DESC LIMIT 1",
            (conv_id,),
        ).fetchone()
        if last_assistant and last_assistant[0] == result_msg:
            result_msg = _rephrase_duplicate_response(result_msg, mode_label)

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


def _rephrase_duplicate_response(message: str, mode: str | None) -> str:
    if mode == "B":
        return "I still need that detail to continue. Could you answer the question with a little more specificity?"
    if mode == "C":
        return "Your case is already with a specialist. I have added this message to the agent transcript."
    return "I have noted your latest message and will continue from the existing case context."


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
    """Build a Mode A response without Gemini — realistic telecom operator message."""
    ticket = investigation.get("ticket", {})
    customer = investigation.get("customer", {})
    subscription = investigation.get("subscription", {})
    network = investigation.get("network", {})
    incidents = investigation.get("incidents", [])
    inv = investigation.get("investigation", {})
    category = ticket.get("category", "general")
    subject = ticket.get("subject", "your issue")
    first_name = customer.get("name", "there").split()[-1]

    parts = []
    parts.append(f"Thanks for reaching out{', ' + first_name if first_name != 'there' else ''}. I can see your {category} issue regarding '{subject}' and I'm on it.")

    if subscription:
        plan = subscription.get("plan_name", "")
        service_type = subscription.get("service_type", "")
        parts.append(f"I can see you're on the {plan} plan ({service_type}), so this is covered under your current subscription.")
        if subscription.get("data_usage_gb") and subscription.get("data_limit_gb"):
            usage_pct = (subscription["data_usage_gb"] / subscription["data_limit_gb"]) * 100
            if usage_pct > 90:
                parts.append(f"Just a note — your data usage is at {usage_pct:.0f}% of your {subscription['data_limit_gb']}GB limit; I'd suggest checking you haven't hit your cap.")

    if network.get("site"):
        site = network["site"]
        status = site.get("status", "unknown")
        parts.append(f"The network site serving you ({site.get('site_code', 'N/A')}, {site.get('technology', 'N/A')}) is currently {status}.")
        if status == "degraded":
            parts.append("It's running at reduced capacity, which can cause slower speeds — we're monitoring it and it should settle shortly.")
        if site.get("capacity_percent", 0) > 85:
            parts.append("That site is also carrying high load right now, which can make speeds dip during peak hours.")

    active = [i for i in incidents if i.get("status") != "resolved"]
    if active:
        parts.append(f"There {('is' if len(active) == 1 else 'are')} {len(active)} ongoing network incident(s) in your region affecting service — this is a known issue and our teams are working on it.")

    parts.append("I've prepared a resolution note for our support team so they can follow up directly. Is there anything else I can help with?")

    hint = _category_step(category)
    if hint:
        parts.append(f"In the meantime, a quick try: {hint}")
    return " ".join(parts)


def _category_step(category: str) -> str | None:
    """Return a quick first-step troubleshooting hint for the category."""
    steps = {
        "connectivity": "power-cycle your router by leaving it off for 30 seconds and turning it back on, then test again.",
        "network": "restart the device and toggle airplane mode off/on once to re-register on the network.",
        "voice": "restart your phone, and if calls still drop, try it in a different area to help us isolate the cause.",
        "sms": "switch between 4G and 3G in your settings once — this often forces a fresh SMS registration.",
        "billing": "your latest bill is available in the app — I can walk you through any charges you don't recognise.",
        "device": "confirm the affected device is updated and try a soft restart of that device.",
        "roaming": "make sure data roaming is enabled in your phone settings when outside your home network.",
    }
    return steps.get(category)




def _build_deterministic_mode_b(classification) -> str:
    """Build a Mode B clarification question without Gemini."""
    missing = classification.missing_fields or classification.required_information
    if not missing:
        missing = ["issue_details"]

    from src.config import FALLBACK_QUESTIONS
    field_name = missing[0]
    question = FALLBACK_QUESTIONS.get(field_name, f"Could you provide more details about your {field_name.replace('_', ' ')}?")

    return f"I want to make sure I fix this properly. {question}"
