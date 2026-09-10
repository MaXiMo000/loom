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
