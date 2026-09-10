"""Shallow git clone to a scratch dir. Explicit argument lists only, never
`shell=True` (SPEC.md §7.3, invariant's security_scan.py precedent) — the
repo URL and ref both come straight from an untrusted user-submitted form."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from app.config import CLONE_TIMEOUT


class CloneError(Exception):
    pass


def clone_repo(repo_url: str, ref: str | None = None) -> tuple[Path, str]:
    """Shallow-clones `repo_url` (optionally at `ref`) into a fresh scratch
    dir under the system tmp dir. Returns (path, resolved_commit_sha).
    Raises CloneError with a human-readable reason on any failure — the
    caller turns that into `scan.status=failed`/`scan.error`, never a
    guessed result."""
    scratch = Path(tempfile.mkdtemp(prefix="loom-clone-"))
    cmd = ["git", "clone", "--depth", "1", "--single-branch"]
    if ref and ref != "HEAD":
        cmd += ["--branch", ref]
    cmd += [repo_url, str(scratch)]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLONE_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise CloneError(f"clone did not finish within {CLONE_TIMEOUT}s")

    if proc.returncode != 0:
        raise CloneError(f"git clone failed: {proc.stderr.strip()[:500]}")

    try:
        rev = subprocess.run(
            ["git", "-C", str(scratch), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        raise CloneError("clone succeeded but `git rev-parse HEAD` timed out")

    if rev.returncode != 0:
        raise CloneError(f"clone succeeded but HEAD could not be resolved: {rev.stderr.strip()[:300]}")

    return scratch, rev.stdout.strip()
