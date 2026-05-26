#!/usr/bin/env python3
"""Regenerate MANIFEST.sha256.json from current disk content.

Walks all git-tracked files, computes SHA256 + byte count for each real
file, and writes a sorted JSON manifest. LFS pointer stubs are detected
and their entries are preserved from the existing manifest (since the
real-content hash cannot be computed from a 130-byte stub).

Usage:
    python scripts/update_manifest.py          # regenerate manifest
    python scripts/update_manifest.py --check  # verify-only (delegates to verify_manifest.py)

Designed to be run after adding or modifying files, before committing.
Referenced by CONTRIBUTING.md and reproducibility/GPU_EXECUTION_GUIDE.md.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "MANIFEST.sha256.json"

LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"

SKIP_PREFIXES = (".git/",)
SKIP_NAMES = ("MANIFEST.sha256.json",)


def is_lfs_stub(path: Path) -> bool:
    try:
        with open(path, "rb") as fh:
            return fh.read(64).startswith(LFS_PREFIX)
    except OSError:
        return False


def git_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def main() -> int:
    if "--check" in sys.argv:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "verify_manifest",
            REPO_ROOT / "scripts" / "ci" / "verify_manifest.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.main()

    existing: dict = {}
    if MANIFEST_PATH.is_file():
        with open(MANIFEST_PATH) as fh:
            existing = json.load(fh)

    tracked = git_tracked_files()
    manifest: dict[str, dict] = {}

    real = 0
    lfs_preserved = 0
    skipped = 0

    for rel_path in sorted(tracked):
        if any(rel_path.startswith(p) for p in SKIP_PREFIXES):
            skipped += 1
            continue
        if rel_path in SKIP_NAMES:
            skipped += 1
            continue

        path = REPO_ROOT / rel_path
        if not path.is_file():
            continue

        if is_lfs_stub(path):
            if rel_path in existing:
                manifest[rel_path] = existing[rel_path]
                lfs_preserved += 1
            continue

        with open(path, "rb") as fh:
            content = fh.read()
        manifest[rel_path] = {
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        real += 1

    with open(MANIFEST_PATH, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")

    print(f"Manifest updated: {MANIFEST_PATH}")
    print(f"  Real files hashed:       {real}")
    print(f"  LFS stubs preserved:     {lfs_preserved}")
    print(f"  Skipped:                 {skipped}")
    print(f"  Total entries:           {len(manifest)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
