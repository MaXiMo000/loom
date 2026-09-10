"""Policy signal (SPEC.md §7.2 point 4). Deferred explicitly in v1 rather
than inventing a generic policy nobody asked for — a submitter's own
`invariant.yaml`, if their repo includes one, would be what this checks;
until that's built, every node honestly reports `unverified`."""

from __future__ import annotations

from pathlib import Path


def check_policy(repo_dir: Path) -> tuple[str, str | None]:
    if (repo_dir / "invariant.yaml").is_file():
        return "unverified", "invariant.yaml found, but running it is deferred past v1 (SPEC.md §7.2/§10)"
    return "unverified", "bring your own invariant.yaml — none found"
