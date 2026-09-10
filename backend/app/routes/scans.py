"""The four scan endpoints from SPEC.md §7.7 — real Phase 1 behavior: a
real clone, real lockfile parse, real PyPI/OSV/carabiner/providence
signals (SPEC.md §10). Drift and policy stay honestly `unverified`."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import DEPTH_CAP_DEFAULT
from app.db import SessionLocal, get_session
from app.diff import diff_nodes
from app.models import Scan
from app.orchestrator import run_scan

router = APIRouter(prefix="/api/scans", tags=["scans"])


def _scan_to_dict(scan: Scan) -> dict:
    return {
        "id": scan.id,
        "repo_url": scan.repo_url,
        "ref": scan.ref,
        "commit_sha": scan.commit_sha,
        "status": scan.status,
        "error": scan.error,
        "lockfile_kind": scan.lockfile_kind,
        "depth_cap": scan.depth_cap,
        "total_package_count": scan.total_package_count,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "nodes": [
            {
                "id": n.id,
                "package_name": n.package_name,
                "package_version": n.package_version,
                "depth": n.depth,
                "vuln_severity": n.vuln_severity,
                "vuln_detail": n.vuln_detail,
                "drift_status": n.drift_status,
                "drift_detail": n.drift_detail,
                "providence_status": n.providence_status,
                "policy_status": n.policy_status,
                "repo_stars": n.repo_stars,
                "repo_last_commit": n.repo_last_commit.isoformat() if n.repo_last_commit else None,
            }
            for n in scan.nodes
        ],
        "edges": [{"id": e.id, "from_node": e.from_node, "to_node": e.to_node} for e in scan.edges],
    }


@router.post("")
def create_scan(body: dict, background_tasks: BackgroundTasks, session: Session = Depends(get_session)) -> dict:
    repo_url = body.get("repo_url")
    if not repo_url:
        raise HTTPException(status_code=422, detail="repo_url is required")

    scan = Scan(repo_url=repo_url, ref=body.get("ref") or "HEAD", status="pending",
                depth_cap=body.get("depth_cap") or DEPTH_CAP_DEFAULT)
    session.add(scan)
    session.commit()
    session.refresh(scan)

    # SessionLocal, not this request's `session` — the job runs on a
    # BackgroundTasks thread after this response is sent, so it needs its
    # own session rather than sharing one whose request-scoped session may
    # already be closed (app/orchestrator.py's own docstring on why).
    background_tasks.add_task(run_scan, SessionLocal, scan.id)

    return {"id": scan.id, "status": scan.status}


@router.get("/{scan_id}")
def get_scan(scan_id: str, session: Session = Depends(get_session)) -> dict:
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="unknown scan id")
    return _scan_to_dict(scan)


@router.get("")
def list_scans(repo_url: str | None = None, session: Session = Depends(get_session)) -> list[dict]:
    query = session.query(Scan)
    if repo_url:
        query = query.filter(Scan.repo_url == repo_url)
    scans = query.order_by(desc(Scan.created_at)).all()
    return [
        {
            "id": s.id,
            "repo_url": s.repo_url,
            "ref": s.ref,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "node_count": len(s.nodes),
        }
        for s in scans
    ]


@router.get("/{scan_id}/diff/{other_id}")
def diff_scans(scan_id: str, other_id: str, session: Session = Depends(get_session)) -> dict:
    a = session.get(Scan, scan_id)
    b = session.get(Scan, other_id)
    if a is None or b is None:
        raise HTTPException(status_code=404, detail="unknown scan id")
    if a.repo_url != b.repo_url:
        raise HTTPException(status_code=422, detail="both scans must be of the same repo_url")
    if a.status != "complete" or b.status != "complete":
        raise HTTPException(status_code=409, detail="both scans must be complete to diff")

    # "Older"/"newer" by when the scan actually ran, regardless of which
    # id the caller passed as {scan_id} vs {other_id} — "drift over time"
    # (SPEC.md §3) only means something in one direction.
    older, newer = (a, b) if a.created_at <= b.created_at else (b, a)
    changes = diff_nodes(older.nodes, newer.nodes)
    changed_names = {c["package_name"] for c in changes}
    common_names = {n.package_name for n in older.nodes} & {n.package_name for n in newer.nodes}

    return {
        "from_scan": {"id": older.id, "created_at": older.created_at.isoformat()},
        "to_scan": {"id": newer.id, "created_at": newer.created_at.isoformat()},
        "changes": changes,
        "unchanged_count": len(common_names - changed_names),
    }
