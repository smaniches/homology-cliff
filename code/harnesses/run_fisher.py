"""
run_fisher.py -- Fisher-Rao Metric Test on the Homology Cliff

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
Date:   April 12, 2026

Tests whether Fisher-information-geometric whitening (within-class
covariance inverse, a.k.a. LDA-style whitening as a computable Fisher-Rao
metric approximation for class-conditional Gaussian models on frozen
embeddings) beats Ledoit-Wolf pooled Mahalanobis on the distant stratum.

Hypothesis H1_fisher: Fisher-whitened k-NN achieves lower close-distant
F1 gap than Mahalanobis at scale t30, R=1000, k=25, with bootstrap 95%
CI excluding zero.

Writes fisher_{scale}_{R}_{k}_{seed}.npz.
Pre-registered in PRE_REGISTRATION_FISHER_CLIFF_v1.md.
"""
from __future__ import annotations
import argparse, logging, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from run_cliff import (  # type: ignore
    SEEDS, BOOTSTRAP_N, RESULTS_DIR,
    verify_prereg_hash, load_labels, load_embeddings,
    build_panel, compute_smax, stratify,
    bootstrap_f1_ci,
)


def fisher_whiten(panel_emb: np.ndarray, panel_labels: np.ndarray,
                  test_emb: np.ndarray, shrink: float = 0.05) -> tuple:
    """Compute within-class pooled covariance + Fisher whitening.

    For two-class Gaussian model with shared covariance, the Fisher-Rao
    metric on the class-conditional embedding reduces to the Mahalanobis
    metric using the WITHIN-class covariance (not pooled all-points
    covariance). Shrink toward diag for numerical stability.
    """
    from sklearn.covariance import LedoitWolf
    pos = panel_emb[panel_labels == 1]
    neg = panel_emb[panel_labels == 0]
    if len(pos) < 2 or len(neg) < 2:
        # Fall back to pooled if one class empty
        lw = LedoitWolf().fit(panel_emb)
        prec = lw.precision_
        mu = lw.location_
    else:
        mu_pos = pos.mean(axis=0)
        mu_neg = neg.mean(axis=0)
        cov_pos = np.cov(pos, rowvar=False)
        cov_neg = np.cov(neg, rowvar=False)
        n_pos, n_neg = len(pos), len(neg)
        cov_wc = (n_pos * cov_pos + n_neg * cov_neg) / (n_pos + n_neg)
        # Shrink toward diag
        cov_wc = (1 - shrink) * cov_wc + shrink * np.diag(np.diag(cov_wc))
        prec = np.linalg.inv(cov_wc + 1e-6 * np.eye(cov_wc.shape[0]))
        mu = (n_pos * mu_pos + n_neg * mu_neg) / (n_pos + n_neg)
    eigvals, eigvecs = np.linalg.eigh(prec)
    eigvals = np.clip(eigvals, 1e-8, None)
    L = (eigvecs * np.sqrt(eigvals)).astype(np.float32)
    mu = mu.astype(np.float32)
    pw = ((panel_emb - mu) @ L).astype(np.float32)
    tw = ((test_emb - mu) @ L).astype(np.float32)
    return pw, tw


def knn_fisher(test_emb, panel_emb, panel_labels, k):
    import faiss
    pw, tw = fisher_whiten(panel_emb, panel_labels, test_emb)
    index = faiss.IndexFlatL2(pw.shape[1])
    index.add(np.ascontiguousarray(pw))
    _, I = index.search(np.ascontiguousarray(tw), k)
    pos = (panel_labels[I] == 1).sum(axis=1)
    return (pos * 2 >= k).astype(np.int64)


def evaluate_fisher_cell(scale, R, k, seed, emb, labels):
    panel_idx = build_panel(labels, R, seed)
    panel_emb = emb[panel_idx]
    panel_labels = labels[panel_idx].copy()
    test_mask = np.ones(len(labels), dtype=bool); test_mask[panel_idx] = False
    test_emb = emb[test_mask]; test_labels = labels[test_mask]
    smax = compute_smax(test_emb, panel_emb)
    strata = stratify(smax)
    y_pred = knn_fisher(test_emb, panel_emb, panel_labels, k)
    out = {"scale": scale, "R": R, "k": k, "seed": seed, "metric": "fisher"}
    for name, mask in strata.items():
        n = int(mask.sum())
        if n == 0:
            out[name] = {"n": 0, "f1": float("nan"),
                          "f1_ci_lo": float("nan"), "f1_ci_hi": float("nan"),
                          "underpowered": True}
            continue
        f1, lo, hi = bootstrap_f1_ci(test_labels[mask], y_pred[mask],
                                      n_boot=BOOTSTRAP_N, seed=seed)
        out[name] = {"n": n, "f1": f1, "f1_ci_lo": lo,
                     "f1_ci_hi": hi, "underpowered": n < 100}
    return out


def cell_done(scale, R, k, seed):
    return (RESULTS_DIR / f"fisher_{scale}_{R}_{k}_{seed}.npz").exists()


def run_fisher(scales, resume=True):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    labels, _ = load_labels()
    for scale in scales:
        emb = load_embeddings(scale)
        for R in (100, 500, 1000):
            for k in (5, 25):
                for seed in SEEDS:
                    if resume and cell_done(scale, R, k, seed): continue
                    t0 = time.time()
                    out = evaluate_fisher_cell(scale, R, k, seed, emb, labels)
                    np.savez(RESULTS_DIR / f"fisher_{scale}_{R}_{k}_{seed}.npz",
                             **out)
                    logging.info("fisher %s R=%d k=%d seed=%d in %.1fs",
                                 scale, R, k, seed, time.time() - t0)


def main():
    verify_prereg_hash()
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", nargs="+", default=["t6", "t12", "t30"])
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s")
    run_fisher(args.scale)


if __name__ == "__main__":
    main()
