import sqlite3
from typing import Optional


class PlanRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def list_plans(
        self,
        plan_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        where_clauses = []
        params: list = []
        if plan_type:
            where_clauses.append("plan_type = ?")
            params.append(plan_type)
        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        cursor = self.conn.execute(
            f"SELECT * FROM plans {where_sql} ORDER BY monthly_price ASC",
            params,
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, plan_id: int) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM plans WHERE id = ?", (plan_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_code(self, plan_code: str) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM plans WHERE plan_code = ?", (plan_code,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
