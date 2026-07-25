from pointjournal import db, report


def build_sample(conn):
    mid = db.add_milestone(conn, 2026, 1, 2026, 6, "Master Rust Programming")
    b1 = db.add_breakdown(conn, mid, "Complete Rust Book Chapters 1-10")
    db.add_breakdown(conn, mid, "Build a CLI App in Rust")
    db.set_breakdown_completed(conn, b1, True)
    db.add_log(conn, mid, "2026-07-25", "Read Chapter 4 on Ownership and Borrowing", breakdown_id=b1)
    return mid, b1


def test_render_milestone_report(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    mid, b1 = build_sample(conn)
    out = report.render_milestone_report(conn, mid)
    assert "Master Rust Programming" in out
    assert "2026/01" in out and "2026/06" in out
    assert "✅" in out and "⬜" in out
    assert "Complete Rust Book Chapters 1-10" in out
    assert "Build a CLI App in Rust" in out
    assert "Read Chapter 4 on Ownership and Borrowing" in out
    assert f"#{b1}" in out  # linked breakdown id shown against the log
    assert "1/2" in out  # progress fraction


def test_render_list_report(tmp_path):
    conn = db.get_connection(tmp_path / "t2.db")
    build_sample(conn)
    out = report.render_list_report(conn)
    assert "Master Rust Programming" in out
    assert "1/2" in out


def test_render_milestone_report_html(tmp_path):
    conn = db.get_connection(tmp_path / "t3.db")
    mid, _ = build_sample(conn)
    out = report.render_milestone_report_html(conn, mid)
    assert "<html" in out
    assert "Master Rust Programming" in out
    assert "Complete Rust Book Chapters 1-10" in out
    assert "bar-fill" in out


def test_render_list_report_html(tmp_path):
    conn = db.get_connection(tmp_path / "t4.db")
    build_sample(conn)
    out = report.render_list_report_html(conn)
    assert "<html" in out
    assert "Master Rust Programming" in out


def test_progress_bar_helpers():
    assert "0%" in report.progress_bar_md(0, 0)
    assert "50%" in report.progress_bar_md(1, 2)
    assert "50%" in report.progress_bar_plain(1, 2)
