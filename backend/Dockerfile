# Render deploy image (SPEC.md §12) — the FastAPI API service. Distinct
# from drift-worker/Dockerfile (the sandboxed drift-check image, which
# this service does NOT run — see HANDOFF.md's Phase 2 entry on why a
# standard Render web service has no Docker daemon to run that sandbox
# with, and what running it for real on Render would still need).
FROM python:3.12-slim

# git: app/resolve/clone.py shells out to the real `git clone` (SPEC.md
# §7.3) — this is the one system dependency the API process itself needs.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 loom
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir -e .
RUN chown -R loom:loom /app
USER loom

# Render sets $PORT; uvicorn must bind to it, not a hardcoded value.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
