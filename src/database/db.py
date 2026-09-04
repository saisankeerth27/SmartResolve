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
        seed_database(conn)
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
