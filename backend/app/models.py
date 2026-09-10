"""SQLAlchemy models — scan/node/edge, matching SPEC.md §7.6 exactly."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Scan(Base):
    __tablename__ = "scan"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    repo_url: Mapped[str] = mapped_column(Text)
    ref: Mapped[str] = mapped_column(String, default="HEAD")
    commit_sha: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    # pending | cloning | resolving | scanning | complete | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    lockfile_kind: Mapped[str | None] = mapped_column(String, nullable=True)
    depth_cap: Mapped[int] = mapped_column(Integer, default=3)
    total_package_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    nodes: Mapped[list["Node"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    edges: Mapped[list["Edge"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "node"
    __table_args__ = (UniqueConstraint("scan_id", "package_name", name="uq_node_scan_package"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scan.id"))
    package_name: Mapped[str] = mapped_column(String)
    package_version: Mapped[str] = mapped_column(String)
    depth: Mapped[int] = mapped_column(Integer)
    vuln_severity: Mapped[str] = mapped_column(String, default="unverified")
    vuln_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    drift_status: Mapped[str] = mapped_column(String, default="unverified")
    # Not in SPEC.md §7.6's original table (only vuln_detail is) — added to
    # match it exactly, once Phase 2 gave drift a real per-package "receipt,
    # not a claim" (lockstep's own detail string) worth keeping, the same
    # reason vuln_detail exists at all.
    drift_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    providence_status: Mapped[str] = mapped_column(String, default="unverified")
    policy_status: Mapped[str] = mapped_column(String, default="unverified")
    repo_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repo_last_commit: Mapped[datetime | None] = mapped_column(nullable=True)

    scan: Mapped[Scan] = relationship(back_populates="nodes")


class Edge(Base):
    __tablename__ = "edge"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    scan_id: Mapped[str] = mapped_column(ForeignKey("scan.id"))
    from_node: Mapped[str] = mapped_column(ForeignKey("node.id"))
    to_node: Mapped[str] = mapped_column(ForeignKey("node.id"))

    scan: Mapped[Scan] = relationship(back_populates="edges")
