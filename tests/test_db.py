import pytest

from pointjournal import db


@pytest.fixture()
def conn(tmp_path):
    return db.get_connection(tmp_path / "test.db")


def test_add_and_get_milestone(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    m = db.get_milestone(conn, mid)
    assert m["description"] == "Master Rust"
    assert m["start_year"] == 2026


def test_breakdown_check_uncheck(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    bid = db.add_breakdown(conn, mid, "Read the book")
    assert db.get_breakdown(conn, bid)["completed"] == 0
    db.set_breakdown_completed(conn, bid, True)
    assert db.get_breakdown(conn, bid)["completed"] == 1
    db.set_breakdown_completed(conn, bid, False)
    assert db.get_breakdown(conn, bid)["completed"] == 0


def test_journal_log_and_cascade_delete(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    db.add_log(conn, mid, "2026-07-25", "Read chapter 4")
    assert len(db.list_logs(conn, mid)) == 1
    db.delete_milestone(conn, mid)
    assert db.get_milestone(conn, mid) is None
    assert db.list_logs(conn, mid) == []


def test_update_milestone(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    db.update_milestone(conn, mid, description="Master Rust Programming")
    assert db.get_milestone(conn, mid)["description"] == "Master Rust Programming"
