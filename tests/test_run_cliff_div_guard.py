"""Regression test for the bootstrap F1 division guard in run_cliff.

run_cliff.bootstrap_f1_ci previously computed ``2 * tp_b / denom`` eagerly and
masked the result with ``np.where(denom > 0, ..., 0.0)``. For resamples with no
positives and no positive predictions the denominator is zero, so the eager
division produced a spurious ``invalid value encountered in divide``
RuntimeWarning (the masked result was already correct). The guard now uses
``np.divide(..., out=zeros, where=denom > 0)``.

These tests pin two properties:
  1. the new ``np.divide`` form is bit-identical to the old ``np.where`` form on
     random counts, including degenerate (denom == 0) rows; and
  2. bootstrap_f1_ci emits no RuntimeWarning on an all-negative stratum, where
     every resample is degenerate.
"""
import sys
import warnings
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "code" / "harnesses"))

import run_cliff  # noqa: E402


def test_divide_guard_matches_legacy_where_formula():
    rng = np.random.default_rng(0)
    tp_b = rng.integers(0, 5, size=2000).astype(np.float64)
    fp_b = rng.integers(0, 5, size=2000).astype(np.float64)
    fn_b = rng.integers(0, 5, size=2000).astype(np.float64)
    # Force a block of all-zero-count rows so denom == 0 is exercised.
    tp_b[:100] = 0.0
    fp_b[:100] = 0.0
    fn_b[:100] = 0.0
    denom = 2 * tp_b + fp_b + fn_b
    with np.errstate(invalid="ignore", divide="ignore"):
        legacy = np.where(denom > 0, 2 * tp_b / denom, 0.0)
    guarded = np.divide(2 * tp_b, denom, out=np.zeros_like(denom), where=denom > 0)
    assert np.array_equal(legacy, guarded)
    assert np.all(np.isfinite(guarded))


def test_bootstrap_emits_no_divide_warning_on_empty_stratum():
    y_true = np.zeros(120, dtype=np.int64)
    y_pred = np.zeros(120, dtype=np.int64)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        point, lo, hi = run_cliff.bootstrap_f1_ci(y_true, y_pred, seed=0)
    assert point == 0.0
    assert lo == 0.0
    assert hi == 0.0
