import sqlite3
from typing import Optional


class NetworkRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get_site_by_id(self, site_id: int) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM network_sites WHERE id = ?", (site_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_sites(
        self,
        region: Optional[str] = None,
        technology: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where_clauses = []
        params: list = []
        if region:
            where_clauses.append("region = ?")
            params.append(region)
        if technology:
            where_clauses.append("technology = ?")
            params.append(technology)
        if status:
            where_clauses.append("status = ?")
            params.append(status)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM network_sites {where_sql}", params
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f"SELECT * FROM network_sites {where_sql} ORDER BY id LIMIT ? OFFSET ?"
        cursor = self.conn.execute(query, params + [page_size, offset])
        return [dict(row) for row in cursor.fetchall()], total

    def get_site_events(
        self,
        site_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        where_clauses = ["ne.site_id = ?"]
        params: list = [site_id]
        if status:
            where_clauses.append("ne.status = ?")
            params.append(status)
        where_sql = "WHERE " + " AND ".join(where_clauses)

        count_cursor = self.conn.execute(
            f"SELECT COUNT(*) FROM network_events ne {where_sql}", params
        )
        total = count_cursor.fetchone()[0]

        offset = (page - 1) * page_size
        query = f"""
            SELECT ne.*, ns.site_code, ns.site_name
            FROM network_events ne
            JOIN network_sites ns ON ne.site_id = ns.id
            {where_sql}
            ORDER BY ne.started_at DESC
            LIMIT ? OFFSET ?
        """
        cursor = self.conn.execute(query, params + [page_size, offset])
        return [dict(row) for row in cursor.fetchall()], total

    def count_all_sites(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM network_sites")
        return cursor.fetchone()[0]

    def count_by_status(self) -> dict:
        cursor = self.conn.execute(
            "SELECT status, COUNT(*) as count FROM network_sites GROUP BY status"
        )
        return {row["status"]: row["count"] for row in cursor.fetchall()}

    def count_active_events(self) -> int:
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM network_events WHERE status = 'active'"
        )
        return cursor.fetchone()[0]

    def get_sites_by_region(self) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT region, COUNT(*) as site_count,
                      SUM(CASE WHEN status = 'operational' THEN 1 ELSE 0 END) as operational,
                      SUM(CASE WHEN status = 'degraded' THEN 1 ELSE 0 END) as degraded,
                      SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maintenance_count,
                      SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline_count
               FROM network_sites
               GROUP BY region
               ORDER BY site_count DESC"""
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_network_health(self) -> dict:
        cursor = self.conn.execute(
            """SELECT
                 COUNT(*) as total,
                 SUM(CASE WHEN status = 'operational' THEN 1 ELSE 0 END) as operational,
                 SUM(CASE WHEN status = 'degraded' THEN 1 ELSE 0 END) as degraded,
                 SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maintenance,
                 SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline
               FROM network_sites"""
        )
        row = cursor.fetchone()
        return dict(row) if row else {"total": 0, "operational": 0, "degraded": 0, "maintenance": 0, "offline": 0}

    def get_active_events_by_site(self, limit: int = 10) -> list[dict]:
        cursor = self.conn.execute(
            """SELECT ne.id, ne.site_id, ne.event_type, ne.severity, ne.title,
                      ne.description, ne.started_at, ne.status,
                      ns.site_code, ns.site_name, ns.region
               FROM network_events ne
               JOIN network_sites ns ON ne.site_id = ns.id
               WHERE ne.status = 'active'
               ORDER BY
                 CASE ne.severity
                   WHEN 'critical' THEN 1
                   WHEN 'high' THEN 2
                   WHEN 'medium' THEN 3
                   WHEN 'low' THEN 4
                 END,
                 ne.started_at DESC
               LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
