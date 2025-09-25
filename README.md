# Book Shop Here

This is a Django-based web application for managing an antique bookstore. It includes features for handling books, authors, customers, orders, roles, and employees, with authentication, permissions, and an admin interface.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation and Setup](#installation-and-setup)
- [Additional Notes](#additional-information)

## Features

- **Book Management:** Add, edit, and delete books and authors.
- **User Management:** Secure user authentication with different roles (e.g., employee, customer).
- **Admin Interface:** Full access to all models for authorized users via the Django Admin.

## Requirements

- [**Python 3.10+**](https://www.python.org/downloads/) (recommended)
- Virtual environment tool (e.g., `venv` or `virtualenv`)
- [**Docker**](https://www.docker.com/get-started) (optional, for running PostgreSQL)

## Installation and Setup

### 1. Clone the Repository
Clone the project to your local machine:
```bash
git clone https://github.com/Evicencio-05/antique_bookshop
cd antique_bookshop
```

### 2. Set Up a Virtual Environment
Create and activate a virtual environment to isolate dependencies:

#### Create
```
# For Linux/macOS
python3 -m venv .venv

# For Windows
python -m venv .venv
```

#### Activate
```
# For Command Prompt 
venv\Scripts\activate.bat

# For PowerShell
.\venv\Scripts\Activate.ps1

# For Git Bash or WSL 
source venv/Scripts/activate
```
**Note: Deactivate using `deactivate`**

### 3. Install Dependencies 
Install the required packages from the requirements.txt file.
```
pip install -r requirements.txt
```

This includes:
- `Django`: The web framework.
- `django-extensions`: For additional management commands (e.g., `shell_plus`).
- `django-environ`: For loading environment variables from a `.env` file.
- `psycopg2-binary`: Binary PostgreSQL adapter (for production database support).
- `dj-database-url`: Simplify the configuration of database connections in Django applications.

### 4. Configure Environment Variables

Create a `.env` file in the project root (next to `manage.py`) and add the following: 

**File:** `.env`
```txt
# --- General Settings ---
DEBUG=True
SECRET_KEY='your-secret-key-here'
ALLOWED_HOSTS=localhost,127.0.0.1

# --- Database Configuration ---
# To use SQLite (default for development), use this line:
DATABASE_URL=sqlite:///db.sqlite3

# To use PostgreSQL (recommended for production), comment out the line above
# and uncomment this one, filling in your details:
# DATABASE_URL=postgres://user:password@host:port/dbname
```
**Note:** A unique `SECRET_KEY` is crucial for security. Generate one with this command: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`

### 5. Database Setup

By default, Django uses SQLite (no separate installation needed), which is ideal for local development. For production or advanced use, PostgreSQL is recommended (via `psycopg2-binary`).

#### For SQLite (Default)

The `DATABASE_URL` for SQLite is already configured. Simply run the migrations:

```
python manage.py makemigrations
python manage.py migrate
```

#### For PostgreSQL (Via Docker)

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
``` docker-compose up -d```

4. Run the migrations:

```
python manage.py makemigrations
python manage.py migrate
``` 
  **Note: Stop the container with `docker-compose down` when done. Data persists via the volume.**

### 6. Create a Superuser

Create an admin account to access the Django admin panel:

```
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 7. Run the Development Server

Start the local server:
```
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser (A link is also provided in the terminal). The login page should appear and log in using you super user credentials.

## Additional Information

- **Admin Panel:** Access the admin interface at /admin/ after logging in with your superuser credentials.

- **Troubleshooting:** If you encounter a SECRET_KEY error, ensure you have correctly set up your .env file and that the SECRET_KEY is not empty.

- **Production Deployment:** For production environments, it is essential to set DEBUG=False and use a production-grade database like PostgreSQL.

