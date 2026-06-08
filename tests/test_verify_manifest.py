"""Regression tests for the CRLF-robust manifest verifier.

`scripts/ci/verify_manifest.py` is advertised as "runnable locally by
anyone". On a Windows checkout with core.autocrlf=true, tracked text files
carry CRLF line endings while the manifest stores the LF-committed hash.
The verifier must treat a CRLF-only difference in a text file as a match
(LF-normalize fallback) while still:

  - matching binary files only on exact raw bytes (never LF-normalized), and
  - failing on a genuine content edit.

These tests build a throwaway repo tree on tmp_path with a hand-written
manifest, so they need no Git LFS payload and run in every environment.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFIER = REPO_ROOT / "scripts" / "ci" / "verify_manifest.py"


def _load_verifier(repo_root: Path):
    """Import verify_manifest with REPO_ROOT/MANIFEST_PATH pointed at a fixture."""
    spec = importlib.util.spec_from_file_location("verify_manifest_fixture", VERIFIER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.REPO_ROOT = repo_root
    mod.MANIFEST_PATH = repo_root / "MANIFEST.sha256.json"
    return mod


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_manifest(repo_root: Path, entries: dict) -> None:
    (repo_root / "MANIFEST.sha256.json").write_text(
        json.dumps(entries, indent=1, sort_keys=True) + "\n"
    )


def test_text_crlf_difference_passes(tmp_path):
    """A text file whose only difference is LF->CRLF must verify OK."""
    lf = b"line one\nline two\nline three\n"
    (tmp_path / "doc.md").write_bytes(lf.replace(b"\n", b"\r\n"))  # CRLF on disk
    _write_manifest(tmp_path, {"doc.md": {"bytes": len(lf), "sha256": _sha(lf)}})
    mod = _load_verifier(tmp_path)
    assert mod.main() == 0


def test_text_genuine_edit_fails(tmp_path):
    """A real content change in a text file must still FAIL."""
    lf = b"original content\n"
    (tmp_path / "doc.md").write_bytes(b"tampered content\n")
    _write_manifest(tmp_path, {"doc.md": {"bytes": len(lf), "sha256": _sha(lf)}})
    mod = _load_verifier(tmp_path)
    assert mod.main() == 1


def test_binary_requires_exact_bytes(tmp_path):
    """Binary files are never LF-normalized: a CRLF-like byte pattern that
    would 'pass' under text normalization must FAIL for a .npz."""
    # Manifest records the LF-collapsed hash; disk has the raw CR LF bytes.
    raw = b"\x00\x01\r\n\x02binary\r\npayload\x03"
    collapsed = raw.replace(b"\r\n", b"\n")
    (tmp_path / "blob.npz").write_bytes(raw)
    _write_manifest(
        tmp_path,
        {"blob.npz": {"bytes": len(collapsed), "sha256": _sha(collapsed)}},
    )
    mod = _load_verifier(tmp_path)
    # Must NOT silently normalize a binary -> mismatch -> exit 1.
    assert mod.main() == 1


def test_exact_match_passes(tmp_path):
    """An untouched file (exact raw-byte match) verifies OK."""
    content = b"exact bytes, no newline translation\n"
    (tmp_path / "f.txt").write_bytes(content)
    _write_manifest(
        tmp_path, {"f.txt": {"bytes": len(content), "sha256": _sha(content)}}
    )
    mod = _load_verifier(tmp_path)
    assert mod.main() == 0


def test_missing_real_file_fails(tmp_path):
    """A manifest entry with no file on disk (and not a build artifact) fails."""
    _write_manifest(
        tmp_path, {"gone.md": {"bytes": 3, "sha256": _sha(b"abc")}}
    )
    mod = _load_verifier(tmp_path)
    assert mod.main() == 1


def test_missing_build_artifact_is_skipped_not_failed(tmp_path):
    """A manifest entry for a gitignored build artifact (.aux/.log/...) that
    is absent from disk is skipped, not counted as a failure."""
    _write_manifest(
        tmp_path, {"papers/x/paper.aux": {"bytes": 3, "sha256": _sha(b"abc")}}
    )
    mod = _load_verifier(tmp_path)
    assert mod.main() == 0


def test_lfs_pointer_stub_is_skipped(tmp_path):
    """An LFS pointer stub on disk cannot be hashed against the real-content
    manifest entry and must be skipped (exit 0), not flagged as a mismatch."""
    stub = (b"version https://git-lfs.github.com/spec/v1\n"
            b"oid sha256:" + b"0" * 64 + b"\nsize 12345\n")
    (tmp_path / "big.npz").write_bytes(stub)
    _write_manifest(
        tmp_path,
        {"big.npz": {"bytes": 99999, "sha256": _sha(b"real-content-hash")}},
    )
    mod = _load_verifier(tmp_path)
    assert mod.main() == 0


def test_bad_format_entry_fails(tmp_path):
    """A manifest entry that is not a {bytes, sha256} object is a hard error."""
    _write_manifest(tmp_path, {"weird.md": "not-an-object"})
    mod = _load_verifier(tmp_path)
    assert mod.main() == 1
