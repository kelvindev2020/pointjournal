"""Markdown report builders. Kept separate from db.py and cli.py so report
formatting can change without touching data access or argument parsing."""

from pointjournal import db


def month_str(year: int, month: int) -> str:
    return f"{year:04d}/{month:02d}"


def render_milestone_report(conn, milestone_id: int) -> str:
    m = db.get_milestone(conn, milestone_id)
    if m is None:
        raise ValueError(f"No milestone with id {milestone_id}")

    breakdowns = db.list_breakdowns(conn, milestone_id)
    logs = db.list_logs(conn, milestone_id)

    lines = []
    lines.append(f"# Milestone Report: {m['description']}")
    lines.append(
        f"**Timeline:** {month_str(m['start_year'], m['start_month'])} "
        f"— {month_str(m['end_year'], m['end_month'])}"
    )
    lines.append("")
    lines.append("## Breakdown Checklist")
    if breakdowns:
        for b in breakdowns:
            box = "x" if b["completed"] else " "
            lines.append(f"- [{box}] {b['description']}")
    else:
        lines.append("_No breakdown items yet._")
    lines.append("")
    lines.append("## Journal Logs")
    if logs:
        for log in logs:
            lines.append(f"- **{log['date']}**: {log['description']}")
    else:
        lines.append("_No journal entries yet._")
    lines.append("")
    lines.append("***")
    return "\n".join(lines)


def render_list_report(conn) -> str:
    milestones = db.list_milestones(conn)
    logs = db.list_all_logs(conn)

    lines = []
    lines.append("# PointJournal — All Milestones & Journal Logs")
    lines.append("")
    lines.append("## Milestones")
    lines.append("")
    lines.append("| ID | Description | Start | End |")
    lines.append("|---|---|---|---|")
    for m in milestones:
        lines.append(
            f"| {m['id']} | {m['description']} | "
            f"{month_str(m['start_year'], m['start_month'])} | "
            f"{month_str(m['end_year'], m['end_month'])} |"
        )
    lines.append("")
    lines.append("## Journal Log")
    lines.append("")
    lines.append("| Date | Milestone | Description |")
    lines.append("|---|---|---|")
    for log in logs:
        lines.append(f"| {log['date']} | {log['milestone_description']} | {log['description']} |")
    lines.append("")
    return "\n".join(lines)
