"""Phase 0 walking-skeleton data: a hand-written, realistic-shaped dependency
graph (real PyPI package names, plausible severities) with NO real scanning
behind it — no clone, no PyPI/OSV/GitHub calls, no carabiner/lockstep
subprocess.

This exists so the frontend's 3D rendering, styling, and click-to-detail
interaction can be proven end to end before any of Phase 1's real data
pipeline (SPEC.md §10) is written. Node/edge ids are readable slugs here,
not real uuids — Phase 1, once nodes are actually persisted to Postgres
(SPEC.md §7.6), switches to real generated uuids.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

FIXTURE_SCAN_ID = "phase0-fixture-scan"

_NODES: list[dict[str, Any]] = [
    # top-level (depth 0), straight from the fixture "lockfile"
    dict(id="requests", package_name="requests", package_version="2.31.0", depth=0,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=52000, repo_last_commit="2024-05-20T00:00:00Z"),
    dict(id="flask", package_name="flask", package_version="3.0.3", depth=0,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="verified", policy_status="unverified",
         repo_stars=67000, repo_last_commit="2024-04-01T00:00:00Z"),
    # depth 1 — requests' direct deps
    dict(id="urllib3", package_name="urllib3", package_version="2.0.7", depth=1,
         vuln_severity="high", vuln_detail="OSV: GHSA-....-.... — improper certificate handling in redirect path",
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=3700, repo_last_commit="2024-03-15T00:00:00Z"),
    dict(id="certifi", package_name="certifi", package_version="2024.2.2", depth=1,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=900, repo_last_commit="2024-02-02T00:00:00Z"),
    dict(id="idna", package_name="idna", package_version="3.6", depth=1,
         vuln_severity="low", vuln_detail="OSV: GHSA-....-.... — denial of service on pathological input",
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=900, repo_last_commit="2023-11-25T00:00:00Z"),
    dict(id="charset-normalizer", package_name="charset-normalizer", package_version="3.3.2", depth=1,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=380, repo_last_commit="2023-10-08T00:00:00Z"),
    # depth 1 — flask's direct deps
    dict(id="werkzeug", package_name="werkzeug", package_version="3.0.1", depth=1,
         vuln_severity="medium", vuln_detail="OSV: GHSA-....-.... — debugger PIN bypass under a narrow config",
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=6600, repo_last_commit="2024-03-28T00:00:00Z"),
    dict(id="jinja2", package_name="jinja2", package_version="3.1.3", depth=1,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=10400, repo_last_commit="2024-01-10T00:00:00Z"),
    dict(id="click", package_name="click", package_version="8.1.7", depth=1,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=15400, repo_last_commit="2023-08-17T00:00:00Z"),
    dict(id="itsdangerous", package_name="itsdangerous", package_version="2.1.2", depth=1,
         vuln_severity="critical", vuln_detail="OSV: GHSA-....-.... — signature verification bypass on malformed tokens",
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=2900, repo_last_commit="2023-01-08T00:00:00Z"),
    dict(id="blinker", package_name="blinker", package_version="1.7.0", depth=1,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=1600, repo_last_commit="2023-11-01T00:00:00Z"),
    # depth 2 — shared transitive dep, exercises "more depended-upon = larger"
    dict(id="markupsafe", package_name="markupsafe", package_version="2.1.5", depth=2,
         vuln_severity="none", vuln_detail=None,
         drift_status="unverified", providence_status="unverified", policy_status="unverified",
         repo_stars=680, repo_last_commit="2024-01-20T00:00:00Z"),
]

_EDGES: list[tuple[str, str]] = [
    ("requests", "urllib3"),
    ("requests", "certifi"),
    ("requests", "idna"),
    ("requests", "charset-normalizer"),
    ("flask", "werkzeug"),
    ("flask", "jinja2"),
    ("flask", "click"),
    ("flask", "itsdangerous"),
    ("flask", "blinker"),
    ("jinja2", "markupsafe"),
    ("werkzeug", "markupsafe"),
]


def fixture_scan() -> dict[str, Any]:
    """The full scan payload GET /api/scans/{id} returns for the fixture id."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": FIXTURE_SCAN_ID,
        "repo_url": "https://github.com/pallets/flask",
        "ref": "HEAD",
        "commit_sha": "0000000fixture",
        "status": "complete",
        "error": None,
        "lockfile_kind": "pip-compile",
        "depth_cap": 3,
        "created_at": now,
        "completed_at": now,
        "nodes": [dict(n) for n in _NODES],
        "edges": [
            {"id": f"{frm}->{to}", "from_node": frm, "to_node": to}
            for frm, to in _EDGES
        ],
    }


def fixture_scan_summary() -> dict[str, Any]:
    """The summary shape GET /api/scans?repo_url=... returns per row."""
    full = fixture_scan()
    return {
        "id": full["id"],
        "repo_url": full["repo_url"],
        "ref": full["ref"],
        "status": full["status"],
        "created_at": full["created_at"],
        "node_count": len(full["nodes"]),
    }
