# Use PowerShell for Windows users by default
set shell := ["cmd.exe", "/c"]

# Default task shows available recipes
default:
    @just --list

# Install uv on Windows PowerShell
uv-install:
    iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex

# Sync dependencies (creates/updates .venv) including dev extras
sync:
    uv sync --all-extras

# Run arbitrary Django manage.py command: just manage migrate
manage *args:
    uv run python manage.py {{args}}

# Common manage shortcuts
migrate:
    uv run python manage.py migrate

makemigrations:
    uv run python manage.py makemigrations

run:
    uv run python manage.py runserver

createsuperuser:
    uv run python manage.py createsuperuser

# Tests
test:
    uv run python manage.py test book_shop_here.tests

# Linting and formatting with Ruff
lint:
    uv run ruff check .

lint-fix:
    uv run ruff check . --fix

format:
    uv run ruff format .

# Static type checking
typecheck:
    uv run mypy --install-types --non-interactive .

# Tailwind / Frontend helpers
tailwind-build:
    npm run build

tailwind-watch:
    npm run watch

dev:
    npm run dev

# Hooks
pre-commit-install:
    uv run pre-commit install

husky-install:
    npm install

# Copy environment template to .env (Windows PowerShell)
env-copy:
    Copy-Item -Path .env.template -Destination .env -Force

# Run the same checks as CI (install deps, lint, type-check, test)
ci:
    uv sync --all-extras
    uv run ruff --version
    uv run ruff check .
    uv run mypy --install-types --non-interactive .
    uv run python manage.py test book_shop_here.tests
