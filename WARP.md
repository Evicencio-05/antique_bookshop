# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project summary
- Stack: Django 5.2 (Python), single project (bookshop) with one main app (book_shop_here)
- Env/config: Settings read from a .env at repo root via django-environ; database configured via dj-database-url (SQLite by default; PostgreSQL supported)
- Auth/permissions: Uses Django auth plus django-group-model with a GroupProfile for metadata; CRUD views are permission-gated
- CI: .github/workflows/django.yml installs requirements and runs python manage.py test with SECRET_KEY and DATABASE_URL provided via GitHub Secrets

Common commands
- Environment setup (bash)
  - Install uv
    - curl -LsSf https://astral.sh/uv/install.sh | sh
  - Sync dependencies (creates/updates .venv)
    - uv sync --all-extras
- Database
  - Make migrations
    - uv run python manage.py makemigrations
  - Apply migrations
    - uv run python manage.py migrate
- Run server
  - uv run python manage.py runserver
- Checks
  - Django system checks
    - uv run python manage.py check
- Tests (Django test runner)
  - All tests
    - uv run python manage.py test
  - Single file
    - uv run python manage.py test book_shop_here.tests.test_models
  - Single test case
    - uv run python manage.py test book_shop_here.tests.test_models.BookModelTests
  - Single test method
    - uv run python manage.py test book_shop_here.tests.test_models.BookModelTests.test_book_str

Environment and configuration
- .env lives at repo root (next to manage.py) and should include at minimum:
  - SECRET_KEY
  - DEBUG (True/False)
  - ALLOWED_HOSTS (comma-separated)
  - DATABASE_URL
- Defaults
  - For local dev, DATABASE_URL=sqlite:///db.sqlite3 works out of the box
- CI variables
  - Workflow uses: secrets.DJANGO_SECRET_KEY → SECRET_KEY, secrets.DJANGO_DATABASE_URL → DATABASE_URL

Architecture overview
- Project layout
  - bookshop/ (project): settings.py reads .env, configures dj-database-url, installs django_extensions and the app; template search path includes <repo>/templates and app templates
  - book_shop_here/ (app): domain models, forms, views, urls, migrations, and templates
- Domain model highlights (book_shop_here/models.py)
  - GroupProfile: One-to-one with Group, stores description
  - Employee: Links to auth User and a Group; helpers
    - create_with_user(password, ...): creates a matching User and Employee, assigning group and syncing names/email
    - sync_user(): keeps the linked User in sync (names/email/username/group)
    - _generate_username(): first.last with numeric suffix on collision
    - set_password(): updates linked User password
  - Author, Book, Customer: Basic entities with __str__ helpers; Book has constrained choices and optional legacy_id
  - Order: Many-to-many to Book; save() computes sale_amount from books; completed_order() marks books sold and updates status/date
- Views and routing (book_shop_here/views.py, urls.py)
  - Class-based views for CRUD on Books, Authors, Orders, Groups, Employees, Customers
  - Access control uses LoginRequiredMixin and PermissionRequiredMixin with model-specific codenames (e.g., book_shop_here.add_book)
  - HomeView redirects authenticated users to the book list; BookListView supports query string search (q) across title/legacy_id and filters available books
  - Templates under book_shop_here/templates/ with resource-specific list/form/delete templates and registration/login.html
- Settings of note (bookshop/settings.py)
  - environ.Env.read_env(BASE_DIR/.env)
  - DATABASES['default'] from env.db('DATABASE_URL')
  - INSTALLED_APPS includes django_extensions and book_shop_here
  - LOGIN_REDIRECT_URL='/' and LOGOUT_REDIRECT_URL uses the app's home route

What to reference from README
- Setup sequence: use uv to create the virtualenv and install from pyproject.toml (uv sync)
- .env keys: SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL (SQLite by default)
- Migrations then runserver; superuser created with uv run python manage.py createsuperuser
- Optional PostgreSQL by setting DATABASE_URL

Notes for future agents
- No repo-defined linter (e.g., flake8/pylint) is configured; use python manage.py check for framework-level validation
- Tests rely on Django’s built-in test runner; pytest is not present in requirements
- Permissions are enforced in views; when extending or adding views, ensure appropriate permission codenames are used

Tooling defaults (standardized)
- Shell: bash first. On Windows, use Git Bash. PowerShell is supported only where explicitly noted.
- CI (GitHub Actions): ubuntu-latest uses bash by default; uv is installed via curl | sh; commands run with uv run ...
- Husky: .husky/pre-commit is POSIX sh and calls `uv run pre-commit run --hook-stage pre-commit`; falls back to `pre-commit` if `uv` is unavailable.
- VS Code: .vscode/settings.json sets terminal.integrated.defaultProfile.windows to "Git Bash"; tasks.json forces bash as the shell for tasks. Launch uses the integrated terminal, so it will use Git Bash.
