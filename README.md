# PointJournal

A CLI learning journal. Track milestones, break each one into a checklist,
and log dated progress notes — all from the terminal, stored in a local
SQLite file. Generates beautiful Markdown or HTML reports.

Package name: `pointjournal`. Command name: **`ptjournal`**.

No account, no server, no ads, no tracking. Your data is one file on your
own disk.

```
$ ptjournal show

#1 Master Rust Programming
2026-01 -> 2026-06  ·  █████░░░░░ 50% (1/2)  ·  2 logs

                    Breakdown
┏━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID ┃ Status ┃ Description                      ┃
┡━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│  1 │ ✅     │ Complete Rust Book Chapters 1-10 │
│  2 │ ⬜     │ Build a CLI App in Rust          │
└────┴────────┴──────────────────────────────────┘
```

## Features

- Three tables: `milestone`, `milestone_breakdown`, `journal_log`
- Full CRUD on all three (`add` / `update` / `delete` / `read`)
- **Current milestone** — set one with `use`, skip `--mid` everywhere else
- `show` — one command, a full table view of a milestone's breakdowns and
  logs with their IDs, so you always know what to pass to `update`/`delete`
- `check`/`uncheck` by ID, or by matching text — no need to memorize IDs
- Optional link from a journal log to a specific breakdown item
- `list` — filterable, sortable tables across milestones, breakdowns, or logs
- Reports in **Markdown or HTML**, with a progress bar and log counts
- Short flag aliases for fast typing (see table below)
- Zero external services — plain SQLite file at `~/.pointjournal/journal.db`

## Requirements

- Python 3.9+
- VS Code with the Python extension (`ms-python.python`) — recommended, not required

## Install & Setup (VS Code)

1. Open the `pointjournal/` folder in VS Code: **File → Open Folder…**
2. Open a terminal: `` Ctrl+` `` (Windows/Linux) or `` Cmd+` `` (macOS)
3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv

   # macOS/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

4. Select the interpreter: VS Code usually prompts automatically. If not,
   `Ctrl+Shift+P` → **Python: Select Interpreter** → choose the one inside `.venv`.
5. Install the project (editable mode — code changes apply immediately, no reinstall):

   ```bash
   pip install -e ".[dev]"
   ```

6. Verify:

   ```bash
   ptjournal --help
   ```

## Install Without VS Code (plain terminal / cmd)

For someone who just wants to *use* the tool — no editor, no cloning the
source, just a terminal.

### Option A — pipx (recommended)

`pipx` installs the command in its own isolated environment and puts it on
your `PATH`, so `ptjournal` just works globally, without you managing a
venv yourself.

**Linux (bash/zsh terminal):**
```bash
python3 -m pip install --user pipx
pipx ensurepath
# close and reopen your terminal, then:
pipx install "git+https://github.com/kelvindev2020/pointjournal.git"
```

**macOS (Terminal.app):** same commands as Linux above.

**Windows (cmd.exe or PowerShell):**
```cmd
py -m pip install --user pipx
py -m pipx ensurepath
:: close and reopen cmd, then:
pipx install "git+https://github.com/kelvindev2020/pointjournal.git"
```

### Option B — plain pip (no isolation)

```bash
pip install --user "git+https://github.com/kelvindev2020/pointjournal.git"
```

### Verify (any option, any OS)

```bash
ptjournal --help
```

### Uninstall

```bash
pipx uninstall pointjournal      # if installed via pipx
pip uninstall pointjournal       # if installed via pip
```

## Quick Start

```bash
ptjournal add milestone -d "Master Rust Programming" -s 2026-01 -e 2026-06
ptjournal use 1                                        # set as current — skip --mid below
ptjournal add breakdown -d "Complete Rust Book Chapters 1-10"
ptjournal add breakdown -d "Build a CLI App in Rust"
ptjournal check -d "Chapters 1-10"                      # check by text match
ptjournal add log -d "Read Chapter 4 on Ownership and Borrowing" --mbid 1

ptjournal show                                          # table view with IDs
ptjournal report                                        # Markdown report for current milestone
```

## Short Flags

Every command below accepts either the full flag or its short form.

| Full flag | Short form | Used on |
|---|---|---|
| `--desc` | `-d` | add/update/check/uncheck |
| `--start` | `-s` | add/update/list milestone |
| `--end` | `-e` | add/update/list milestone |
| `--milestone-id` | `--mid` | add/read/list/check/uncheck |
| `--breakdown-id` | `--mbid` | add log |
| `--date` | `--date` (no short form) | add/update log |
| `--id` | `--id` (no short form) | update/delete |

## Current Milestone

Set once, then omit `--mid` on `add breakdown`, `add log`, `read breakdown`,
`read log`, `show`, and `check`/`uncheck --desc`:

```bash
ptjournal use 1          # set milestone #1 as current
ptjournal current        # show which one is current
```

You can still pass `--mid <id>` explicitly on any command to override it for
that one call.

## Command Reference

### Add
```bash
ptjournal add milestone -d "..." -s YYYY-MM -e YYYY-MM
ptjournal add breakdown [--mid <id>] -d "..."
ptjournal add log [--mid <id>] -d "..." [--date YYYY-MM-DD] [--mbid <breakdown_id>]
```
`--date` defaults to today. `--mbid` optionally links the log entry to a
specific breakdown item.

### Update
```bash
ptjournal update milestone --id <id> [-d "..."] [-s YYYY-MM] [-e YYYY-MM]
ptjournal update breakdown --id <id> -d "..."
ptjournal update log --id <id> [-d "..."] [--date YYYY-MM-DD]
```

### Delete
*Always asks for confirmation before deleting.*
```bash
ptjournal delete milestone --id <id>   # also deletes its breakdowns + logs
ptjournal delete breakdown --id <id>
ptjournal delete log --id <id>
```

### Read
```bash
ptjournal read milestone               # list all
ptjournal read milestone --id <id>     # single milestone
ptjournal read breakdown [--mid <id>]
ptjournal read log [--mid <id>]
```

### Show
```bash
ptjournal show [milestone_id]          # defaults to current milestone
```
Prints the milestone's progress summary plus two tables (breakdown items and
journal logs), each with IDs — the fastest way to find an ID for `update`,
`delete`, `check`, or `uncheck`.

### Check / Uncheck
```bash
ptjournal check <breakdown_id>
ptjournal check -d "partial description text" [--mid <id>]
ptjournal uncheck <breakdown_id>
ptjournal uncheck -d "partial description text" [--mid <id>]
```
If `-d` matches more than one item, PointJournal lists the matches and their
IDs instead of guessing — rerun with a more specific phrase or the exact ID.

### List
```bash
ptjournal list milestone [--limit 100] [--id-min N] [--id-max N] [-s YYYY-MM] [-e YYYY-MM]
ptjournal list breakdown [--mid <id>] [--limit 500]
ptjournal list log [--mid <id>] [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--limit 500]
```
Unlike `read`, `list` works across all milestones by default and supports
filtering and row limits — useful once you have many milestones.

### Reports
```bash
ptjournal report [--mid <id>]                     # Markdown, current milestone if omitted
ptjournal report --mid <id> -o report.html         # HTML (auto-detected from .html)
ptjournal report --mid <id> --format html          # HTML, printed to terminal
ptjournal report --list                            # overview of all milestones, Markdown
ptjournal report --list --format html -o all.html  # overview, HTML
```
Reports include a progress bar, completion percentage, and log counts per
milestone/checklist.

## Data Storage

All data lives in a single SQLite file, in your user home folder:

| OS | Actual path |
|---|---|
| Linux | `/home/<you>/.pointjournal/journal.db` |
| macOS | `/Users/<you>/.pointjournal/journal.db` |
| Windows | `C:\Users\<you>\.pointjournal\journal.db` |

Shorthand: `~/.pointjournal/journal.db` (`~` = your home folder on any OS).

It's a plain SQLite file — back it up by copying it, inspect it with any
SQLite browser (e.g. `sqlite3`, DB Browser for SQLite), or sync it via
Dropbox/iCloud if you point `POINTJOURNAL_DB` at a synced folder. Nothing is
sent anywhere over the network.

Override the location:

```bash
export POINTJOURNAL_DB=/path/to/your/journal.db     # Linux/macOS
set POINTJOURNAL_DB=C:\path\to\your\journal.db       # Windows cmd
```

## Project Layout

```
pointjournal/
├── pyproject.toml           # dependencies + `ptjournal` command entry point
├── README.md
├── LICENSE
├── .gitignore
├── .github/FUNDING.yml
├── src/pointjournal/
│   ├── cli.py                # command definitions (Typer) — the "controller" layer
│   ├── db.py                 # SQLite schema + CRUD functions — the "DAO" layer
│   └── report.py              # Markdown + HTML report rendering
└── tests/
    ├── test_db.py             # CRUD + filtering correctness
    └── test_report.py         # Markdown and HTML report output
```

## Testing

```bash
pytest
```

## Roadmap (not yet built)

- [ ] Encryption at rest (app-level, passphrase-gated)
- [ ] Export / import (JSON backup and restore)
- [ ] Input validation hardening (invalid months, empty descriptions)
- [ ] Optional PyPI publish for `pip install pointjournal` without cloning the repo

## Support

This is a free, independently-built tool. If it's useful to you, a donation
is appreciated but never required: PayPal — **[paypal.me/kelvindev2020](https://www.paypal.me/kelvindev2020)**

(GitHub Sponsors coming later once approved.)

## License

MIT — see [LICENSE](LICENSE).
