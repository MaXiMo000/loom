"""The Providence bundle shape, v1. See ../SPEC.md for the full writeup.

Two conformant forms, both just "content + sha256(content) + when":

  Bundle directory: manifest.json + one file per item, `<id>.json`, whose
  exact on-disk bytes hash to the item's `sha256`. This is invariant's
  evidence.write() shape today, field names aside.

  Single file: one JSON object holding `payload` plus a `sha256` of that
  payload's canonical serialization. This is receipt's evidence.write()
  shape today, field names aside.
"""
from __future__ import annotations

import hashlib
import json

PROVIDENCE_VERSION = 1


def canonical_bytes(payload) -> bytes:
    """The one serialization Providence hashes payloads with: compact,
    sorted keys, so the same logical content always hashes the same way
    regardless of who wrote it or with what json.dumps() options.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def canonical_hash(payload) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def file_hash(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
