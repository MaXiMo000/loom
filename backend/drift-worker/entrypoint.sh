#!/bin/sh
# Two subcommands, run as two separate `docker run`s by app/signals/drift.py
# so the host can cut network between them (see Dockerfile's own comment).
set -eu

case "${1:-}" in
  install)
    python -m venv /work/venv
    /work/venv/bin/pip install --no-cache-dir --disable-pip-version-check -q \
      -r /work/requirements.txt
    # From the wheel baked into this image at build time -- no network,
    # no git, no PyPI lookup for lockstep itself at scan time.
    /work/venv/bin/pip install --no-cache-dir --disable-pip-version-check -q \
      --no-index --find-links=/opt/wheels lockstep-evidence
    ;;
  check)
    /work/venv/bin/lockstep check /work/requirements.txt --json
    ;;
  *)
    echo "usage: install|check" >&2
    exit 2
    ;;
esac
