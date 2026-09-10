"""Drift signal (SPEC.md §7.2 point 2, §10 Phase 2): a disposable, sandboxed
venv-install of the target repo's own lockfile, then a real `lockstep
check` against it.

Two SEPARATE short-lived containers, not one (drift-worker/Dockerfile has
the full reasoning): `install` has network (has to reach PyPI for
whatever a random submitted repo pins), `check` is started with
`--network=none` from here — it only reads local importlib.metadata, so
there is no legitimate call for it to ever make, and the host cuts the
capability rather than trusting the process not to attempt one.

"Executing arbitrary pip install output for a repo a random user
submitted is a real code-execution surface" (SPEC.md §7.2's own words) —
every container run here is non-root, capability-dropped, resource-capped,
network-restricted, `--rm`, and gets nothing from this process's own
environment (no `docker run --env-file`, no secrets, no host mounts
besides one throwaway scratch dir).
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from app.config import DRIFT_CHECK_TIMEOUT, DRIFT_IMAGE, DRIFT_INSTALL_TIMEOUT
from app.resolve.graph import ResolvedNode

NO_SANDBOX_REASON = "not yet computed — the drift sandbox (Docker) isn't available in this deployment (SPEC.md §7.2/§10)"
NO_PIP_COMPILE_REASON = "not yet computed — drift-checking only supports a pip-compile requirements.txt, not poetry.lock yet"

# Every fresh venv carries these regardless of what the target repo pins;
# they'd otherwise show up as `extra` (installed, not declared) on every
# single scan, which is noise about loom's own sandbox, not a finding
# about the scanned repo.
_INFRA_NOISE = {"pip", "setuptools", "wheel", "lockstep-evidence", "lockstep"}

# Dropped into every container run: no inherited capabilities, no
# privilege escalation, hard resource caps so a hostile lockfile can't
# fork-bomb or memory-exhaust the host, and the fixed non-root uid the
# image itself already runs as (drift-worker/Dockerfile).
_SANDBOX_FLAGS = [
    "--rm",
    "--cap-drop=ALL",
    "--security-opt", "no-new-privileges",
    "--memory=768m",
    "--pids-limit=256",
    "--cpus=1",
    "--user", "10001:10001",
]


def sandbox_available() -> bool:
    return shutil.which("docker") is not None


def _run_docker(args: list[str], timeout: float) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None


def compute_drift(
    lockfile_kind: str, lockfile_path: Path, nodes: list[ResolvedNode]
) -> dict[str, tuple[str, str | None]]:
    """Returns {package_name: (drift_status, detail)}."""
    if not sandbox_available():
        return {n.name: ("unverified", NO_SANDBOX_REASON) for n in nodes}
    if lockfile_kind != "pip-compile":
        return {n.name: ("unverified", NO_PIP_COMPILE_REASON) for n in nodes}

    scratch = Path(tempfile.mkdtemp(prefix="loom-drift-"))
    # Both containers run as a fixed non-root uid different from this
    # process's own — world-writable is the simplest way to let both
    # actually use it; it's a single-purpose, single-scan, deleted-after
    # scratch dir, never anything else on the host.
    os.chmod(scratch, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    try:
        shutil.copy(lockfile_path, scratch / "requirements.txt")

        install = _run_docker(
            ["run", *_SANDBOX_FLAGS, "-v", f"{scratch}:/work", DRIFT_IMAGE, "install"],
            timeout=DRIFT_INSTALL_TIMEOUT,
        )
        if install is None:
            return {n.name: ("unverified", f"drift sandbox install did not finish within {DRIFT_INSTALL_TIMEOUT}s") for n in nodes}
        if install.returncode != 0:
            return {n.name: ("unverified", f"drift sandbox install failed: {install.stderr[-500:]}") for n in nodes}

        check = _run_docker(
            ["run", *_SANDBOX_FLAGS, "--network=none", "-v", f"{scratch}:/work", DRIFT_IMAGE, "check"],
            timeout=DRIFT_CHECK_TIMEOUT,
        )
        if check is None:
            return {n.name: ("unverified", f"drift sandbox check did not finish within {DRIFT_CHECK_TIMEOUT}s") for n in nodes}
        # lockstep's own exit code is 1 when real drift is found, 0 when
        # clean -- both are valid results, never treated as a failure.
        try:
            results = json.loads(check.stdout)
        except json.JSONDecodeError:
            return {n.name: ("unverified", f"drift sandbox check produced unparseable output: {check.stderr[-300:]}") for n in nodes}

        by_name = {r["name"]: r for r in results if r["name"] not in _INFRA_NOISE}
        out: dict[str, tuple[str, str | None]] = {}
        for n in nodes:
            r = by_name.get(n.name)
            out[n.name] = (r["status"], r["detail"]) if r else ("unverified", "lockstep did not report this package")
        return out
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
