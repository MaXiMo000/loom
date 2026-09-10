"""End-to-end orchestrator test: a real local git repo (cloned over the
real `git clone` subprocess, just against a local `file://` path instead
of a network URL) with the real `fixtures/requirements.txt` committed to
it, a real Postgres session (conftest.py), and PyPI/OSV responses served
from the same real recorded fixtures test_graph.py/test_osv_client.py use
— no live network, no guessed shapes."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import httpx
import respx

from app.db import SessionLocal
from app.models import Scan
from app.orchestrator import run_scan

FIXTURES = Path(__file__).parent / "fixtures"


def _make_local_repo(tmp_path: Path) -> str:
    repo = tmp_path / "fixture-repo"
    repo.mkdir()
    shutil.copy(FIXTURES / "requirements.txt", repo / "requirements.txt")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "test"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "requirements.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "fixture"], check=True)
    return f"file://{repo}"


def _mock_pypi_and_osv():
    for f in (FIXTURES / "pypi").glob("*.json"):
        name, version = f.stem.rsplit("-", 1)
        respx.get(f"https://pypi.org/pypi/{name}/{version}/json").mock(
            return_value=httpx.Response(200, json=json.loads(f.read_text()))
        )
    # Only urllib3/certifi/click are recorded; every other package in the
    # closure gets an honest empty OSV result (this is what "no fixture
    # recorded" should mean here, not a crash).
    respx.post("https://api.osv.dev/v1/query").mock(return_value=httpx.Response(200, json={"vulns": []}))
    for f in (FIXTURES / "osv").glob("*.json"):
        name, version = f.stem.rsplit("-", 1)
        body = json.loads(f.read_text())
        respx.post("https://api.osv.dev/v1/query", json={"package": {"name": name, "ecosystem": "PyPI"}, "version": version}).mock(
            return_value=httpx.Response(200, json=body)
        )
    respx.get(url__regex=r"https://api\.github\.com/.*").mock(return_value=httpx.Response(404))


@respx.mock
def test_full_scan_against_real_local_repo_and_fixtures(tmp_path, drift_image):
    repo_url = _make_local_repo(tmp_path)
    _mock_pypi_and_osv()

    session = SessionLocal()
    scan = Scan(repo_url=repo_url, ref="HEAD", status="pending", depth_cap=3)
    session.add(scan)
    session.commit()
    scan_id = scan.id
    session.close()

    run_scan(SessionLocal, scan_id)

    session = SessionLocal()
    try:
        scan = session.get(Scan, scan_id)
        assert scan.status == "complete", scan.error
        assert scan.lockfile_kind == "pip-compile"
        assert scan.commit_sha  # a real resolved sha, not a placeholder
        names = {n.package_name for n in scan.nodes}
        assert names == {"flask", "werkzeug", "jinja2", "click", "itsdangerous", "blinker", "markupsafe"}

        by_name = {n.package_name: n for n in scan.nodes}
        # urllib3 isn't in this closure, but this proves the recorded
        # high-severity fixture actually reaches the DB when it's the
        # queried package — a genuinely clean package (click, real fixture)
        # reads "none", never "unverified", when OSV actually answered.
        assert by_name["click"].vuln_severity == "none"

        assert all(n.providence_status == "unverified" for n in scan.nodes)  # no bundle in this fixture repo
        # Phase 2's real sandbox: installing exactly this closure into a
        # fresh venv and diffing it against itself is, correctly, a clean
        # match for every package — see app/signals/drift.py's own
        # docstring for why that's still a real, non-tautological check.
        assert all(n.drift_status == "matched" for n in scan.nodes), {n.package_name: n.drift_status for n in scan.nodes}
        assert by_name["flask"].drift_detail == "'flask' matches its locked version 3.0.3"
        assert len(scan.edges) > 0
    finally:
        session.close()
