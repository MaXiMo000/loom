"""Real disposable-Postgres discipline (this portfolio's own convention —
see recur/LabLedger's test setup): tests that touch the DB run against a
real local Postgres (DATABASE_URL, defaulting to the same instance
app/config.py points dev at), not sqlite or a mock. Tables are created
once and truncated between tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text

from app.db import engine
from app.models import Base

DRIFT_WORKER_DIR = Path(__file__).parent.parent / "drift-worker"
DRIFT_IMAGE = "loom-drift-worker:local"


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(engine)
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE scan, node, edge RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="session")
def drift_image():
    """Explicit, order-independent: any test that needs the real drift
    sandbox image depends on this fixture by name rather than relying on
    another test module happening to build it first. Skipped (not failed)
    when Docker itself isn't available."""
    if shutil.which("docker") is None:
        pytest.skip("Docker not available")
    subprocess.run(["docker", "build", "-t", DRIFT_IMAGE, str(DRIFT_WORKER_DIR)], check=True, capture_output=True)
    return DRIFT_IMAGE
