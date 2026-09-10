"""PyPI JSON API client. One HTTP call per (name, version) feeds two
things: `info.requires_dist` (the direct-dependency edges the graph
resolver walks, SPEC.md §6 step 4) and whichever `project_urls`/`home_page`
entry points at GitHub (the repo the "is this package maintained" signal,
SPEC.md §3, is actually about — the package's own upstream repo, not the
repo being scanned)."""

from __future__ import annotations

import re

import httpx

from app.config import HTTP_TIMEOUT, PYPI_BASE
from app.clients.github import parse_owner_repo

# A requires_dist entry looks like "idna (>=2.5,<4)" or "PySocks[socks]
# (>=1.5.6,!=1.5.7) ; extra == 'socks'". Only the bare name is wanted here —
# resolve/graph.py already knows real pinned versions from the lockfile
# itself (SPEC.md §6: no live resolution), so a version specifier from PyPI
# would be redundant at best, wrong at worst.
_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def parse_requirement_name(requires_dist_entry: str) -> str | None:
    m = _NAME_RE.match(requires_dist_entry.strip())
    return m.group(1).lower().replace("_", "-") if m else None


def direct_dependency_names(info: dict) -> list[str]:
    requires = info.get("requires_dist") or []
    names = []
    for entry in requires:
        # Only unconditional runtime deps — anything with a `;` marker is
        # environment-conditional (extras, python_version, sys_platform);
        # SPEC.md's no-live-resolution stance means loom can't evaluate
        # those markers, so it only follows the deps that always apply.
        if ";" in entry:
            continue
        n = parse_requirement_name(entry)
        if n:
            names.append(n)
    return names


def github_repo(info: dict) -> tuple[str, str] | None:
    candidates = list((info.get("project_urls") or {}).values())
    if info.get("home_page"):
        candidates.append(info["home_page"])
    for url in candidates:
        parsed = parse_owner_repo(url or "")
        if parsed:
            return parsed
    return None


class PyPIClient:
    def __init__(self, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=HTTP_TIMEOUT)

    def close(self) -> None:
        self._client.close()

    def get_info(self, name: str, version: str) -> dict | None:
        """Returns the raw `info` object, or None on any failure —
        resolve/graph.py treats that as "unknown edges for this node",
        never as "this node has no dependencies", which would be a guess
        dressed as a fact."""
        try:
            resp = self._client.get(f"{PYPI_BASE}/{name}/{version}/json")
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except ValueError:
            return None
        return data.get("info")
