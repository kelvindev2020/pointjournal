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

from pointjournal import db, report

app = typer.Typer(help="PointJournal (ptjournal) — a CLI learning journal.", no_args_is_help=True)

add_app = typer.Typer(help="Add a milestone, breakdown, or log entry.", no_args_is_help=True)
update_app = typer.Typer(help="Update a milestone, breakdown, or log entry.", no_args_is_help=True)
delete_app = typer.Typer(help="Delete a milestone, breakdown, or log entry.", no_args_is_help=True)
read_app = typer.Typer(help="Read milestones, breakdowns, or log entries.", no_args_is_help=True)

app.add_typer(add_app, name="add")
app.add_typer(update_app, name="update")
app.add_typer(delete_app, name="delete")
app.add_typer(read_app, name="read")


def _conn():
    return db.get_connection()


def _parse_year_month(value: str, flag_name: str) -> tuple[int, int]:
    try:
        year_str, month_str = value.split("-")
        return int(year_str), int(month_str)
    except ValueError:
        raise typer.BadParameter(f"{flag_name} must be in YYYY-MM format, got '{value}'")


# ---------------- add ----------------

@add_app.command("milestone")
def add_milestone(
    desc: str = typer.Option(..., "--desc", help="Milestone description"),
    start: str = typer.Option(..., "--start", help="Start, YYYY-MM"),
    end: str = typer.Option(..., "--end", help="End, YYYY-MM"),
):
    sy, sm = _parse_year_month(start, "--start")
    ey, em = _parse_year_month(end, "--end")
    conn = _conn()
    new_id = db.add_milestone(conn, sy, sm, ey, em, desc)
    typer.echo(f"Added milestone #{new_id}: {desc}")


@add_app.command("breakdown")
def add_breakdown(
    milestone_id: int = typer.Option(..., "--milestone-id"),
    desc: str = typer.Option(..., "--desc"),
):
    conn = _conn()
    if db.get_milestone(conn, milestone_id) is None:
        typer.secho(f"No milestone with id {milestone_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    new_id = db.add_breakdown(conn, milestone_id, desc)
    typer.echo(f"Added breakdown #{new_id} under milestone #{milestone_id}: {desc}")


@add_app.command("log")
def add_log(
    milestone_id: int = typer.Option(..., "--milestone-id"),
    desc: str = typer.Option(..., "--desc"),
    date: Optional[str] = typer.Option(None, "--date", help="YYYY-MM-DD, defaults to today"),
):
    conn = _conn()
    if db.get_milestone(conn, milestone_id) is None:
        typer.secho(f"No milestone with id {milestone_id}", fg=typer.colors.RED)
        raise typer.Exit(1)
    log_date = date or _date.today().isoformat()
    new_id = db.add_log(conn, milestone_id, log_date, desc)
    typer.echo(f"Added log #{new_id} under milestone #{milestone_id} ({log_date}): {desc}")


# ---------------- update ----------------

@update_app.command("milestone")
def update_milestone(
    id: int = typer.Option(..., "--id"),
    desc: Optional[str] = typer.Option(None, "--desc"),
    start: Optional[str] = typer.Option(None, "--start"),
    end: Optional[str] = typer.Option(None, "--end"),
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
    desc: str = typer.Option(..., "--desc"),
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
    desc: Optional[str] = typer.Option(None, "--desc"),
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
            typer.echo(
                f"#{m['id']} [{m['start_year']}-{m['start_month']:02d} -> "
                f"{m['end_year']}-{m['end_month']:02d}] {m['description']}"
            )
    else:
        m = db.get_milestone(conn, id)
        if m is None:
            typer.secho(f"No milestone with id {id}", fg=typer.colors.RED)
            raise typer.Exit(1)
        typer.echo(
            f"#{m['id']} [{m['start_year']}-{m['start_month']:02d} -> "
            f"{m['end_year']}-{m['end_month']:02d}] {m['description']}"
        )


@read_app.command("breakdown")
def read_breakdown(milestone_id: int = typer.Option(..., "--milestone-id")):
    conn = _conn()
    rows = db.list_breakdowns(conn, milestone_id)
    if not rows:
        typer.echo("No breakdown items yet.")
    for b in rows:
        box = "x" if b["completed"] else " "
        typer.echo(f"#{b['id']} [{box}] {b['description']}")


@read_app.command("log")
def read_log(milestone_id: int = typer.Option(..., "--milestone-id")):
    conn = _conn()
    rows = db.list_logs(conn, milestone_id)
    if not rows:
        typer.echo("No log entries yet.")
    for log in rows:
        typer.echo(f"#{log['id']} {log['date']}: {log['description']}")


# ---------------- check / uncheck ----------------

@app.command()
def check(id: int = typer.Argument(..., help="Breakdown item id")):
    """Mark a breakdown item as completed."""
    conn = _conn()
    rows = db.set_breakdown_completed(conn, id, True)
    typer.echo(f"Checked #{id}" if rows else f"No breakdown item with id {id}")


@app.command()
def uncheck(id: int = typer.Argument(..., help="Breakdown item id")):
    """Mark a breakdown item as not completed."""
    conn = _conn()
    rows = db.set_breakdown_completed(conn, id, False)
    typer.echo(f"Unchecked #{id}" if rows else f"No breakdown item with id {id}")


# ---------------- report ----------------

@app.command(name="report")
def report_cmd(
    milestone_id: Optional[int] = typer.Option(None, "--milestone-id", help="Milestone to report on"),
    list_: bool = typer.Option(False, "--list", help="List all milestones + journal logs instead"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to file instead of stdout"),
):
    """Generate a Markdown report."""
    conn = _conn()
    if list_:
        content = report.render_list_report(conn)
    else:
        if milestone_id is None:
            typer.secho("Provide --milestone-id, or use --list for all milestones.", fg=typer.colors.RED)
            raise typer.Exit(1)
        try:
            content = report.render_milestone_report(conn, milestone_id)
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
