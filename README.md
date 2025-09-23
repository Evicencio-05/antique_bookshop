# Book Shop Here

This is a Django-based web application for managing an antique bookstore. It includes features for handling books, authors, customers, orders, roles, and employees, with authentication, permissions, and an admin interface.

## Requirements

- Python 3.10+ (recommended)
- Virtual environment tool (e.g., `venv` or `virtualenv`)
- Docker (optional, for running PostgreSQL without a local installation)

## Installation and Setup

### 1. Clone the Repository
Clone the project to your local machine:
```bash
git clone https://github.com/Evicencio-05/antique_bookshop
cd antique_bookshop
```

### 2. Set Up a Virtual Environment
Create and activate a virtual environment to isolate dependencies:
```bash
python -m venv venv

# For Windows
.\venv\Scripts\activate

# For Linux/MacOS
source venv/bin/activate

pip install -r requirements.txt
```

This includes:
- `Django`: The web framework.
- `django-extensions`: For additional management commands (e.g., `shell_plus`).
- `python-dotenv`: For loading environment variables from a `.env` file.
- `psycopg2-binary`: Binary PostgreSQL adapter (for production database support).

### 4. Configure Environment Variables
Create a `.env` file in the project root (next to `manage.py`) and add the following:
```txt
SECRET_KEY=your-secret-key-here  # Generate a secure key (e.g., using django.core.management.utils.get_random_secret_key())
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1  # Comma-separated list; add your domain in production
```

For database configuration, see the next section.

### 5. Database Setup
By default, Django uses SQLite (no separate installation needed), which is ideal for local development. For production or advanced use, PostgreSQL is recommended (via `psycopg2-binary`).

#### Option 1: Use SQLite (No Separate Database Installation Required)

- In your project's `settings.py`, ensure the `DATABASES` setting is configured for SQLite (default behavior if not overridden):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

No additional setup needed—proceed to migrations.

#### Option 2: Use PostgreSQL Without Installing It Locally (Via Docker)
To avoid installing PostgreSQL on your machine, use Docker to run a PostgreSQL container. This is possible and recommended for development/testing.

1. Install Docker if not already (download from [docker.com](https://www.docker.com/)).
2. Create a `docker-compose.yml` file in the project root:

```yml
version: '3.8'

services:
  db:
    image: postgres:16  # Latest stable PostgreSQL version
    restart: always
    environment:
      POSTGRES_DB: bookshopdb
      POSTGRES_USER: bookshopuser
      POSTGRES_PASSWORD: yoursecurepassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

3. Start the PostgreSQL container:
    - docker-compose up -d

4. Update your `.env` file with the PostgreSQL credentials:
```
    DATABASE_ENGINE=django.db.backends.postgresql  
    DATABASE_NAME=bookshopdb  
    DATABASE_USER=bookshopuser  
    DATABASE_PASSWORD=yoursecurepassword  
    DATABASE_HOST=localhost  
    DATABASE_PORT=5432  
```

5. In `settings.py`, configure `DATABASES` to load from environment variables (using `dotenv` implicitly via `os.environ`):

```python
import os
from pathlib import Path

# ... (other settings)

# Load .env if not in production
if os.environ.get('DEBUG') == 'True':
    from dotenv import load_dotenv
    load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DATABASE_USER', ''),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('DATABASE_HOST', ''),
        'PORT': os.environ.get('DATABASE_PORT', ''),
    }
}
```
 * This allows switching between SQLite and PostgreSQL via .env.  
    **Note: Stop the container with `docker-compose down` when done. Data persists via the volume.**

### 6. Apply Migrations

Run database migrations to create the schema:
```
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a Superuser

Create an admin account to access the Django admin panel:

```
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 8. Run the Development Server

Start the local server:
```
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser. The home page should appear. Log in at `/login/` using your superuser credentials.

## Additional Notes

- **Admin Access**: Go to `/admin/` after logging in to manage models (books, authors, etc.).
- **Permissions and Employees**: The app links Employees to Users via signals. Create Employees in the admin; they auto-assign to groups based on Role.
- **Production Deployment**: For production, set `DEBUG=False`, use a WSGI server (e.g., Gunicorn), and host PostgreSQL on a cloud service (e.g., AWS RDS) instead of Docker. Consider adding `whitenoise` for static files.
- **Troubleshooting**: If migrations fail, check validators/constraints in models.py. Ensure Docker is running for PostgreSQL.
- **Testing**: Run tests with python manage.py test.

If you encounter issues, check Django logs or consult the [Django documentation](https://docs.djangoproject.com/en/5.2/).