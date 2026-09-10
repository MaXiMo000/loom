# Kickoff prompt — paste this into a fresh agent session to start building

Copy everything below the line into a new session (any coding agent) with
this repo (`/Users/ritis/Documents/Personal/loom`) open as the working
directory.

---

Read `SPEC.md` in this repo in full before doing anything else — it's
written to be self-contained and answers almost every "what should this
do" question you'll have. Don't start writing application code until
you've read all of it, including §13 (the questions it deliberately left
open for you).

This is a new project: **loom**, a 3D dependency-graph visualizer that
weaves together the real, working outputs of four sibling tools
(`carabiner`, `lockstep`, `providence`, `invariant`) — all cloned locally
alongside this repo, under `/Users/ritis/Documents/Personal/`. Read
`../HANDOFF.md` (the parent portfolio's own handoff doc) for the process
discipline this whole family of repos already follows — git identity
per repo, live-verification bar, honest "unverified ≠ pass" three-state
model, redaction discipline — and hold loom to the same bar from the
first commit, not as cleanup later.

**Before your first commit in this repo**: run `git config user.email` and
confirm it's `109451965+MaXiMo000@users.noreply.github.com` (the personal
account) — the global default is a work email and must never land in a
commit here. If it's not set, set it locally in this repo only.

**Start with SPEC.md's Phase 0** (§10): a walking skeleton with a fixture
graph, proving the 3D rendering, styling, and click-to-detail interaction
actually work before any real scanning logic exists. Don't skip ahead to
Phase 1's real data pipeline before Phase 0 is genuinely running and
looks right — "see the actual rendering work before investing in the
pipeline that feeds it" is the whole point of that ordering.

**Create `HANDOFF.md` in this repo** (this repo doesn't have one yet — you're
creating it, not continuing one) the first time you have real progress to
record: what's done, what's next, and any decision you made from SPEC.md
§13's open-questions list, stated plainly the same way the parent
portfolio's own `HANDOFF.md` documents its own decisions. Update it as you
go, not only at the end of a session.

**When you have something real running**: create the GitHub repo under the
`MaXiMo000` account and push, following the exact steps in
`~/.claude/CLAUDE.md`'s "New personal/portfolio projects" section (gh auth
switch, `gh repo create --public`, fix the remote to the personal SSH host
alias, switch gh auth back). Don't wait to be asked.

Ask me directly only if something in SPEC.md is genuinely contradictory or
missing information that would change the architecture, not for ordinary
implementation judgment calls — those are yours to make and document, the
same way every sibling repo in this portfolio was actually built.
