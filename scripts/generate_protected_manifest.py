#!/usr/bin/env python3
"""Regenerates scoring/PROTECTED_MANIFEST.json from the current tree.

Run this and commit the result whenever you (the hackathon organizer)
intentionally change anything outside submissions/. This script
prints the manifest file's own sha256 at the end - update the
PROTECTED_MANIFEST_SHA256 repository variable (Settings -> Secrets and
variables -> Actions -> Variables) to match every time you regenerate;
that variable lives outside the git tree, which is what makes the
manifest file itself tamper-evident (see scoring/integrity.py).

Usage (from repo root):
    python scripts/generate_protected_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring.integrity import build_manifest  # noqa: E402


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    manifest = build_manifest(repo_root)
    out_path = repo_root / "scoring" / "PROTECTED_MANIFEST.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {len(manifest)} protected file hashes to {out_path}")

    manifest_sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print("")
    print("Now update the PROTECTED_MANIFEST_SHA256 repository variable to:")
    print(f"  {manifest_sha256}")
    print("(Settings -> Secrets and variables -> Actions -> Variables tab)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
