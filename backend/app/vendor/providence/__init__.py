"""Vendored from github.com/MaXiMo000/providence (MIT, same author) at
commit ce396ab8c6dd09998428443f9ff3d57fae289acb — `check.py` + `spec.py`
only, unmodified except this note. Re-vendored for the fix that rejects
item ids escaping the bundle directory -- which matters here, since loom
runs this against repos cloned from the internet. Swap this for a real
`providence-evidence>=0.1.1` dependency once that release is on PyPI --
don't let this copy silently drift from the real package."""
