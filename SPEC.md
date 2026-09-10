# loom — SPEC v1

**Read this file first, in full, before writing any code.** It is written to be
self-contained: everything a fresh agent needs to start building is here or
linked from here. If something is genuinely ambiguous after reading this
whole document, say so and propose a default rather than blocking — see §13.

---

## 1. What this is, in one line

**loom weaves the separate answers four existing tools give about one
dependency tree — vulnerable? drifted? tamper-evident? policy-compliant? —
into a single 3D graph you can actually walk through.**

Point it at a real GitHub repo. It clones the repo, finds its lockfile,
resolves the real dependency graph, and renders every package as a node in
an explorable 3D scene — colored, sized, and annotated by real signals, not
synthetic ones. Click a node, see exactly why it's colored that way, with a
link back to the real evidence.

## 2. Why this, why now

Four repos in this portfolio already independently answer a piece of "can I
trust this dependency tree":

- [`carabiner`](https://github.com/MaXiMo000/carabiner) — does a package have
  a known CVE, secret, or misconfiguration (its `deps` engine)
- [`lockstep`](https://github.com/MaXiMo000/lockstep) — does what's actually
  installed match what the lockfile declares (`missing`/`extra`/
  `version_mismatch`)
- [`providence`](https://github.com/MaXiMo000/providence) — is there a
  tamper-evident evidence bundle for this at all (usually: no — most of the
  software world has no evidence trail, and that absence is itself the
  finding)
- [`invariant`](https://github.com/MaXiMo000/invariant) — does a declared
  policy about this system still hold

Nobody has ever put all four answers on one picture. That's the gap. This is
also a real, currently-monetized problem category — Snyk, Socket.dev, and
Chainguard all sell some version of "see your software supply chain" — so
this isn't an invented need.

**loom does not reimplement any of the four tools.** It shells out to the
real installed CLIs the same way `invariant`'s `security_scan` check type
already shells out to a real `carabiner` binary — see §7.3. Existing,
working code is the backend; loom's own new code is the orchestration, the
graph resolution, and the 3D presentation.

## 3. Scope decisions for v1 (each with its reasoning — don't relitigate
     these without a real new fact, but they're not sacred either)

| Decision | Choice | Why |
|---|---|---|
| Ecosystem | **Python only** (pip/pip-compile lockfiles) | Matches every sibling tool (`lockstep`, `carabiner`'s depth-over-breadth stance in its own docstring). npm is real, named future work — see §4. |
| Lockfile requirement | **Requires a real, fully-pinned lockfile** (`requirements.txt` output of `pip-compile`, or `poetry.lock`) already in the target repo | Same assumption `lockstep` already makes and states plainly. loom does not attempt live dependency resolution itself — that's a correctness minefield (version solvers, extras, markers) that isn't the point of this project. A repo with no lockfile gets a clear, honest error, not a guess. |
| Auth / accounts | **None in v1** — no login, no per-user saved projects | The value is in the graph, not in a dashboard. A scan is keyed by `(repo_url, commit_sha)`, not by a user. Matches `firedrill`'s public-results-page precedent, not `recur`'s (recur's auth exists because it stores other people's financial data — loom stores nothing sensitive, only public repo metadata). Revisit only if real demand for saved history per person shows up. |
| Persistence | **Postgres, scans persisted** | A single ephemeral scan wastes the one thing `lockstep` already proved is worth showing: drift *over time*. Every scan of a given repo is stored; the UI can show "this package went from `matched` to `version_mismatch` between scan N and N+1." |
| Hosting | **Hosted, like `recur`/`LabLedger`** | "Awesome UI like my portfolio" implies a live, linkable demo, not a CLI only you can run. Render, same as the other two live deployments — no new infra decision to make. |
| Vulnerability data | **OSV.dev API** (https://osv.dev/docs/) | Free, no API key, no rate-limit wall for reasonable use, and it's the same open, vendor-neutral database GitHub's own advisory feed is partly built from. `carabiner`'s own `deps` engine can also be pointed at OSV — reuse the same source of truth loom's own carabiner subprocess call already returns, and additionally call OSV directly per-package for the graph coloring so a package with no lockfile-level finding yet (carabiner didn't flag it) can still show a real severity if one exists. |
| Repo metadata | **GitHub REST API, unauthenticated, best-effort** | Stars/last-commit-date as a minor "is this package maintained" signal. Unauthenticated GitHub API is heavily rate-limited (60 req/hr) — cache aggressively (see §7.2), and if the budget runs out mid-scan, that signal just reads `unverified` for the remaining nodes. Never block a scan on this. |
| 3D approach | **Procedurally generated primitives, force-directed layout — no modeled/imported 3D assets** | This is the one non-negotiable aesthetic constraint. The portfolio site's whole visual identity is "generated, not modeled, ships zero bytes of mesh" (see its own README's Design section) — loom is a new flagship in the same family and must hold the same discipline. A node is a sphere or a small instrument-like primitive built the same way `scene/geometry.ts` builds its shapes: code, not an imported `.glb`. |
| Package manager for the frontend | **pnpm** if available on the build agent, else npm — either is fine, don't block on this | Not a real decision, just don't waste a question on it. |

## 4. What v1 explicitly does NOT do (state it, don't silently skip it)

- **No npm/Cargo/Go ecosystem support.** Python only. A real, sized follow-up,
  not attempted here — adding one more ecosystem is a resolver-and-schema
  problem per ecosystem, not a content edit.
- **No live dependency resolution.** If a repo has no recognized lockfile,
  loom reports that plainly (`unverified: no lockfile found`) and does not
  attempt to resolve one on the fly.
- **No write access to the scanned repo, ever.** loom only ever reads
  (clones, greps, parses). It never opens a PR, never comments, never
  modifies anything about the target.
- **No auth, no teams, no saved dashboards** — see §3.
- **No continuous/scheduled scanning.** A scan is triggered by a user
  submitting a repo URL. A cron-driven "watch this repo forever" mode is
  real, future work (and would rhyme nicely with `escrow`'s own dead-man's-
  switch idea — "alert me when a repo's graph gets meaningfully worse" — but
  that's v2, not v1).
- **No private repos.** Public GitHub repos only, cloned over HTTPS with no
  credentials. Scanning someone's private code is a different trust
  boundary this version doesn't take on.

## 5. Architecture overview

```
                    ┌──────────────────────────┐
                    │   Browser (React + R3F)  │
                    │  3D graph · scan form ·   │
                    │  history sidebar · panel  │
                    └────────────┬──────────────┘
                                 │ REST + polling (see §7.4 on why not WS)
                    ┌────────────▼──────────────┐
                    │   FastAPI backend          │
                    │  ┌───────────────────────┐ │
                    │  │ scan orchestrator      │ │   shells out to:
                    │  │ (background task)      │─┼──▶ carabiner (real CLI)
                    │  └───────────┬───────────┘ │─┼──▶ lockstep  (real CLI)
                    │              │              │
                    │  ┌───────────▼───────────┐ │   calls:
                    │  │ graph resolver         │─┼──▶ PyPI JSON API
                    │  │ (lockfile → node/edge)│ │─┼──▶ OSV.dev API
                    │  └───────────┬───────────┘ │─┼──▶ GitHub REST API
                    │              │              │      (best-effort)
                    │  ┌───────────▼───────────┐ │
                    │  │ providence check       │ │   reads (if present in
                    │  │ (in-process, stdlib)   │ │   the cloned repo):
                    │  └────────────────────────┘ │   .providence/ bundles
                    └────────────┬──────────────┘
                                 │
                          ┌──────▼──────┐
                          │  Postgres   │
                          │  scans,     │
                          │  nodes,     │
                          │  edges      │
                          └─────────────┘
```

## 6. Data flow: from "paste a repo URL" to "walk the graph"

1. User submits a public GitHub repo URL (and optionally a ref/branch) in
   the frontend.
2. `POST /api/scans` creates a `scan` row (`status=pending`), returns its id
   immediately, and kicks off a FastAPI `BackgroundTasks` job (or a real
   worker queue — see §7.5 for the call on which).
3. The job: shallow-clones the repo to a scratch dir, looks for
   `requirements.txt` (pip-compile output) or `poetry.lock`, parses it into
   a flat package list (name, pinned version).
4. For each package: fetch its real metadata from the PyPI JSON API
   (`https://pypi.org/pypi/<name>/<version>/json`) — this is also where the
   edges come from, since a release's `info.requires_dist` names its own
   direct dependencies. Build the graph by following those edges from every
   top-level package (bounded depth — see §7.2 on the depth cap and why).
5. In parallel: run real `carabiner scan --json` and `lockstep check --json`
   against the cloned checkout (via subprocess, matching `invariant`'s own
   `security_scan` check type's exact pattern — see §7.3). Query OSV.dev
   per unique `(name, version)` pair found in the graph. Check whether the
   repo has a `.providence/` bundle and validate it in-process if so.
6. Every node gets annotated with whichever of the four signals actually
   produced a result for it — **`unverified`, not a blended score, for any
   signal that didn't fire** (no lockstep run possible because there's no
   local install to diff against inside a fresh clone — v1 should be honest
   that `lockstep`'s "installed vs. pinned" check only makes sense once
   loom's own scratch clone has the lockfile's exact versions actually
   `pip install`ed into a throwaway venv first; do that install as a real
   step before running `lockstep`, in a container/sandbox — see §7.3 for
   why this must be sandboxed).
7. Results are written to Postgres (`scan.status=complete`, plus `node` and
   `edge` rows). The frontend, which has been polling `GET
   /api/scans/{id}`, gets the full graph payload and renders it.

## 7. Backend

### 7.1 Stack

- **FastAPI** (async), **SQLAlchemy 2.x** + **Alembic** for migrations,
  **Postgres** (matches `recur`'s and `LabLedger`'s own precedent —
  `LabLedger` uses Mongo because its data is genuinely document-shaped
  lab reports; loom's data is genuinely relational — packages, edges,
  scans — so Postgres is the right call here, not cargo-culted from
  either sibling).
- **httpx** for the three external API clients (PyPI, OSV, GitHub) —
  async, and one client class per API, each with its own narrow
  responsibility (see `backend/app/clients/`).
- **subprocess** (stdlib, not a shell-injection-prone `shell=True` call —
  argument lists only) for the real `carabiner`/`lockstep` invocations.

### 7.2 The four signals, exactly how each is computed

1. **Vulnerability (from `carabiner` + direct OSV lookups)** — `carabiner
   scan --json` against the cloned repo gives one pass; additionally, for
   every `(name, version)` node in the resolved graph (including transitive
   ones carabiner's own repo-scoped scan wouldn't see), call OSV.dev's
   `POST /v1/query` with `{"package": {"name": ..., "ecosystem": "PyPI"},
   "version": ...}`. Worst severity across both sources wins, same
   dedup-keep-worse-severity rule `carabiner`'s own README already
   documents for its cross-engine dedup. **Graph depth is capped (default
   3 levels of transitive deps)** specifically because OSV lookups are
   per-package HTTP calls — an uncapped resolution of a real Python
   project's full transitive tree can be hundreds of packages, and this is
   a demo tool, not a production scanner; state the cap plainly in the UI
   ("showing N of M total dependencies, 3 levels deep") rather than
   silently truncating.
2. **Drift (from `lockstep`)** — needs a real installed environment to diff
   against the lockfile, which is `lockstep`'s whole premise ("what's
   actually installed vs. what's pinned"). In loom's context there is no
   pre-existing "installed" environment — so loom creates one: a disposable
   venv, `pip install -r requirements.txt` from the cloned repo's own
   lockfile, then `lockstep check requirements.txt`. Run inside a
   sandboxed subprocess with no network access after the initial install
   (or in a short-lived container if the deploy target supports it) —
   **executing arbitrary `pip install` output for a repo a random user
   submitted is a real code-execution surface, treat it as such**: a
   dedicated low-privilege worker, no secrets in its environment, a hard
   wall-clock timeout, and it should never be the same process handling
   API requests. If this venv-install step is skipped for v1 (a legitimate
   phased-build call — see §10 Phase 1 vs Phase 2), every node's drift
   status is honestly `unverified` with a clear "not yet checked" reason,
   never guessed.
3. **Tamper-evidence (from `providence`)** — check whether the cloned repo
   has a `.providence/` directory or any file matching the single-file
   bundle shape (`providence`'s own `SPEC.md` documents both forms exactly)
   anywhere in the repo. If found, validate it in-process (providence is a
   stdlib-only library — `pip install providence-evidence` if published,
   otherwise vendor the ~200 lines of `check.py` directly, same
   `receipt`/`providence` precedent of small stdlib-only deps). Almost
   every real repo will have none — **that absence is itself the finding**,
   rendered as `unverified`, not swept under a default.
4. **Policy (from `invariant`)** — genuinely optional for v1, and the
   weakest-fit of the four signals, because `invariant` checks are
   repo-specific and hand-written (there's no universal "does this
   dependency tree satisfy a policy" without someone writing that policy
   first). **Recommendation: defer this signal explicitly in v1** rather
   than build a fake generic policy just to have four colors instead of
   three. Note it in the UI as "policy checks: bring your own
   `invariant.yaml`" — an optional file a submitter's repo can include,
   which loom runs if present, `unverified` if absent. This keeps the
   real four-tool story intact without inventing a policy nobody asked
   for.

### 7.3 Shelling out to real tools, safely

`invariant`'s `security_scan` check type is the existing, working precedent
for "call a real sibling CLI as a subprocess and parse its `--json`
output" — read `invariant/checks/security_scan.py` before writing loom's
equivalent, don't reinvent the pattern. Rules to carry over:

- Always pass an explicit argument list, never `shell=True`.
- Always set a timeout; a hung subprocess must produce `unverified` with a
  timeout reason, never hang the whole scan job.
- Capture and redact stdout/stderr the same way `receipt.redact` already
  does, before persisting anything a subprocess printed — a scanned repo's
  own dependency names could theoretically echo something secret-shaped in
  a build script's output, however unlikely; the discipline costs nothing
  and this portfolio has paid for the lesson twice already (`receipt`,
  `invariant`'s DSN redaction).

### 7.4 Why polling, not WebSockets, for v1

A scan takes anywhere from a few seconds (small repo, no lockstep venv
step) to a couple of minutes (large graph, the venv-install path). Simple
`GET /api/scans/{id}` polling every 2s from the frontend is enough,
adds zero new infrastructure, and matches this portfolio's own bias toward
boring-and-correct over impressive-and-fragile. A WebSocket-driven live
node-by-node reveal (each node lighting up as its signal resolves) is a
genuinely nice v2 upgrade — the data model already supports it (nodes get
individually updated rows) — just not a v1 requirement.

### 7.5 Background jobs: `BackgroundTasks` vs. a real queue

Start with FastAPI's own `BackgroundTasks` for Phase 0/1 (see §10) — it's
already there, no new infrastructure. If deployment reveals scans need to
survive an app restart, or need to run on a separate low-privilege worker
(see §7.2's code-execution warning), promote to a real queue (RQ over
Redis is the lightest option, and Render has a one-click Redis add-on) —
but don't build that on day one speculatively. This is a real "upgrade when
it hurts" call, not a shortcut to leave silently undocumented — say so in
the repo's own README when this decision is made for real.

### 7.6 Data model (Postgres, via SQLAlchemy)

```
scan
  id            uuid pk
  repo_url      text
  ref           text (branch/tag/sha submitted, default "HEAD")
  commit_sha    text (resolved once cloned)
  status        text  # pending | cloning | resolving | scanning | complete | failed
  error         text nullable
  lockfile_kind text nullable  # "pip-compile" | "poetry" | null (none found)
  depth_cap     int
  created_at    timestamptz
  completed_at  timestamptz nullable

node
  id                uuid pk
  scan_id           uuid fk -> scan
  package_name      text
  package_version   text
  depth             int  # 0 = top-level, from the lockfile directly
  vuln_severity     text nullable  # none | low | medium | high | critical | unverified
  vuln_detail       text nullable
  drift_status      text nullable  # matched | version_mismatch | missing | extra | unverified
  providence_status text  # verified | unverified  (repo-wide, but denormalized onto every node for simple client rendering)
  policy_status     text  # pass | fail | unverified
  repo_stars        int nullable
  repo_last_commit  timestamptz nullable

edge
  id          uuid pk
  scan_id     uuid fk -> scan
  from_node   uuid fk -> node
  to_node     uuid fk -> node
```

### 7.7 API endpoints (v1)

```
POST   /api/scans                 {repo_url, ref?}        -> {id, status}
GET    /api/scans/{id}            -> full scan + nodes + edges (client polls this)
GET    /api/scans?repo_url=...    -> scan history for a given repo, newest first
GET    /api/scans/{id}/diff/{other_id}  -> node-level diff between two scans of
                                            the same repo (the "drift over time"
                                            payoff from §3's persistence call) —
                                            real, but fine to land in Phase 2/3,
                                            not Phase 0
```

## 8. Frontend

### 8.1 Stack

Vite + React + TypeScript (exactly the portfolio's own toolchain — reuse
its `vite.config.ts`/`tsconfig.json` starting points rather than
reinventing them), **React Three Fiber** + **three.js** for the 3D graph,
**three-forcegraph** or a hand-rolled `d3-force-3d` layout (see §8.3) for
the graph physics, plain CSS (no Tailwind/component library — the
portfolio's own restraint here, "one design system, fully hand-built,"
is a deliberate identity, not a gap to fill with a library).

### 8.2 Visual design system — reuse the portfolio's, don't invent a new one

This is a hard constraint, not a suggestion: loom is a sibling flagship in
the same portfolio, and should read as unmistakably part of the same
family the instant someone lands on it.

- **Palette**: lift `--void`, `--chalk`, `--beam` (`#86E9DE`), `--escalate`
  (`#E8873B`), `--alloy`, `--hair` directly from `portfolio/web/src/
  styles.css`'s `:root` block. `--beam` means "verified/good" everywhere
  in this portfolio already (receipt seals, vessel dials, core sample
  reads) — a `providence`-verified node uses it. `--escalate` means
  "needs a human/escalated" already (the core sample's one non-resolving
  band) — repurpose it here for "vulnerable" severity, which is the same
  underlying idea (something a human needs to look at).
  Reserve full white/`--chalk` for chrome/text only, matching every
  sibling section's own discipline.
- **Typography**: `Archivo` (display), `Instrument Serif` (the one italic
  accent word per heading, exactly like the portfolio's own `<span
  className="serif">` convention), `JetBrains Mono` (numbers, code, package
  names/versions — a package name is exactly the kind of "measured value"
  the portfolio already reserves monospace for).
- **Motion restraint**: the portfolio's scroll-jacked instrument sequence
  does NOT need to be replicated here — loom is a tool, not a landing
  page, and forcing every interaction through a scroll narrative would be
  the wrong transplant. What DOES transplant: the "presence, not
  visibility" weighting discipline (`Instrument.tsx`'s `useWeight`) for
  UI panels appearing/disappearing, `power3.out` easing everywhere,
  `prefers-reduced-motion` respected exactly the way the portfolio's own
  `STILL`/`mode.ts` already models — copy that file's pattern directly.

### 8.3 The 3D graph itself

- **Nodes**: small procedural primitives (see §3's non-negotiable
  constraint) — a sphere is the honest default (a package is a point, not
  a mechanism with moving parts the way the portfolio's own six flagship
  instruments are), sized by dependency count (more depended-upon =
  larger, a real, meaningful signal — not decoration) and colored by the
  worst of its four signal severities. **Bloom** (already proven in the
  portfolio's own `postprocessing` pipeline) on `--beam`/`--escalate`
  nodes for the same "verified glows" language the vessel's seal already
  uses.
- **Edges**: thin lines or thin cylinders (cylinders read better with the
  bloom pass and match the "everything is a machined primitive" material
  language more than a `THREE.Line`, which ignores lighting entirely).
- **Layout**: force-directed in 3D — `three-forcegraph` wraps `d3-force-3d`
  and is the pragmatic choice (a working, maintained library solving a
  genuinely hard problem — this is exactly the "already-installed
  dependency solves it" rung of the ladder, not a place to hand-roll
  physics). If it fights the visual language too hard once real data is
  in it, a custom `d3-force-3d` + hand-written R3F node renderer is the
  fallback — don't decide this in the abstract, decide it after Phase 2's
  first real render.
- **Interaction**: orbit controls (`@react-three/drei`'s `OrbitControls`)
  for free look-around — this is the one place loom's camera model should
  differ from the portfolio's own scroll-locked camera, because "explore
  a graph" and "read a scroll narrative" are different jobs. Click a node
  → a detail panel slides in (reuse the portfolio's own `DeepDive.tsx`
  panel pattern — `inert` on the rest of the page, `Escape`/backdrop-click
  to close, focus returned on close) showing the package name/version and
  all four signals with their real evidence (a link to the OSV entry, the
  raw `carabiner`/`lockstep` finding, etc.) — the same "this is the
  receipt for it, not a claim to take on faith" idea `DeepDive.tsx`'s own
  code comment already states.

### 8.4 Non-3D chrome

- A single input (repo URL, optional ref) + submit — the entire "home
  screen." No marketing copy needed beyond one honest sentence restating
  §1.
- A left rail: scan history for the currently-viewed repo (reuse the
  portfolio's own `.rail` component's visual language — vertical, thin,
  numbered — repurposed from "which section" to "which scan").
  A "compare to previous scan" affordance surfaces the `/diff` endpoint.
- A legend (always visible, small, corner-anchored): what each color and
  size means, plus the depth-cap disclosure from §7.2 — "showing N of M
  dependencies, 3 levels deep" stated on-screen, not just in a tooltip,
  matching this whole portfolio's "state the limit where the limit is
  actually true" discipline.

## 9. Folder structure

```
loom/
├── SPEC.md                    # this file
├── HANDOFF.md                 # progress log — create on first real session,
│                               # same role as the parent portfolio's own
│                               # HANDOFF.md: what's done, what's next, gotchas
├── README.md                  # public-facing, written once Phase 1 is real —
│                               # don't front-load marketing copy before the
│                               # thing exists
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml              # backend tests + frontend build, same shape
│                                # as every sibling repo's own ci.yml
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py             # FastAPI app, route registration
│   │   ├── config.py           # env-driven settings (DB url, external API
│   │   │                        # timeouts, depth cap default)
│   │   ├── models.py           # SQLAlchemy models — scan/node/edge (§7.6)
│   │   ├── db.py                # engine/session setup
│   │   ├── routes/
│   │   │   └── scans.py        # the four endpoints in §7.7
│   │   ├── clients/
│   │   │   ├── pypi.py         # PyPI JSON API client
│   │   │   ├── osv.py          # OSV.dev client
│   │   │   └── github.py       # GitHub REST client, best-effort/cached
│   │   ├── resolve/
│   │   │   ├── clone.py        # shallow git clone to a scratch dir
│   │   │   ├── lockfile.py     # parse requirements.txt / poetry.lock
│   │   │   └── graph.py        # build the node/edge graph from a parsed
│   │   │                        # lockfile + PyPI metadata, depth-capped
│   │   ├── signals/
│   │   │   ├── vuln.py          # carabiner subprocess + OSV per-package
│   │   │   ├── drift.py         # venv install + lockstep subprocess
│   │   │   │                     # (Phase 2 — see §10)
│   │   │   ├── providence.py    # find + validate a .providence/ bundle
│   │   │   └── policy.py        # optional invariant.yaml, if present
│   │   └── orchestrator.py     # the background job tying §6's steps together
│   └── tests/
│       ├── test_lockfile.py     # real requirements.txt / poetry.lock fixtures,
│       │                         # not synthetic one-liners
│       ├── test_graph.py
│       ├── test_pypi_client.py  # against real recorded responses (vcrpy or
│       │                         # a committed fixture), not live network in
│       │                         # every test run
│       ├── test_osv_client.py
│       └── test_orchestrator.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx              # scan form + routes to a graph view
        ├── styles.css           # start from the portfolio's own tokens (§8.2)
        ├── api.ts               # typed client for the backend's 4 endpoints
        ├── scene/
        │   ├── Graph.tsx        # the R3F canvas, force layout, node/edge render
        │   ├── Node.tsx
        │   └── Edge.tsx
        ├── components/
        │   ├── ScanForm.tsx
        │   ├── HistoryRail.tsx
        │   ├── Legend.tsx
        │   └── DetailPanel.tsx  # ported pattern from portfolio's DeepDive.tsx
        └── lib/
            └── mode.ts           # STILL / prefers-reduced-motion, copied
                                    # pattern from the portfolio's own lib/mode.ts
```

## 10. Phased build order

**Phase 0 — walking skeleton (prove the shape end to end with fake data).**
FastAPI app with the four routes returning a hand-written fixture graph (no
real cloning, no real external calls yet). Frontend renders that fixture
as a real 3D force-directed graph with working orbit controls and a click
→ detail panel. **Goal: see a real, walkable, correctly-styled 3D graph on
screen before any scanning logic exists.** This is deliberately the same
discipline `HANDOFF.md`'s own process (§8 of the parent portfolio's
process doc) calls "live-verify, not just unit tests" — here it means
"see the actual rendering work before investing in the data pipeline
that feeds it."

**Phase 1 — real graph, no drift/policy signals yet.** Real clone, real
lockfile parse, real PyPI-metadata-driven edges, real `carabiner` +
direct OSV severity coloring, real `providence` bundle check (usually
`unverified`, and that's correct). Drift (`lockstep`) and policy
(`invariant`) signals both report `unverified` with an honest "not yet
computed" reason — **do not fake these**, ship the honest three-of-four
picture rather than a fake four-of-four.

**Phase 2 — drift signal, sandboxed.** The venv-install + real `lockstep
check` step from §7.2, with its sandboxing/timeout/low-privilege-worker
requirements actually in place — this is explicitly gated behind getting
the code-execution boundary right, not a corner to cut for a demo.

**Phase 3 — polish, deploy, and the diff endpoint.** `/diff` endpoint +
UI, the depth-cap disclosure and legend finished, deploy to Render,
real Lighthouse-style pass on the frontend (the parent portfolio's own
`lighthouse` CI job is the precedent — informational, not a gate, for
the same GPU-less-runner reason documented there).

**Explicitly out of scope for any v1 phase**: the optional `invariant`
policy signal (§7.3's honest call), npm/Cargo ecosystems, auth, scheduled
re-scans, WebSocket live-reveal. Note each here so nobody "discovers" them
mid-build as if they were forgotten — they were considered and deferred on
purpose.

## 11. Testing & verification discipline

Same bar every repo in this portfolio already holds itself to (see the
parent `HANDOFF.md`'s §6, "Portfolio-wide quality standard"):

- Real fixtures, not synthetic one-liners: a real `requirements.txt` from
  a real pip-compile run, a real (small, public) repo's real lockfile
  committed as a test fixture, the same way `drift`'s tests use a real
  downloaded Wireshark capture rather than a hand-built one.
- External API clients (`pypi.py`, `osv.py`, `github.py`) get tests against
  **recorded real responses** (commit a small number of real JSON
  fixtures captured once, don't hit live network on every CI run, don't
  mock the shape of a response you've never actually seen).
- **Live-verify the whole pipeline against a real, small, public
  repo** before calling any phase done — not just unit tests on parsers.
  Pick something genuinely small (a handful of dependencies) for this,
  not this portfolio's own biggest repos.
- The subprocess-sandboxing boundary in §7.2 gets its own explicit
  adversarial test once Phase 2 is built: a lockfile engineered to try
  something hostile during its `pip install` step, confirming the
  sandbox actually holds — the same "adversarial pass, not just the happy
  path" discipline `carabiner`'s Jenkins-fixture work and `portable`'s
  own audit pass already modeled in this portfolio.

## 12. Deployment

Render, matching `recur` and `LabLedger`: a web service for the FastAPI
backend, a static site (or a second Render service) for the Vite build,
a managed Postgres instance. Environment variables for DB URL, OSV/GitHub
API base URLs (no keys needed for either in v1), and the depth-cap
default. Once Phase 2's sandboxing lands, the drift-signal worker should
run as its own Render service with a minimal environment — no shared
secrets with the API service — per §7.2's own requirement.

## 13. Open questions / decisions deliberately left to the building agent

These are real unknowns this spec didn't resolve, on purpose — pick a
reasonable default, state the choice plainly in `HANDOFF.md` when you make
it (same discipline as everything else in this portfolio), and move on
rather than blocking:

- **Exact force-directed layout tuning** (charge strength, link distance)
  can't be right until real data is in front of it — Phase 0's fixture
  graph is exactly for finding this out cheaply.
- **poetry.lock parsing** — `poetry.lock` is TOML with its own real shape;
  confirm the exact fields to read against a real, current Poetry version's
  actual output (poetry's lockfile format has changed across major
  versions) rather than trusting a remembered schema.
- **GitHub API rate-limit handling under real load** — the 60 req/hr
  unauthenticated ceiling is tight; decide whether to skip this signal
  entirely past a certain graph size, or queue/cache more aggressively,
  once Phase 1 shows real usage patterns.
- **Whether `three-forcegraph` or a hand-rolled layout wins** — see §8.3,
  decide after Phase 2's first real render, not before.

---

*Written 2026-09-10, as a sibling project to the 9+8-repo "Evidence, Not
Claims" portfolio at `/Users/ritis/Documents/Personal/`. If this file and
that portfolio's own `HANDOFF.md`/repo READMEs ever disagree about a
shared convention (palette tokens, subprocess-calling pattern, redaction
discipline), the actual current code in those sibling repos wins — this
spec describes them accurately as of the date above, but they may have
moved since, the same "don't trust a stale doc" lesson that portfolio's
own `HANDOFF.md` had to learn about itself more than once.*
