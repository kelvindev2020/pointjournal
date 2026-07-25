"""
CLI layer. Only argument parsing and printing live here -- all real logic
stays in db.py / report.py so it's testable without invoking the CLI.

Java analogy: this file is roughly your Controller layer; db.py is the DAO
layer; report.py is a view/formatter.
"""

from datetime import date as _date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pointjournal import db, report

app = typer.Typer(help="PointJournal (ptjournal) — a CLI learning journal.", no_args_is_help=True)

add_app = typer.Typer(help="Add a milestone, breakdown, or log entry.", no_args_is_help=True)
update_app = typer.Typer(help="Update a milestone, breakdown, or log entry.", no_args_is_help=True)
delete_app = typer.Typer(help="Delete a milestone, breakdown, or log entry.", no_args_is_help=True)
read_app = typer.Typer(help="Read milestones, breakdowns, or log entries.", no_args_is_help=True)
list_app = typer.Typer(help="List milestones, breakdowns, or logs with filters.", no_args_is_help=True)

app.add_typer(add_app, name="add")
app.add_typer(update_app, name="update")
app.add_typer(delete_app, name="delete")
app.add_typer(read_app, name="read")
app.add_typer(list_app, name="list")

CURRENT_MILESTONE_KEY = "current_milestone_id"


def _conn():
    return db.get_connection()


def _parse_year_month(value: str, flag_name: str) -> tuple[int, int]:
    try:
        year_str, month_str = value.split("-")
        return int(year_str), int(month_str)
    except ValueError:
        raise typer.BadParameter(f"{flag_name} must be in YYYY-MM format, got '{value}'")


def _resolve_mid(conn, mid: Optional[int]) -> int:
    """Return the given milestone id, or fall back to the current one."""
    if mid is not None:
        return mid
    val = db.get_state(conn, CURRENT_MILESTONE_KEY)
    if val is None:
        typer.secho(
            "No --mid given and no current milestone set. "
            "Pass --mid <id>, or run: ptjournal use <id>",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    return int(val)


def _milestone_timeline(m) -> str:
    return f"{m['start_year']}-{m['start_month']:02d} -> {m['end_year']}-{m['end_month']:02d}"


# ---------------- use / current ----------------

@app.command()
def use(milestone_id: int = typer.Argument(..., help="Milestone ID to set as current")):
    """Set the current milestone so --mid can be omitted on other commands."""
    conn = _conn()
    m = db.get_milestone(conn, milestone_id)
    if m is None:
        typer.secho(f"No milestone with id {milestone_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    db.set_state(conn, CURRENT_MILESTONE_KEY, milestone_id)
    typer.echo(f"Current milestone set to #{milestone_id}: {m['description']}")


@app.command()
def current():
    """Show which milestone is currently set as default."""
    conn = _conn()
    val = db.get_state(conn, CURRENT_MILESTONE_KEY)
    if val is None:
        typer.echo("No current milestone set. Use: ptjournal use <id>")
        raise typer.Exit()
    m = db.get_milestone(conn, int(val))
    if m is None:
        typer.echo("Current milestone was set but no longer exists. Use: ptjournal use <id>")
        raise typer.Exit()
    typer.echo(f"Current milestone: #{m['id']} — {m['description']}")


# ---------------- add ----------------

@add_app.command("milestone")
def add_milestone(
    desc: str = typer.Option(..., "--desc", "-d", help="Milestone description"),
    start: str = typer.Option(..., "--start", "-s", help="Start, YYYY-MM"),
    end: str = typer.Option(..., "--end", "-e", help="End, YYYY-MM"),
):
    sy, sm = _parse_year_month(start, "--start")
    ey, em = _parse_year_month(end, "--end")
    conn = _conn()
    new_id = db.add_milestone(conn, sy, sm, ey, em, desc)
    typer.echo(f"Added milestone #{new_id}: {desc}")


@add_app.command("breakdown")
def add_breakdown(
    mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid", help="Defaults to current milestone"),
    desc: str = typer.Option(..., "--desc", "-d"),
):
    conn = _conn()
    milestone_id = _resolve_mid(conn, mid)
    if db.get_milestone(conn, milestone_id) is None:
        typer.secho(f"No milestone with id {milestone_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    new_id = db.add_breakdown(conn, milestone_id, desc)
    typer.echo(f"Added breakdown #{new_id} under milestone #{milestone_id}: {desc}")


@add_app.command("log")
def add_log(
    mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid", help="Defaults to current milestone"),
    desc: str = typer.Option(..., "--desc", "-d"),
    date: Optional[str] = typer.Option(None, "--date", help="YYYY-MM-DD, defaults to today"),
    mbid: Optional[int] = typer.Option(
        None, "--breakdown-id", "--mbid", help="Optionally link this log to a breakdown item"
    ),
):
    conn = _conn()
    milestone_id = _resolve_mid(conn, mid)
    if db.get_milestone(conn, milestone_id) is None:
        typer.secho(f"No milestone with id {milestone_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    if mbid is not None:
        b = db.get_breakdown(conn, mbid)
        if b is None or b["milestone_id"] != milestone_id:
            typer.secho(f"No breakdown item #{mbid} under milestone #{milestone_id}", fg=typer.colors.RED)
            raise typer.Exit(1)
    log_date = date or _date.today().isoformat()
    new_id = db.add_log(conn, milestone_id, log_date, desc, breakdown_id=mbid)
    link_note = f" (linked to breakdown #{mbid})" if mbid else ""
    typer.echo(f"Added log #{new_id} under milestone #{milestone_id} ({log_date}): {desc}{link_note}")


# ---------------- update ----------------

@update_app.command("milestone")
def update_milestone(
    id: int = typer.Option(..., "--id"),
    desc: Optional[str] = typer.Option(None, "--desc", "-d"),
    start: Optional[str] = typer.Option(None, "--start", "-s"),
    end: Optional[str] = typer.Option(None, "--end", "-e"),
):
    fields = {}
    if desc is not None:
        fields["description"] = desc
    if start is not None:
        sy, sm = _parse_year_month(start, "--start")
        fields["start_year"], fields["start_month"] = sy, sm
    if end is not None:
        ey, em = _parse_year_month(end, "--end")
        fields["end_year"], fields["end_month"] = ey, em

    conn = _conn()
    rows = db.update_milestone(conn, id, **fields)
    if rows == 0:
        typer.secho(f"No milestone updated (id {id} not found or no fields given)", fg=typer.colors.YELLOW)
    else:
        typer.echo(f"Updated milestone #{id}")


@update_app.command("breakdown")
def update_breakdown(
    id: int = typer.Option(..., "--id"),
    desc: str = typer.Option(..., "--desc", "-d"),
):
    conn = _conn()
    rows = db.update_breakdown(conn, id, description=desc)
    if rows == 0:
        typer.secho(f"No breakdown item with id {id}", fg=typer.colors.YELLOW)
    else:
        typer.echo(f"Updated breakdown #{id}")


@update_app.command("log")
def update_log(
    id: int = typer.Option(..., "--id"),
    desc: Optional[str] = typer.Option(None, "--desc", "-d"),
    date: Optional[str] = typer.Option(None, "--date"),
):
    fields = {}
    if desc is not None:
        fields["description"] = desc
    if date is not None:
        fields["date"] = date
    conn = _conn()
    rows = db.update_log(conn, id, **fields)
    if rows == 0:
        typer.secho(f"No log entry updated (id {id} not found or no fields given)", fg=typer.colors.YELLOW)
    else:
        typer.echo(f"Updated log #{id}")


# ---------------- delete ----------------

@delete_app.command("milestone")
def delete_milestone(id: int = typer.Option(..., "--id")):
    if not typer.confirm(f"Delete milestone #{id} and ALL its breakdowns/logs?"):
        typer.echo("Cancelled.")
        raise typer.Exit()
    conn = _conn()
    rows = db.delete_milestone(conn, id)
    typer.echo(f"Deleted milestone #{id}" if rows else f"No milestone with id {id}")


@delete_app.command("breakdown")
def delete_breakdown(id: int = typer.Option(..., "--id")):
    if not typer.confirm(f"Delete breakdown #{id}?"):
        typer.echo("Cancelled.")
        raise typer.Exit()
    conn = _conn()
    rows = db.delete_breakdown(conn, id)
    typer.echo(f"Deleted breakdown #{id}" if rows else f"No breakdown with id {id}")


@delete_app.command("log")
def delete_log(id: int = typer.Option(..., "--id")):
    if not typer.confirm(f"Delete log entry #{id}?"):
        typer.echo("Cancelled.")
        raise typer.Exit()
    conn = _conn()
    rows = db.delete_log(conn, id)
    typer.echo(f"Deleted log #{id}" if rows else f"No log entry with id {id}")


# ---------------- read ----------------

@read_app.command("milestone")
def read_milestone(id: Optional[int] = typer.Option(None, "--id", help="Omit to list all")):
    conn = _conn()
    if id is None:
        rows = db.list_milestones(conn)
        if not rows:
            typer.echo("No milestones yet.")
        for m in rows:
            typer.echo(f"#{m['id']} [{_milestone_timeline(m)}] {m['description']}")
    else:
        m = db.get_milestone(conn, id)
        if m is None:
            typer.secho(f"No milestone with id {id}", fg=typer.colors.RED)
            raise typer.Exit(1)
        typer.echo(f"#{m['id']} [{_milestone_timeline(m)}] {m['description']}")


@read_app.command("breakdown")
def read_breakdown(mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid")):
    conn = _conn()
    milestone_id = _resolve_mid(conn, mid)
    rows = db.list_breakdowns(conn, milestone_id)
    if not rows:
        typer.echo("No breakdown items yet.")
    for b in rows:
        box = "x" if b["completed"] else " "
        typer.echo(f"#{b['id']} [{box}] {b['description']}")


@read_app.command("log")
def read_log(mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid")):
    conn = _conn()
    milestone_id = _resolve_mid(conn, mid)
    rows = db.list_logs(conn, milestone_id)
    if not rows:
        typer.echo("No log entries yet.")
    for log in rows:
        typer.echo(f"#{log['id']} {log['date']}: {log['description']}")


# ---------------- show (item 1: breakdown+log table with IDs) ----------------

@app.command()
def show(mid: Optional[int] = typer.Argument(None, help="Milestone ID (defaults to current)")):
    """Show a milestone's breakdown and log tables with IDs -- for finding
    IDs to pass to update/delete/check/uncheck."""
    conn = _conn()
    milestone_id = _resolve_mid(conn, mid)
    m = db.get_milestone(conn, milestone_id)
    if m is None:
        typer.secho(f"No milestone with id {milestone_id}", fg=typer.colors.RED)
        raise typer.Exit(1)

    done, total = db.breakdown_stats(conn, milestone_id)
    log_count = db.count_logs(conn, milestone_id)

    console = Console()
    console.print(f"\n[bold]#{m['id']} {m['description']}[/bold]")
    console.print(
        f"[dim]{_milestone_timeline(m)}  ·  {report.progress_bar_plain(done, total)}  ·  "
        f"{log_count} log{'s' if log_count != 1 else ''}[/dim]\n"
    )

    b_table = Table(title="Breakdown")
    b_table.add_column("ID", justify="right")
    b_table.add_column("Status")
    b_table.add_column("Description")
    for b in db.list_breakdowns(conn, milestone_id):
        b_table.add_row(str(b["id"]), "✅" if b["completed"] else "⬜", b["description"])
    console.print(b_table)

    l_table = Table(title="Journal Log")
    l_table.add_column("ID", justify="right")
    l_table.add_column("Date")
    l_table.add_column("Linked")
    l_table.add_column("Description")
    for log in db.list_logs(conn, milestone_id):
        linked = f"#{log['breakdown_id']}" if log["breakdown_id"] else "—"
        l_table.add_row(str(log["id"]), log["date"], linked, log["description"])
    console.print(l_table)


# ---------------- check / uncheck (item 2: friendlier targeting) ----------------

def _check_uncheck(id: Optional[int], desc: Optional[str], mid: Optional[int], completed: bool):
    conn = _conn()
    verb = "Checked" if completed else "Unchecked"

    if id is not None:
        rows = db.set_breakdown_completed(conn, id, completed)
        typer.echo(f"{verb} #{id}" if rows else f"No breakdown item with id {id}")
        return

    if desc is None:
        typer.secho("Provide an ID, or --desc to match by text (e.g. ptjournal check --desc \"CLI App\").",
                     fg=typer.colors.RED)
        raise typer.Exit(1)

    milestone_id = _resolve_mid(conn, mid)
    matches = db.find_breakdowns_by_desc(conn, milestone_id, desc)
    if not matches:
        typer.secho(f"No breakdown items matching '{desc}' under milestone #{milestone_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    if len(matches) > 1:
        typer.secho(f"Multiple matches for '{desc}' — be more specific, or use the ID:", fg=typer.colors.YELLOW)
        for b in matches:
            typer.echo(f"  #{b['id']}  {b['description']}")
        raise typer.Exit(1)

    b = matches[0]
    db.set_breakdown_completed(conn, b["id"], completed)
    typer.echo(f"{verb} #{b['id']}: {b['description']}")


@app.command()
def check(
    id: Optional[int] = typer.Argument(None, help="Breakdown item id"),
    desc: Optional[str] = typer.Option(None, "--desc", "-d", help="Match by description instead of ID"),
    mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid", help="Scope for --desc search"),
):
    """Mark a breakdown item as completed. Use an ID, or --desc to match by text."""
    _check_uncheck(id, desc, mid, completed=True)


@app.command()
def uncheck(
    id: Optional[int] = typer.Argument(None, help="Breakdown item id"),
    desc: Optional[str] = typer.Option(None, "--desc", "-d", help="Match by description instead of ID"),
    mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid", help="Scope for --desc search"),
):
    """Mark a breakdown item as not completed. Use an ID, or --desc to match by text."""
    _check_uncheck(id, desc, mid, completed=False)


# ---------------- list (item 7) ----------------

def _print_milestone_table(conn, rows):
    table = Table(title="Milestones")
    table.add_column("ID", justify="right")
    table.add_column("Timeline")
    table.add_column("Progress")
    table.add_column("Description")
    for m in rows:
        done, total = db.breakdown_stats(conn, m["id"])
        table.add_row(
            str(m["id"]),
            f"{month_str(m)} → {month_str(m, end=True)}",
            report.progress_bar_plain(done, total),
            m["description"],
        )
    Console().print(table)


def month_str(m, end: bool = False) -> str:
    if end:
        return f"{m['end_year']:04d}/{m['end_month']:02d}"
    return f"{m['start_year']:04d}/{m['start_month']:02d}"


@list_app.command("milestone")
def list_milestone(
    limit: int = typer.Option(100, "--limit", help="Max rows to show"),
    id_min: Optional[int] = typer.Option(None, "--id-min"),
    id_max: Optional[int] = typer.Option(None, "--id-max"),
    start: Optional[str] = typer.Option(None, "--start", "-s", help="Only milestones overlapping from YYYY-MM"),
    end: Optional[str] = typer.Option(None, "--end", "-e", help="Only milestones overlapping up to YYYY-MM"),
):
    conn = _conn()
    start_t = _parse_year_month(start, "--start") if start else None
    end_t = _parse_year_month(end, "--end") if end else None
    rows = db.list_milestones_filtered(conn, limit=limit, id_min=id_min, id_max=id_max, start=start_t, end=end_t)
    if not rows:
        typer.echo("No milestones match.")
        return
    _print_milestone_table(conn, rows)


@list_app.command("breakdown")
def list_breakdown(
    mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid", help="Omit to list across all milestones"),
    limit: int = typer.Option(500, "--limit"),
):
    conn = _conn()
    rows = db.list_breakdowns_filtered(conn, milestone_id=mid, limit=limit)
    if not rows:
        typer.echo("No breakdown items match.")
        return
    table = Table(title="Breakdown Items")
    table.add_column("ID", justify="right")
    table.add_column("Milestone ID", justify="right")
    table.add_column("Status")
    table.add_column("Description")
    for b in rows:
        table.add_row(str(b["id"]), str(b["milestone_id"]), "✅" if b["completed"] else "⬜", b["description"])
    Console().print(table)


@list_app.command("log")
def list_log(
    mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid", help="Omit to list across all milestones"),
    date_from: Optional[str] = typer.Option(None, "--from", help="YYYY-MM-DD"),
    date_to: Optional[str] = typer.Option(None, "--to", help="YYYY-MM-DD"),
    limit: int = typer.Option(500, "--limit"),
):
    conn = _conn()
    rows = db.list_logs_filtered(conn, milestone_id=mid, date_from=date_from, date_to=date_to, limit=limit)
    if not rows:
        typer.echo("No log entries match.")
        return
    table = Table(title="Journal Logs")
    table.add_column("ID", justify="right")
    table.add_column("Milestone ID", justify="right")
    table.add_column("Date")
    table.add_column("Linked", justify="right")
    table.add_column("Description")
    for log in rows:
        linked = f"#{log['breakdown_id']}" if log["breakdown_id"] else "—"
        table.add_row(str(log["id"]), str(log["milestone_id"]), log["date"], linked, log["description"])
    Console().print(table)


# ---------------- report ----------------

@app.command(name="report")
def report_cmd(
    mid: Optional[int] = typer.Option(None, "--milestone-id", "--mid", help="Milestone to report on"),
    list_: bool = typer.Option(False, "--list", help="List all milestones + journal logs instead"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to file instead of stdout"),
    fmt: Optional[str] = typer.Option(
        None, "--format", help="md or html (auto-detected from --output extension if omitted)"
    ),
):
    """Generate a report, in Markdown or HTML."""
    conn = _conn()

    format_ = fmt
    if format_ is None and output is not None:
        format_ = "html" if output.suffix.lower() == ".html" else "md"
    if format_ is None:
        format_ = "md"
    if format_ not in ("md", "html"):
        typer.secho("Format must be 'md' or 'html'.", fg=typer.colors.RED)
        raise typer.Exit(1)

    if list_:
        content = report.render_list_report_html(conn) if format_ == "html" else report.render_list_report(conn)
    else:
        if mid is None:
            typer.secho("Provide --mid, or use --list for all milestones.", fg=typer.colors.RED)
            raise typer.Exit(1)
        try:
            content = (
                report.render_milestone_report_html(conn, mid)
                if format_ == "html"
                else report.render_milestone_report(conn, mid)
            )
        except ValueError as e:
            typer.secho(str(e), fg=typer.colors.RED)
            raise typer.Exit(1)

    if output:
        output.write_text(content)
        typer.echo(f"Report written to {output}")
    else:
        typer.echo(content)


if __name__ == "__main__":
    app()
