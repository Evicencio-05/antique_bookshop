# Use Git Bash for Windows users explicitly to avoid invoking WSL's bash.exe
# If your Git is installed in a non-default location, set GIT_BASH env var
# to the full path of bash.exe before running `just`.
set windows-shell := ["C:/Program Files/Git/usr/bin/bash.exe", "-c"]
# set shell := ["powershell.exe", "-NoProfile", "-Command"]

# Ensure git works in recipes
hello:
    echo "Hello from just!"

# Default task shows available recipes
default:
    @just --list

# Install uv using PowerShell (invokes powershell.exe explicitly)
uv-install-pwsh:
    powershell.exe -NoProfile -Command "iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex"

# Install uv (bash; Git Bash/macOS/Linux)
uv-install-bash:
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates/updates .venv) including dev extras
sync:
    uv sync --all-extras

# # Activate the virtualenv in the current shell (bash; Git Bash/macOS/Linux)
# activate:
#     if [ -f .venv/Scripts/activate ]; then source .venv/Scripts/activate; elif [ -f .venv/bin/activate ]; then source .venv/bin/activate; else echo "No virtualenv found. Run 'just sync' first."; exit 1; fi

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
    uv run python manage.py test book_shop_here.tests --pattern="test_*.py"

test-ff:
    uv run python manage.py test book_shop_here.tests --pattern="test_*.py" --failfast

# Seed development data
seed:
    uv run python manage.py seed_dev_data

test-file file:
    uv run python manage.py test {{file}} --pattern="test_*.py"

test-views:
    uv run python manage.py test book_shop_here.tests.test_views --pattern="test_*.py"

test-forms:
    uv run python manage.py test book_shop_here.tests.test_forms --pattern="test_*.py"

test-models:
    uv run python manage.py test book_shop_here.tests.test_models --pattern="test_*.py"

# Linting and formatting with Ruff
lint:
    uv run ruff check .

lint-fix:
    uv run ruff check . --fix

quick:
    uv run ruff format .
    uv run ruff check . --fix
    uv run mypy --install-types --non-interactive .

format:
    uv run ruff format .

# Static type checking
typecheck:
    uv run mypy --install-types --non-interactive .

# Tailwind / Frontend helpers
build:
    npm run build

watch:
    npm run watch

watch-independent:
    "assets\css\tailwind.css" -i "book_shop_here\static\book_shop_here\site.css" -o "dist/output.css" --watch

dev:
    npm run dev

# Hooks
pre-commit-install:
    uv run pre-commit install

# Remove and recreate the virtualenv using the Windows/Git Bash context.
venv-reset:
    rm -rf .venv
    uv sync --all-extras

husky-install:
    npm install

# Copy environment template to .env (bash)
env-copy:
    cp -f .env.template .env

# Run the same checks as CI (install deps, lint, type-check, test)
ci:
    uv sync --all-extras
    uv run ruff --version
    uv run ruff check .
    uv run mypy --install-types --non-interactive .
    uv run python manage.py test book_shop_here.tests --pattern="test_*.py"

# Generate a Django SECRET_KEY
secret-key:
    @python -c 'import secrets; print(secrets.token_urlsafe(50))'

# Generate and set SECRET_KEY in .env
secret-key-set:
    #!/usr/bin/env bash
    set -euo pipefail
    # Create .env from template if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.template .env 2>/dev/null || touch .env
    fi
    # Generate new key
    NEW_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
    # Update or append SECRET_KEY
    if grep -q "^SECRET_KEY=" .env; then
        # Key exists, replace it (works on macOS and Linux)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=$NEW_KEY|" .env
        else
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$NEW_KEY|" .env
        fi
    else
        # Key doesn't exist, append it
        echo "SECRET_KEY=$NEW_KEY" >> .env
    fi
    echo "SECRET_KEY updated in .env"

# Check if required secrets exist in .env
ci-secrets:
    #!/usr/bin/env bash
    set -euo pipefail
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "Missing .env file. Run 'just env-copy' or 'just secret-key-set'"
        exit 1
    fi
    # Check SECRET_KEY
    if grep -q "^SECRET_KEY=.\+" .env; then
        echo "SECRET_KEY is set"
    else
        echo "SECRET_KEY is missing or empty. Run 'just secret-key-set'"
        exit 1
    fi
    # Check DATABASE_URL (optional, just info)
    if grep -q "^DATABASE_URL=" .env; then
        echo "DATABASE_URL is set"
    else
        echo "ℹ DATABASE_URL not set (will use SQLite default)"
    fi

# Show status of environment variables (never fails)
secrets-status:
    #!/usr/bin/env bash
    echo "=== Environment Status ==="
    if [ -f .env ]; then
        echo ".env file exists"
    else
        echo ".env file missing"
    fi
    if [ -f .env ] && grep -q "^SECRET_KEY=.\+" .env; then
        echo "SECRET_KEY is set"
    else
        echo "SECRET_KEY is missing or empty"
    fi
    if [ -f .env ] && grep -q "^DATABASE_URL=.\+" .env; then
        echo "DATABASE_URL is set"
    else
        echo "ℹ DATABASE_URL not set (using SQLite)"
    fi
