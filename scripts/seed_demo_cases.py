"""Demo cases seed data for SmartResolve.

Creates specific demo cases that demonstrate:
- Case A: Routine grounded resolution (Mode A)
- Case B: Missing information (Mode B)
- Case C: Escalation (Mode C)
- Conflict case
- Gemini failure safe case
"""
import sqlite3
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "smartresolve.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _get_or_create_ticket(cursor, conn, ticket_num, cust_id, sub_id, category, priority, subject, description, now):
    """Get existing ticket or create new one, return ticket_id."""
    cursor.execute("SELECT id FROM tickets WHERE ticket_number = ?", (ticket_num,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute("""
        INSERT INTO tickets
        (ticket_number, customer_id, subscription_id, category, priority, subject, description, status, channel, assigned_team, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', 'web', 'Support', ?, ?)
    """, (ticket_num, cust_id, sub_id, category, priority, subject, description, now, now))
    conn.commit()
    return cursor.lastrowid


def _add_ticket_event(conn, ticket_id, description, now):
    conn.execute("""
        INSERT INTO ticket_events (ticket_id, event_type, actor_type, description, created_at)
        VALUES (?, 'created', 'customer', ?, ?)
    """, (ticket_id, description, now))


def _add_interaction(conn, cust_id, ticket_id, summary, sentiment, now):
    conn.execute("""
        INSERT INTO customer_interactions (customer_id, ticket_id, interaction_type, summary, sentiment, created_at)
        VALUES (?, ?, 'chat', ?, ?, ?)
    """, (cust_id, ticket_id, summary, sentiment, now))


def create_demo_cases():
    """Create 5 specific demo cases."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    cursor.execute("SELECT id, name, segment FROM customers LIMIT 10")
    customers = cursor.fetchall()

    cursor.execute("""
        SELECT s.id, s.customer_id, p.plan_name, p.plan_type, tp.name as provider_name
        FROM subscriptions s
        JOIN plans p ON s.plan_id = p.id
        JOIN telecom_providers tp ON p.provider_id = tp.id
        LIMIT 10
    """)
    subscriptions = cursor.fetchall()

    demo_cases = []

    # ── CASE A: Routine Billing Dispute (Mode A) ──────
    if customers and subscriptions:
        cust = customers[0]
        sub = subscriptions[0]
        ticket_num = "TKT-DEMO-001"
        ticket_id = _get_or_create_ticket(cursor, conn, ticket_num, cust["id"], sub["id"],
            "billing", "medium", "Duplicate charge on last bill",
            "I was charged 599 twice on my last billing cycle. My plan is 299 per month. Please refund the extra charge.", now)
        demo_cases.append(("A", ticket_id, ticket_num, "Mode A - Routine billing dispute with clear evidence"))
        _add_ticket_event(conn, ticket_id, "Customer reported duplicate charge of 599", now)
        _add_interaction(conn, cust["id"], ticket_id, "Customer reports being charged 599 twice instead of 299. Requests refund.", "frustrated", now)

    # ── CASE B: Slow Internet - Missing Info (Mode B) ─
    if customers and subscriptions:
        cust = customers[1]
        sub = subscriptions[1]
        ticket_num = "TKT-DEMO-002"
        ticket_id = _get_or_create_ticket(cursor, conn, ticket_num, cust["id"], sub["id"],
            "network", "medium", "Internet is slow",
            "My internet has been very slow for the past few days. Please help.", now)
        demo_cases.append(("B", ticket_id, ticket_num, "Mode B - Missing location/timing/scope information"))
        _add_ticket_event(conn, ticket_id, "Customer reported slow internet", now)
        _add_interaction(conn, cust["id"], ticket_id, "Customer says internet is very slow for past few days", "frustrated", now)

    # ── CASE C: Repeat Complaint + Enterprise (Mode C) ─
    if customers and subscriptions:
        cursor.execute("SELECT id, name, segment FROM customers WHERE segment = 'enterprise' LIMIT 1")
        ent_cust = cursor.fetchone()
        if not ent_cust:
            ent_cust = customers[min(2, len(customers) - 1)]

        cursor.execute("SELECT id FROM subscriptions WHERE customer_id = ? LIMIT 1", (ent_cust["id"],))
        ent_sub = cursor.fetchone()
        if not ent_sub and subscriptions:
            ent_sub = subscriptions[min(2, len(subscriptions) - 1)]

        if ent_sub:
            ticket_num = "TKT-DEMO-003"
            ticket_id = _get_or_create_ticket(cursor, conn, ticket_num, ent_cust["id"], ent_sub["id"],
                "connectivity", "critical", "Repeated connection drops - Enterprise",
                "Our enterprise link keeps dropping every evening. This is the 4th time we are reporting this. Previous tickets were resolved but issue recurs. We need immediate attention.", now)
            demo_cases.append(("C", ticket_id, ticket_num, "Mode C - Enterprise repeat complaint, escalation required"))
            _add_ticket_event(conn, ticket_id, "Enterprise customer reporting 4th connection drop issue", now)
            _add_interaction(conn, ent_cust["id"], ticket_id, "Enterprise customer angry - 4th time reporting same issue. Previous resolutions failed.", "angry", now)

            # Create previous tickets for repeat complaint
            for i in range(3):
                prev_num = f"TKT-PREV-{100+i}"
                prev_time = (datetime.now(timezone.utc) - timedelta(days=30 * (3 - i))).strftime("%Y-%m-%dT%H:%M:%S")
                cursor.execute("SELECT id FROM tickets WHERE ticket_number = ?", (prev_num,))
                if not cursor.fetchone():
                    conn.execute("""
                        INSERT INTO tickets
                        (ticket_number, customer_id, subscription_id, category, priority, subject, description, status, channel, assigned_team, created_at, updated_at, resolved_at)
                        VALUES (?, ?, ?, 'connectivity', 'high', ?, 'Previous connection drop report', 'resolved', 'web', 'Network Support', ?, ?, ?)
                    """, (prev_num, ent_cust["id"], ent_sub["id"], f"Connection drop #{i+1}", prev_time, prev_time, prev_time))

    # ── CASE D: Conflict - Site Operational but Events ─
    if customers and subscriptions:
        cust = customers[min(3, len(customers) - 1)]
        sub = subscriptions[min(3, len(subscriptions) - 1)]
        ticket_num = "TKT-DEMO-004"
        ticket_id = _get_or_create_ticket(cursor, conn, ticket_num, cust["id"], sub["id"],
            "network", "high", "No internet but site shows operational",
            "My site shows operational but I have no internet. Check your systems.", now)
        demo_cases.append(("D", ticket_id, ticket_num, "Conflict - Site operational but high-severity active events"))
        _add_ticket_event(conn, ticket_id, "Customer reports no internet despite site showing operational", now)

    # ── CASE E: Missing Subscription Data (Edge Case) ──────
    if customers:
        cust = customers[min(4, len(customers) - 1)]
        ticket_num = "TKT-DEMO-005"
        ticket_id = _get_or_create_ticket(cursor, conn, ticket_num, cust["id"], None,
            "account", "medium", "Account access issue",
            "I cannot access my account. Please help me regain access.", now)
        demo_cases.append(("E", ticket_id, ticket_num, "Edge case - Missing subscription data"))
        _add_ticket_event(conn, ticket_id, "Customer reporting account access issue", now)

    conn.commit()
    conn.close()

    return demo_cases


if __name__ == "__main__":
    print("Creating demo cases...")
    cases = create_demo_cases()
    print(f"Created {len(cases)} demo cases:")
    for mode, ticket_id, ticket_num, description in cases:
        print(f"  Case {mode}: {ticket_num} (ID: {ticket_id}) - {description}")
    print("\nDemo cases are ready for testing in the Agent Console.")
