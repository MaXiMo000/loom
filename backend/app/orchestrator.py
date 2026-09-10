"""The background job tying SPEC.md §6's steps together. Started via
FastAPI `BackgroundTasks` (SPEC.md §7.5 — start here, promote to a real
queue only once deployment shows a real need for it)."""

from __future__ import annotations

import shutil
import traceback
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.clients.github import GitHubClient
from app.clients.osv import OSVClient
from app.clients.pypi import PyPIClient
from app.config import DEPTH_CAP_DEFAULT
from app.models import Edge, Node, Scan
from app.resolve.clone import CloneError, clone_repo
from app.resolve.graph import resolve_graph
from app.resolve.lockfile import find_lockfile, parse_lockfile
from app.signals.policy import check_policy
from app.signals.providence import check_providence
from app.signals.vuln import compute_vuln_severities


def _fail(session: Session, scan: Scan, message: str) -> None:
    scan.status = "failed"
    scan.error = message[:2000]
    scan.completed_at = datetime.now(timezone.utc)
    session.commit()


def run_scan(session_factory, scan_id: str) -> None:
    """`session_factory` is a callable (SessionLocal) rather than a shared
    Session — this runs on a BackgroundTasks thread, so it gets its own
    session rather than sharing one with the request that kicked it off."""
    session = session_factory()
    scratch = None
    try:
        scan = session.get(Scan, scan_id)
        if scan is None:
            return

        scan.status = "cloning"
        session.commit()

        try:
            scratch, commit_sha = clone_repo(scan.repo_url, scan.ref)
        except CloneError as exc:
            _fail(session, scan, f"clone failed: {exc}")
            return
        scan.commit_sha = commit_sha
        session.commit()

        found = find_lockfile(scratch)
        if found is None:
            _fail(session, scan, "unverified: no lockfile found (requirements.txt or poetry.lock required — SPEC.md §3)")
            return
        lockfile_kind, lockfile_path = found
        scan.lockfile_kind = lockfile_kind
        scan.status = "resolving"
        session.commit()

        pinned = parse_lockfile(lockfile_kind, lockfile_path)
        if not pinned:
            _fail(session, scan, f"{lockfile_kind} lockfile found but no pinned packages could be parsed from it")
            return

        pypi = PyPIClient()
        try:
            graph = resolve_graph(pinned, pypi, scan.depth_cap or DEPTH_CAP_DEFAULT)
        finally:
            pypi.close()

        scan.status = "scanning"
        scan.total_package_count = graph.total_pinned
        session.commit()

        osv = OSVClient()
        try:
            vuln_by_name = compute_vuln_severities(scratch, graph.nodes, osv)
        finally:
            osv.close()

        # Node model (SPEC.md §7.6) has no providence/policy *detail* column
        # (unlike vuln_detail) — only the repo-wide status. The detail
        # strings are still real and used in tests/logs; not stored, since
        # there's no field to put them in without inventing one the spec
        # doesn't call for.
        providence_status, _providence_detail = check_providence(scratch)
        policy_status, _policy_detail = check_policy(scratch)

        github = GitHubClient()
        db_nodes: dict[str, Node] = {}
        try:
            for rn in graph.nodes:
                vuln_severity, vuln_detail = vuln_by_name.get(rn.name, ("unverified", None))
                stars, last_commit = None, None
                if rn.github_repo:
                    meta = github.repo_meta(*rn.github_repo)
                    if meta:
                        stars = meta.get("stars")
                        lc = meta.get("last_commit")
                        last_commit = datetime.fromisoformat(lc.replace("Z", "+00:00")) if lc else None

                node = Node(
                    scan_id=scan.id,
                    package_name=rn.name,
                    package_version=rn.version,
                    depth=rn.depth,
                    vuln_severity=vuln_severity,
                    vuln_detail=vuln_detail,
                    drift_status="unverified",
                    providence_status=providence_status,
                    policy_status=policy_status,
                    repo_stars=stars,
                    repo_last_commit=last_commit,
                )
                session.add(node)
                db_nodes[rn.name] = node
        finally:
            github.close()

        session.flush()  # assigns real ids before edges reference them

        for frm, to in graph.edges:
            if frm in db_nodes and to in db_nodes:
                session.add(Edge(scan_id=scan.id, from_node=db_nodes[frm].id, to_node=db_nodes[to].id))

        scan.status = "complete"
        scan.completed_at = datetime.now(timezone.utc)
        # Denormalized providence/drift/policy detail lives on nodes per
        # SPEC.md §7.6; scan.error carries a repo-wide note when there's
        # nothing more specific to say (both are almost always the honest
        # "not found"/"not yet computed" case).
        scan.error = None
        session.commit()

    except Exception as exc:  # noqa: BLE001 — a background job's last resort: never leave a scan stuck "scanning" forever
        session.rollback()
        scan = session.get(Scan, scan_id)
        if scan is not None:
            _fail(session, scan, f"unexpected error: {exc}\n{traceback.format_exc()[-1500:]}")
    finally:
        session.close()
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=True)
