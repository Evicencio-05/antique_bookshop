"""
Render-specific Django settings override
"""

import os

import dj_database_url

# ruff: noqa: F403,F405
from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
# The SECRET_KEY will be set as an environment variable on Render
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Update ALLOWED_HOSTS to include Render's provided hostname
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "antique-bookshop.onrender.com", ".onrender.com"]

# Database configuration for Render PostgreSQL
if "DATABASE_URL" in os.environ:
    DATABASES = {"default": dj_database_url.parse(os.environ.get("DATABASE_URL"))}
else:
    # Fallback to SQLite for testing without Render
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Serve static files with WhiteNoise (required for Render)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# Static files configuration for Render
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Django 5.2 security settings
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_REFERRER_POLICY = "same-origin"
