"""Against real recorded OSV.dev responses (tests/fixtures/osv/*.json,
captured once — SPEC.md §11): urllib3==2.0.7 (real, multiple HIGH-severity
advisories), certifi==2024.2.2 (one real LOW advisory), click==8.5.0
(genuinely clean, `vulns: []`)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

from app.clients.osv import OSVClient

FIXTURES = Path(__file__).parent / "fixtures" / "osv"


def _mock(name: str, version: str) -> None:
    body = json.loads((FIXTURES / f"{name}-{version}.json").read_text())
    respx.post("https://api.osv.dev/v1/query").mock(return_value=httpx.Response(200, json=body))


@respx.mock
def test_worst_severity_wins_across_real_multi_vuln_response():
    _mock("urllib3", "2.0.7")
    client = OSVClient()
    try:
        severity, detail = client.query("urllib3", "2.0.7")
    finally:
        client.close()
    assert severity == "high"
    assert "OSV" in detail


@respx.mock
def test_single_low_severity_vuln():
    _mock("certifi", "2024.2.2")
    client = OSVClient()
    try:
        severity, detail = client.query("certifi", "2024.2.2")
    finally:
        client.close()
    assert severity == "low"


@respx.mock
def test_genuinely_clean_package_reads_none_not_unverified():
    _mock("click", "8.5.0")
    client = OSVClient()
    try:
        result = client.query("click", "8.5.0")
    finally:
        client.close()
    assert result == ("none", None)


@respx.mock
def test_network_failure_returns_none_not_a_guessed_severity():
    respx.post("https://api.osv.dev/v1/query").mock(side_effect=httpx.ConnectError("boom"))
    client = OSVClient()
    try:
        result = client.query("urllib3", "2.0.7")
    finally:
        client.close()
    assert result is None  # caller (signals/vuln.py) turns this into "unverified", never "none"
