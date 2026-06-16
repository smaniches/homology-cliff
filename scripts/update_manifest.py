#!/usr/bin/env python3
"""Regenerate MANIFEST.sha256.json from current disk content.

Walks all git-tracked files, computes SHA256 + byte count for each real
file, and writes a sorted JSON manifest. LFS pointer stubs are detected
and their entries are preserved from the existing manifest (since the
real-content hash cannot be computed from a 130-byte stub).

Cross-platform hash canonicalization
------------------------------------
The manifest stores the *LF-committed* form of every tracked TEXT file --
the exact bytes git records -- so a manifest regenerated on any platform is
byte-identical. A file's bytes are CRLF->LF normalized before hashing iff
git treats it as text in the working tree AND it is not Git-LFS tracked:

    normalize  <=>  working-tree EOL == "crlf"  AND  path not LFS-tracked

Real binaries (.npy/.npz/.png/.pdf/...) report a non-"crlf" working-tree EOL
and are hashed raw; LFS-smudged payloads (whose pointer is text but whose
content is binary, e.g. the large data/*.json) are excluded by the LFS guard
and hashed raw. This mirrors the raw-then-LF acceptance logic in
scripts/ci/verify_manifest.py. Without this normalization, regenerating on a
Windows checkout (core.autocrlf=true, working tree carries CRLF) would write
CRLF-based hashes that a Linux clone -- and the verifier -- cannot reproduce.

The manifest itself is written with explicit LF newlines (newline="\\n") so
that regenerating on Windows does not emit a CRLF JSON file.

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


def working_tree_eol() -> dict[str, str]:
    """Map each tracked path to its working-tree end-of-line token.

    Parses `git ls-files --eol`, whose rows look like::

        i/lf    w/crlf  attr/text=auto      pyproject.toml
        i/lf    w/-text attr/-text          data/embeddings/embeddings_t6.npy

    We key off the working-tree (``w/``) field: only genuine autocrlf text
    files report ``w/crlf``; binaries report ``w/-text`` or ``w/none``.
    """
    result = subprocess.run(
        ["git", "ls-files", "--eol"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    eol: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        w_field = next((tok for tok in meta.split() if tok.startswith("w/")), "w/?")
        eol[path.strip()] = w_field[2:]
    return eol


def lfs_tracked_files() -> set[str]:
    """Set of Git-LFS-tracked paths.

    Prefers ``git lfs ls-files`` (authoritative on any LFS clone); falls back
    to ``git check-attr filter`` (core git, no git-lfs binary required) so the
    tool still works if git-lfs is not installed.
    """
    try:
        result = subprocess.run(
            ["git", "lfs", "ls-files", "-n"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        files = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    # Fallback: ask git's attribute machinery which paths use the lfs filter.
    tracked = git_tracked_files()
    result = subprocess.run(
        ["git", "check-attr", "--stdin", "filter"],
        cwd=REPO_ROOT,
        input="\n".join(tracked),
        capture_output=True,
        text=True,
        check=True,
    )
    lfs: set[str] = set()
    suffix = ": filter: lfs"
    for line in result.stdout.splitlines():
        if line.endswith(suffix):
            lfs.add(line[: -len(suffix)].strip())
    return lfs


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
    eol = working_tree_eol()
    lfs = lfs_tracked_files()
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

        content = path.read_bytes()
        # Canonicalize to the LF-committed form for genuine text files only.
        if eol.get(rel_path) == "crlf" and rel_path not in lfs:
            content = content.replace(b"\r\n", b"\n")
        manifest[rel_path] = {
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        real += 1

    with open(MANIFEST_PATH, "w", newline="\n") as fh:
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
