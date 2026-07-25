"""Markdown and HTML report builders for PointJournal."""

from datetime import datetime
from html import escape

from pointjournal import db


def month_str(year: int, month: int) -> str:
    return f"{year:04d}/{month:02d}"


def _status_label(m) -> str:
    today = datetime.now()
    now_ord = today.year * 12 + today.month
    start_ord = m["start_year"] * 12 + m["start_month"]
    end_ord = m["end_year"] * 12 + m["end_month"]
    if now_ord < start_ord:
        return "Upcoming"
    if now_ord > end_ord:
        return "Past Due"
    return "In Progress"


def progress_bar_md(done: int, total: int, width: int = 20) -> str:
    if total == 0:
        return f"`{'░' * width}` **0%** (0/0)"
    pct = done / total
    filled = round(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"`{bar}` **{pct * 100:.0f}%** ({done}/{total})"


def progress_bar_plain(done: int, total: int, width: int = 10) -> str:
    """Plain-text version (no Markdown backticks) for terminal tables."""
    if total == 0:
        return f"{'░' * width} 0% (0/0)"
    pct = done / total
    filled = round(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {pct * 100:.0f}% ({done}/{total})"


# ---------------- Markdown ----------------

def render_milestone_report(conn, milestone_id: int) -> str:
    m = db.get_milestone(conn, milestone_id)
    if m is None:
        raise ValueError(f"No milestone with id {milestone_id}")

    breakdowns = db.list_breakdowns(conn, milestone_id)
    logs = db.list_logs(conn, milestone_id)
    done, total = db.breakdown_stats(conn, milestone_id)
    status = _status_label(m)

    lines = []
    lines.append(f"# 🎯 {m['description']}")
    lines.append(
        f"**Timeline:** {month_str(m['start_year'], m['start_month'])} → "
        f"{month_str(m['end_year'], m['end_month'])}  ·  **Status:** {status}  ·  "
        f"**Milestone ID:** {m['id']}"
    )
    lines.append("")
    lines.append(f"**Progress:** {progress_bar_md(done, total)}")
    lines.append(f"**Journal Activity:** {len(logs)} log{'s' if len(logs) != 1 else ''}")
    lines.append("")
    lines.append("## ✅ Breakdown Checklist")
    lines.append("")
    if breakdowns:
        lines.append("| ID | Status | Description |")
        lines.append("|---|---|---|")
        for b in breakdowns:
            box = "✅" if b["completed"] else "⬜"
            lines.append(f"| {b['id']} | {box} | {b['description']} |")
    else:
        lines.append("_No breakdown items yet._")
    lines.append("")
    lines.append(f"## 📝 Journal Logs ({len(logs)})")
    lines.append("")
    if logs:
        lines.append("| ID | Date | Linked Item | Description |")
        lines.append("|---|---|---|---|")
        for log in logs:
            linked = f"#{log['breakdown_id']}" if log["breakdown_id"] else "—"
            lines.append(f"| {log['id']} | {log['date']} | {linked} | {log['description']} |")
    else:
        lines.append("_No journal entries yet._")
    lines.append("")
    lines.append("***")
    return "\n".join(lines)


def render_list_report(conn) -> str:
    milestones = db.list_milestones(conn)

    lines = []
    lines.append("# 📚 PointJournal — All Milestones")
    lines.append("")
    lines.append("| ID | Milestone | Timeline | Progress | Logs |")
    lines.append("|---|---|---|---|---|")
    for m in milestones:
        done, total = db.breakdown_stats(conn, m["id"])
        log_count = db.count_logs(conn, m["id"])
        timeline = f"{month_str(m['start_year'], m['start_month'])} → {month_str(m['end_year'], m['end_month'])}"
        lines.append(
            f"| {m['id']} | {m['description']} | {timeline} | "
            f"{progress_bar_md(done, total, width=10)} | {log_count} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------- HTML ----------------

_HTML_STYLE = """
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; max-width: 820px;
         margin: 40px auto; padding: 0 20px; color: #1c1c1e; background: #fafafa; }
  h1 { font-size: 1.6rem; }
  .meta { color: #666; margin-bottom: 4px; }
  .bar-wrap { background: #e5e5ea; border-radius: 8px; height: 16px; width: 100%;
              max-width: 320px; overflow: hidden; display: inline-block; vertical-align: middle; }
  .bar-fill { background: linear-gradient(90deg,#34c759,#30d158); height: 100%; }
  .pct { font-weight: 600; margin-left: 8px; }
  table { border-collapse: collapse; width: 100%; margin: 14px 0 28px; background: #fff; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #e5e5ea; font-size: 0.92rem; }
  th { background: #f0f0f3; }
  tr:hover { background: #f5f5f7; }
  .section-title { margin-top: 32px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 6px; background: #eee; font-size: 0.8rem; }
</style>
"""


def _bar_html(done: int, total: int) -> str:
    pct = 0 if total == 0 else round(done / total * 100)
    return (
        f'<div class="bar-wrap"><div class="bar-fill" style="width:{pct}%"></div></div>'
        f'<span class="pct">{pct}% ({done}/{total})</span>'
    )


def render_milestone_report_html(conn, milestone_id: int) -> str:
    m = db.get_milestone(conn, milestone_id)
    if m is None:
        raise ValueError(f"No milestone with id {milestone_id}")

    breakdowns = db.list_breakdowns(conn, milestone_id)
    logs = db.list_logs(conn, milestone_id)
    done, total = db.breakdown_stats(conn, milestone_id)
    status = _status_label(m)

    rows_b = "".join(
        f"<tr><td>{b['id']}</td><td>{'✅ Done' if b['completed'] else '⬜ Pending'}</td>"
        f"<td>{escape(b['description'])}</td></tr>"
        for b in breakdowns
    ) or "<tr><td colspan='3'><em>No breakdown items yet.</em></td></tr>"

    rows_l = "".join(
        f"<tr><td>{log['id']}</td><td>{log['date']}</td>"
        f"<td>{'#' + str(log['breakdown_id']) if log['breakdown_id'] else '—'}</td>"
        f"<td>{escape(log['description'])}</td></tr>"
        for log in logs
    ) or "<tr><td colspan='4'><em>No journal entries yet.</em></td></tr>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{escape(m['description'])}</title>{_HTML_STYLE}</head>
<body>
  <h1>🎯 {escape(m['description'])}</h1>
  <div class="meta">Timeline: {month_str(m['start_year'], m['start_month'])} → {month_str(m['end_year'], m['end_month'])}
    &nbsp;·&nbsp; <span class="badge">{status}</span> &nbsp;·&nbsp; Milestone ID: {m['id']}</div>
  <div>{_bar_html(done, total)}</div>
  <div class="meta">{len(logs)} journal log{'s' if len(logs) != 1 else ''} recorded</div>

  <h2 class="section-title">✅ Breakdown Checklist</h2>
  <table><tr><th>ID</th><th>Status</th><th>Description</th></tr>{rows_b}</table>

  <h2 class="section-title">📝 Journal Logs ({len(logs)})</h2>
  <table><tr><th>ID</th><th>Date</th><th>Linked Item</th><th>Description</th></tr>{rows_l}</table>
</body></html>
"""


def render_list_report_html(conn) -> str:
    milestones = db.list_milestones(conn)
    rows = []
    for m in milestones:
        done, total = db.breakdown_stats(conn, m["id"])
        log_count = db.count_logs(conn, m["id"])
        timeline = f"{month_str(m['start_year'], m['start_month'])} → {month_str(m['end_year'], m['end_month'])}"
        rows.append(
            f"<tr><td>{m['id']}</td><td>{escape(m['description'])}</td><td>{timeline}</td>"
            f"<td>{_bar_html(done, total)}</td><td>{log_count}</td></tr>"
        )
    body_rows = "".join(rows) or "<tr><td colspan='5'><em>No milestones yet.</em></td></tr>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>PointJournal — All Milestones</title>{_HTML_STYLE}</head>
<body>
  <h1>📚 PointJournal — All Milestones</h1>
  <table><tr><th>ID</th><th>Milestone</th><th>Timeline</th><th>Progress</th><th>Logs</th></tr>{body_rows}</table>
</body></html>
"""
