"""Conflict detection for conflicting data between sources.

Never silently choose one source. Display the conflict and require human action.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Conflict:
    conflict_type: str
    source_a: str
    source_b: str
    description: str
    impact: str
    human_action_required: str


def detect_conflicts(context: dict) -> list[Conflict]:
    """Detect all data conflicts in the case context."""
    conflicts = []

    ticket = context.get("ticket", {})
    subscription = context.get("subscription")
    customer = context.get("customer", {})
    network = context.get("network", {})
    incidents = context.get("incidents", [])
    investigation = context.get("investigation", {})

    # ── Ticket vs Subscription status conflict ────────
    if subscription:
        ticket_status = ticket.get("status", "").lower()
        sub_status = subscription.get("status", "").lower()
        if ticket_status in ("open", "in_progress") and sub_status == "suspended":
            conflicts.append(Conflict(
                conflict_type="ticket_sub_status",
                source_a=f"Ticket status: {ticket_status}",
                source_b=f"Subscription status: {sub_status}",
                description="Ticket is active but subscription is suspended.",
                impact="Cannot proceed with standard resolution — service may be blocked.",
                human_action_required="Verify subscription status and determine if service can be restored.",
            ))

    # ── Network site vs active events conflict ────────
    site = network.get("site")
    events = network.get("events", [])
    if site:
        site_status = site.get("status", "").lower()
        active_events = [e for e in events if e.get("status") == "active"]
        high_sev_events = [e for e in active_events if e.get("severity") in ("critical", "high")]
        if site_status == "operational" and high_sev_events:
            conflicts.append(Conflict(
                conflict_type="site_vs_events",
                source_a=f"Site status: {site_status}",
                source_b=f"Active high-severity events: {len(high_sev_events)}",
                description=f"Site '{site.get('site_code', '')}' reports operational but has {len(high_sev_events)} high-severity active events.",
                impact="Site status may be stale or events may not be accurately reflected.",
                human_action_required="Verify actual site status with network operations.",
            ))

    # ── Multiple active incidents overlap ─────────────
    active_incidents = [i for i in incidents if i.get("status") in ("investigating", "identified", "monitoring")]
    if len(active_incidents) > 2:
        conflicts.append(Conflict(
            conflict_type="multiple_incidents",
            source_a=f"{len(active_incidents)} active incidents",
            source_b="Single customer ticket",
            description="Multiple active incidents overlap — customer may be affected by more than one.",
            impact="Cannot determine which incident is the primary cause.",
            human_action_required="Determine which incident is the root cause and which are symptoms.",
        ))

    # ── Subscription vs available service conflict ─────
    if subscription:
        plan_name = subscription.get("plan_name", "")
        service_type = subscription.get("service_type", "")
        if service_type == "broadband" and "fiber" not in plan_name.lower():
            # Check if network site supports broadband
            if site and "fiber" not in site.get("technology", "").lower():
                conflicts.append(Conflict(
                    conflict_type="service_mismatch",
                    source_a=f"Plan: {plan_name} ({service_type})",
                    source_b=f"Site technology: {site.get('technology', 'N/A')}",
                    description="Broadband subscription but serving site may not support fiber.",
                    impact="Service may not be deliverable at this location.",
                    human_action_required="Verify service availability at customer location.",
                ))

    # ── Previous ticket says resolved, customer says not ──
    prev_tickets = context.get("previous_tickets", [])
    for pt in prev_tickets:
        pt_status = pt.get("status", "").lower()
        pt_category = pt.get("category", "").lower()
        current_category = ticket.get("category", "").lower()
        if pt_status == "resolved" and pt_category == current_category:
            # Check if interactions indicate ongoing issue
            interactions = context.get("interactions", [])
            recent_complaints = [
                i for i in interactions
                if i.get("sentiment") in ("negative", "frustrated")
            ]
            if recent_complaints:
                conflicts.append(Conflict(
                    conflict_type="resolved_but_ongoing",
                    source_a=f"Previous ticket {pt.get('ticket_number', '')}: resolved",
                    source_b=f"Recent negative interactions: {len(recent_complaints)}",
                    description="Previous ticket was marked resolved but customer still reports issues.",
                    impact="Previous resolution may have been incomplete or issue has recurred.",
                    human_action_required="Review previous resolution and determine if issue is truly resolved.",
                ))
                break  # Only report once

    return conflicts
