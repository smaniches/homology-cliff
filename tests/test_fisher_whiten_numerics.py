"""Known-answer tests for run_fisher.fisher_whiten.

The Fisher-Rao harness (code/harnesses/run_fisher.py) reports only ~14% line
coverage because every path except fisher_whiten needs faiss. fisher_whiten
itself is pure numpy + scikit-learn (faiss/torch are deferred to knn_fisher),
so its linear-algebra contract can be pinned without the heavy stack or the
LFS payload.

The core property: with shrink=0 the returned transform L satisfies
L @ L.T == inv(cov_wc + eps*I) where cov_wc is the pooled within-class
covariance, so whitening the panel makes its pooled within-class covariance
the identity. This is an algebraic identity on the estimated covariance (not a
sampling claim), so it holds tightly regardless of sample size.
"""
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "code" / "harnesses"))

import run_fisher  # noqa: E402


def _pooled_within_class_cov(emb: np.ndarray, labels: np.ndarray) -> np.ndarray:
    pos = emb[labels == 1]
    neg = emb[labels == 0]
    cov_pos = np.cov(pos, rowvar=False)
    cov_neg = np.cov(neg, rowvar=False)
    n_pos, n_neg = len(pos), len(neg)
    return (n_pos * cov_pos + n_neg * cov_neg) / (n_pos + n_neg)


def _two_class_panel(rng, d, n):
    a = rng.standard_normal((d, d))
    chol = np.linalg.cholesky(a @ a.T + np.eye(d))
    shift = np.zeros(d)
    shift[0] = 1.5
    pos = rng.standard_normal((n, d)) @ chol.T + shift
    neg = rng.standard_normal((n, d)) @ chol.T - shift
    panel = np.vstack([pos, neg]).astype(np.float32)
    labels = np.array([1] * n + [0] * n)
    return panel, labels


def test_fisher_whiten_shapes_dtype_finite():
    rng = np.random.default_rng(0)
    panel, labels = _two_class_panel(rng, d=4, n=300)
    test = rng.standard_normal((20, 4)).astype(np.float32)
    pw, tw = run_fisher.fisher_whiten(panel, labels, test, shrink=0.0)
    assert pw.shape == panel.shape
    assert tw.shape == test.shape
    assert pw.dtype == np.float32
    assert tw.dtype == np.float32
    assert np.all(np.isfinite(pw))
    assert np.all(np.isfinite(tw))


def test_fisher_whiten_makes_within_class_cov_identity():
    rng = np.random.default_rng(1)
    d = 3
    panel, labels = _two_class_panel(rng, d=d, n=500)
    pw, _ = run_fisher.fisher_whiten(panel, labels, panel[:1], shrink=0.0)
    cov_white = _pooled_within_class_cov(pw.astype(np.float64), labels)
    assert np.allclose(cov_white, np.eye(d), atol=2e-2), cov_white


def test_fisher_whiten_fallback_when_one_class_degenerate():
    # Fewer than two negatives triggers the LedoitWolf pooled-covariance
    # fallback; it must still return finite, correctly shaped projections.
    rng = np.random.default_rng(2)
    d = 3
    panel = rng.standard_normal((50, d)).astype(np.float32)
    labels = np.ones(50, dtype=int)
    test = rng.standard_normal((5, d)).astype(np.float32)
    pw, tw = run_fisher.fisher_whiten(panel, labels, test)
    assert pw.shape == panel.shape
    assert tw.shape == test.shape
    assert np.all(np.isfinite(pw))
    assert np.all(np.isfinite(tw))
