"""Smoke tests for the Phase 0 fixture-backed routes.

Real logic (lockfile parsing, graph resolution, signal computation) doesn't
exist yet in Phase 0 — these tests exist to catch a broken route/response
shape, which is the one thing that actually could regress at this phase.
"""

from fastapi.testclient import TestClient

from app.fixtures import FIXTURE_SCAN_ID
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_scan_requires_repo_url():
    r = client.post("/api/scans", json={})
    assert r.status_code == 422


def test_create_scan_returns_fixture_id():
    r = client.post("/api/scans", json={"repo_url": "https://github.com/pallets/flask"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == FIXTURE_SCAN_ID
    assert body["status"] == "complete"


def test_get_scan_returns_full_graph():
    r = client.get(f"/api/scans/{FIXTURE_SCAN_ID}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "complete"
    node_ids = {n["id"] for n in body["nodes"]}
    assert {"requests", "flask", "markupsafe"} <= node_ids
    # every edge endpoint must be a real node in the same payload
    for edge in body["edges"]:
        assert edge["from_node"] in node_ids
        assert edge["to_node"] in node_ids


def test_get_unknown_scan_is_404():
    r = client.get("/api/scans/not-a-real-id")
    assert r.status_code == 404


def test_list_scans():
    r = client.get("/api/scans", params={"repo_url": "https://github.com/pallets/flask"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["id"] == FIXTURE_SCAN_ID


def test_diff_scans_stub():
    r = client.get(f"/api/scans/{FIXTURE_SCAN_ID}/diff/{FIXTURE_SCAN_ID}")
    assert r.status_code == 200
    assert r.json()["changes"] == []
