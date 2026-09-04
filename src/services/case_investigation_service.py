import sqlite3
import logging

from src.database.repositories.customer_repository import CustomerRepository
from src.database.repositories.ticket_repository import TicketRepository
from src.database.repositories.network_repository import NetworkRepository
from src.database.repositories.incident_repository import IncidentRepository

logger = logging.getLogger(__name__)


def get_case_investigation(conn: sqlite3.Connection, ticket_id: int) -> dict | None:
    tr = TicketRepository(conn)
    cr = CustomerRepository(conn)
    nr = NetworkRepository(conn)
    ir = IncidentRepository(conn)

    ticket = tr.get_by_id(ticket_id)
    if not ticket:
        return None

    customer_id = ticket["customer_id"]
    customer = cr.get_by_id(customer_id)
    if not customer:
        return _build_degraded_context(ticket)

    subscription = tr.get_subscription_for_ticket(ticket_id)
    customer_subs = cr.get_subscriptions(customer_id)
    ticket_history = tr.get_history(ticket_id)
    previous_tickets = tr.get_previous_tickets_by_customer(
        customer_id, ticket_id, limit=20
    )
    interactions_data, _ = cr.get_interactions(customer_id, page=1, page_size=20)

    network_site = None
    network_events = []
    active_incidents = []
    if subscription:
        site_id = subscription.get("network_site_id")
        if site_id:
            network_site = nr.get_site_by_id(site_id)
            network_events = nr.get_events_for_site(site_id, limit=10)
        region = subscription.get("region")
        if region:
            active_incidents = ir.get_active_by_region_list(region)

    sub_count = cr.count_active_subscriptions(customer_id)
    ticket_count = cr.count_tickets(customer_id)
    interaction_count = cr.count_interactions(customer_id)

    same_category_count = tr.count_previous_by_category(
        customer_id, ticket["category"], ticket_id
    )

    known_facts, missing_info = _compute_facts_and_gaps(
        ticket, customer, subscription, network_site,
        network_events, active_incidents, previous_tickets,
        same_category_count,
    )

    readiness = _compute_readiness(ticket, customer, subscription, network_site)

    return {
        "ticket": ticket,
        "customer": customer,
        "subscription": subscription,
        "previous_tickets": previous_tickets,
        "network": {
            "site": network_site,
            "events": network_events,
        },
        "incidents": active_incidents,
        "ticket_history": ticket_history,
        "interactions": interactions_data,
        "customer_stats": {
            "active_subscriptions": sub_count,
            "total_tickets": ticket_count,
            "total_interactions": interaction_count,
        },
        "investigation": {
            "readiness": readiness,
            "known_facts": known_facts,
            "missing_information": missing_info,
            "same_category_previous_tickets": same_category_count,
        },
    }


def _build_degraded_context(ticket: dict) -> dict:
    return {
        "ticket": ticket,
        "customer": None,
        "subscription": None,
        "previous_tickets": [],
        "network": {"site": None, "events": []},
        "incidents": [],
        "ticket_history": [],
        "interactions": [],
        "customer_stats": {
            "active_subscriptions": 0,
            "total_tickets": 0,
            "total_interactions": 0,
        },
        "investigation": {
            "readiness": "INSUFFICIENT DATA",
            "known_facts": ["Ticket record found"],
            "missing_information": [
                "Customer record not found - data integrity issue",
            ],
            "same_category_previous_tickets": 0,
        },
    }


def _compute_readiness(
    ticket: dict,
    customer: dict,
    subscription: dict | None,
    network_site: dict | None,
) -> str:
    if not customer:
        return "INSUFFICIENT DATA"

    has_subscription = subscription is not None
    has_network = network_site is not None

    if has_subscription and has_network:
        return "READY"
    if has_subscription or has_network:
        return "PARTIAL"
    return "PARTIAL"


def _compute_facts_and_gaps(
    ticket: dict,
    customer: dict,
    subscription: dict | None,
    network_site: dict | None,
    network_events: list,
    active_incidents: list,
    previous_tickets: list,
    same_category_count: int,
) -> tuple[list[str], list[str]]:
    known_facts: list[str] = []
    missing_info: list[str] = []

    known_facts.append(
        f"Customer identified: {customer.get('name', 'Unknown')} "
        f"({customer.get('customer_number', 'N/A')})"
    )
    known_facts.append(
        f"Customer segment: {customer.get('segment', 'Unknown')}"
    )
    known_facts.append(
        f"Account status: {customer.get('status', 'Unknown')}"
    )

    if subscription:
        known_facts.append(
            f"Active subscription found: {subscription.get('service_number', 'N/A')} "
            f"({subscription.get('service_type', 'Unknown')})"
        )
        known_facts.append(
            f"Plan: {subscription.get('plan_name', 'Unknown')} "
            f"({subscription.get('plan_type', 'Unknown')})"
        )
        usage = subscription.get("data_usage_gb", 0)
        limit = subscription.get("data_limit_gb", 0)
        if limit > 0:
            pct = round((usage / limit) * 100, 1)
            known_facts.append(
                f"Data usage: {usage} GB / {limit} GB ({pct}%)"
            )
    else:
        missing_info.append("No subscription record linked to this ticket")

    if network_site:
        known_facts.append(
            f"Serving network site: {network_site.get('site_code', 'N/A')} "
            f"({network_site.get('site_name', 'Unknown')})"
        )
        known_facts.append(
            f"Site technology: {network_site.get('technology', 'Unknown')}"
        )
        known_facts.append(
            f"Site region: {network_site.get('region', 'Unknown')}, "
            f"{network_site.get('city', 'Unknown')}"
        )
        site_status = network_site.get("status", "unknown")
        known_facts.append(f"Site status: {site_status}")
        capacity = network_site.get("capacity_percent", 0)
        known_facts.append(f"Site capacity: {capacity}%")

        if site_status == "degraded":
            known_facts.append(
                "Customer service is associated with a degraded network site"
            )
        if site_status == "offline":
            known_facts.append(
                "Customer service is associated with an offline network site"
            )
        if capacity > 85:
            known_facts.append(
                f"Network site operating at high capacity ({capacity}%)"
            )
    else:
        missing_info.append("No network site information available")

    active_events = [e for e in network_events if e.get("status") == "active"]
    if active_events:
        known_facts.append(
            f"Active network events at serving site: {len(active_events)}"
        )
        for ev in active_events[:3]:
            known_facts.append(
                f"  - {ev.get('title', 'Unknown')} "
                f"(severity: {ev.get('severity', 'Unknown')})"
            )
    else:
        missing_info.append("No active network events at serving site")

    if active_incidents:
        inc = active_incidents[0]
        known_facts.append(
            f"Active incident in region: {inc.get('incident_number', 'N/A')} "
            f"- {inc.get('title', 'Unknown')}"
        )
        known_facts.append(
            f"  Severity: {inc.get('severity', 'Unknown')}, "
            f"Status: {inc.get('status', 'Unknown')}"
        )
        known_facts.append(
            f"  Estimated affected customers: "
            f"{inc.get('affected_customers_estimate', 0):,}"
        )
    else:
        known_facts.append(
            "No active incident in the customer's region"
        )

    if same_category_count > 0:
        known_facts.append(
            f"Previous related tickets found: {same_category_count} "
            f"other {ticket.get('category', '')} ticket(s) for this customer"
        )

    known_facts.append(
        f"Ticket created via: {ticket.get('channel', 'Unknown')}"
    )
    if ticket.get("assigned_team"):
        known_facts.append(
            f"Assigned to: {ticket['assigned_team']}"
        )

    missing_info.append("Device model not recorded in operational data")
    missing_info.append("Exact customer location not available")
    missing_info.append("Signal strength measurements not recorded")
    missing_info.append("Customer-reported symptoms not systematically captured")

    return known_facts, missing_info
