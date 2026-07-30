"""Regression tests for reproduce.py's field-aware Mapper comparison and the
committed-artifact preservation/restoration around `--full` re-derivation.

Context: a hydrated Windows/Python 3.13 `python reproduce.py --full` run
against commit 636ea8e completed every computation successfully but exited 1
because `mapper_augmentation_results.json` was not SHA256-identical --
`results.uniform[2].close_f1` drifted by 6.1563885830229204e-05 (FAISS/BLAS
threshold behavior differs across platforms), while every other field
(all dist_f1, n_dist, seeds, rescue_mean, rescue_ci_lo, rescue_ci_hi) was
exactly identical and the Mapper H1 decision was unchanged. `--full` now
checks calibration_results.json for strict byte-identity (unchanged) but
checks mapper_augmentation_results.json field-aware instead
(`reproduce.mapper_results_match`), and always restores both re-derived
artifacts to their committed bytes afterward (`_preserved` /
`_reproduce_and_restore`), so `--full` never leaves the working tree
modified regardless of outcome.

Imports reproduce.py via importlib (it lives at the repo root, not a
package), matching tests/test_verify_manifest.py's pattern for scripts/
ci/verify_manifest.py. No LFS/faiss/torch needed: these tests exercise the
comparison and restoration logic directly with synthetic and real-committed
(but LFS-free) JSON fixtures and throwaway subprocess scripts.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REPRODUCE_PY = REPO_ROOT / "reproduce.py"
COMMITTED_MAPPER_JSON = REPO_ROOT / "data" / "results_summaries" / "mapper_augmentation_results.json"


def _load_reproduce():
    spec = importlib.util.spec_from_file_location("reproduce_fixture", REPRODUCE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reproduce = _load_reproduce()


@pytest.fixture
def committed():
    """The real committed mapper_augmentation_results.json (not LFS-tracked,
    so this is always the real content, never a pointer stub)."""
    return json.loads(COMMITTED_MAPPER_JSON.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# mapper_results_match: the observed real-world drift + deliberate violations
# ---------------------------------------------------------------------------

def test_exact_identity_passes(committed):
    ok, msg = reproduce.mapper_results_match(committed, copy.deepcopy(committed))
    assert ok is True
    assert "worst drift" in msg


def test_observed_close_f1_drift_passes(committed):
    """The exact scenario from the Windows/Python 3.13 reproduction: only
    results.uniform[2].close_f1 drifts, by 6.1563885830229204e-05."""
    generated = copy.deepcopy(committed)
    drifted = 0.8649725959143
    assert committed["results"]["uniform"][2]["close_f1"] == pytest.approx(0.8649110320284698)
    generated["results"]["uniform"][2]["close_f1"] = drifted
    drift = abs(drifted - committed["results"]["uniform"][2]["close_f1"])
    assert drift == pytest.approx(6.1563885830229204e-05)

    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is True, msg
    assert "results.uniform[2].close_f1" in msg
    assert "tol=1e-04" in msg


def test_close_f1_drift_above_tolerance_fails(committed):
    generated = copy.deepcopy(committed)
    generated["results"]["uniform"][2]["close_f1"] += 2e-4  # > 1e-4 tolerance
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "results.uniform[2].close_f1" in msg
    assert "exceeds tolerance 1e-04" in msg


def test_close_f1_drift_at_boundary_is_inclusive(committed):
    """abs_tol is a <= boundary: exactly 1e-4 must still pass."""
    generated = copy.deepcopy(committed)
    generated["results"]["uniform"][2]["close_f1"] += 1e-4
    ok, _ = reproduce.mapper_results_match(committed, generated)
    assert ok is True


@pytest.mark.parametrize("field,delta", [("dist_f1", 1e-6), ("rescue_mean", 1e-6)])
def test_tight_tolerance_fields_reject_drift_far_looser_than_close_f1(committed, field, delta):
    """dist_f1 and rescue_mean use abs_tol=1e-12: a drift that would pass for
    close_f1 (1e-6 << 1e-4) must still fail here."""
    generated = copy.deepcopy(committed)
    if field == "dist_f1":
        generated["results"]["uniform"][0]["dist_f1"] += delta
    else:
        generated[field] += delta
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "exceeds tolerance 1e-12" in msg


@pytest.mark.parametrize("field", ["rescue_mean", "rescue_ci_lo", "rescue_ci_hi"])
def test_rescue_statistics_violation_fails(committed, field):
    generated = copy.deepcopy(committed)
    generated[field] += 1e-6
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert field in msg


def test_seed_value_change_fails(committed):
    generated = copy.deepcopy(committed)
    generated["results"]["uniform"][0]["seed"] = 99999999
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "results.uniform[0].seed" in msg


def test_seed_reordering_fails_even_though_the_value_set_is_unchanged(committed):
    """Swapping two seeds' positions changes neither the seed *set* nor any
    individual seed's presence -- only order. Ordering must still be enforced
    (entries are compared positionally), so this must fail."""
    generated = copy.deepcopy(committed)
    u = generated["results"]["uniform"]
    u[0]["seed"], u[1]["seed"] = u[1]["seed"], u[0]["seed"]
    assert {e["seed"] for e in u} == {e["seed"] for e in committed["results"]["uniform"]}
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "seed" in msg


def test_n_dist_violation_fails(committed):
    generated = copy.deepcopy(committed)
    generated["results"]["biased"][3]["n_dist"] += 1
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "results.biased[3].n_dist" in msg


def test_r_k_scale_violation_fails(committed):
    generated = copy.deepcopy(committed)
    generated["k"] = committed["k"] + 1
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "k:" in msg


def test_structural_arm_name_violation_fails(committed):
    generated = copy.deepcopy(committed)
    generated["results"]["extra_arm"] = generated["results"].pop("biased")
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "arm names" in msg


def test_structural_result_list_length_violation_fails(committed):
    generated = copy.deepcopy(committed)
    generated["results"]["uniform"] = generated["results"]["uniform"][:-1]
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "results.uniform: length" in msg


def test_structural_top_level_key_violation_fails(committed):
    generated = copy.deepcopy(committed)
    generated["extra_key"] = 1
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "top-level keys" in msg


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_close_f1_fails(committed, bad_value):
    generated = copy.deepcopy(committed)
    generated["results"]["uniform"][0]["close_f1"] = bad_value
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "non-finite" in msg


def test_non_finite_dist_f1_fails(committed):
    generated = copy.deepcopy(committed)
    generated["results"]["biased"][0]["dist_f1"] = float("nan")
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "non-finite" in msg


def test_non_finite_rescue_mean_fails(committed):
    generated = copy.deepcopy(committed)
    generated["rescue_mean"] = float("nan")
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is False
    assert "non-finite" in msg


def test_worst_drift_is_reported_even_when_it_still_passes(committed):
    """`worst` tracks the single largest float drift found across every
    comparison, independent of pass/fail, so the message is diagnostic even
    on a clean pass (not just on failure)."""
    generated = copy.deepcopy(committed)
    generated["results"]["uniform"][2]["close_f1"] += 3e-5
    generated["results"]["biased"][5]["close_f1"] += 1e-5
    ok, msg = reproduce.mapper_results_match(committed, generated)
    assert ok is True
    assert "results.uniform[2].close_f1" in msg  # the larger of the two drifts


# ---------------------------------------------------------------------------
# calibration_results.json: strict byte-identity retained
# ---------------------------------------------------------------------------

def test_calibration_matches_requires_exact_bytes():
    ok, _ = reproduce._calibration_matches(b'{"a": 1}', b'{"a": 1}')
    assert ok is True
    ok, _ = reproduce._calibration_matches(b'{"a": 1}', b'{"a": 1.0000001}')
    assert ok is False


def test_calibration_matches_fails_with_no_committed_artifact():
    ok, msg = reproduce._calibration_matches(None, b'{"a": 1}')
    assert ok is False
    assert "no committed artifact" in msg


# ---------------------------------------------------------------------------
# _preserved / _reproduce_and_restore: the artifact must always be restored
# ---------------------------------------------------------------------------

def test_preserved_restores_after_normal_exit(tmp_path):
    p = tmp_path / "artifact.json"
    p.write_bytes(b"ORIGINAL")
    with reproduce._preserved(p) as original:
        assert original == b"ORIGINAL"
        p.write_bytes(b"MUTATED")
    assert p.read_bytes() == b"ORIGINAL"


def test_preserved_restores_after_exception(tmp_path):
    p = tmp_path / "artifact.json"
    p.write_bytes(b"ORIGINAL")
    with pytest.raises(RuntimeError):
        with reproduce._preserved(p) as _original:
            p.write_bytes(b"MUTATED")
            raise RuntimeError("boom")
    assert p.read_bytes() == b"ORIGINAL"


def test_preserved_removes_an_artifact_that_did_not_exist_beforehand(tmp_path):
    """If the artifact was absent on entry and the block created it, it must be
    removed on exit -- otherwise `--full` run from a checkout missing one of the
    two committed artifacts would leave a new untracked file behind, making the
    'never leaves the working tree modified' contract only conditionally true."""
    p = tmp_path / "absent.json"
    assert not p.exists()
    with reproduce._preserved(p) as original:
        assert original is None
        p.write_bytes(b"CREATED_BY_RERUN")
        assert p.exists()
    assert not p.exists()


def test_preserved_removes_a_created_artifact_even_after_exception(tmp_path):
    p = tmp_path / "absent.json"
    with pytest.raises(RuntimeError):
        with reproduce._preserved(p) as _original:
            p.write_bytes(b"CREATED_THEN_CRASHED")
            raise RuntimeError("boom")
    assert not p.exists()


def test_preserved_is_a_noop_when_the_artifact_stays_absent(tmp_path):
    """Nothing created, nothing to clean up -- and no error from unlinking a
    file that was never there."""
    p = tmp_path / "absent.json"
    with reproduce._preserved(p) as original:
        assert original is None
    assert not p.exists()


def _write_script(tmp_path, name, body):
    script = tmp_path / name
    script.write_text(body, encoding="utf-8")
    return script


def test_reproduce_and_restore_restores_after_passing_comparison(tmp_path):
    out = tmp_path / "out.json"
    out.write_bytes(b'{"committed": true}')
    script = _write_script(tmp_path, "rewrite.py",
                           f"import pathlib; pathlib.Path(r'{out}').write_bytes(b'REGENERATED')\n")
    ok = reproduce._reproduce_and_restore(str(script), out, lambda o, g: (True, "ok"))
    assert ok is True
    assert out.read_bytes() == b'{"committed": true}'


def test_reproduce_and_restore_restores_after_failing_comparison(tmp_path):
    out = tmp_path / "out.json"
    out.write_bytes(b'{"committed": true}')
    script = _write_script(tmp_path, "rewrite.py",
                           f"import pathlib; pathlib.Path(r'{out}').write_bytes(b'REGENERATED')\n")
    ok = reproduce._reproduce_and_restore(str(script), out, lambda o, g: (False, "mismatch"))
    assert ok is False
    assert out.read_bytes() == b'{"committed": true}'


def test_reproduce_and_restore_restores_if_comparison_raises(tmp_path):
    out = tmp_path / "out.json"
    out.write_bytes(b'{"committed": true}')
    script = _write_script(tmp_path, "rewrite.py",
                           f"import pathlib; pathlib.Path(r'{out}').write_bytes(b'REGENERATED')\n")

    def boom(_original, _generated):
        raise ValueError("comparison exploded")

    with pytest.raises(ValueError):
        reproduce._reproduce_and_restore(str(script), out, boom)
    assert out.read_bytes() == b'{"committed": true}'


def test_reproduce_and_restore_restores_if_script_crashes(tmp_path):
    out = tmp_path / "out.json"
    out.write_bytes(b'{"committed": true}')
    script = _write_script(
        tmp_path, "crash.py",
        f"import pathlib, sys; pathlib.Path(r'{out}').write_bytes(b'PARTIAL_WRITE'); sys.exit(1)\n",
    )
    ok = reproduce._reproduce_and_restore(str(script), out, lambda o, g: (True, "unreached"))
    assert ok is False
    assert out.read_bytes() == b'{"committed": true}'


def test_reproduce_and_restore_fails_cleanly_if_script_writes_nothing(tmp_path):
    out = tmp_path / "missing_output.json"
    script = _write_script(tmp_path, "noop.py", "pass\n")
    ok = reproduce._reproduce_and_restore(str(script), out, lambda o, g: (True, "unreached"))
    assert ok is False
    assert not out.exists()


def test_reproduce_and_restore_removes_output_created_from_an_absent_artifact(tmp_path):
    """End-to-end version of the absent-artifact case: no committed file exists,
    the re-derivation creates one, the comparison sees original=None (and every
    real comparator fails on that -- there is nothing to check against), and the
    created file is cleaned up rather than left in the tree."""
    out = tmp_path / "absent.json"
    script = _write_script(tmp_path, "create.py",
                           f"import pathlib; pathlib.Path(r'{out}').write_bytes(b'CREATED')\n")
    seen = {}

    def record(original, generated):
        seen["original"] = original
        return reproduce._calibration_matches(original, generated)

    ok = reproduce._reproduce_and_restore(str(script), out, record)
    assert seen["original"] is None
    assert ok is False
    assert not out.exists()
