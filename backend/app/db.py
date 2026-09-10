"""Engine/session setup. Sync SQLAlchemy on purpose — routes are sync `def`s
(FastAPI runs those in its own threadpool) and the scan job is a
`BackgroundTasks` function, also thread-run; nothing here needs an async
driver, and a sync session is one less moving part than async SQLAlchemy
for a tool that isn't high-concurrency (SPEC.md §7.5)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
