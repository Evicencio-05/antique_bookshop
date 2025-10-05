# Use PowerShell for Windows users by default
set shell := ["powershell.exe", "-NoProfile", "-Command"]

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
    uv run python manage.py test book_shop_here.tests --pattern="test_*.py"

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
    uv run python manage.py test book_shop_here.tests --pattern="test_*.py"

# Generate a Django SECRET_KEY (robust across shells)
# Uses Python's secrets module to avoid quoting issues and Django import dependency.
secret-key:
    if (Get-Command uv -ErrorAction SilentlyContinue) { uv run python -c "import secrets; print(secrets.token_urlsafe(50))" } else { python -c "import secrets; print(secrets.token_urlsafe(50))" }

# Generate and set SECRET_KEY in .env (creates .env from template if missing)
secret-key-set:
    $envPath = ".env"; if (-not (Test-Path $envPath)) { if (Test-Path ".env.template") { Copy-Item ".env.template" $envPath } else { New-Item -Path $envPath -ItemType File -Force | Out-Null } }; $k = (& { if (Get-Command uv -ErrorAction SilentlyContinue) { uv run python -c "import secrets; print(secrets.token_urlsafe(50))" } else { python -c "import secrets; print(secrets.token_urlsafe(50))" } }).Trim(); $lines = Get-Content $envPath -ErrorAction SilentlyContinue; if (-not $lines) { $lines = @() }; $updated = $false; $newLines = foreach ($line in $lines) { if ($line -match '^\s*SECRET_KEY\s*=') { $updated = $true; "SECRET_KEY=$k" } else { $line } }; if (-not $updated) { $newLines += "SECRET_KEY=$k" }; Set-Content -Path $envPath -Value $newLines; Write-Output "Updated SECRET_KEY in .env"

# Check local env for CI-required secrets and fail fast if missing
ci-secrets:
    $envPath = ".env"; if (-not (Test-Path $envPath)) { Write-Error "Missing .env. Run 'just env-copy' or 'just secret-key-set'."; exit 1 }; $content = Get-Content $envPath -Raw -ErrorAction SilentlyContinue; if ($null -eq $content -or ($content -notmatch '(?m)^\s*SECRET_KEY\s*=\s*\S+')) { Write-Error "SECRET_KEY missing or empty in .env. Run 'just secret-key-set'."; exit 1 } else { Write-Output "OK: SECRET_KEY present in .env" }; if ($content -match '(?m)^\s*DATABASE_URL\s*=\s*\S+') { Write-Output "Info: DATABASE_URL is set in .env" } else { Write-Output "Info: DATABASE_URL not set; SQLite default will be used unless overridden." }

# Strict variant: fail if any required secret is missing
ci-secrets-strict:
    $envPath = ".env"; if (-not (Test-Path $envPath)) { Write-Error "Missing .env. Run 'just env-copy' or 'just secret-key-set'."; exit 1 }; $content = Get-Content $envPath -Raw -ErrorAction SilentlyContinue; $ok = $true; if ($null -eq $content -or ($content -notmatch '(?m)^\s*SECRET_KEY\s*=\s*\S+')) { Write-Error "SECRET_KEY missing or empty in .env."; $ok = $false } if ($null -eq $content -or ($content -notmatch '(?m)^\s*DATABASE_URL\s*=\s*\S+')) { Write-Error "DATABASE_URL missing in .env (set it or use SQLite default explicitly)."; $ok = $false } if (-not $ok) { Write-Error "One or more required settings are missing."; exit 1 } else { Write-Output "OK: Required settings present." }

# Report variant: print which variables are set (no values), never fail
ci-secrets-report:
    $envPath = ".env"; if (Test-Path $envPath) { Write-Output "Env file: FOUND (.env)" } else { Write-Output "Env file: MISSING (.env)" }; $content = if (Test-Path $envPath) { Get-Content $envPath -Raw -ErrorAction SilentlyContinue } else { "" }; $hasSecret = [bool]($content -match '(?m)^\s*SECRET_KEY\s*=\s*\S+'); $hasDb = [bool]($content -match '(?m)^\s*DATABASE_URL\s*=\s*\S+'); Write-Output ("SECRET_KEY: " + ($(if ($hasSecret) {"SET"} else {"MISSING"}))); Write-Output ("DATABASE_URL: " + ($(if ($hasDb) {"SET"} else {"MISSING (SQLite default)"})))
