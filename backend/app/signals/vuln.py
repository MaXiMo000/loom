"""Vulnerability signal: carabiner's repo-scoped scan + a direct OSV lookup
per node, worst-severity-wins (SPEC.md §7.2 point 1). Subprocess pattern
copied from invariant's `checks/security_scan.py` (SPEC.md §7.3): explicit
argument list, a hard timeout, never `shell=True`."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from app.clients.osv import SEVERITY_RANK, OSVClient
from app.config import CARABINER_TIMEOUT
from app.resolve.graph import ResolvedNode


def _run_carabiner(repo_dir: Path) -> list[dict]:
    """Returns carabiner's `new` findings from the `deps` engine, or []
    if carabiner isn't installed, times out, or fails to run — matching
    security_scan.py's own "unverified, not a guess" handling of the same
    failure modes. Direct OSV lookups below are still the primary,
    complete source for vuln_severity; carabiner only ever adds to it."""
    if shutil.which("carabiner") is None:
        return []
    cmd = ["carabiner", "scan", "--root", str(repo_dir), "--all", "--json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CARABINER_TIMEOUT)
    except subprocess.TimeoutExpired:
        return []
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return [f for f in report.get("new", []) if f.get("engine") == "deps"]


def compute_vuln_severities(
    repo_dir: Path, nodes: list[ResolvedNode], osv: OSVClient
) -> dict[str, tuple[str, str | None]]:
    """Returns {package_name: (vuln_severity, vuln_detail)}."""
    carabiner_findings = _run_carabiner(repo_dir)

    result: dict[str, tuple[str, str | None]] = {}
    for node in nodes:
        osv_result = osv.query(node.name, node.version)
        if osv_result is None:
            # OSV itself unreachable/unparseable for this node — honestly
            # unverified, never defaulted to "none" (SPEC.md §6 step 6).
            severity, detail = "unverified", "OSV.dev was unreachable for this package"
        else:
            severity, detail = osv_result

        # carabiner's deps-engine findings aren't structured by package
        # name (Finding has no such field) — a best-effort substring match
        # against the finding's own message/path text. Known limitation,
        # not a silent guess: a match only ever raises severity, never
        # lowers what OSV already found.
        for f in carabiner_findings:
            haystack = f"{f.get('path', '')} {f.get('message', '')}".lower()
            if node.name.lower() in haystack:
                cb_sev = f.get("severity", "info")
                cb_sev = cb_sev if cb_sev in SEVERITY_RANK else "low"
                if SEVERITY_RANK[cb_sev] > SEVERITY_RANK.get(severity, 0):
                    severity = cb_sev
                    detail = f"carabiner[{f.get('rule')}]: {f.get('message', '')[:200]}"

        result[node.name] = (severity, detail)
    return result
