FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder
# Builder stage

ENV PYTHONUNBUFFERED=1 \
    PYTHONWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY README.md ./

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

RUN npm run build

RUN python manage.py collectstatic --noinput

# Runner Stage
FROM python:3.10-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/node_modules /app/node_modules
# Include collected static files from the builder so CSS/JS are available in the runtime image
COPY --from=builder --chown=appuser:appuser /app/staticfiles /app/staticfiles

COPY --chown=appuser:appuser . .

COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R appuser:appuser /app/staticfiles /app/media /app/logs

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "bookshop.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--reload"]
