# Antique Bookshop

A Django-based web inventory management system for a bookstore to centralize and digitize records for books, employees, authors, customers, and orders. The system utilizes a relational database to store all data, allowing for efficient tracking of both current and historical inventory. CRUD operations for books, authors, customers, and employee information will be restricted to the Owner and Assistant Manager. All employees will have read-only access to books, authors, and customers, with full CRUD access to orders for streamlined sales processing.

**Note: This is a school project and not meant to be used for real-world use.**

---

## Table of Contents

- [Overview](#overview)
- [Quickstart](#quickstart)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Run](#run)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Common Tasks](#common-tasks#git-hooks)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

- Backend: Django 5
- App: `book_shop_here`
- Project: `bookshop`
- Frontend tooling: Tailwind CSS (via npm)
- Tooling: `uv` for Python env and commands, Ruff for lint/format, mypy for types, pre-commit + Husky for hooks

This repo follows a modern Python project layout with a single source of truth for dependencies in `pyproject.toml`, fast environment setup via `uv`, and opinionated linting/typing for code quality.

---

## Quickstart

### Prerequisites

- Python 3.10+
- [nvm](https://github.com/coreybutler/nvm-windows#readme) (for Node.js and npm)
  - [Install guide (freecodecamp.org)](https://www.freecodecamp.org/news/node-version-manager-nvm-install-guide/)
- [Git](https://git-scm.com/downloads)

Install `uv`:

- Bash (Git Bash/macOS/Linux):

  ```
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- PowerShell (alternative; only if you must use PowerShell):

  ```
  iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex
  ```

Install Node (optional, for Tailwind):

- macOS/Linux (nvm):

  ```
  nvm install --lts && nvm use --lts
  ```

- Windows (nvm-windows; works from Git Bash too):

  ```
  nvm install lts
  nvm use lts
  ```

### Setup

Clone and enter the project directory, then create your environment file and install dependencies:

- Bash (recommended):

  ```
  cp .env.template .env
  uv sync --all-extras
  ```

- PowerShell (alternative):

  ```
  just env-copy
  just sync
  ```

### Run

Apply migrations and start the server:

- Either shell:

  ```
  just migrate
  just run
  ```

Visit <http://127.0.0.1:8000/> and log in with your superuser once created.

---


## Configuration

Create a `.env` at the repository root. Use `.env.template` as a starting point.

Required for local dev (safe defaults provided in the template):

- `DEBUG=True`
- `SECRET_KEY=...` (use a unique, random value locally)
- `ALLOWED_HOSTS=localhost,127.0.0.1`
- `DATABASE_URL=sqlite:///db.sqlite3` (default local DB)

Optional:

- `DJANGO_SECRET_KEY` — used by CI only; do not reuse your local `SECRET_KEY`
- `CSRF_TRUSTED_ORIGINS` — if using custom hostnames during local dev
- `EMAIL_BACKEND` — e.g., console backend for local testing

For PostgreSQL, set:

```
DATABASE_URL=postgres://user:password@host:5432/dbname
```

---

## Common Tasks

This project uses a `justfile` with bash (Git Bash on Windows is recommended). PowerShell-only alternatives are explicitly marked:

- Environment & dependencies
  - `just uv-install-bash` — install `uv` (bash)
  - `just sync` — create/update `.venv` and install dependencies (incl. dev extras)
  - `just env-copy` — copy `.env.template` to `.env`
- Django
  - `just migrate` — apply migrations
  - `just run` — start the dev server
  - `just manage <command>` — run any `manage.py` command
- Quality
  - `just lint` — Ruff lint (errors, imports, Django, bugbear, simplify, security, pyupgrade)
  - `just format` — Ruff format
  - `just typecheck` — mypy with Django stubs
- Tests
  - `just test` — run Django tests
- Frontend
  - `just tailwind-watch` — rebuild CSS on changes
  - `just tailwind-build` — one-time minified build
- Hooks
  - `just pre-commit-install` — enable Python pre-commit hooks
  - `just husky-install` — install Node hooks (Husky)

---

## Git Hooks

- Python hooks (pre-commit):
  - Install: `just pre-commit-install`
  - Hooks run Ruff and basic hygiene checks before commits.
- Husky (Node-based hooks):
  - Install Node via NVM, then run: `just husky-install` (executes `npm install` and activates Husky via `prepare` script)
  - The `.husky/pre-commit` hook calls `uv run pre-commit` so Python checks run consistently.

---

## Continuous Integration

- Workflow: `.github/workflows/django.yml`
  - Installs `uv`
  - `uv sync` to install from `pyproject.toml`
  - Lints with Ruff
  - Type-checks with mypy (auto-installs types)
  - Runs Django tests
- Required secrets (configure in repository settings):
  - `DJANGO_SECRET_KEY`
  - Optional: `DJANGO_DATABASE_URL` if you need a non-default DB in CI

---

## Troubleshooting

- `uv: command not found`
  - Install `uv` (see Quickstart) and ensure your shell picks up the installed path.
- Windows execution policy blocks scripts
  - If you use PowerShell: start it as Administrator and adjust policy if needed. Prefer Git Bash to avoid execution policy issues.
- `SECRET_KEY` errors on startup
  - Ensure `.env` exists with a non-empty `SECRET_KEY`.
- Migrations or DB issues
  - For local SQLite: delete `db.sqlite3` (if acceptable) and rerun `just migrate`.
  - For Postgres: verify `DATABASE_URL` is correct and the DB is reachable.
- Use the following command to install Just via bash. (No nvm download)  
  ```curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin```

---

## License

Proprietary (see `pyproject.toml`).
