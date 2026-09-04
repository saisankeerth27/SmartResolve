import sqlite3
import logging
from datetime import datetime

from src.database.repositories.customer_repository import CustomerRepository
from src.database.repositories.ticket_repository import TicketRepository
from src.database.repositories.network_repository import NetworkRepository
from src.database.repositories.incident_repository import IncidentRepository

logger = logging.getLogger(__name__)

# ── Network Health Status Thresholds ────────────────────
# Deterministic rules for network health classification:
#   - healthy:    0 degraded, 0 offline
#   - degraded:   >0 degraded OR >0 offline
#   - critical:   >0 offline
def _compute_network_health_status(health: dict) -> str:
    if health.get("offline", 0) > 0:
        return "critical"
    if health.get("degraded", 0) > 0 or health.get("maintenance", 0) > 0:
        return "degraded"
    return "healthy"


# ── Priority Case Scoring ───────────────────────────────
# Deterministic scoring for attention ranking:
#   critical priority  → +100
#   high priority      → +50
#   escalated status   → +40
#   assigned to team   → +10 (indicates active handling)
#   recent creation    → +5  (within 24h)
PRIORITY_WEIGHTS = {"critical": 100, "high": 50, "medium": 20, "low": 5}
STATUS_WEIGHTS = {"escalated": 40, "in_progress": 15, "open": 10, "pending_customer": 5}


def _score_ticket(ticket: dict) -> int:
    score = 0
    score += PRIORITY_WEIGHTS.get(ticket.get("priority", ""), 0)
    score += STATUS_WEIGHTS.get(ticket.get("status", ""), 0)
    if ticket.get("assigned_team"):
        score += 10
    return score


def get_dashboard_overview(conn: sqlite3.Connection) -> dict:
    cr = CustomerRepository(conn)
    tr = TicketRepository(conn)
    nr = NetworkRepository(conn)
    ir = IncidentRepository(conn)

    # ── Metrics ──────────────────────────────────────────
    total_customers = cr.count_all()
    open_tickets = tr.count_active_tickets()
    high_priority_tickets = tr.count_high_priority_active()
    active_incidents = ir.count_active()
    network_sites = nr.count_all_sites()
    affected_customers = ir.get_total_affected_customers()

    # ── Ticket Breakdown ─────────────────────────────────
    ticket_status = tr.count_by_status()
    ticket_priority = tr.count_by_priority()
    ticket_category = tr.count_by_category()

    # ── Network Health ───────────────────────────────────
    network_health = nr.get_network_health()
    network_health_status = _compute_network_health_status(network_health)

    # ── Regional Impact ──────────────────────────────────
    tickets_by_region = {r["region"]: r["ticket_count"] for r in tr.get_open_tickets_by_region()}
    incidents_by_region = {r["region"]: r for r in ir.get_active_by_region()}
    sites_by_region = nr.get_sites_by_region()

    regions = sorted(set(
        list(tickets_by_region.keys()) +
        list(incidents_by_region.keys()) +
        [s["region"] for s in sites_by_region]
    ))

    regional_impact = []
    for region in regions:
        t_count = tickets_by_region.get(region, 0)
        inc_data = incidents_by_region.get(region, {})
        inc_count = inc_data.get("incident_count", 0)
        affected = inc_data.get("total_affected", 0) or 0
        regional_impact.append({
            "region": region,
            "open_tickets": t_count,
            "active_incidents": inc_count,
            "affected_customers": affected,
        })

    # ── Active Incidents ─────────────────────────────────
    active_incidents_list = ir.get_active_incidents_list(limit=10)

    # ── Priority Cases ───────────────────────────────────
    # Gather candidates: escalated + high/critical open tickets
    escalated = tr.get_escalated_tickets(limit=20)
    # Score and rank
    scored = [(t, _score_ticket(t)) for t in escalated]
    scored.sort(key=lambda x: (-x[1], x[0].get("created_at", "")))
    priority_cases = []
    for ticket, score in scored[:10]:
        reasons = []
        if ticket.get("priority") in ("critical", "high"):
            reasons.append(f"{ticket['priority'].capitalize()} priority")
        if ticket.get("status") == "escalated":
            reasons.append("Escalated")
        if ticket.get("assigned_team"):
            reasons.append(f"Assigned to {ticket['assigned_team']}")
        priority_cases.append({
            "ticket_number": ticket.get("ticket_number", ""),
            "customer_name": ticket.get("customer_name", ""),
            "customer_number": ticket.get("customer_number", ""),
            "subject": ticket.get("subject", ""),
            "priority": ticket.get("priority", ""),
            "status": ticket.get("status", ""),
            "region": ticket.get("region") or "Unknown",
            "reasons": reasons,
            "score": score,
            "created_at": ticket.get("created_at", ""),
        })

    # ── Recent Activity ──────────────────────────────────
    recent_events = tr.get_recent_events(limit=15)
    recent_incidents = ir.get_recent_incidents(limit=5)
    recent_network_events = nr.get_active_events_by_site(limit=5)

    activity = []
    for ev in recent_events:
        activity.append({
            "type": "ticket_event",
            "timestamp": ev.get("created_at", ""),
            "description": ev.get("description", ""),
            "related_id": ev.get("ticket_number", ""),
            "event_type": ev.get("event_type", ""),
        })
    for inc in recent_incidents:
        activity.append({
            "type": "incident",
            "timestamp": inc.get("started_at", ""),
            "description": f"{inc.get('incident_number')}: {inc.get('title')}",
            "related_id": inc.get("incident_number", ""),
            "event_type": inc.get("status", ""),
        })
    for ne in recent_network_events:
        activity.append({
            "type": "network_event",
            "timestamp": ne.get("started_at", ""),
            "description": f"{ne.get('site_code')}: {ne.get('title')}",
            "related_id": ne.get("site_code", ""),
            "event_type": ne.get("event_type", ""),
        })

    activity.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    activity = activity[:20]

    # ── Network Events Summary ───────────────────────────
    active_network_events = nr.count_active_events()

    return {
        "metrics": {
            "open_tickets": open_tickets,
            "high_priority_tickets": high_priority_tickets,
            "active_incidents": active_incidents,
            "network_sites": network_sites,
            "affected_customers": affected_customers,
            "total_customers": total_customers,
        },
        "ticket_breakdown": {
            "by_status": ticket_status,
            "by_priority": ticket_priority,
            "by_category": ticket_category,
        },
        "network_health": {
            "total": network_health.get("total", 0),
            "operational": network_health.get("operational", 0),
            "degraded": network_health.get("degraded", 0),
            "maintenance": network_health.get("maintenance", 0),
            "offline": network_health.get("offline", 0),
            "status": network_health_status,
            "active_events": active_network_events,
        },
        "regional_impact": regional_impact,
        "active_incidents": active_incidents_list,
        "priority_cases": priority_cases,
        "recent_activity": activity,
    }
