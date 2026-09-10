"""Build the node/edge graph from a parsed lockfile + PyPI metadata,
depth-capped (SPEC.md §6 step 4, §7.2).

No live dependency resolution (SPEC.md §4): the pinned {name: version} map
from lockfile.py is the entire universe of packages this scan can ever
show. PyPI's `requires_dist` is only used to find *edges within* that
already-known, already-pinned set — a `requires_dist` name that isn't in
the pinned map is simply not drawn as an edge (loom doesn't know what
version it would have resolved to, and isn't going to guess).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from app.clients.pypi import PyPIClient, direct_dependency_names, github_repo
from app.config import MAX_PACKAGES_PER_SCAN


@dataclass
class ResolvedNode:
    name: str
    version: str
    depth: int
    github_repo: tuple[str, str] | None


@dataclass
class ResolvedGraph:
    nodes: list[ResolvedNode]
    edges: list[tuple[str, str]]  # (from_name, to_name)
    total_pinned: int  # size of the full lockfile, before any truncation


def resolve_graph(pinned: dict[str, str], pypi: PyPIClient, depth_cap: int) -> ResolvedGraph:
    total_pinned = len(pinned)

    # A safety cap on how many PyPI calls one scan can trigger — distinct
    # from depth_cap's user-facing "N of M, 3 levels deep" disclosure
    # (SPEC.md §7.2). Deterministic (alphabetical) so the same repo always
    # resolves to the same working set.
    # ponytail: fetches metadata for the whole (capped) pinned set up front
    # rather than a true frontier-only BFS bounded by depth — fine for a
    # realistic lockfile (<150 pkgs); revisit with real incremental fetch
    # if a huge lockfile makes a scan too slow.
    names = sorted(pinned)[:MAX_PACKAGES_PER_SCAN]

    infos: dict[str, dict | None] = {name: pypi.get_info(name, pinned[name]) for name in names}

    edges: list[tuple[str, str]] = []
    github_repos: dict[str, tuple[str, str] | None] = {}
    for name, info in infos.items():
        if info is None:
            github_repos[name] = None
            continue
        github_repos[name] = github_repo(info)
        for dep in direct_dependency_names(info):
            if dep in pinned and dep != name:
                edges.append((name, dep))

    in_degree = {name: 0 for name in names}
    for _, to in edges:
        if to in in_degree:
            in_degree[to] += 1
    roots = [n for n in names if in_degree[n] == 0]
    if not roots:
        # No name has zero incoming edges — an unexpected cycle-shaped
        # graph rather than a real dependency tree. Fail open (treat
        # everything as depth 0) instead of an infinite/empty BFS.
        roots = list(names)

    depth: dict[str, int] = {}
    queue = deque()
    for r in roots:
        depth[r] = 0
        queue.append(r)
    adjacency: dict[str, list[str]] = {n: [] for n in names}
    for frm, to in edges:
        adjacency[frm].append(to)
    while queue:
        cur = queue.popleft()
        for nxt in adjacency.get(cur, []):
            if nxt not in depth:
                depth[nxt] = depth[cur] + 1
                queue.append(nxt)
    # Anything unreachable from a root (shouldn't happen given the
    # zero-in-degree construction above, but stay honest if it does)
    # reads as depth 0 rather than being silently dropped.
    for n in names:
        depth.setdefault(n, 0)

    nodes = [
        ResolvedNode(name=n, version=pinned[n], depth=depth[n], github_repo=github_repos.get(n))
        for n in names
        if depth[n] <= depth_cap
    ]
    kept = {n.name for n in nodes}
    kept_edges = [(f, t) for f, t in edges if f in kept and t in kept]

    return ResolvedGraph(nodes=nodes, edges=kept_edges, total_pinned=total_pinned)
