# ==========================================
#                 Builder
# ==========================================
FROM python:3.14-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ==========================================
#                  Runner
# ==========================================
FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN groupadd -r appgroup && useradd -r -g appgroup -m -s /bin/bash appuser
RUN chown appuser:appgroup /app

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY --chown=appuser:appgroup src/ ./src/

COPY --chown=appuser:appgroup docker-compose.prod.yml ./docker-compose.prod.yml
# COPY --chown=appuser:appgroup .env.example ./.env.example

USER appuser

CMD ["python", "src/main.py"]
