"""Unit tests for scripts/ci/verify_prereg_locks.py.

The CI pre-registration-lock verifier reports 0% line coverage because its only
entry point is ``__main__`` against the committed pre-registrations. These
tests drive ``main()`` against a throwaway fixture tree (monkeypatched
``REPO_ROOT`` and ``EXPECTED``) so the OK, CRLF-normalized, MISMATCH and MISSING
branches are all exercised without depending on the real locked files.

The loader mirrors tests/test_verify_manifest.py: import the script by path and
reassign its module-level constants to point at a tmp fixture.
"""
import hashlib
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFIER = REPO_ROOT / "scripts" / "ci" / "verify_prereg_locks.py"


def _load(repo_root: Path, expected: dict):
    spec = importlib.util.spec_from_file_location(
        "verify_prereg_locks_fixture", VERIFIER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.REPO_ROOT = repo_root
    mod.EXPECTED = expected
    return mod


def _sha_lf(raw: bytes) -> str:
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def test_all_hashes_match_returns_zero(tmp_path):
    rel = "data/prereg/FIXTURE_A.md"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    body = b"hypothesis: H1\ncriterion: bootstrap CI excludes zero\n"
    path.write_bytes(body)
    mod = _load(tmp_path, {rel: _sha_lf(body)})
    assert mod.main() == 0


def test_crlf_working_tree_still_matches(tmp_path):
    rel = "data/prereg/FIXTURE_B.md"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    lf_body = b"line one\nline two\n"
    path.write_bytes(lf_body.replace(b"\n", b"\r\n"))
    mod = _load(tmp_path, {rel: hashlib.sha256(lf_body).hexdigest()})
    assert mod.main() == 0


def test_edited_file_mismatch_returns_one(tmp_path):
    rel = "data/prereg/FIXTURE_C.md"
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(b"content edited after lock\n")
    mod = _load(tmp_path, {rel: "0" * 64})
    assert mod.main() == 1


def test_missing_file_returns_one(tmp_path):
    rel = "data/prereg/DOES_NOT_EXIST.md"
    mod = _load(tmp_path, {rel: "0" * 64})
    assert mod.main() == 1
