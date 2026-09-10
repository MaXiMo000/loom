"""Tamper-evidence signal (SPEC.md §7.2 point 3). Almost every real repo
has neither form of bundle — that absence is itself the finding, rendered
as `unverified`, never swept under a default."""

from __future__ import annotations

from pathlib import Path

from app.vendor.providence.check import check_bundle

# Bounded, not a full recursive walk of the clone — matches carabiner's own
# manifest_dirs discipline (resolve/graph.py's MAX_PACKAGES_PER_SCAN
# comment on the same idea): a repo this large already isn't the "small
# public repo" SPEC.md §11 says to live-verify against, and providence
# bundles that exist are conventionally at the repo root anyway.
_MAX_SCAN_DEPTH = 2
_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".tox"}


def _candidate_json_files(repo_dir: Path) -> list[Path]:
    out = []
    stack = [(repo_dir, 0)]
    while stack:
        d, depth = stack.pop()
        if depth > _MAX_SCAN_DEPTH:
            continue
        try:
            entries = list(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.is_dir():
                if e.name not in _SKIP_DIRS:
                    stack.append((e, depth + 1))
            elif e.suffix == ".json":
                out.append(e)
    return out


def check_providence(repo_dir: Path) -> tuple[str, str | None]:
    """Returns (providence_status, detail)."""
    bundle_dir = repo_dir / ".providence"
    if bundle_dir.is_dir():
        issues = check_bundle(bundle_dir)
        if not issues:
            return "verified", f".providence/ bundle conformant ({len(list(bundle_dir.glob('*.json')))} items)"
        return "unverified", f".providence/ bundle found but not conformant: {issues[0]}"

    for candidate in _candidate_json_files(repo_dir):
        issues = check_bundle(candidate)
        if not issues:
            return "verified", f"{candidate.relative_to(repo_dir)} is a conformant single-file bundle"

    return "unverified", "no .providence/ bundle or conformant single-file bundle found"
