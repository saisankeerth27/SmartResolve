import sqlite3
from typing import Optional


class IncidentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get_by_id(self, incident_id: int) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_number(self, incident_number: str) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM incidents WHERE incident_number = ?",
            (incident_number,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_incidents(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        region: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where_clauses = []
        params: list = []
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if severity:
            where_clauses.append("severity = ?")
            params.append(severity)
        if region:
            where_clauses.append("region = ?")
            params.append(region)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM incidents {where_sql}", params
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f"SELECT * FROM incidents {where_sql} ORDER BY started_at DESC LIMIT ? OFFSET ?"
        cursor = self.conn.execute(query, params + [page_size, offset])
        return [dict(row) for row in cursor.fetchall()], total

    def get_active_incidents(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where_sql = "WHERE status IN ('investigating', 'identified', 'monitoring')"

        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM incidents {where_sql}"
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f"SELECT * FROM incidents {where_sql} ORDER BY severity DESC, started_at DESC LIMIT ? OFFSET ?"
        cursor = self.conn.execute(query, (page_size, offset))
        return [dict(row) for row in cursor.fetchall()], total

    def count_all(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM incidents")
        return cursor.fetchone()[0]

    def count_active(self) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE status IN ('investigating', 'identified', 'monitoring')"
        )
        return cursor.fetchone()[0]

    def count_by_status(self) -> dict:
        cursor = self.conn.execute(
            "SELECT status, COUNT(*) as count FROM incidents GROUP BY status"
        )
        return {row["status"]: row["count"] for row in cursor.fetchall()}

    def get_active_incidents_list(self, limit: int = 10) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT * FROM incidents
               WHERE status IN ('investigating', 'identified', 'monitoring')
               ORDER BY
                 CASE severity
                   WHEN 'critical' THEN 1
                   WHEN 'high' THEN 2
                   WHEN 'medium' THEN 3
                   WHEN 'low' THEN 4
                 END,
                 started_at DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_active_by_region(self) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT region, COUNT(*) as incident_count,
                      SUM(affected_customers_estimate) as total_affected
               FROM incidents
               WHERE status IN ('investigating', 'identified', 'monitoring')
               GROUP BY region
               ORDER BY incident_count DESC"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_total_affected_customers(self) -> int:
        cursor = self.conn.execute(
            """SELECT COALESCE(SUM(affected_customers_estimate), 0)
               FROM incidents
               WHERE status IN ('investigating', 'identified', 'monitoring')"""
        )
        return cursor.fetchone()[0]

    def get_recent_incidents(self, limit: int = 10) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT * FROM incidents
               ORDER BY started_at DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
