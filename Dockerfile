# Builder stage
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

    
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

# Runner Stage
FROM python:3.10-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/node_modules /app/node_modules

ENV PATH="/app/.venv/bin:${PATH}"

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && chown appuser:appuser /app/entrypoint.sh

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/staticfiles /app/media

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "bookshop.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
