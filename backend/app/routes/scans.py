"""The four scan endpoints from SPEC.md §7.7.

Phase 0: every route returns the one hand-written fixture graph
(app/fixtures.py) — no clone, no real orchestration, no Postgres. Real
persistence and a real background job land in Phase 1 (SPEC.md §10);
the route *shapes* here are the real, final contract so the frontend
built against them today doesn't need to change later.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.fixtures import FIXTURE_SCAN_ID, fixture_scan, fixture_scan_summary

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("")
def create_scan(body: dict) -> dict:
    if not body.get("repo_url"):
        raise HTTPException(status_code=422, detail="repo_url is required")
    # Phase 0 has no orchestrator — hand back the fixture id immediately,
    # already "complete", instead of faking a pending->polling sequence.
    return {"id": FIXTURE_SCAN_ID, "status": "complete"}


@router.get("/{scan_id}")
def get_scan(scan_id: str) -> dict:
    if scan_id != FIXTURE_SCAN_ID:
        raise HTTPException(status_code=404, detail="unknown scan id (Phase 0 only serves the fixture scan)")
    return fixture_scan()


@router.get("")
def list_scans(repo_url: str | None = None) -> list[dict]:
    # Phase 0: one fixture scan exists; real history comes with Phase 1
    # persistence. repo_url is accepted (matches the real contract) but not
    # filtered against yet since there's nothing else to filter out.
    return [fixture_scan_summary()]


@router.get("/{scan_id}/diff/{other_id}")
def diff_scans(scan_id: str, other_id: str) -> dict:
    # Real node-level diffing needs two distinct persisted scans (Phase 3).
    # Phase 0 has exactly one scan to compare against itself, so this is
    # honestly an empty diff, not a fabricated one.
    for sid in (scan_id, other_id):
        if sid != FIXTURE_SCAN_ID:
            raise HTTPException(status_code=404, detail="unknown scan id (Phase 0 only serves the fixture scan)")
    return {"scan_id": scan_id, "other_id": other_id, "changes": [], "note": "diffing lands in Phase 3"}
