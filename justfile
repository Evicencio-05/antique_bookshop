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

# Generate a Django SECRET_KEY (bash)
# Uses Python's secrets module to avoid quoting issues and Django import dependency.
secret-key:
    k="$$(if command -v uv >/dev/null 2>&1; then uv run python -c 'import secrets; print(secrets.token_urlsafe(50))'; else python -c 'import secrets; print(secrets.token_urlsafe(50))'; fi)"; \
    echo "$$k"

# Generate and set SECRET_KEY in .env (creates .env from template if missing)
secret-key-set:
    if [ ! -f .env ]; then \
        if [ -f .env.template ]; then cp .env.template .env; else : > .env; fi; \
    fi; \
    k="$$(if command -v uv >/dev/null 2>&1; then uv run python -c 'import secrets; print(secrets.token_urlsafe(50))'; else python -c 'import secrets; print(secrets.token_urlsafe(50))'; fi)"; \
    tmp="$$(mktemp)"; \
    awk -v k="$$k" 'BEGIN{updated=0} /^[[:space:]]*SECRET_KEY[[:space:]]*=/ {print "SECRET_KEY="k; updated=1; next} {print} END{ if(!updated) print "SECRET_KEY="k }' .env > "$$tmp" && mv "$$tmp" .env; \
    echo "Updated SECRET_KEY in .env"

# Check local env for CI-required secrets and fail fast if missing
ci-secrets:
    if [ ! -f .env ]; then echo "Missing .env. Run 'just env-copy' or 'just secret-key-set'." >&2; exit 1; fi; \
    if grep -Eq '^[[:space:]]*SECRET_KEY[[:space:]]*=[[:space:]]*[^[:space:]]+' .env; then \
        echo "OK: SECRET_KEY present in .env"; \
    else \
        echo "SECRET_KEY missing or empty in .env. Run 'just secret-key-set'." >&2; exit 1; \
    fi; \
    if grep -Eq '^[[:space:]]*DATABASE_URL[[:space:]]*=' .env; then \
        echo "Info: DATABASE_URL is set in .env"; \
    else \
        echo "Info: DATABASE_URL not set; SQLite default will be used unless overridden."; \
    fi

# Strict variant: fail if any required secret is missing
ci-secrets-strict:
    if [ ! -f .env ]; then echo "Missing .env. Run 'just env-copy' or 'just secret-key-set'." >&2; exit 1; fi; \
    ok=1; \
    grep -Eq '^[[:space:]]*SECRET_KEY[[:space:]]*=[[:space:]]*[^[:space:]]+' .env || { echo "SECRET_KEY missing or empty in .env." >&2; ok=0; }; \
    grep -Eq '^[[:space:]]*DATABASE_URL[[:space:]]*=[[:space:]]*[^[:space:]]+' .env || { echo "DATABASE_URL missing in .env (set it or use SQLite default explicitly)." >&2; ok=0; }; \
    [ "$$ok" -eq 1 ] && echo "OK: Required settings present." || { echo "One or more required settings are missing." >&2; exit 1; }

# Report variant: print which variables are set (no values), never fail
ci-secrets-report:
    if [ -f .env ]; then echo "Env file: FOUND (.env)"; else echo "Env file: MISSING (.env)"; fi; \
    content="$$( [ -f .env ] && cat .env || echo "" )"; \
    if echo "$$content" | grep -Eq '^[[:space:]]*SECRET_KEY[[:space:]]*='; then s="SET"; else s="MISSING"; fi; \
    if echo "$$content" | grep -Eq '^[[:space:]]*DATABASE_URL[[:space:]]*='; then d="SET"; else d="MISSING (SQLite default)"; fi; \
    echo "SECRET_KEY: $$s"; \
    echo "DATABASE_URL: $$d"
