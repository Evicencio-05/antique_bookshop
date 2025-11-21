FROM python:3.10-alpine AS builder

ENV PYTHONUNBUFFERED=1 \
    USER_ID=1000 \
    GROUP_ID=1000

RUN apk add --no-cache curl gcc musl-dev libc-dev

RUN curl -LsSL https://astral.sh/uv/instrall.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

COPY ruff.toml .pre-commit-config.yaml ./

RUN uv env --system && uv sync --all-extras

FROM python:3.10-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=bookshop.settings \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}"

RUN adduser --system --no-create-home appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . /app

RUN mkdir -p /app/db/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["/bin/sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn bookshop.wsgi:application --bind 0.0.0.0:8000"]