#!/bin/sh
# Two subcommands, run as two separate `docker run`s by app/signals/drift.py
# so the host can cut network between them (see Dockerfile's own comment).
set -eu

case "${1:-}" in
  install)
    python -m venv /work/venv
    /work/venv/bin/pip install --no-cache-dir --disable-pip-version-check -q \
      -r /work/requirements.txt
    # From the wheels baked into this image at build time -- no network,
    # no PyPI lookup for lockstep itself at scan time. --no-deps so it can
    # never change a version the target repo pinned; its one dependency
    # (packaging) is only added when the target environment has none.
    /work/venv/bin/pip install --no-cache-dir --disable-pip-version-check -q \
      --no-index --find-links=/opt/wheels --no-deps lockstep-evidence
    /work/venv/bin/python -c "import packaging.version" 2>/dev/null || \
      /work/venv/bin/pip install --no-cache-dir --disable-pip-version-check -q \
        --no-index --find-links=/opt/wheels packaging
    ;;
  check)
    /work/venv/bin/lockstep check /work/requirements.txt --json
    ;;
  *)
    echo "usage: install|check" >&2
    exit 2
    ;;
esac
