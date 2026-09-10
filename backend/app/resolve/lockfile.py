"""Parse requirements.txt (pip-compile output) or poetry.lock into a flat
{name: version} map — the pinned closure SPEC.md §3 requires already exist
in the repo. No live resolution (SPEC.md §4): a name found here is trusted
exactly as pinned, never re-resolved."""

from __future__ import annotations

import re
from pathlib import Path

import toml

# name[extra]==version, with everything after a `;` marker or trailing
# `--hash=...` stripped first. PEP 503 normalization (lowercase,
# underscore/dot -> hyphen) so "Flask" and "flask_login" match how PyPI's
# own API and the graph's other names are keyed.
_REQ_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*==\s*([^\s;]+)")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def find_lockfile(repo_dir: Path) -> tuple[str, Path] | None:
    """Returns (kind, path) for whichever lockfile SPEC.md §3 recognizes,
    preferring pip-compile's requirements.txt since it's the spec's primary
    documented path. None means "no recognized lockfile" — an honest
    `unverified: no lockfile found`, not a guess (SPEC.md §3)."""
    req = repo_dir / "requirements.txt"
    if req.is_file():
        return "pip-compile", req
    poetry = repo_dir / "poetry.lock"
    if poetry.is_file():
        return "poetry", poetry
    return None


def parse_requirements_txt(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    # Join backslash line-continuations (hash-checking mode wraps each
    # `--hash=...` onto its own continuation line) before stripping comments,
    # since a continuation can appear mid-logical-line.
    text = text.replace("\\\n", " ")

    pinned: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        m = _REQ_RE.match(line)
        if m:
            pinned[_normalize(m.group(1))] = m.group(2)
    return pinned


def parse_poetry_lock(path: Path) -> dict[str, str]:
    # poetry.lock's shape has moved across major Poetry versions (SPEC.md
    # §13 flags this explicitly); the one field that has stayed stable
    # across every version this was checked against is `[[package]]` with
    # `name`/`version` — that's all this reads. If a future Poetry version
    # moves even that, a repo using it fails closed (empty pinned set ->
    # "no lockfile found"-shaped error from the caller), not silently wrong.
    doc = toml.loads(path.read_text(encoding="utf-8", errors="replace"))
    pinned: dict[str, str] = {}
    for pkg in doc.get("package", []):
        name = pkg.get("name")
        version = pkg.get("version")
        if name and version:
            pinned[_normalize(name)] = version
    return pinned


def parse_lockfile(kind: str, path: Path) -> dict[str, str]:
    if kind == "pip-compile":
        return parse_requirements_txt(path)
    if kind == "poetry":
        return parse_poetry_lock(path)
    raise ValueError(f"unknown lockfile kind {kind!r}")
