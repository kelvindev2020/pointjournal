# PointJournal

A CLI learning journal. Track milestones, break each one into a checklist,
and log dated progress notes — all from the terminal, stored in a local
SQLite file. Generates clean Markdown reports you can drop into a wiki,
GitHub README, or blog post.

Package name: `pointjournal`. Command name: **`ptjournal`**.

No account, no server, no ads, no tracking. Your data is one file on your
own disk.

```
$ ptjournal report --milestone-id 1

# Milestone Report: Master Rust Programming
**Timeline:** 2026/01 — 2026/06

## Breakdown Checklist
- [x] Complete Rust Book Chapters 1-10
- [ ] Build a CLI App in Rust

## Journal Logs
- **2026-07-25**: Read Chapter 4 on Ownership and Borrowing
***
```

## Features

- Three simple tables: `milestone`, `milestone_breakdown`, `journal_log`
- Full CRUD on all three (`add` / `update` / `delete` / `read`)
- Check/uncheck breakdown items as you complete them
- Two Markdown report modes: single-milestone report, or a flat listing of everything
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
pipx install "git+https://github.com/<your-username>/pointjournal.git"
```

**macOS (Terminal.app):** same commands as Linux above.

**Windows (cmd.exe or PowerShell):**
```cmd
py -m pip install --user pipx
py -m pipx ensurepath
:: close and reopen cmd, then:
pipx install "git+https://github.com/<your-username>/pointjournal.git"
```

### Option B — plain pip (no isolation)

Simpler, but installs into your regular user Python environment instead of
an isolated one:

```bash
pip install --user "git+https://github.com/<your-username>/pointjournal.git"
```

### Verify (any option, any OS)

```bash
ptjournal --help
```

If `ptjournal` isn't found after install, your Python "user scripts"
folder isn't on `PATH` yet — `pipx ensurepath` (Option A) fixes this
automatically; for Option B you may need to add it manually.

### Uninstall

```bash
pipx uninstall pointjournal      # if installed via pipx
pip uninstall pointjournal       # if installed via pip
```

## Quick Start

```bash
ptjournal add milestone --desc "Master Rust Programming" --start 2026-01 --end 2026-06
ptjournal add breakdown --milestone-id 1 --desc "Complete Rust Book Chapters 1-10"
ptjournal add breakdown --milestone-id 1 --desc "Build a CLI App in Rust"
ptjournal check 1
ptjournal add log --milestone-id 1 --desc "Read Chapter 4 on Ownership and Borrowing"

ptjournal report --milestone-id 1
```

## Command Reference

### Add
```bash
ptjournal add milestone --desc "..." --start YYYY-MM --end YYYY-MM
ptjournal add breakdown --milestone-id <id> --desc "..."
ptjournal add log --milestone-id <id> --desc "..." [--date YYYY-MM-DD]
```
`--date` defaults to today if omitted.

### Update
```bash
ptjournal update milestone --id <id> [--desc "..."] [--start YYYY-MM] [--end YYYY-MM]
ptjournal update breakdown --id <id> --desc "..."
ptjournal update log --id <id> [--desc "..."] [--date YYYY-MM-DD]
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
ptjournal read breakdown --milestone-id <id>
ptjournal read log --milestone-id <id>
```

### Check / Uncheck
```bash
ptjournal check <breakdown_id>
ptjournal uncheck <breakdown_id>
```

### Reports
```bash
ptjournal report --milestone-id <id>              # single milestone, printed to terminal
ptjournal report --milestone-id <id> -o out.md     # write to a file instead
ptjournal report --list                            # flat table of all milestones + logs
```

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
Dropbox/iCloud if you point `POINTJOURNAL_DB` at a synced folder (below).
Nothing is sent anywhere over the network.

Override the location (e.g. to store it in a synced folder):

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
│   └── report.py              # Markdown report rendering
└── tests/
    ├── test_db.py             # CRUD correctness
    └── test_report.py         # report output format
```

## Testing

```bash
pytest
```

## Roadmap (not yet built)

- [ ] Input validation hardening (invalid months, empty descriptions, missing IDs on `update`/`read`)
- [ ] Additional edge-case tests
- [ ] Optional PyPI publish for `pip install pointjournal` without cloning the repo
- [ ] Encryption Feature
- [ ] Default Milestone
- [ ] More features

## License

MIT — see [LICENSE](LICENSE).
