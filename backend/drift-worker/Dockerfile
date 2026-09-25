# The drift signal's sandbox (SPEC.md §7.2 point 2, §10 Phase 2).
#
# Never the API process, never privileged, never holds secrets. Run twice
# per scan, as two SEPARATE `docker run` invocations sharing one bind-
# mounted scratch dir (app/signals/drift.py orchestrates both):
#   1. `install` — network enabled (has to reach PyPI for whatever a
#      random submitted repo's lockfile pins). Creates a fresh venv and
#      installs the target requirements.txt PLUS lockstep, from a wheel
#      already baked into this image — never from PyPI or git at scan
#      time, so this step needs no more network access than the target
#      repo's own dependencies already require.
#   2. `check`   — the container for this stage is started with
#      `--network=none` from the host side (app/signals/drift.py, not
#      this file). `lockstep check` only reads local importlib.metadata;
#      there is no legitimate reason for this stage to ever make a
#      network call, so the host cuts the capability outright rather than
#      trusting the process not to.
#
# lockstep-evidence is pinned to an exact PyPI release and baked in as
# wheels (it plus its one dependency, packaging) once at image-build time,
# so a scan never fetches it.
FROM python:3.12-slim AS wheel-builder
RUN pip wheel --no-cache-dir -w /wheels "lockstep-evidence==0.1.1"

FROM python:3.12-slim
COPY --from=wheel-builder /wheels /opt/wheels

# Non-root: this container runs arbitrary, untrusted pip-install-time code
# (setup.py / build backends) for whatever a random submitted repo pins.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin loom
WORKDIR /work
RUN chown loom:loom /work
USER loom

COPY --chown=loom:loom entrypoint.sh /home/loom/entrypoint.sh
ENTRYPOINT ["/bin/sh", "/home/loom/entrypoint.sh"]
