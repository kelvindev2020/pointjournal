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
    assert m["created_at"] is not None


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


def test_current_milestone_state(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    assert db.get_state(conn, "current_milestone_id") is None
    db.set_state(conn, "current_milestone_id", mid)
    assert db.get_state(conn, "current_milestone_id") == str(mid)
    # overwrite works
    mid2 = db.add_milestone(conn, 2026, 7, 2026, 12, "Master Go")
    db.set_state(conn, "current_milestone_id", mid2)
    assert db.get_state(conn, "current_milestone_id") == str(mid2)


def test_log_optional_breakdown_link(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    bid = db.add_breakdown(conn, mid, "Read the book")
    log_id = db.add_log(conn, mid, "2026-07-25", "Read chapter 4", breakdown_id=bid)
    log = db.get_log(conn, log_id)
    assert log["breakdown_id"] == bid

    log_id2 = db.add_log(conn, mid, "2026-07-26", "Unrelated note")
    assert db.get_log(conn, log_id2)["breakdown_id"] is None


def test_breakdown_stats(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    b1 = db.add_breakdown(conn, mid, "Item 1")
    db.add_breakdown(conn, mid, "Item 2")
    done, total = db.breakdown_stats(conn, mid)
    assert (done, total) == (0, 2)
    db.set_breakdown_completed(conn, b1, True)
    done, total = db.breakdown_stats(conn, mid)
    assert (done, total) == (1, 2)


def test_find_breakdowns_by_desc(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    db.add_breakdown(conn, mid, "Build a CLI App in Rust")
    db.add_breakdown(conn, mid, "Complete Rust Book Chapters 1-10")
    matches = db.find_breakdowns_by_desc(conn, mid, "CLI App")
    assert len(matches) == 1
    assert matches[0]["description"] == "Build a CLI App in Rust"


def test_list_milestones_filtered_limit_and_id_range(conn):
    for i in range(5):
        db.add_milestone(conn, 2026, 1, 2026, 6, f"Milestone {i}")
    rows = db.list_milestones_filtered(conn, limit=2)
    assert len(rows) == 2
    rows = db.list_milestones_filtered(conn, id_min=3, id_max=4)
    ids = sorted(r["id"] for r in rows)
    assert ids == [3, 4]


def test_list_logs_filtered_by_date_range(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust")
    db.add_log(conn, mid, "2026-01-01", "Early note")
    db.add_log(conn, mid, "2026-07-25", "Later note")
    rows = db.list_logs_filtered(conn, milestone_id=mid, date_from="2026-06-01")
    assert len(rows) == 1
    assert rows[0]["description"] == "Later note"
