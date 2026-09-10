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
  `lockstep`'s already-vetted `ci.yml`; `actions/setup-node@v4` is a tag
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

### Next (Phase 1, SPEC.md §10)

Real clone, real lockfile parse (`requirements.txt`/`poetry.lock`), real
PyPI-metadata-driven edges, real `carabiner` + direct OSV severity
coloring, real `providence` bundle check. Drift (`lockstep`) and policy
(`invariant`) stay honestly `unverified` until Phase 2 — do not fake a
four-of-four picture early.
