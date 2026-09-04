import sqlite3
from typing import Optional


class CustomerRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get_by_id(self, customer_id: int) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_number(self, customer_number: str) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM customers WHERE customer_number = ?",
            (customer_number,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_customers(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        segment: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where_clauses = []
        params: list = []
        if search:
            where_clauses.append(
                "(name LIKE ? OR customer_number LIKE ? OR email LIKE ? OR phone LIKE ?)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like])
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if segment:
            where_clauses.append("segment = ?")
            params.append(segment)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM customers {where_sql}", params
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f"SELECT * FROM customers {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?"
        cursor = self.conn.execute(query, params + [page_size, offset])
        rows = [dict(row) for row in cursor.fetchall()]
        return rows, total

    def get_subscriptions(self, customer_id: int) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT s.*, p.plan_name, p.plan_code, p.monthly_price, p.data_limit_gb,
                      ns.site_name, ns.site_code, ns.technology, ns.region, ns.city
               FROM subscriptions s
               JOIN plans p ON s.plan_id = p.id
               JOIN network_sites ns ON s.network_site_id = ns.id
               WHERE s.customer_id = ?
               ORDER BY s.id""",
            (customer_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_tickets(
        self,
        customer_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where_clauses = ["t.customer_id = ?"]
        params: list = [customer_id]
        if status:
            where_clauses.append("t.status = ?")
            params.append(status)
        where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM tickets t {where_sql}", params
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f"""
            SELECT t.*, s.service_number, s.service_type, p.plan_name
            FROM tickets t
            LEFT JOIN subscriptions s ON t.subscription_id = s.id
            LEFT JOIN plans p ON s.plan_id = p.id
            {where_sql}
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
        """
        cursor = self.conn.execute(query, params + [page_size, offset])
        return [dict(row) for row in cursor.fetchall()], total

    def get_interactions(
        self,
        customer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        count_cursor = self.conn.execute(
            "SELECT COUNT(*) FROM customer_interactions WHERE customer_id = ?",
            (customer_id,),
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor = self.conn.execute(
            """SELECT ci.*, t.ticket_number
               FROM customer_interactions ci
               LEFT JOIN tickets t ON ci.ticket_id = t.id
               WHERE ci.customer_id = ?
               ORDER BY ci.created_at DESC
               LIMIT ? OFFSET ?""",
            (customer_id, page_size, offset),
        )
        return [dict(row) for row in cursor.fetchall()], total

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM customers")
        return cursor.fetchone()[0]
