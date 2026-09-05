import sqlite3
import logging
from pathlib import Path

from src.database.init_db import create_schema
from src.database.seed import seed_database

logger = logging.getLogger(__name__)

DATABASE_PATH: Path | None = None


def init_database(db_path: Path) -> None:
    global DATABASE_PATH
    DATABASE_PATH = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        create_schema(conn)
        _migrate_ticket_schema(conn)
        seed_database(conn)
        _repair_seed_relationships(conn)
        logger.info("Database initialized and seeded at %s", db_path)
    finally:
        conn.close()


def get_connection() -> sqlite3.Connection:
    if DATABASE_PATH is None:
        raise RuntimeError("Database not initialized. Call init_database first.")
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _repair_seed_relationships(conn: sqlite3.Connection) -> None:
    """Repair deterministic demo relationships without treating a broken join as no service."""
    customers_without_subscriptions = conn.execute(
        "SELECT id, customer_number FROM customers WHERE NOT EXISTS "
        "(SELECT 1 FROM subscriptions s WHERE s.customer_id = customers.id)"
    ).fetchall()
    plan_id = conn.execute("SELECT id FROM plans ORDER BY id LIMIT 1").fetchone()
    site_id = conn.execute("SELECT id FROM network_sites ORDER BY id LIMIT 1").fetchone()
    if plan_id and site_id:
        for customer_id, customer_number in customers_without_subscriptions:
            service_number = f"+91 700{customer_id:07d}"
            conn.execute(
                "INSERT OR IGNORE INTO subscriptions "
                "(customer_id, plan_id, service_number, service_type, activation_date, status, network_site_id, data_usage_gb, billing_cycle_day) "
                "VALUES (?, ?, ?, 'mobile', '2026-01-01T00:00:00', 'active', ?, 0, 1)",
                (customer_id, plan_id[0], service_number, site_id[0]),
            )

    conn.execute(
        "UPDATE tickets SET subscription_id = ("
        "SELECT s.id FROM subscriptions s WHERE s.customer_id = tickets.customer_id "
        "AND s.status = 'active' ORDER BY s.id LIMIT 1"
        ") WHERE subscription_id IS NULL OR subscription_id NOT IN "
        "(SELECT s2.id FROM subscriptions s2 WHERE s2.customer_id = tickets.customer_id)"
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS resolution_drafts (
            ticket_id INTEGER PRIMARY KEY REFERENCES tickets(id),
            draft TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL DEFAULT 'agent'
        )"""
    )

    # Keep ticket summaries short: conversation turns belong in the transcript.
    rows = conn.execute(
        "SELECT id FROM tickets WHERE description LIKE '% Customer:%' OR subject = 'Hello i need help'"
    ).fetchall()
    for (ticket_id,) in rows:
        messages = conn.execute(
            "SELECT content FROM conversation_messages cm JOIN conversations v ON v.id = cm.conversation_id "
            "WHERE v.ticket_id = ? AND cm.sender = 'customer' ORDER BY cm.id",
            (ticket_id,),
        ).fetchall()
        substantive = next(
            (r[0].strip() for r in messages if len(r[0].strip()) > 8 and r[0].strip().lower() not in {
                'hello', 'hi', 'hey', 'hello i need help', 'hello, i need help', 'ok', 'okay', 'thanks', 'thankyou', 'no'
            }),
            None,
        )
        if substantive:
            summary = substantive.splitlines()[0][:120]
            conn.execute(
                "UPDATE tickets SET subject = ?, description = ? WHERE id = ?",
                (summary, substantive[:500], ticket_id),
            )

    conn.execute(
        """UPDATE tickets SET archived = 1
                       WHERE (subject = 'New conversation' OR lower(trim(subject)) LIKE 'hello%')
             AND NOT EXISTS (
                 SELECT 1 FROM conversations v
                 JOIN conversation_messages cm ON cm.conversation_id = v.id
                                 WHERE v.ticket_id = tickets.id AND cm.sender = 'customer'
                                     AND lower(trim(cm.content)) NOT IN ('hello', 'hello.', 'hi', 'hey', 'hello i need help', 'hello, i need help', 'hello i need help.', 'hello, i need help.', 'ok', 'okay', 'thanks', 'thankyou', 'no')
             )"""
    )

    # Repeated browser/test conversations are archived after the five most recent
    # web cases per customer; real seeded call/email/store history remains intact.
    customer_rows = conn.execute(
        "SELECT customer_id FROM tickets WHERE archived = 0 AND channel = 'web' GROUP BY customer_id HAVING COUNT(*) > 10"
    ).fetchall()
    for (customer_id,) in customer_rows:
        old_web = conn.execute(
            "SELECT id FROM tickets WHERE customer_id = ? AND channel = 'web' AND archived = 0 ORDER BY created_at DESC, id DESC LIMIT -1 OFFSET 5",
            (customer_id,),
        ).fetchall()
        if old_web:
            conn.executemany("UPDATE tickets SET archived = 1 WHERE id = ?", old_web)

    # Remove stale duplicate bot escalations from earlier demo runs while retaining
    # the customer's follow-up message and the first escalation response.
    duplicate_escalations = conn.execute(
        """SELECT cm.id FROM conversation_messages cm
           JOIN conversations v ON v.id = cm.conversation_id
           JOIN tickets t ON t.id = v.ticket_id
           WHERE cm.sender = 'assistant'
             AND cm.content = 'I''m connecting you with a specialist who has your full context, so you won''t need to repeat the issue.'
             AND t.status IN ('escalated', 'escalation_requested', 'human_review')
             AND cm.id > (
                 SELECT MIN(first.id) FROM conversation_messages first
                 WHERE first.conversation_id = cm.conversation_id
                   AND first.sender = 'assistant'
                   AND first.content = cm.content
             )"""
    ).fetchall()
    if duplicate_escalations:
        conn.executemany(
            "DELETE FROM conversation_messages WHERE id = ?",
            duplicate_escalations,
        )
    conn.commit()


def _migrate_ticket_schema(conn: sqlite3.Connection) -> None:
    """Upgrade older demo databases with closed/archive and internal-note support."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(tickets)").fetchall()}
    if "archived" not in columns:
        conn.execute("ALTER TABLE tickets ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")
    ticket_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tickets'"
    ).fetchone()[0]
    if "'closed'" not in ticket_sql:
        conn.execute("PRAGMA writable_schema = ON")
        conn.execute(
            "UPDATE sqlite_master SET sql = REPLACE(sql, ?, ?) "
            "WHERE type = 'table' AND name = 'tickets'",
            ("'dismissed', 'new'))", "'dismissed', 'closed', 'new'))"),
        )
        conn.execute("PRAGMA writable_schema = OFF")
        schema_version = conn.execute("PRAGMA schema_version").fetchone()[0]
        conn.execute(f"PRAGMA schema_version = {schema_version + 1}")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS internal_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id),
            note TEXT NOT NULL,
            author TEXT NOT NULL DEFAULT 'agent',
            created_at TEXT NOT NULL
        )"""
    )
    conn.commit()
