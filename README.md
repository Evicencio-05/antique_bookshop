# Antique Bookshop

A Django-based web inventory management system for a bookstore to centralize and digitize records for books, employees, authors, customers, and orders.

> Note: This is a school project and not intended for real-world production use.

---

## Overview

- Backend: Django 5
- Database: PostgreSQL (via Docker)
- Project: `bookshop`
- App: `book_shop_here`
- Frontend: Tailwind CSS (built at image build time)
- Runtime: Gunicorn + Nginx, all managed with Docker Compose

---

## How to run (Docker + Nginx)

From the project root:

1. Copy and edit the environment file:

   ```bash
   cp .env.template .env
   ```

   In `.env`, set at least:

   ```bash
   SECRET_KEY=your-strong-secret-key
   DEBUG=1
   ALLOWED_HOSTS=localhost,127.0.0.1,app
   DATABASE_URL=postgres://postgres:devpassword@db:5432/bookshop_db
   ```

2. Build and start the stack:

   ```bash
   docker compose up --build
   ```

3. Open the app in your browser:

   ```text
   http://localhost/
   ```

4. Stop everything:

   ```bash
   docker compose down
   ```

---

## Common management commands (Docker)

Run these from the project root while the stack is up:

```bash
# Create a superuser
docker compose exec app python manage.py createsuperuser

# Make new migrations
docker compose exec app python manage.py makemigrations

# Apply migrations
docker compose exec app python manage.py migrate
```

---

## License

Proprietary (see `pyproject.toml`).
