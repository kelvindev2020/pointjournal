"""
Database layer for PointJournal.

Design note for a Java dev reading this for the first time:
- No ORM. At this table count and single-user scale, raw SQL via sqlite3
  is simpler to read/debug/ship than adding an ORM dependency. Each
  function here is the rough equivalent of a DAO method.
- sqlite3 is in the Python standard library -- no driver dependency needed.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS milestone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_year INTEGER NOT NULL,
    start_month INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    end_month INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS milestone_breakdown (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT,
    FOREIGN KEY (milestone_id) REFERENCES milestone(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS journal_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_id INTEGER NOT NULL,
    breakdown_id INTEGER,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (milestone_id) REFERENCES milestone(id) ON DELETE CASCADE,
    FOREIGN KEY (breakdown_id) REFERENCES milestone_breakdown(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def default_db_path() -> Path:
    """
    Default DB location: ~/.pointjournal/journal.db
    Override with the POINTJOURNAL_DB environment variable.
    """
    override = os.environ.get("POINTJOURNAL_DB")
    if override:
        return Path(override)
    return Path.home() / ".pointjournal" / "journal.db"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _has_column(conn, table, col) -> bool:
    return any(r["name"] == col for r in conn.execute(f"PRAGMA table_info({table})"))


def _migrate(conn) -> None:
    """
    Lightweight forward-only migration for people who created a DB before a
    given column existed. Safe to run every time -- it's a no-op once caught up.
    """
    additions = [
        ("milestone", "created_at", "TEXT"),
        ("milestone_breakdown", "created_at", "TEXT"),
        ("journal_log", "created_at", "TEXT"),
        ("journal_log", "breakdown_id", "INTEGER"),
    ]
    changed = False
    for table, col, coltype in additions:
        if not _has_column(conn, table, col):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
            changed = True
    if changed:
        conn.commit()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


# ---------- app_state (e.g. "current milestone") ----------

def get_state(conn, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_state(conn, key: str, value) -> None:
    conn.execute(
        "INSERT INTO app_state (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    conn.commit()


# ---------- milestone ----------

def add_milestone(conn, start_year, start_month, end_year, end_month, description) -> int:
    cur = conn.execute(
        "INSERT INTO milestone (start_year, start_month, end_year, end_month, description, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (start_year, start_month, end_year, end_month, description, _now()),
    )
    conn.commit()
    return cur.lastrowid


def update_milestone(conn, milestone_id, **fields) -> int:
    if not fields:
        return 0
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [milestone_id]
    cur = conn.execute(f"UPDATE milestone SET {cols} WHERE id = ?", values)
    conn.commit()
    return cur.rowcount


def delete_milestone(conn, milestone_id) -> int:
    cur = conn.execute("DELETE FROM milestone WHERE id = ?", (milestone_id,))
    conn.commit()
    return cur.rowcount


def get_milestone(conn, milestone_id):
    return conn.execute("SELECT * FROM milestone WHERE id = ?", (milestone_id,)).fetchone()


def list_milestones(conn):
    return conn.execute("SELECT * FROM milestone ORDER BY start_year, start_month").fetchall()


def list_milestones_filtered(conn, limit=100, id_min=None, id_max=None, start=None, end=None):
    """
    start/end are optional (year, month) tuples. Filters to milestones whose
    timeline overlaps the given bound(s). Ordered most-recently-started first.
    """
    clauses, params = [], []
    if id_min is not None:
        clauses.append("id >= ?")
        params.append(id_min)
    if id_max is not None:
        clauses.append("id <= ?")
        params.append(id_max)
    if start is not None:
        sy, sm = start
        clauses.append("(end_year * 12 + end_month) >= ?")
        params.append(sy * 12 + sm)
    if end is not None:
        ey, em = end
        clauses.append("(start_year * 12 + start_month) <= ?")
        params.append(ey * 12 + em)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        f"SELECT * FROM milestone {where} "
        "ORDER BY (start_year * 12 + start_month) DESC, id DESC LIMIT ?"
    )
    params.append(limit)
    return conn.execute(sql, params).fetchall()


# ---------- milestone_breakdown ----------

def add_breakdown(conn, milestone_id, description) -> int:
    cur = conn.execute(
        "INSERT INTO milestone_breakdown (milestone_id, description, completed, created_at) "
        "VALUES (?, ?, 0, ?)",
        (milestone_id, description, _now()),
    )
    conn.commit()
    return cur.lastrowid


def update_breakdown(conn, breakdown_id, **fields) -> int:
    if not fields:
        return 0
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [breakdown_id]
    cur = conn.execute(f"UPDATE milestone_breakdown SET {cols} WHERE id = ?", values)
    conn.commit()
    return cur.rowcount


def delete_breakdown(conn, breakdown_id) -> int:
    cur = conn.execute("DELETE FROM milestone_breakdown WHERE id = ?", (breakdown_id,))
    conn.commit()
    return cur.rowcount


def set_breakdown_completed(conn, breakdown_id, completed: bool) -> int:
    cur = conn.execute(
        "UPDATE milestone_breakdown SET completed = ? WHERE id = ?",
        (1 if completed else 0, breakdown_id),
    )
    conn.commit()
    return cur.rowcount


def list_breakdowns(conn, milestone_id):
    return conn.execute(
        "SELECT * FROM milestone_breakdown WHERE milestone_id = ? ORDER BY id",
        (milestone_id,),
    ).fetchall()


def list_breakdowns_filtered(conn, milestone_id=None, limit=500):
    if milestone_id is not None:
        sql = "SELECT * FROM milestone_breakdown WHERE milestone_id = ? ORDER BY id DESC LIMIT ?"
        params = (milestone_id, limit)
    else:
        sql = "SELECT * FROM milestone_breakdown ORDER BY id DESC LIMIT ?"
        params = (limit,)
    return conn.execute(sql, params).fetchall()


def get_breakdown(conn, breakdown_id):
    return conn.execute("SELECT * FROM milestone_breakdown WHERE id = ?", (breakdown_id,)).fetchone()


def find_breakdowns_by_desc(conn, milestone_id, needle: str):
    return conn.execute(
        "SELECT * FROM milestone_breakdown WHERE milestone_id = ? AND description LIKE ? ORDER BY id",
        (milestone_id, f"%{needle}%"),
    ).fetchall()


def breakdown_stats(conn, milestone_id):
    """Returns (completed_count, total_count) for a milestone's checklist."""
    row = conn.execute(
        "SELECT COUNT(*) AS total, SUM(completed) AS done "
        "FROM milestone_breakdown WHERE milestone_id = ?",
        (milestone_id,),
    ).fetchone()
    return (row["done"] or 0), (row["total"] or 0)


# ---------- journal_log ----------

def add_log(conn, milestone_id, date, description, breakdown_id=None) -> int:
    cur = conn.execute(
        "INSERT INTO journal_log (milestone_id, breakdown_id, date, description, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (milestone_id, breakdown_id, date, description, _now()),
    )
    conn.commit()
    return cur.lastrowid


def update_log(conn, log_id, **fields) -> int:
    if not fields:
        return 0
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [log_id]
    cur = conn.execute(f"UPDATE journal_log SET {cols} WHERE id = ?", values)
    conn.commit()
    return cur.rowcount


def delete_log(conn, log_id) -> int:
    cur = conn.execute("DELETE FROM journal_log WHERE id = ?", (log_id,))
    conn.commit()
    return cur.rowcount


def list_logs(conn, milestone_id):
    return conn.execute(
        "SELECT * FROM journal_log WHERE milestone_id = ? ORDER BY date, id",
        (milestone_id,),
    ).fetchall()


def list_logs_filtered(conn, milestone_id=None, date_from=None, date_to=None, limit=500):
    clauses, params = [], []
    if milestone_id is not None:
        clauses.append("milestone_id = ?")
        params.append(milestone_id)
    if date_from is not None:
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to is not None:
        clauses.append("date <= ?")
        params.append(date_to)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM journal_log {where} ORDER BY date DESC, id DESC LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def list_all_logs(conn):
    return conn.execute(
        "SELECT journal_log.*, milestone.description AS milestone_description "
        "FROM journal_log JOIN milestone ON journal_log.milestone_id = milestone.id "
        "ORDER BY date"
    ).fetchall()


def count_logs(conn, milestone_id) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM journal_log WHERE milestone_id = ?", (milestone_id,)
    ).fetchone()
    return row["c"] or 0


def get_log(conn, log_id):
    return conn.execute("SELECT * FROM journal_log WHERE id = ?", (log_id,)).fetchone()
