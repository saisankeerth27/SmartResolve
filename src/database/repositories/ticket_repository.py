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
                "(t.subject LIKE ? OR t.description LIKE ? OR t.ticket_number LIKE ?)"
            )
            like = f"%{search}%"
            params.extend([like, like, like])

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM tickets t {where_sql}", params
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

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM tickets")
        return cursor.fetchone()[0]
