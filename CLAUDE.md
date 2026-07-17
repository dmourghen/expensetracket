# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```powershell
python app.py
```

Runs on http://127.0.0.1:5001. On Windows, background it with:

```powershell
Start-Process python -ArgumentList "app.py" -WindowStyle Hidden
```

## Running tests

```powershell
pytest
```

Run a single test file:

```powershell
pytest tests/test_auth.py
```

## Installing dependencies

```powershell
pip install -r requirements.txt
```

## Architecture

This is a Flask app taught as a step-by-step course project. Students build features incrementally across numbered steps.

**Entry point:** `app.py` — all routes are defined here. Placeholder routes return plain strings for steps not yet implemented.

**Template inheritance:** All pages extend `templates/base.html`, which provides the navbar, footer, and loads `static/css/style.css` + `static/js/main.js`. Pages override `{% block title %}`, `{% block head %}` (for page-specific CSS), `{% block content %}`, and `{% block scripts %}`.

**CSS split:** `static/css/style.css` defines all CSS variables (`--ink`, `--accent`, `--paper`, `--paper-warm`, `--border`, etc.) and shared component styles. `static/css/landing.css` is loaded only by `landing.html` and overrides the hero layout from 2-column grid to single-column centered.

**Database (not yet implemented):** `database/db.py` is a student exercise placeholder. It should provide `get_db()`, `init_db()`, and `seed_db()` using SQLite with `row_factory` and foreign keys enabled.

**JavaScript:** `static/js/main.js` is a blank file for students to add feature JS. Page-specific JS goes in `{% block scripts %}` in the relevant template (e.g., the video modal in `landing.html`).

**Routes:**

| Path | Function | Status |
|------|----------|--------|
| `/` | `landing` | Done |
| `/register` | `register` | Template done, logic pending |
| `/login` | `login` | Template done, logic pending |
| `/terms` | `terms` | Done |
| `/privacy` | `privacy` | Done |
| `/logout` | `logout` | Placeholder |
| `/profile` | `profile` | Placeholder |
| `/expenses/add` | `add_expense` | Placeholder |
| `/expenses/<id>/edit` | `edit_expense` | Placeholder |
| `/expenses/<id>/delete` | `delete_expense` | Placeholder |

## Git

Remote: https://github.com/dmourghen/expensetracket.git

PowerShell multiline commit messages require here-string syntax (not bash heredoc):

```powershell
git commit -m @'
Your commit message here.
'@
```
