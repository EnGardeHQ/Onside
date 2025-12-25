FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

FROM python:3.11-slim-bookworm AS production
LABEL org.opencontainers.image.title="OnSide API"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app PATH="/opt/venv/bin:$PATH"
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 1000 onside && useradd --uid 1000 --gid onside --shell /bin/bash --create-home onside
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY --chown=onside:onside src/ ./src/
COPY --chown=onside:onside alembic/ ./alembic/
COPY --chown=onside:onside alembic.ini ./
COPY --chown=onside:onside requirements.txt ./
RUN mkdir -p /app/logs /app/exports && chown -R onside:onside /app
USER onside
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

FROM production AS development
USER root
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov httpx black flake8 mypy
USER onside
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
