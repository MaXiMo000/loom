"""OSV.dev client — one `POST /v1/query` per (name, version) node (SPEC.md
§7.2). Not the `/v1/querybatch` endpoint: batch responses carry only vuln
ids, no severity, and severity is the entire point of this call — the N
per-package calls this costs are exactly why the depth cap (SPEC.md §7.2)
exists."""

from __future__ import annotations

import httpx

from app.config import HTTP_TIMEOUT, OSV_BASE

# Same normalization carabiner's deps.py already documents needing: OSV's
# GHSA-sourced `database_specific.severity` uses these tokens.
_SEVERITY_MAP = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MODERATE": "medium",
    "MEDIUM": "medium",
    "LOW": "low",
}

SEVERITY_RANK = {"none": 0, "unverified": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _vuln_severity(vuln: dict) -> str:
    """A vuln entry with no explicit severity still means *something* was
    found — floors at "low" rather than silently reading as clean."""
    sev = (vuln.get("database_specific") or {}).get("severity")
    if isinstance(sev, str) and sev.upper() in _SEVERITY_MAP:
        return _SEVERITY_MAP[sev.upper()]
    return "low"


class OSVClient:
    def __init__(self, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=HTTP_TIMEOUT)

    def close(self) -> None:
        self._client.close()

    def query(self, name: str, version: str) -> tuple[str, str | None] | None:
        """Returns (severity, detail) — severity is "none" if OSV was
        reachable and reported nothing; returns None (not a severity) if
        OSV itself couldn't be reached/parsed, which the caller must treat
        as unverified, never as "none"."""
        try:
            resp = self._client.post(
                f"{OSV_BASE}/query",
                json={"package": {"name": name, "ecosystem": "PyPI"}, "version": version},
            )
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except ValueError:
            return None

        vulns = data.get("vulns") or []
        if not vulns:
            return "none", None

        worst = max(vulns, key=lambda v: SEVERITY_RANK[_vuln_severity(v)])
        severity = _vuln_severity(worst)
        summary = worst.get("summary") or (worst.get("details") or "")[:200]
        detail = f"OSV {worst.get('id', '?')}: {summary}" if summary else f"OSV {worst.get('id', '?')}"
        if len(vulns) > 1:
            detail += f" (+{len(vulns) - 1} more)"
        return severity, detail
