"""Drift signal (SPEC.md §7.2 point 2, §10 Phase 2). Needs a disposable,
sandboxed venv-install step that hasn't been built yet — every node reports
`unverified` with an honest reason, never a guessed `matched` (SPEC.md §10:
"ship the honest three-of-four picture rather than a fake four-of-four")."""

from __future__ import annotations

DRIFT_UNVERIFIED_REASON = "not yet computed — lockstep's sandboxed venv-install step is Phase 2 (SPEC.md §7.2/§10)"
