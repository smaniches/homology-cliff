"""Known-answer (KAT) tests for the numerical functions that compute the
compendium's published numbers.

Unlike test_cell_schema.py (which checks the committed .npz artifacts and skips
without the LFS payload), these tests pin the *logic* of the pure functions in
the harnesses and analysis scripts to hand-computed reference values. They run
in any environment with numpy alone -- faiss and torch are imported lazily
inside the k-NN functions, so importing the modules for their pure helpers
needs no heavy dependency and no LFS data.

Every expected value below is computed by hand in the test or its comment, not
copied from documentation, so the test is an independent check on the code.

Style mirrors tests/test_cell_schema.py: module-level ``test_*`` functions, no
classes, the built-in ``tmp_path`` fixture only, and assertions that interpolate
the actual value into the failure message.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

# The harnesses/analysis scripts are designed to be imported via sys.path
# injection (see scripts/ci/verify_smoke_imports.py and run_calibration.py,
# which do the same). faiss/torch are deferred to call sites, so these imports
# need only numpy.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "code" / "harnesses"))
sys.path.insert(0, str(REPO_ROOT / "code" / "analyses"))

import run_cliff  # noqa: E402
import run_calibration  # noqa: E402
import run_cascade  # noqa: E402
import run_cliff_fullnull  # noqa: E402


# ---------------------------------------------------------------------------
# run_cliff._f1_from_counts
# ---------------------------------------------------------------------------

def test_f1_from_counts_perfect():
    # tp=5, fp=0, fn=0 -> precision=recall=1 -> F1=1
    assert run_cliff._f1_from_counts(5, 0, 0) == 1.0


def test_f1_from_counts_zero_tp_guard():
    # tp=0 short-circuits to 0.0 regardless of fp/fn (avoids 0/0)
    assert run_cliff._f1_from_counts(0, 3, 4) == 0.0
    assert run_cliff._f1_from_counts(0, 0, 0) == 0.0


def test_f1_from_counts_balanced_half():
    # tp=2, fp=2, fn=2 -> p=r=0.5 -> F1 = 2*0.25/1.0 = 0.5
    assert run_cliff._f1_from_counts(2, 2, 2) == pytest.approx(0.5)


def test_f1_from_counts_two_thirds():
    # tp=2, fp=1, fn=1 -> p=r=2/3 -> F1 = 2/3
    got = run_cliff._f1_from_counts(2, 1, 1)
    assert got == pytest.approx(2.0 / 3.0), f"expected 2/3, got {got}"


# ---------------------------------------------------------------------------
# run_cliff._majority_vote  (ties broken toward label 1: pos*2 >= k)
# ---------------------------------------------------------------------------

def test_majority_vote_clear_cases():
    nl = np.array([[1, 1, 0], [1, 0, 0], [0, 0, 0]])
    got = run_cliff._majority_vote(nl)
    # row0: pos=2,k=3 -> 4>=3 -> 1 ; row1: pos=1 -> 2>=3 -> 0 ; row2: 0 -> 0
    assert got.tolist() == [1, 0, 0], f"got {got.tolist()}"


def test_majority_vote_tie_breaks_to_one():
    # k=2, one positive: pos*2 = 2 >= k=2 -> tie resolves to 1
    assert run_cliff._majority_vote(np.array([[1, 0]])).tolist() == [1]


def test_majority_vote_k1():
    assert run_cliff._majority_vote(np.array([[0]])).tolist() == [0]
    assert run_cliff._majority_vote(np.array([[1]])).tolist() == [1]


# ---------------------------------------------------------------------------
# run_cliff.stratify  (close >=0.95 ; moderate [0.90,0.95) ; distant <0.90)
# ---------------------------------------------------------------------------

def test_stratify_boundaries():
    smax = np.array([0.96, 0.95, 0.92, 0.90, 0.89])
    s = run_cliff.stratify(smax)
    assert s["close"].tolist() == [True, True, False, False, False]
    assert s["moderate"].tolist() == [False, False, True, True, False]
    assert s["distant"].tolist() == [False, False, False, False, True]


def test_stratify_partition_is_exclusive_and_exhaustive():
    rng = np.random.default_rng(0)
    smax = rng.uniform(0.80, 1.00, size=500)
    s = run_cliff.stratify(smax)
    stacked = np.vstack([s["close"], s["moderate"], s["distant"]]).astype(int)
    per_element = stacked.sum(axis=0)
    # Exactly one stratum is True for every element.
    assert np.all(per_element == 1), (
        f"non-partition: counts seen = {sorted(set(per_element.tolist()))}")


# ---------------------------------------------------------------------------
# run_cliff.build_panel
# ---------------------------------------------------------------------------

def _toy_labels(n_pos=30, n_neg=70):
    return np.array([1] * n_pos + [0] * n_neg, dtype=np.int64)


def test_build_panel_balanced_unique():
    labels = _toy_labels()
    R, seed = 20, 7
    panel = run_cliff.build_panel(labels, R, seed)
    assert len(panel) == R
    assert len(set(panel.tolist())) == R, "panel indices must be unique"
    half = R // 2
    # First R/2 are drawn from positives, last R/2 from negatives.
    assert int(labels[panel[:half]].sum()) == half
    assert int(labels[panel[half:]].sum()) == 0


def test_build_panel_deterministic_and_seed_sensitive():
    labels = _toy_labels()
    a = run_cliff.build_panel(labels, 20, 7)
    b = run_cliff.build_panel(labels, 20, 7)
    c = run_cliff.build_panel(labels, 20, 8)
    assert np.array_equal(a, b), "same (labels,R,seed) must reproduce"
    assert not np.array_equal(a, c), "different seed must change the panel"


# ---------------------------------------------------------------------------
# run_cliff.compute_smax  (max cosine of each test row to any panel row)
# ---------------------------------------------------------------------------

def test_compute_smax_known_values():
    test = np.array([[1.0, 0.0]])
    panel = np.array([[0.0, 1.0], [0.6, 0.8]])
    # inner products: [1,0].[0,1]=0 ; [1,0].[0.6,0.8]=0.6 -> max=0.6
    got = run_cliff.compute_smax(test, panel)
    assert got.shape == (1,)
    assert got[0] == pytest.approx(0.6), f"expected 0.6, got {got[0]}"


def test_compute_smax_identical_and_orthogonal():
    test = np.array([[1.0, 0.0]])
    assert run_cliff.compute_smax(test, np.array([[1.0, 0.0]]))[0] == pytest.approx(1.0)
    assert run_cliff.compute_smax(test, np.array([[0.0, 1.0]]))[0] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# run_cliff.bootstrap_f1_ci
# ---------------------------------------------------------------------------

def test_bootstrap_point_and_ci_invariants():
    y_true = np.array([1, 1, 1, 0, 0, 0])
    y_pred = np.array([1, 1, 1, 0, 0, 0])  # perfect
    point, lo, hi = run_cliff.bootstrap_f1_ci(y_true, y_pred, seed=0)
    assert point == pytest.approx(1.0)
    # CI must bracket the point estimate (lo can dip below 1.0 because an
    # all-negative resample yields F1=0; that is correct behaviour).
    assert lo <= point <= hi, f"CI [{lo}, {hi}] does not bracket point {point}"
    assert 0.0 <= lo <= hi <= 1.0


def test_bootstrap_imperfect_point():
    # tp=1, fp=1, fn=1 -> F1 = 0.5
    y_true = np.array([1, 1, 0, 0])
    y_pred = np.array([1, 0, 0, 1])
    point, lo, hi = run_cliff.bootstrap_f1_ci(y_true, y_pred, seed=0)
    assert point == pytest.approx(0.5), f"expected 0.5, got {point}"
    assert lo <= point <= hi


def test_bootstrap_empty_is_nan():
    point, lo, hi = run_cliff.bootstrap_f1_ci(np.array([]), np.array([]))
    assert np.isnan(point) and np.isnan(lo) and np.isnan(hi)


def test_bootstrap_is_deterministic():
    y_true = np.array([1, 0, 1, 0, 1, 1, 0, 0])
    y_pred = np.array([1, 0, 0, 0, 1, 1, 1, 0])
    r1 = run_cliff.bootstrap_f1_ci(y_true, y_pred, seed=123)
    r2 = run_cliff.bootstrap_f1_ci(y_true, y_pred, seed=123)
    assert r1 == r2, f"non-deterministic for fixed seed: {r1} vs {r2}"


# ---------------------------------------------------------------------------
# run_cliff.is_lfs_stub
# ---------------------------------------------------------------------------

def test_is_lfs_stub_detection(tmp_path):
    stub = tmp_path / "stub.npz"
    stub.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:deadbeef\n")
    real = tmp_path / "real.bin"
    real.write_bytes(b"\x00\x01\x02 not a pointer")
    assert run_cliff.is_lfs_stub(stub) is True
    assert run_cliff.is_lfs_stub(real) is False
    # Nonexistent path: OSError is swallowed, returns False (does not raise).
    assert run_cliff.is_lfs_stub(tmp_path / "nope.npz") is False


# ---------------------------------------------------------------------------
# run_calibration: bin_index / reliability_table / ECE / pos-pred precision
# ---------------------------------------------------------------------------

def test_bin_index_six_unequal_bins():
    # edges = (0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0001)
    vf = np.array([0.0, 0.04, 0.12, 0.48, 0.52, 0.92, 1.0])
    got = run_calibration.bin_index(vf).tolist()
    assert got == [0, 0, 1, 2, 3, 5, 5], f"got {got}"


def test_reliability_table_known():
    vf = np.array([0.0, 0.0, 1.0])
    yt = np.array([0, 1, 1])
    rows = run_calibration.reliability_table(vf, yt)
    assert rows[0]["n"] == 2
    assert rows[0]["mean_pred"] == pytest.approx(0.0)
    assert rows[0]["mean_obs"] == pytest.approx(0.5)  # mean of [0, 1]
    assert rows[5]["n"] == 1
    assert rows[5]["mean_pred"] == pytest.approx(1.0)
    assert rows[5]["mean_obs"] == pytest.approx(1.0)
    for b in (1, 2, 3, 4):
        assert rows[b]["n"] == 0
        assert np.isnan(rows[b]["mean_pred"]) and np.isnan(rows[b]["mean_obs"])


def test_expected_calibration_error_known():
    rows = [
        dict(n=10, mean_pred=0.9, mean_obs=0.6),  # contributes (10/20)*0.3 = 0.15
        dict(n=10, mean_pred=0.1, mean_obs=0.1),  # contributes 0
    ]
    assert run_calibration.expected_calibration_error(rows) == pytest.approx(0.15)


def test_expected_calibration_error_empty_is_nan():
    rows = [dict(n=0, mean_pred=float("nan"), mean_obs=float("nan"))]
    assert np.isnan(run_calibration.expected_calibration_error(rows))


def test_positive_prediction_precision_known():
    vf = np.array([0.6, 0.6, 0.4])
    yt = np.array([1, 0, 1])
    out = run_calibration.positive_prediction_precision(vf, yt, threshold=0.5)
    # predicted positive at idx 0,1 ; tp=1 (idx0), fp=1 (idx1)
    assert out["n_predicted_positive"] == 2
    assert out["tp"] == 1 and out["fp"] == 1
    assert out["precision"] == pytest.approx(0.5)


def test_positive_prediction_precision_no_positives_is_nan():
    vf = np.array([0.1, 0.2, 0.3])
    yt = np.array([1, 0, 1])
    out = run_calibration.positive_prediction_precision(vf, yt, threshold=0.5)
    assert out["n_predicted_positive"] == 0
    assert np.isnan(out["precision"])


# ---------------------------------------------------------------------------
# run_cascade.pooled_f1
# ---------------------------------------------------------------------------

def test_pooled_f1_half():
    yt = np.array([1, 1, 0, 0])
    yp = np.array([1, 0, 0, 1])  # tp=1, fp=1, fn=1 -> F1=0.5
    assert run_cascade.pooled_f1(yt, yp) == pytest.approx(0.5)


def test_pooled_f1_perfect_and_zero():
    yt = np.array([1, 1, 0, 0])
    assert run_cascade.pooled_f1(yt, yt) == pytest.approx(1.0)
    # predict all-negative while positives exist -> tp=0 -> 0.0
    assert run_cascade.pooled_f1(yt, np.zeros_like(yt)) == 0.0


# ---------------------------------------------------------------------------
# run_cliff_fullnull.permute_labels_fullpool
# ---------------------------------------------------------------------------

def test_permute_labels_preserves_multiset():
    labels = np.array([1, 1, 0, 0, 0, 1, 0])
    out = run_cliff_fullnull.permute_labels_fullpool(labels, seed=20260412)
    assert sorted(out.tolist()) == sorted(labels.tolist())  # multiset preserved
    assert int(out.sum()) == int(labels.sum())  # positive count unchanged
    # Original vector is not mutated (function copies before shuffling).
    assert labels.tolist() == [1, 1, 0, 0, 0, 1, 0]


def test_permute_labels_deterministic():
    labels = np.array([1, 1, 0, 0, 0, 1, 0, 0, 1, 0])
    a = run_cliff_fullnull.permute_labels_fullpool(labels, seed=5)
    b = run_cliff_fullnull.permute_labels_fullpool(labels, seed=5)
    assert np.array_equal(a, b), "fixed seed must reproduce the permutation"
