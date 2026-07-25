from pointjournal import db, report


def build_sample(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust Programming")
    db.add_breakdown(conn, mid, "Complete Rust Book Chapters 1-10")
    b2 = db.add_breakdown(conn, mid, "Build a CLI App in Rust")
    db.set_breakdown_completed(conn, mid - mid + 1, True)  # id 1 = first breakdown
    db.add_log(conn, mid, "2026-07-25", "Read Chapter 4 on Ownership and Borrowing")
    return mid, b2


def test_render_milestone_report(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    mid, _ = build_sample(conn)
    out = report.render_milestone_report(conn, mid)
    assert "# Milestone Report: Master Rust Programming" in out
    assert "**Timeline:** 2026/01 — 2026/06" in out
    assert "- [x] Complete Rust Book Chapters 1-10" in out
    assert "- [ ] Build a CLI App in Rust" in out
    assert "- **2026-07-25**: Read Chapter 4 on Ownership and Borrowing" in out


def test_render_list_report(tmp_path):
    conn = db.get_connection(tmp_path / "t2.db")
    build_sample(conn)
    out = report.render_list_report(conn)
    assert "Master Rust Programming" in out
    assert "Read Chapter 4 on Ownership and Borrowing" in out
