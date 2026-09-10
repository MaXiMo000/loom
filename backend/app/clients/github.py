"""GitHub REST client — best-effort repo stars/last-commit (SPEC.md §3).
Unauthenticated GitHub API is rate-limited to 60 req/hr; this never blocks
a scan on it (SPEC.md §7.2's "never block a scan on this"). §13 leaves real
rate-limit handling under load open — Phase 1's answer: stop calling once
the response itself says the budget is spent (rather than pre-emptively
guessing a request budget), and every remaining node just reads
`repo_stars: None` for the rest of that scan."""

from __future__ import annotations

import re

import httpx

from app.config import GITHUB_BASE, HTTP_TIMEOUT

_GITHUB_URL_RE = re.compile(r"github\.com[:/]([^/]+)/([^/#]+?)(?:\.git)?/?$")


def parse_owner_repo(url: str) -> tuple[str, str] | None:
    m = _GITHUB_URL_RE.search(url.strip())
    return (m.group(1), m.group(2)) if m else None


class GitHubClient:
    def __init__(self, client: httpx.Client | None = None):
        self._client = client or httpx.Client(timeout=HTTP_TIMEOUT)
        self._budget_spent = False

    def close(self) -> None:
        self._client.close()

    def repo_meta(self, owner: str, repo: str) -> dict | None:
        """Returns {"stars": int, "last_commit": str | None} or None on any
        failure, including a spent rate-limit budget — never guessed."""
        if self._budget_spent:
            return None
        try:
            resp = self._client.get(f"{GITHUB_BASE}/repos/{owner}/{repo}")
        except httpx.HTTPError:
            return None
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            self._budget_spent = True
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except ValueError:
            return None
        return {"stars": data.get("stargazers_count"), "last_commit": data.get("pushed_at")}
