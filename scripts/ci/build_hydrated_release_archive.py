#!/usr/bin/env python3
"""Build a complete, manifest-verified companion for a frozen LFS release.

The original Git tag and Zenodo deposit are never modified by this program.
It verifies source bytes, not their scientific interpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"
MANIFEST = "MANIFEST.sha256.json"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def git_output(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root).decode("utf-8").strip()


def build(root: Path, destination: Path, tag: str, expected_lfs: int) -> dict:
    root = root.resolve(strict=True)
    if destination.resolve().is_relative_to(root):
        raise ValueError("output must be outside the frozen source checkout")
    manifest_bytes = (root / MANIFEST).read_bytes()
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError("empty or invalid source manifest")
    tracked = set(git_output(root, "ls-files", "-z").split("\x00")) - {""}
    expected = set(manifest) | {MANIFEST}
    if tracked != expected:
        raise ValueError(f"manifest/tracked inventory mismatch: {len(tracked ^ expected)} paths")
    lfs_paths: set[str] = set()
    if expected_lfs:
        lfs_paths = set(git_output(root, "lfs", "ls-files", "-n").splitlines())
        if len(lfs_paths) != expected_lfs or not lfs_paths <= set(manifest):
            raise ValueError("unexpected LFS path count or inventory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    with zipfile.ZipFile(destination, "w", allowZip64=True) as archive:
        for relative in sorted(tracked):
            name = PurePosixPath(relative)
            if name.is_absolute() or ".." in name.parts or str(name) != relative:
                raise ValueError(f"unsafe source path: {relative!r}")
            path = root / relative
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
                raise ValueError(f"not a regular in-tree file: {relative}")
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError(f"unsupported file type: {relative}")
            content = path.read_bytes()
            if content.startswith(LFS_POINTER):
                raise ValueError(f"LFS object is still a pointer: {relative}")
            if relative in manifest:
                record = manifest[relative]
                if not isinstance(record, dict) or record.get("bytes") != len(content):
                    raise ValueError(f"manifest size mismatch: {relative}")
                if record.get("sha256") != hashlib.sha256(content).hexdigest():
                    raise ValueError(f"manifest digest mismatch: {relative}")
            total_bytes += len(content)
            info = zipfile.ZipInfo(f"homology-cliff-{tag}/{relative}", FIXED_ZIP_DATE)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    sidecar = destination.with_suffix(destination.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {destination.name}\n", encoding="ascii")
    report = {
        "scope": "complete source-byte reconstruction only; no new biological finding",
        "source_tag": tag,
        "source_commit": git_output(root, "rev-parse", "HEAD"),
        "tracked_files": len(tracked),
        "manifest_entries_verified": len(manifest),
        "lfs_objects_expected": expected_lfs,
        "lfs_objects_found": len(lfs_paths),
        "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "total_uncompressed_bytes": total_bytes,
        "archive_file": destination.name,
        "archive_sha256": digest,
        "archive_bytes": destination.stat().st_size,
    }
    destination.with_suffix(destination.suffix + ".json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tag", default="v1.6.0")
    parser.add_argument("--expected-lfs", type=int, default=9365)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.output, args.tag, args.expected_lfs), indent=2))


if __name__ == "__main__":
    main()
