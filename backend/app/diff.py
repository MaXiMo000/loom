"""Real node-level diffing between two scans of the same repo (SPEC.md
§7.7, §10 Phase 3) — the "drift over time" payoff SPEC.md §3's persistence
decision exists for: "this package went from matched to version_mismatch
between scan N and N+1."
"""

from __future__ import annotations

from app.models import Node

# Every signal worth flagging a change in — vuln_detail/drift_detail text
# changing on its own (same status, reworded evidence) isn't a real change
# worth surfacing here, only the status itself.
SIGNAL_FIELDS = ("vuln_severity", "drift_status", "providence_status", "policy_status")


def diff_nodes(older_nodes: list[Node], newer_nodes: list[Node]) -> list[dict]:
    """Every package that's new, gone, or changed between the older and
    newer scan — package name is the join key (unique per scan, SPEC.md
    §7.6's own uq_node_scan_package constraint). Unchanged packages are
    deliberately not included; the caller reports their count separately
    rather than padding this list with "nothing happened" entries."""
    older_by_name = {n.package_name: n for n in older_nodes}
    newer_by_name = {n.package_name: n for n in newer_nodes}
    changes: list[dict] = []

    for name in sorted(set(older_by_name) | set(newer_by_name)):
        o, n = older_by_name.get(name), newer_by_name.get(name)
        if o is None:
            changes.append({
                "package_name": name, "change_type": "added",
                "from_version": None, "to_version": n.package_version,
                "detail": f"'{name}' {n.package_version} appeared in the resolved graph",
            })
        elif n is None:
            changes.append({
                "package_name": name, "change_type": "removed",
                "from_version": o.package_version, "to_version": None,
                "detail": f"'{name}' {o.package_version} is no longer in the resolved graph",
            })
        else:
            field_changes = []
            if o.package_version != n.package_version:
                field_changes.append(f"version {o.package_version} → {n.package_version}")
            for field in SIGNAL_FIELDS:
                ov, nv = getattr(o, field), getattr(n, field)
                if ov != nv:
                    field_changes.append(f"{field} {ov} → {nv}")
            if field_changes:
                changes.append({
                    "package_name": name, "change_type": "changed",
                    "from_version": o.package_version, "to_version": n.package_version,
                    "detail": "; ".join(field_changes),
                })

    return changes
