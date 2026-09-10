"""Against real recorded PyPI responses (tests/fixtures/pypi/*.json,
captured once from the real API — SPEC.md §11), not live network on every
CI run and not a hand-guessed shape."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

from app.clients.pypi import PyPIClient, direct_dependency_names, github_repo, parse_requirement_name

FIXTURES = Path(__file__).parent / "fixtures" / "pypi"


def _load(name: str, version: str) -> dict:
    return json.loads((FIXTURES / f"{name}-{version}.json").read_text())


def test_parse_requirement_name_strips_specifiers_and_extras():
    assert parse_requirement_name("idna (>=2.5,<4)") == "idna"
    assert parse_requirement_name("PySocks[socks] (>=1.5.6)") == "pysocks"
    assert parse_requirement_name("Flask_Login") == "flask-login"


def test_direct_dependency_names_skips_marker_conditional_extras():
    info = _load("flask", "3.0.3")["info"]
    deps = direct_dependency_names(info)
    assert "werkzeug" in deps
    assert "jinja2" in deps
    assert "click" in deps
    assert "itsdangerous" in deps
    assert "blinker" in deps
    # flask's real requires_dist includes optional extras like "asgiref ...;
    # extra == 'async'" — those carry a `;` marker and must be excluded.
    assert "asgiref" not in deps


def test_github_repo_found_in_real_project_urls():
    info = _load("flask", "3.0.3")["info"]
    assert github_repo(info) == ("pallets", "flask")


@respx.mock
def test_get_info_returns_none_on_404():
    respx.get("https://pypi.org/pypi/doesnotexist/1.0/json").mock(return_value=httpx.Response(404))
    client = PyPIClient()
    try:
        assert client.get_info("doesnotexist", "1.0") is None
    finally:
        client.close()


@respx.mock
def test_get_info_returns_none_on_network_error():
    respx.get("https://pypi.org/pypi/flask/3.0.3/json").mock(side_effect=httpx.ConnectError("boom"))
    client = PyPIClient()
    try:
        assert client.get_info("flask", "3.0.3") is None
    finally:
        client.close()


@respx.mock
def test_get_info_returns_real_fixture_shape():
    real = _load("flask", "3.0.3")
    respx.get("https://pypi.org/pypi/flask/3.0.3/json").mock(return_value=httpx.Response(200, json=real))
    client = PyPIClient()
    try:
        info = client.get_info("flask", "3.0.3")
    finally:
        client.close()
    assert info["name"] == "Flask"
    assert "werkzeug" in direct_dependency_names(info)
