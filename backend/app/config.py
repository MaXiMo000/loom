"""Env-driven settings (SPEC.md §9's config.py). Real Phase 1 defaults, no
values baked into call sites."""

from __future__ import annotations

import os


def _int(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v else default


def _float(name: str, default: float) -> float:
    v = os.environ.get(name)
    return float(v) if v else default


DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://loom:loom@127.0.0.1:5439/loom"
)

# "*" (any origin) is the local-dev default; SPEC.md §12's real deploy
# sets LOOM_ALLOWED_ORIGIN to the actual static site origin.
ALLOWED_ORIGINS = [os.environ.get("LOOM_ALLOWED_ORIGIN", "*")]

DEPTH_CAP_DEFAULT = _int("LOOM_DEPTH_CAP", 3)

# Defensive guard against a pathological lockfile, not the depth-cap
# disclosure itself (SPEC.md §7.2's "showing N of M, 3 levels deep" is a
# separate, always-true-to-the-user statement). This just bounds how many
# PyPI/OSV HTTP calls one scan can trigger.
MAX_PACKAGES_PER_SCAN = _int("LOOM_MAX_PACKAGES", 150)

HTTP_TIMEOUT = _float("LOOM_HTTP_TIMEOUT", 15.0)
CLONE_TIMEOUT = _float("LOOM_CLONE_TIMEOUT", 60.0)
CARABINER_TIMEOUT = _float("LOOM_CARABINER_TIMEOUT", 120.0)

PYPI_BASE = os.environ.get("LOOM_PYPI_BASE", "https://pypi.org/pypi")
OSV_BASE = os.environ.get("LOOM_OSV_BASE", "https://api.osv.dev/v1")
GITHUB_BASE = os.environ.get("LOOM_GITHUB_BASE", "https://api.github.com")

# Phase 2 (SPEC.md §7.2 point 2, §10) — the sandboxed drift signal.
# Auto-detected at call time (app/signals/drift.py's sandbox_available()),
# not gated by a separate on/off flag here: if Docker isn't reachable in
# this deployment, drift honestly reads unverified rather than needing a
# human to remember to also flip a switch.
DRIFT_IMAGE = os.environ.get("LOOM_DRIFT_IMAGE", "loom-drift-worker:local")
DRIFT_INSTALL_TIMEOUT = _float("LOOM_DRIFT_INSTALL_TIMEOUT", 180.0)
DRIFT_CHECK_TIMEOUT = _float("LOOM_DRIFT_CHECK_TIMEOUT", 30.0)
