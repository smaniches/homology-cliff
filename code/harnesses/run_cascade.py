"""
run_cascade.py -- Stratified Metric Cascade Experiment

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
Date:   April 12, 2026

Tests pre-registered H1: a per-stratum metric cascade (cosine for close,
Mahalanobis for moderate + distant) beats any single-metric baseline on
pooled F1 with 95% CI excluding +0.02.

Uses the locked harness machinery from run_cliff.py without modifying it.
Writes cascade_{scale}_{R}_{k}_{seed}.npz -- one cell per (scale, R, k,
seed), containing four pooled F1 values (cosine, mahalanobis, learned,
cascade) + per-stratum numbers + within-cell bootstrap CIs.

Usage:
    python run_cascade.py --scale t6 t12 t30 --resume
"""

from __future__ import annotations
import argparse, logging, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from run_cliff import (  # type: ignore
    SCALES, SEEDS, CLOSE_THRESHOLD, MODERATE_LOWER, DISTANT_UPPER,
    BOOTSTRAP_N, CASCADE_DIR,
    verify_prereg_hash, load_labels, load_embeddings,
    build_panel, compute_smax, stratify,
    knn_cosine, knn_mahalanobis, knn_learned,
    bootstrap_f1_ci,
)

CASCADE_R = (100, 500, 1000)
CASCADE_K = (5, 25)
CASCADE_METRICS = ("cosine", "mahalanobis", "learned", "cascade")


def pooled_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    if tp == 0: return 0.0
    p = tp / (tp + fp); r = tp / (tp + fn)
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def evaluate_cascade_cell(scale: str, R: int, k: int, seed: int,
                          emb: np.ndarray, labels: np.ndarray) -> dict:
    panel_idx = build_panel(labels, R, seed)
    panel_emb = emb[panel_idx]
    panel_labels = labels[panel_idx].copy()
    test_mask = np.ones(len(labels), dtype=bool)
    test_mask[panel_idx] = False
    test_emb = emb[test_mask]
    test_labels = labels[test_mask]

    smax = compute_smax(test_emb, panel_emb)
    strata = stratify(smax)
    close_m = strata["close"]; mod_m = strata["moderate"]; dist_m = strata["distant"]

    # Three single-metric predictions over the whole test set
    y_cos = knn_cosine(test_emb, panel_emb, panel_labels, k)
    y_mah = knn_mahalanobis(test_emb, panel_emb, panel_labels, k)
    y_lrn = knn_learned(test_emb, panel_emb, panel_labels, k)

    # Cascade: cosine where close, mahalanobis elsewhere
    y_cas = np.where(close_m, y_cos, y_mah)

    out = {
        "scale": scale, "R": R, "k": k, "seed": seed,
        "n_close": int(close_m.sum()),
        "n_moderate": int(mod_m.sum()),
        "n_distant": int(dist_m.sum()),
    }
    for name, y_pred in [("cosine", y_cos), ("mahalanobis", y_mah),
                         ("learned", y_lrn), ("cascade", y_cas)]:
        pooled = pooled_f1(test_labels, y_pred)
        p, lo, hi = bootstrap_f1_ci(test_labels, y_pred,
                                     n_boot=BOOTSTRAP_N, seed=seed)
        out[f"{name}_pooled_f1"] = pooled
        out[f"{name}_ci_lo"] = lo
        out[f"{name}_ci_hi"] = hi
        for sname, smask in [("close", close_m), ("mod", mod_m),
                              ("dist", dist_m)]:
            if smask.sum() > 0:
                out[f"{name}_{sname}_f1"] = pooled_f1(
                    test_labels[smask], y_pred[smask])
            else:
                out[f"{name}_{sname}_f1"] = float("nan")
    return out


def cell_done(scale, R, k, seed) -> bool:
    return (CASCADE_DIR / f"cascade_{scale}_{R}_{k}_{seed}.npz").exists()


def run_cascade(scales, resume=True):
    CASCADE_DIR.mkdir(parents=True, exist_ok=True)
    labels, _ = load_labels()
    for scale in scales:
        emb = load_embeddings(scale)
        for R in CASCADE_R:
            for k in CASCADE_K:
                for seed in SEEDS:
                    if resume and cell_done(scale, R, k, seed):
                        continue
                    t0 = time.time()
                    out = evaluate_cascade_cell(scale, R, k, seed, emb, labels)
                    np.savez(CASCADE_DIR / f"cascade_{scale}_{R}_{k}_{seed}.npz", **out)
                    logging.info("cascade %s R=%d k=%d seed=%d done in %.1fs",
                                 scale, R, k, seed, time.time() - t0)


def main():
    verify_prereg_hash()
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", nargs="+", default=["t6", "t12", "t30"])
    ap.add_argument("--resume", action="store_true", default=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s")
    logging.info("stratified cascade starting for scales: %s", args.scale)
    run_cascade(args.scale, resume=args.resume)
    logging.info("stratified cascade complete")


if __name__ == "__main__":
    main()
