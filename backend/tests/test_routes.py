"""HTTP-level tests for the 4 real routes (SPEC.md §7.7), against a real
Postgres session (conftest.py) — complements test_orchestrator.py (which
exercises run_scan directly) and test_diff.py (pure diff_nodes logic) by
covering the route layer itself: validation, status codes, and the real
diff endpoint's own request/response contract end to end."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import Node, Scan

client = TestClient(app)


def _make_scan(repo_url: str, status: str, created_at: datetime, nodes: list[dict]) -> str:
    session = SessionLocal()
    try:
        scan = Scan(repo_url=repo_url, ref="HEAD", status=status, created_at=created_at,
                    completed_at=created_at, lockfile_kind="pip-compile", depth_cap=3,
                    total_package_count=len(nodes))
        session.add(scan)
        session.flush()
        for n in nodes:
            session.add(Node(scan_id=scan.id, depth=0, vuln_severity="none",
                              drift_status="unverified", providence_status="unverified",
                              policy_status="unverified", **n))
        session.commit()
        return scan.id
    finally:
        session.close()


def test_create_scan_requires_repo_url():
    r = client.post("/api/scans", json={})
    assert r.status_code == 422


def test_get_unknown_scan_is_404():
    r = client.get("/api/scans/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_diff_unknown_scan_is_404():
    r = client.get("/api/scans/00000000-0000-0000-0000-000000000000/diff/11111111-1111-1111-1111-111111111111")
    assert r.status_code == 404


def test_diff_rejects_different_repos():
    now = datetime.now(timezone.utc)
    a = _make_scan("https://github.com/x/a", "complete", now, [{"package_name": "flask", "package_version": "3.0.3"}])
    b = _make_scan("https://github.com/x/b", "complete", now, [{"package_name": "flask", "package_version": "3.0.3"}])
    r = client.get(f"/api/scans/{a}/diff/{b}")
    assert r.status_code == 422


def test_diff_rejects_incomplete_scans():
    now = datetime.now(timezone.utc)
    a = _make_scan("https://github.com/x/a", "complete", now, [])
    b = _make_scan("https://github.com/x/a", "scanning", now, [])
    r = client.get(f"/api/scans/{a}/diff/{b}")
    assert r.status_code == 409


def test_diff_real_drift_over_time_scenario():
    # SPEC.md §10's own headline scenario, exercised through the real
    # HTTP route this time, not just diff_nodes() directly.
    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(hours=1)
    older = _make_scan("https://github.com/x/repo", "complete", t0, [
        {"package_name": "urllib3", "package_version": "2.0.6"},
        {"package_name": "flask", "package_version": "3.0.3"},
    ])
    newer = _make_scan("https://github.com/x/repo", "complete", t1, [
        {"package_name": "urllib3", "package_version": "2.0.7"},
        {"package_name": "werkzeug", "package_version": "3.1.8"},
    ])

    # Request in reverse order — the route must still resolve from/to by
    # actual created_at, not by which id came first in the URL.
    r = client.get(f"/api/scans/{newer}/diff/{older}")
    assert r.status_code == 200
    body = r.json()
    assert body["from_scan"]["id"] == older
    assert body["to_scan"]["id"] == newer

    by_name = {c["package_name"]: c for c in body["changes"]}
    assert by_name["urllib3"]["change_type"] == "changed"
    assert "version 2.0.6 → 2.0.7" in by_name["urllib3"]["detail"]
    assert by_name["flask"]["change_type"] == "removed"
    assert by_name["werkzeug"]["change_type"] == "added"
    assert body["unchanged_count"] == 0
