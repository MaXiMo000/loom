"""Graph resolution against the real pinned closure from
fixtures/requirements.txt, with PyPI responses served from the real
recorded fixtures (tests/fixtures/pypi/*.json) via respx — no live
network, no hand-guessed requires_dist shape."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

from app.clients.pypi import PyPIClient
from app.resolve.graph import resolve_graph
from app.resolve.lockfile import parse_requirements_txt

FIXTURES = Path(__file__).parent / "fixtures"
PYPI_FIXTURES = FIXTURES / "pypi"

PINNED = parse_requirements_txt(FIXTURES / "requirements.txt")


def _mock_all_pypi():
    for f in PYPI_FIXTURES.glob("*.json"):
        name, version = f.stem.rsplit("-", 1)
        body = json.loads(f.read_text())
        respx.get(f"https://pypi.org/pypi/{name}/{version}/json").mock(
            return_value=httpx.Response(200, json=body)
        )


@respx.mock
def test_resolve_real_flask_closure():
    _mock_all_pypi()
    client = PyPIClient()
    try:
        graph = resolve_graph(PINNED, client, depth_cap=3)
    finally:
        client.close()

    names = {n.name for n in graph.nodes}
    assert names == set(PINNED)  # nothing dropped within a generous depth cap
    assert graph.total_pinned == len(PINNED)

    by_name = {n.name: n for n in graph.nodes}
    assert by_name["flask"].depth == 0  # nothing in this closure depends on flask
    assert by_name["werkzeug"].depth == 1
    assert by_name["jinja2"].depth == 1
    assert by_name["markupsafe"].depth == 2  # only reachable via jinja2/werkzeug

    edge_set = set(graph.edges)
    assert ("flask", "werkzeug") in edge_set
    assert ("jinja2", "markupsafe") in edge_set


@respx.mock
def test_depth_cap_truncates_and_drops_orphaned_edges():
    _mock_all_pypi()
    client = PyPIClient()
    try:
        graph = resolve_graph(PINNED, client, depth_cap=1)
    finally:
        client.close()

    names = {n.name for n in graph.nodes}
    assert "markupsafe" not in names  # depth 2, past the cap
    assert "flask" in names and "werkzeug" in names  # depth 0/1, within the cap
    # an edge can't survive with one endpoint cut by the cap
    assert all(f in names and t in names for f, t in graph.edges)


@respx.mock
def test_a_failed_pypi_lookup_still_resolves_the_rest():
    _mock_all_pypi()
    respx.get("https://pypi.org/pypi/click/8.5.0/json").mock(return_value=httpx.Response(500))
    client = PyPIClient()
    try:
        graph = resolve_graph(PINNED, client, depth_cap=3)
    finally:
        client.close()

    names = {n.name for n in graph.nodes}
    assert "click" in names  # still a node (it's in the lockfile), just with no discovered edges
    assert "flask" in names
    assert not any(f == "click" for f, _ in graph.edges)
