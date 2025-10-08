# WARP.md

Project operating rules for Warp/Agent Mode in this repository. These rules override personal defaults when working in this project.

Project summary
- Stack: Django 5.2 (Python), project: `bookshop`, app: `book_shop_here`
- Dependencies: managed via `pyproject.toml` and `uv` (creates/uses `.venv`)
- Env/config: `.env` at repo root via `django-environ`; DB via `dj-database-url` (SQLite by default, PostgreSQL supported)
- Auth/permissions: Django auth + GroupProfile metadata; views enforce permissions (CRUD + custom report permissions)
- CI: GitHub Actions installs `uv`, lints with Ruff, type-checks with mypy, then runs Django tests

Shell and tooling defaults
- Primary shell: bash. On Windows, use Git Bash (required for `just` recipes).
- PowerShell: supported for quick commands; when invoking executables use PowerShell’s call operator `&`.
- Git: avoid pagers. Use `--no-pager` on commands that could page (e.g., `git --no-pager log -n 10`).

Environment and secrets
- `.env` lives at the repo root (next to `manage.py`). Required keys for local dev:
  - SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL
- Prefer setting secrets without printing them to the terminal:
  - Use `just secret-key-set` to write a generated SECRET_KEY into `.env` silently.
  - Avoid echoing or logging secret values. If a command requires a secret, refer to it as an environment variable (e.g., `$SECRET_KEY`) and do not print it.

Dependency and environment management
- Install `uv` (bash): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Create/sync venv and install all deps (incl. dev): `just sync`
- Run arbitrary Django management: `just manage <args>`
- PowerShell alternatives (when needed): `& .\.venv\Scripts\python.exe manage.py <args>`

Run and database
- Migrations: `just makemigrations` then `just migrate`
- Dev server: `just run` (visits http://127.0.0.1:8000/)
- DB defaults to SQLite via `DATABASE_URL=sqlite:///db.sqlite3`; override for PostgreSQL in `.env` if needed

Testing (Django test runner)
- Standard: `just test` (uses `uv run python manage.py test`)
- Scope:
  - Single file: `just test-file book_shop_here/tests/test_models.py`
  - Specific modules: `just test-views`, `just test-forms`, `just test-models`
- PowerShell direct (when needed): `& .\.venv\Scripts\python.exe manage.py test -v 2`

Quality (lint/format/types)
- Lint: `just lint` (Ruff)
- Format: `just format` (Ruff)
- Type check: `just typecheck` (mypy + django-stubs)
- Quick sweep: `just quick` (format + lint + mypy)

Frontend helpers
- Tailwind watch/build: `just tailwind-watch`, `just tailwind-build`

Git hooks
- Python hooks: `just pre-commit-install`
- Node/Husky hooks: `just husky-install` (requires Node via nvm)

Architecture overview
- Project layout
  - `bookshop/`: settings, urls, wsgi, asgi (settings read `.env`, DB from `DATABASE_URL`, crispy-tailwind enabled)
  - `book_shop_here/`: models, forms, urls, tests, utils, views, templates, static, migrations
- Views are modular (split by domain) under `book_shop_here/views/`:
  - `base.py`: `HomeView`, `DocsView`
  - `books.py`, `authors.py`, `orders.py`, `customers.py`, `employees.py`, `groups.py`: CRUD views
  - `reports.py`: `SalesDashboardView` (perm: `book_shop_here.view_sales_reports`), `EmployeeSalesView` (perm: `book_shop_here.view_employee_sales`)
- URLs import modules explicitly (see `book_shop_here/urls.py`): `from .views import base as views_base`, etc.
- Models at a glance:
  - `GroupProfile` (one-to-one with `Group`, description)
  - `Employee` linked to `User` with helpers: `_generate_username`, `create_with_user`, `sync_user`, `set_password`
  - `Book` has `rating` choices, optional `condition_notes`, `legacy_id`
  - `Order` tracks status, payment, books; tests assert auto-calculation and completion behavior

Permissions and roles
- Standard Django model perms are used (view/add/change/delete).
- Custom report perms (migration 0004) on the `Order` content type:
  - `book_shop_here.view_sales_reports` — store-wide sales dashboard
  - `book_shop_here.view_employee_sales` — individual employee sales
- Role pages (Groups) expose an additional permissions matrix; ensure these codenames appear and are assigned appropriately.

Coding conventions
- When adding features:
  - Place new views in the appropriate module under `book_shop_here/views/` and wire them in `book_shop_here/urls.py`.
  - Add templates under `book_shop_here/templates/book_shop_here/` with consistent naming (list/form/detail/delete_confirm).
  - Extend forms in `book_shop_here/forms.py` and keep validation pragmatic with clear error messages.
- Searching: `book_shop_here/utils/search.py` provides `build_advanced_search`; reuse it for consistent search behavior and normalization.

Testing rules (always apply)
1) Create new tests for new features or behaviors; update or delete tests when removing or changing features.
2) After significant code changes, run relevant tests (or all) to ensure nothing regresses.
3) Favor deterministic, fast tests; for templates, assert against stable markers (IDs/roles/semantic classes) instead of brittle fragments.

Windows notes
- `just` uses Git Bash on Windows (configured via `windows-shell`); run `just` from Git Bash for best results.
- In PowerShell, avoid `&&`. Use separate commands or the call operator `&`. Example test run:
  - `& .\.venv\Scripts\python.exe manage.py test -v 2`

Troubleshooting
- `uv: command not found`: install `uv` (see above) and ensure shell PATH is refreshed.
- Missing `.env`: run `just env-copy` or `just secret-key-set`.
- Execution policy issues (PowerShell): prefer Git Bash or adjust policy if necessary.

Precedence
- These project rules supersede personal rules when they conflict (e.g., shell choice). Prefer Git Bash here because `just` recipes are bash-centric.
