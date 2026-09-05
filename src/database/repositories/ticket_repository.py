import sqlite3
from typing import Optional


class TicketRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get_by_id(self, ticket_id: int) -> Optional[dict]:
        cursor = self.conn.execute(
            """SELECT t.*, c.name as customer_name, c.customer_number,
                      c.phone as customer_phone, c.email as customer_email,
                      s.service_number, s.service_type, p.plan_name
               FROM tickets t
               JOIN customers c ON t.customer_id = c.id
               LEFT JOIN subscriptions s ON t.subscription_id = s.id
               LEFT JOIN plans p ON s.plan_id = p.id
               WHERE t.id = ?""",
            (ticket_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_number(self, ticket_number: str) -> Optional[dict]:
        cursor = self.conn.execute(
            """SELECT t.*, c.name as customer_name, c.customer_number
               FROM tickets t
               JOIN customers c ON t.customer_id = c.id
               WHERE t.ticket_number = ?""",
            (ticket_number,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_tickets(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        customer_id: Optional[int] = None,
        search: Optional[str] = None,
        archived: Optional[bool] = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where_clauses = []
        params: list = []
        if status:
            where_clauses.append("t.status = ?")
            params.append(status)
        if priority:
            where_clauses.append("t.priority = ?")
            params.append(priority)
        if category:
            where_clauses.append("t.category = ?")
            params.append(category)
        if customer_id:
            where_clauses.append("t.customer_id = ?")
            params.append(customer_id)
        if search:
            where_clauses.append(
                "(t.subject LIKE ? OR t.description LIKE ? OR t.ticket_number LIKE ? "
                "OR c.name LIKE ? OR c.customer_number LIKE ?)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like, like])
        if archived is not None:
            where_clauses.append("t.archived = ?")
            params.append(1 if archived else 0)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.conn.execute(
            f"""SELECT COUNT(*) FROM tickets t
                JOIN customers c ON t.customer_id = c.id {where_sql}""",
            params,
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f"""
            SELECT t.*, c.name as customer_name, c.customer_number,
                   s.service_number, s.service_type, p.plan_name
            FROM tickets t
            JOIN customers c ON t.customer_id = c.id
            LEFT JOIN subscriptions s ON t.subscription_id = s.id
            LEFT JOIN plans p ON s.plan_id = p.id
            {where_sql}
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
        """
        cursor = self.conn.execute(query, params + [page_size, offset])
        return [dict(row) for row in cursor.fetchall()], total

    def get_history(self, ticket_id: int) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT * FROM ticket_events
               WHERE ticket_id = ?
               ORDER BY created_at ASC""",
            (ticket_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def count_by_status(self) -> dict:
        cursor = self.conn.execute(
            "SELECT status, COUNT(*) as count FROM tickets GROUP BY status"
        )
        return {row["status"]: row["count"] for row in cursor.fetchall()}

    def count_by_priority(self) -> dict:
        cursor = self.conn.execute(
            "SELECT priority, COUNT(*) as count FROM tickets GROUP BY priority"
        )
        return {row["priority"]: row["count"] for row in cursor.fetchall()}

    def count_by_category(self) -> dict:
        cursor = self.conn.execute(
            "SELECT category, COUNT(*) as count FROM tickets GROUP BY category"
        )
        return {row["category"]: row["count"] for row in cursor.fetchall()}

    def count_active_tickets(self) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE status NOT IN ('resolved', 'dismissed')"
        )
        return cursor.fetchone()[0]

    def count_high_priority_active(self) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE priority IN ('high', 'critical') AND status NOT IN ('resolved', 'dismissed')"
        )
        return cursor.fetchone()[0]

    def get_open_tickets_by_region(self) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT ns.region, COUNT(*) as ticket_count
               FROM tickets t
               JOIN subscriptions s ON t.subscription_id = s.id
               JOIN network_sites ns ON s.network_site_id = ns.id
               WHERE t.status NOT IN ('resolved', 'dismissed')
               GROUP BY ns.region
               ORDER BY ticket_count DESC"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_escalated_tickets(self, limit: int = 10) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT t.id, t.ticket_number, t.subject, t.priority, t.status,
                      t.category, t.created_at, t.assigned_team,
                      c.name as customer_name, c.customer_number,
                      ns.region
               FROM tickets t
               JOIN customers c ON t.customer_id = c.id
               LEFT JOIN subscriptions s ON t.subscription_id = s.id
               LEFT JOIN network_sites ns ON s.network_site_id = ns.id
               WHERE t.status = 'escalated'
               ORDER BY
                 CASE t.priority
                   WHEN 'critical' THEN 1
                   WHEN 'high' THEN 2
                   WHEN 'medium' THEN 3
                   WHEN 'low' THEN 4
                 END,
                 t.created_at DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_events(self, limit: int = 15) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT te.id, te.ticket_id, te.event_type, te.actor_type,
                      te.description, te.created_at,
                      t.ticket_number, t.subject
               FROM ticket_events te
               JOIN tickets t ON te.ticket_id = t.id
               ORDER BY te.created_at DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM tickets")
        return cursor.fetchone()[0]

    def get_previous_tickets_by_customer(
        self, customer_id: int, exclude_ticket_id: int, limit: int = 20
    ) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT t.id, t.ticket_number, t.subject, t.category, t.priority,
                      t.status, t.created_at, t.resolved_at, t.assigned_team
               FROM tickets t
               WHERE t.customer_id = ? AND t.id != ?
               ORDER BY t.created_at DESC
               LIMIT ?""",
            (customer_id, exclude_ticket_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def count_previous_by_category(
        self, customer_id: int, category: str, exclude_ticket_id: int
    ) -> int:
        cursor = self.conn.execute(
            """SELECT COUNT(*) FROM tickets
               WHERE customer_id = ? AND category = ? AND id != ?
                                 AND archived = 0
                                 AND status NOT IN ('resolved', 'dismissed', 'closed')""",
            (customer_id, category, exclude_ticket_id),
        )
        return cursor.fetchone()[0]

    def get_subscription_for_ticket(self, ticket_id: int) -> Optional[dict]:
        cursor = self.conn.execute(
            """SELECT s.*, p.plan_name, p.plan_code, p.plan_type, p.monthly_price,
                      p.data_limit_gb, p.voice_minutes, p.sms_limit, p.speed_mbps,
                      ns.site_code, ns.site_name, ns.technology, ns.region, ns.city,
                      ns.capacity_percent, ns.status as site_status,
                      ns.last_maintenance_at
               FROM tickets t
               JOIN subscriptions s ON t.subscription_id = s.id
               JOIN plans p ON s.plan_id = p.id
               JOIN network_sites ns ON s.network_site_id = ns.id
               WHERE t.id = ?""",
            (ticket_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
