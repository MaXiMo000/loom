# loom — HANDOFF

**Read this first if picking this up in a new session.** Same role as the
parent portfolio's own `HANDOFF.md`: what's done, what's next, decisions
made along the way. Read `SPEC.md` first regardless — it's the actual
architecture doc, this is only the progress log.

## 2026-09-10: Phase 0 walking skeleton — done, live-verified

**What's running**: a real FastAPI backend (`backend/`) serving a
hand-written fixture dependency graph (12 real PyPI package names —
`requests`/`flask` and their direct/transitive deps — with varied,
plausible severities) over the real 4-route contract from SPEC.md §7.7. A
real Vite + React + TypeScript + React Three Fiber frontend (`frontend/`)
fetches that fixture and renders it as an actual 3D force-directed graph:
orbit controls, click-a-node → detail panel (with the four signals, real
evidence text, stars/last-commit meta), a corner-anchored legend stating
the depth-cap disclosure, bloom on emissive nodes. Palette/type tokens and
fonts are copied directly from `portfolio/web` (SPEC.md §8.2's hard
constraint), and the detail panel's focus/inert/Escape handling is ported
line-for-line from `portfolio/web/src/DeepDive.tsx`'s own pattern.

**No real scanning exists yet** — no clone, no PyPI/OSV/GitHub calls, no
carabiner/lockstep subprocess. That's Phase 1.

### Decisions made (SPEC.md §13 + implementation calls along the way)

- **three-forcegraph vs. hand-rolled d3-force-3d (§13, explicitly left
  open)**: went hand-rolled for Phase 0. Reasoning: click-to-detail is a
  hard Phase-0 requirement, and a hand-rolled R3F renderer gives every
  node its own real `<mesh onClick>` wired straight to React state —
  three-forcegraph manages its own internal Three.js object graph, which
  would mean raycasting into it and mapping hits back to React state
  instead. `d3-force-3d` itself is still the "already-installed dependency
  solves the hard physics problem" rung of the ladder — only the
  rendering/interaction layer is hand-rolled, matching SPEC.md §8.3's own
  stated fallback. Revisit at Phase 2 if a real, much larger graph makes
  hand-rolled per-node meshes a real performance problem.
- **Force-layout tuning (§13, explicitly left open)**: the fixture graph
  resolves to two *disconnected* components (no edge between the
  `requests` family and the `flask` family) — under repulsion-only forces
  they drift apart without bound (found by live-verifying: they settled
  ~50 units apart, invisible outside a normal camera frustum). Fixed two
  ways, not by guessing a "correct" charge constant: (1) a weak `forceX/Y/Z`
  pull-to-origin on every node keeps disconnected components in the same
  neighborhood without fighting each component's own internal link/charge
  structure; (2) `@react-three/drei`'s `<Bounds fit clip observe>` auto-
  fits the camera to whatever the layout actually produces, so the exact
  charge/link constants stop being something that has to be "right" for
  the scene to be visible at all. This is the real answer to §13's "can't
  be tuned right until real data is in front of it" — Phase 1's real,
  bigger, more connected graphs may still want different constants, but
  the scene won't go dark again while that gets found out.
- **Node/edge ids in the fixture are readable slugs, not uuids.** SPEC.md
  §7.6's real schema is uuid pks; Phase 1, once nodes are actually
  persisted to Postgres, switches to real generated uuids. Fine for a
  fixture that's never written to a database.
- **HistoryRail (SPEC.md §8.4) deferred past Phase 0.** There's exactly
  one fixture scan — a "scan history" rail has nothing real to show yet.
  ScanForm and Legend are both built (cheap, and Legend's depth-cap
  disclosure is a real SPEC.md requirement); ScanForm is present but
  disabled, since faking a scan result would be worse than an honest
  "arrives in Phase 1."
- **`/api/scans/{id}/diff/{other}` (Phase 3 per SPEC.md §10) exists as a
  route now**, returning an honest empty diff with a note — the real
  4-route contract was worth landing in full even though only 3 of the 4
  routes have real Phase-0 behavior behind them, so the frontend never has
  to change its API surface later.
- **CI**: `actions/checkout`/`actions/setup-python` pins copied from
  `lockstep`'s already-vetted `ci.yml`; `actions/setup-node@v5` is a tag
  ref, not a pinned sha, since no vetted pin for it exists elsewhere in
  this portfolio yet — a minor, known inconsistency, not a security
  regression for a personal-portfolio CI job.

### Verified

- Backend: `cd backend && .venv/bin/python -m pytest -q` — 7 passed
  (route shapes, 404 on unknown scan id, every edge endpoint resolves to a
  real node in the same payload).
- Frontend: `cd frontend && npx vitest run` — 6 passed (severity/color
  priority logic — vuln beats a verified providence status, a clean node
  reads neutral rather than guessed-good — and in-degree/radius math).
  `npx tsc -b` clean, `npx vite build` clean (one expected bundle-size
  warning from three.js — real, deferred code-splitting, not a bug).
- **Live-verified in a real browser** (not just the above), the actual bar
  this portfolio holds itself to: loaded the real dev server against the
  real backend, confirmed the 3D graph renders with correct per-severity
  colors (escalate-orange for vulnerable nodes, beam-teal for the one
  providence-verified node, neutral for everything else), dragged to
  confirm orbit controls actually rotate the camera, clicked a node and
  confirmed the detail panel opens with the right package's real signal
  values, confirmed Escape closes it and focus returns to the graph, and
  confirmed via `document.querySelector` that `inert` lands on
  `.scene-root` (not on the panel itself — an actual bug caught this way:
  the panel was originally nested inside the element it made inert, which
  would have made its own Close button unreachable; fixed by giving the
  scene its own wrapper sibling to the panel, matching the portfolio's own
  `<main>`/`<DeepDive>` sibling split exactly).

### Run it locally

```
cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --port 8123

cd frontend && npm install && npm run dev -- --port 5190 --strictPort
```

## 2026-09-10 (same day): Phase 1 — real graph, real signals — done, live-verified

**What's running now**: the fixture is gone (`backend/app/fixtures.py`
deleted, nothing referenced it once real data flowed). `POST /api/scans`
kicks a real `BackgroundTasks` job (`app/orchestrator.py`) that: shallow-
clones the real repo over a real `git clone` subprocess (`app/resolve/
clone.py`), finds and parses a real `requirements.txt`/`poetry.lock`
(`app/resolve/lockfile.py`), resolves the real dependency graph by walking
real PyPI `requires_dist` metadata with a depth cap (`app/resolve/
graph.py`), computes real vulnerability severity from a real `carabiner
scan --json` subprocess plus a real per-package OSV.dev `POST /v1/query`
(`app/signals/vuln.py`), checks for a real Providence bundle
(`app/signals/providence.py`, using the vendored `check_bundle` —
`app/vendor/providence/`), and persists everything to a real Postgres
(`app/models.py` + Alembic). Drift and policy stay honestly `unverified`
(Phase 2/deferred, per SPEC.md §10 — not faked). The frontend's `ScanForm`
is real and enabled now: submit a URL, watch real stage labels (cloning →
resolving → scanning) as the UI polls `GET /api/scans/{id}` every 2s
(SPEC.md §7.4), then the real 3D graph renders.

### Decisions made (SPEC.md §13 + implementation calls along the way)

- **PyPI-driven edges over `pip-compile`'s own `# via` comments.** A real
  pip-compile `requirements.txt` already states its own edges as comments
  (`# via requests`) — cheaper than an HTTP call per package. Went with
  SPEC.md §6's explicit instruction (PyPI `requires_dist`) anyway, for one
  reason: `poetry.lock` has no equivalent annotation, and a single
  edge-resolution code path for both lockfile kinds beat two. Depth is
  computed from the *derived* edges (BFS from in-degree-0 roots), not from
  `# via` presence, for the same reason.
- **Depth-cap fetching fetches the whole (size-capped) pinned closure up
  front, not a true frontier-bounded BFS.** A real pip-compile lockfile is
  already a finite, fully-resolved set — fetching PyPI metadata for all of
  it (capped at `LOOM_MAX_PACKAGES`, default 150, a defensive guard
  distinct from the user-facing "3 levels deep" disclosure) is simpler
  than incrementally expanding a frontier level-by-level, and correct for
  any realistic demo-sized repo. `# ponytail: revisit with real
  incremental fetching if a huge lockfile makes a scan too slow.`
- **`POST /v1/query` per node, not `/v1/querybatch`.** Checked both against
  the real API: batch responses carry only vuln ids, no severity — and
  severity is the entire point. The N-calls cost this implies is exactly
  what SPEC.md §7.2 already says the depth cap exists to bound.
- **carabiner-finding-to-node correlation is a best-effort substring match**
  on the finding's own `message`/`path` text — carabiner's `Finding` has no
  structured package-name field. Only ever *raises* a node's severity above
  what OSV found directly, never lowers it. A real, live-verified case
  actually exercised this for real (see below) — carabiner's own
  `osv-scanner`-backed `deps` engine found a real CVE on `flask==3.0.3`
  that this session's direct OSV query alone had NOT surfaced, and the
  worst-of-both merge correctly picked it up.
- **providence-evidence vendored, not pip-installed** — confirmed via
  `pip index versions providence-evidence` that it's genuinely not
  published yet (matches the parent portfolio's own HANDOFF notes).
  `check.py`+`spec.py` copied verbatim from providence's real repo at a
  pinned commit (`app/vendor/providence/__init__.py` records which one) —
  MIT, same author, exactly SPEC.md §7.2's stated fallback.
  `carabiner-sec`, by contrast, genuinely is on PyPI (confirmed the same
  way) — it's a real `pip install` dependency, subprocess-invoked per
  `invariant/checks/security_scan.py`'s exact pattern.
- **Sync SQLAlchemy, not async.** Routes are sync `def`s (FastAPI runs
  those in its own threadpool) and the scan job is a `BackgroundTasks`
  function (also thread-run) — nothing here is high-concurrency enough to
  need async SQLAlchemy on top.
- **CI runs a real Postgres service container**, not sqlite — the same
  "real disposable Postgres, not a mock" discipline `recur`/`LabLedger`
  already hold themselves to in this portfolio. `osv-scanner` is
  deliberately *not* installed in CI (carabiner's `deps` engine just finds
  nothing to run without it) — the direct per-package OSV.dev calls stay
  the real, complete vulnerability source regardless; carabiner only ever
  adds to that.
- **HistoryRail (SPEC.md §8.4) still deferred**, now past Phase 1 too.
  Real scan history exists (`GET /api/scans?repo_url=...` is real and
  tested) but the frontend doesn't surface it yet — SPEC.md pairs the
  "compare to previous scan" affordance with the `/diff` endpoint, and
  `/diff` is explicitly Phase 3. Landing both together avoids a rail that
  can list scans but can't yet do anything with more than one.

### Verified

- Backend: `cd backend && .venv/bin/python -m pytest -q` — **28 passed**
  (was 7). Real fixtures throughout, not synthetic one-liners (SPEC.md
  §11): `tests/fixtures/requirements.txt` is a real `pip-compile` output
  (flask==3.0.3 closure), `tests/fixtures/poetry.lock` a real
  `poetry lock` output (requests==2.31.0) — both generated by actually
  running the real tools. `tests/fixtures/pypi/*.json` and `tests/
  fixtures/osv/*.json` are real recorded API responses (respx serves them
  in tests — no live network in CI). `test_orchestrator.py` runs the real
  orchestrator end-to-end against a real local git repo + real Postgres,
  with only the two genuinely-external APIs (PyPI/OSV) mocked from those
  same real recordings.
- Frontend: `npx vitest run` — 6 passed, `npx tsc -b` clean, `npx vite
  build` clean.
- **Live-verified against real, live infrastructure** — not just the
  fixtures above: started the real FastAPI app against a real local
  Postgres (`docker compose up -d` in `backend/`, or the standalone `docker
  run` in "Run it locally" below) and drove it two ways:
  1. `POST /api/scans` for `https://github.com/MaXiMo000/lockstep` (a
     real public repo, real network clone) — correctly ended `failed` with
     the honest "no lockfile found" error, since `lockstep` genuinely has
     no pip-compile/poetry lockfile. Proves the real-network clone path
     and the honest-failure path together, for real.
  2. `POST /api/scans` for a real local git repo seeded with the real
     `flask==3.0.3` fixture lockfile — completed for real, hitting the
     **real live PyPI and OSV.dev APIs** (not mocked): 7 nodes, 7 edges,
     correct depths (flask=0, its direct deps=1, markupsafe=2, reached
     only via jinja2/werkzeug). `flask` came back `vuln_severity: medium`
     from a real carabiner-correlated finding (`CVE-2026-27205`) — a
     genuine real-world hit, not a planted fixture.
  3. Drove the same scan through the real browser UI end to end: typed a
     URL, watched the real stage labels progress, watched the real 3D
     graph render with `flask` correctly colored escalate-orange, clicked
     it, and confirmed the detail panel showed the real carabiner finding
     **and** real GitHub metadata (flask's real star count and last-commit
     date, fetched live from `api.github.com` for `pallets/flask` — the
     package's own upstream repo, not the scanned repo).
  4. **A real bug found this way, not by a unit test**: clicking a node
     made the camera visibly drift on every subsequent click. Root cause —
     `<Bounds observe>` re-fits the camera to its children's live bounding
     box, and `Node.tsx` scaled a node 1.15× on hover, which shifted that
     box every time the mouse crossed a node. Fixed by dropping the hover
     scale (brightness alone is enough feedback) and dropping `observe` in
     favor of fitting once, keyed on the graph itself.

### Run it locally

```
cd backend
docker compose up -d          # real local Postgres on 127.0.0.1:5439
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --port 8123

cd frontend && npm install && npm run dev -- --port 5190 --strictPort
```

## 2026-09-10 (same day): Phase 2 — sandboxed drift signal — done, adversarially verified

**What's running now**: `node.drift_status` is real. `app/signals/drift.py`
runs two separate short-lived Docker containers per scan (`backend/
drift-worker/Dockerfile` + `entrypoint.sh`) — `install` (network enabled,
creates a fresh venv, installs the target repo's own pinned
`requirements.txt` plus `lockstep` from a wheel baked into the image at
build time, never from PyPI/git at scan time) and `check` (started with
`--network=none` from the host side — `lockstep check` only reads local
`importlib.metadata`, so there's no legitimate reason for this stage to
ever make a network call, and the host removes the capability outright
rather than trusting the process not to attempt one). Both containers are
non-root (fixed uid `10001`), `--cap-drop=ALL`, `--security-opt
no-new-privileges`, resource-capped (`--memory=768m --pids-limit=256
--cpus=1`), `--rm`, and get nothing from the API process's own
environment. Auto-detected: if Docker isn't reachable in a deployment
(true of the current setup — Render's web/worker services don't expose a
Docker daemon, see the decision below), drift honestly reads `unverified`
with a stated reason, never guessed.

### Decisions made (SPEC.md §7.2/§13 + implementation calls along the way)

- **A real, discovered deployment blocker, decided explicitly rather than
  worked around silently**: SPEC.md §7.2 offers two sandboxing shapes — "a
  sandboxed subprocess with no network access after the initial install"
  or "a short-lived container if the deploy target supports it." The
  actual v1 deploy target (SPEC.md §12) is Render, whose standard
  web/worker services do **not** expose a Docker daemon to the running
  container — so the container approach this session built cannot run
  as-is on the currently-targeted deployment. Decided to build it for
  real anyway (auto-detected via `sandbox_available()`) rather than build
  the weaker subprocess-only path first: it's the stronger, spec-sanctioned
  isolation, it's fully real and adversarially verified today for local
  dev/self-hosted/any Docker-capable deploy, and it degrades to an honest
  `unverified` everywhere else — exactly SPEC.md §7.2's own explicitly
  sanctioned fallback ("If this venv-install step is skipped for v1... every
  node's drift status is honestly unverified"). Making the current Render
  deployment actually support this (its own worker service with Docker
  access, or rewriting the sandbox as a resource-limited subprocess with
  `resource.setrlimit`, which SPEC.md §12 already anticipates: "Once Phase
  2's sandboxing lands, the drift-signal worker should run as its own
  Render service") is real, separately-scoped infra work, not a reason to
  not build the real signal today.
- **Two separate containers sharing a bind-mounted scratch dir, not one.**
  Satisfies SPEC.md §7.2's stricter "no network access after the initial
  install" literally, rather than settling for the "short-lived container"
  fallback's weaker bar. `lockstep` itself is installed from a wheel baked
  into the image at *build* time (not fetched from PyPI/git per scan) so
  the `check` stage never needs network for its own tooling either.
- **`node.drift_detail` added**, mirroring `vuln_detail` — not in SPEC.md
  §7.6's original table, added because lockstep's own real `detail` string
  ("'flask' matches its locked version 3.0.3") is exactly the kind of
  "receipt, not a claim" the detail panel already promises for every other
  signal; leaving drift as the one signal with no evidence text would have
  been the actual inconsistency.
- **Known infra noise filtered before it reaches a node**: a fresh venv
  always carries `pip` (and would carry `setuptools`/`wheel` on some
  Python versions) plus `lockstep-evidence` itself — all would otherwise
  read as `extra` (installed, not declared) on *every single scan*,
  which is a fact about loom's own sandbox, not a finding about the
  scanned repo. Filtered by name before results are matched to nodes.
- **Why comparing installed-vs-pinned isn't tautological even though loom
  controls both sides** (worth stating since it's not obvious): loom
  installs exactly what the lockfile pins into a fresh venv, so of course
  it usually matches — the real value is in when it *doesn't*: a package
  version yanked from PyPI since the lockfile was written fails to
  install and reads `missing` (real, live-verified below), or a lockfile
  that's silently incomplete (declares fewer packages than its own
  transitive closure actually needs) would surface undeclared packages as
  `extra`. Both are genuine facts about whether the repo's own lockfile
  still holds up, not artifacts of loom's process.
- **poetry.lock drift-checking not supported yet** — `pip install -r` needs
  a real `requirements.txt`; a `poetry.lock` repo would need `poetry
  export` run first, which is real, scoped, separate work. Reads
  `unverified` with that reason stated, not silently skipped.

### Verified

- Backend: **36 passed** (was 28) — 8 new tests in
  `tests/test_drift_signal.py`, all against the **real image**, not a
  mock (a session-scoped `conftest.py` fixture builds it once, skips the
  whole module if Docker isn't available — every CI run has it). Covers:
  a real clean install reading `matched` for every package, infra-noise
  filtering not eating a real package, a genuinely nonexistent pinned
  package failing to install and reading honestly rather than crashing,
  poetry/no-sandbox both reading their stated `unverified` reasons — **and
  the real adversarial pass SPEC.md §11 requires**: a real local package
  whose `setup.py` (executed unconditionally at pip-install time — real,
  not simulated) tries three real attacks, run against the real sandbox:
  1. writes to `/tmp/loom-adversarial-marker` — "succeeds" from the
     hostile code's own point of view (it's writing into the container's
     own ephemeral filesystem), and the test asserts that path **does
     not exist on the host** — the actual isolation guarantee.
  2. reads the process's own environment — asserts nothing SECRET/TOKEN/
     DATABASE-shaped ever appears (`docker run` here never forwards this
     process's own env).
  3. a direct proof of the `check` stage's exact flag
     (`--network=none`) actually returns "Network is unreachable" against
     a real external host, independent of any package's own behavior.
     A separate test confirms `--pids-limit` actually caps a real fork
     bomb at the configured ceiling, not merely in theory.
  `test_orchestrator.py`'s full end-to-end test now asserts real
  `drift_status == "matched"` results (was a Phase-1-era `unverified`
  placeholder) with a real `drift_detail` string — updated because it's
  now genuinely wrong to assert otherwise, not loosened.
- Frontend: `npx vitest run` (6 passed), `npx tsc -b` clean.
- **Live-verified beyond the test suite**: built the real image
  (`docker build`), ran the real two-container flow manually against the
  real flask fixture closure (`install` succeeds silently, `check` — run
  with `--network=none` — returns real JSON: 7 `matched`, plus `pip` and
  `lockstep-evidence` correctly filtered as expected infra noise before
  reaching any node). Ran the *adversarial* package manually the same
  way before it became a committed test, confirming by hand what the
  automated version now asserts. Then drove a real scan through the real
  browser UI end to end: `flask`'s detail panel showed real `vuln_detail`
  (a real carabiner-found CVE) **and** real `drift_detail`
  (`'flask' matches its locked version 3.0.3`) together for the first
  time, plus real GitHub metadata — three of the four signals now
  genuinely computed on one node, exactly SPEC.md §1's whole premise.

### Run it locally

```
cd backend
docker compose up -d                                   # real local Postgres
docker build -t loom-drift-worker:local drift-worker/   # the drift sandbox image
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --port 8123

cd frontend && npm install && npm run dev -- --port 5190 --strictPort
```

### Next (Phase 3, SPEC.md §10)

`/diff` endpoint's real node-level implementation + UI, the `HistoryRail`
(deferred twice now — SPEC.md §8.4 pairs it with `/diff`, landing both
together), deploy to Render (SPEC.md §12 — including deciding for real
whether the drift-signal worker gets its own Docker-capable Render
service, or whether Phase 2's sandbox gets reimplemented as a
resource-limited subprocess for that specific deployment target, per the
decision recorded above), a real Lighthouse-style pass on the frontend.
