"""check_providence against real providence bundles, written with the real
vendored check_bundle logic (app/vendor/providence) — not a hand-simulated
shape."""

from __future__ import annotations

import json

from app.signals.providence import check_providence
from app.vendor.providence.spec import canonical_hash


def test_no_bundle_reads_unverified(tmp_path):
    status, detail = check_providence(tmp_path)
    assert status == "unverified"


def test_real_conformant_single_file_bundle_reads_verified(tmp_path):
    payload = {"hello": "world"}
    bundle = {
        "providence_version": 1,
        "generated_at": "2026-01-01T00:00:00Z",
        "tool": "test",
        "payload": payload,
        "sha256": canonical_hash(payload),
    }
    (tmp_path / "evidence.json").write_text(json.dumps(bundle))
    status, detail = check_providence(tmp_path)
    assert status == "verified"


def test_tampered_bundle_reads_unverified_not_verified(tmp_path):
    bundle = {
        "providence_version": 1, "generated_at": "2026-01-01T00:00:00Z", "tool": "test",
        "payload": {"hello": "world"}, "sha256": "0" * 64,  # deliberately wrong
    }
    (tmp_path / "evidence.json").write_text(json.dumps(bundle))
    status, detail = check_providence(tmp_path)
    assert status == "unverified"


def test_dot_providence_directory_form(tmp_path):
    import hashlib

    bundle_dir = tmp_path / ".providence"
    bundle_dir.mkdir()
    # Directory form hashes the raw on-disk bytes of each item file, not
    # canonical_hash(payload) (that's the single-file form's rule) — write
    # the file first, then hash exactly those bytes.
    raw = json.dumps({"x": 1})
    (bundle_dir / "a.json").write_text(raw)
    item = {"id": "a", "sha256": hashlib.sha256(raw.encode()).hexdigest()}
    (bundle_dir / "manifest.json").write_text(json.dumps(
        {"providence_version": 1, "generated_at": "2026-01-01T00:00:00Z", "tool": "test", "items": [item]}
    ))
    status, detail = check_providence(tmp_path)
    assert status == "verified"
