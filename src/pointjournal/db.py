"""
Database layer for PointJournal.

Design note for a Java dev reading this for the first time:
- There is no ORM (no Hibernate/JPA equivalent). At 3 tables and single-user
  scale, raw SQL via sqlite3 is simpler to read, debug, and ship than adding
  an ORM dependency. Each function here is the rough equivalent of a DAO method.
- sqlite3 is in the Python standard library -- no driver/dependency needed,
  similar to how JDBC ships with the JDK but you still need a driver jar for
  a specific DB. SQLite's driver is just... included.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS milestone (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_year INTEGER NOT NULL,
    start_month INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    end_month INTEGER NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS milestone_breakdown (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (milestone_id) REFERENCES milestone(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS journal_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (milestone_id) REFERENCES milestone(id) ON DELETE CASCADE
);
"""


def default_db_path() -> Path:
    """
    Default DB location: ~/.pointjournal/journal.db
    Override with the POINTJOURNAL_DB environment variable (useful for tests
    or for pointing at a synced folder like Dropbox/iCloud).
    """
    override = os.environ.get("POINTJOURNAL_DB")
    if override:
        return Path(override)
    return Path.home() / ".pointjournal" / "journal.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = db_path or default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


# ---------- milestone ----------

def add_milestone(conn, start_year, start_month, end_year, end_month, description) -> int:
    cur = conn.execute(
        "INSERT INTO milestone (start_year, start_month, end_year, end_month, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (start_year, start_month, end_year, end_month, description),
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


# ---------- milestone_breakdown ----------

def add_breakdown(conn, milestone_id, description) -> int:
    cur = conn.execute(
        "INSERT INTO milestone_breakdown (milestone_id, description, completed) VALUES (?, ?, 0)",
        (milestone_id, description),
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


def get_breakdown(conn, breakdown_id):
    return conn.execute("SELECT * FROM milestone_breakdown WHERE id = ?", (breakdown_id,)).fetchone()


# ---------- journal_log ----------

def add_log(conn, milestone_id, date, description) -> int:
    cur = conn.execute(
        "INSERT INTO journal_log (milestone_id, date, description) VALUES (?, ?, ?)",
        (milestone_id, date, description),
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
        "SELECT * FROM journal_log WHERE milestone_id = ? ORDER BY date",
        (milestone_id,),
    ).fetchall()


def list_all_logs(conn):
    return conn.execute(
        "SELECT journal_log.*, milestone.description AS milestone_description "
        "FROM journal_log JOIN milestone ON journal_log.milestone_id = milestone.id "
        "ORDER BY date"
    ).fetchall()


def get_log(conn, log_id):
    return conn.execute("SELECT * FROM journal_log WHERE id = ?", (log_id,)).fetchone()
