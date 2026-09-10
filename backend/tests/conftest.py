"""Real disposable-Postgres discipline (this portfolio's own convention —
see recur/LabLedger's test setup): tests that touch the DB run against a
real local Postgres (DATABASE_URL, defaulting to the same instance
app/config.py points dev at), not sqlite or a mock. Tables are created
once and truncated between tests."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.db import engine
from app.models import Base


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(engine)
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE scan, node, edge RESTART IDENTITY CASCADE"))
