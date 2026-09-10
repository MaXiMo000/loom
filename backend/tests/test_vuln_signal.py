"""compute_vuln_severities: worst-of-both-sources merge logic (SPEC.md
§7.2 point 1). carabiner itself is stubbed here (its own real subprocess
behavior isn't this module's job to test) so the merge rule is exercised
in isolation against real recorded OSV fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

from app.clients.osv import OSVClient
from app.resolve.graph import ResolvedNode
from app.signals import vuln as vuln_mod

FIXTURES = Path(__file__).parent / "fixtures" / "osv"


def _osv_mock(name: str, version: str) -> None:
    body = json.loads((FIXTURES / f"{name}-{version}.json").read_text())
    respx.post(
        "https://api.osv.dev/v1/query",
        json={"package": {"name": name, "ecosystem": "PyPI"}, "version": version},
    ).mock(return_value=httpx.Response(200, json=body))


@respx.mock
def test_osv_severity_used_when_carabiner_finds_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(vuln_mod, "_run_carabiner", lambda repo_dir: [])
    _osv_mock("urllib3", "2.0.7")
    nodes = [ResolvedNode(name="urllib3", version="2.0.7", depth=0, github_repo=None)]
    osv = OSVClient()
    try:
        result = vuln_mod.compute_vuln_severities(tmp_path, nodes, osv)
    finally:
        osv.close()
    assert result["urllib3"][0] == "high"


@respx.mock
def test_carabiner_finding_can_raise_but_never_lower_severity(monkeypatch, tmp_path):
    # click's real OSV fixture is genuinely clean ("none") — a matching
    # carabiner critical finding must still win (worst-of-both).
    _osv_mock("click", "8.5.0")
    monkeypatch.setattr(
        vuln_mod, "_run_carabiner",
        lambda repo_dir: [{"engine": "deps", "rule": "OSV-FAKE", "severity": "critical",
                            "path": "requirements.txt", "message": "click==8.5.0: fabricated for this test"}],
    )
    nodes = [ResolvedNode(name="click", version="8.5.0", depth=0, github_repo=None)]
    osv = OSVClient()
    try:
        result = vuln_mod.compute_vuln_severities(tmp_path, nodes, osv)
    finally:
        osv.close()
    severity, detail = result["click"]
    assert severity == "critical"
    assert "carabiner" in detail


@respx.mock
def test_unrelated_carabiner_finding_does_not_correlate(monkeypatch, tmp_path):
    _osv_mock("click", "8.5.0")
    monkeypatch.setattr(
        vuln_mod, "_run_carabiner",
        lambda repo_dir: [{"engine": "deps", "rule": "OSV-FAKE", "severity": "critical",
                            "path": "requirements.txt", "message": "flask==3.0.3: unrelated finding"}],
    )
    nodes = [ResolvedNode(name="click", version="8.5.0", depth=0, github_repo=None)]
    osv = OSVClient()
    try:
        result = vuln_mod.compute_vuln_severities(tmp_path, nodes, osv)
    finally:
        osv.close()
    assert result["click"] == ("none", None)


def test_osv_unreachable_reads_unverified_not_none(monkeypatch, tmp_path):
    monkeypatch.setattr(vuln_mod, "_run_carabiner", lambda repo_dir: [])
    nodes = [ResolvedNode(name="urllib3", version="2.0.7", depth=0, github_repo=None)]

    class DeadOSV:
        def query(self, name, version):
            return None

    result = vuln_mod.compute_vuln_severities(tmp_path, nodes, DeadOSV())
    assert result["urllib3"][0] == "unverified"
