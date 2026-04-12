"""
run_cliff_fullnull.py -- Full-Dataset Label Permutation Null Control

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
Date:   April 12, 2026

Post-hoc addendum to the homology-cliff pre-registration. The original
pre-reg specified panel-label shuffling as the negative control, but that
control conflates label-signal loss with the test set's retained 28.7%
class prior. Under panel-only shuffling the observed shuffled-label gap
was +0.20 to +0.44 across (scale, R, k, metric) cells, which does NOT
satisfy the pre-reg's stated criterion "distant F1 at chance (0.5 +/-
bootstrap CI)". A shuffled-panel gap of +0.35 can be explained by
geometric clustering alone and does not falsify the cliff.

This script runs the STRICTER null: permute labels across the full 24,885
pool (panel + test) once per (scale, R, seed). Under this null, if any
close-distant F1 gap remains, the gap is pure geometric artifact of the
stratification operation applied to the embedding manifold, independent
of any label signal.

Expected outcome: close F1 ~ 0.5, distant F1 ~ 0.5, gap ~ 0 per the
original pre-reg's stated criterion. If observed, the cliff claim is
defensible. If not observed, the cliff is in part a property of the
stratification procedure itself and must be reframed accordingly.

Namespace: writes fullnull_{cell.key()}.npz, distinct from cell_ and
negctrl_ outputs. No collision with existing data.

RNG offset: seed + 7_777_777 (distinct from seed+R panel RNG and from
seed+999_999 negctrl RNG) to guarantee independent permutation stream.

Usage:
    python run_cliff_fullnull.py --scale t12 --resume
    python run_cliff_fullnull.py --scale t6 t12 t30 --resume

Pre-reg addendum: _prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np

# Import from the pre-reg-locked harness; do NOT modify that file.
sys.path.insert(0, str(Path(__file__).parent))
from run_cliff import (  # type: ignore
    Cell, StratumResult,
    SCALES, PANEL_SIZES, K_VALUES, METRICS, SEEDS,
    CLOSE_THRESHOLD, MODERATE_LOWER, DISTANT_UPPER,
    MIN_STRATUM_N, BOOTSTRAP_N,
    RESULTS_DIR, PANELS_DIR,
    verify_prereg_hash, load_labels, load_embeddings,
    build_panel, save_panel,
    compute_smax, stratify,
    METRIC_FNS, bootstrap_f1_ci,
)

FULLNULL_RNG_OFFSET = 7_777_777


def permute_labels_fullpool(labels: np.ndarray, seed: int) -> np.ndarray:
    """Permute the full 24,885 label vector once per seed.

    Determinism: rng seeded with (seed + FULLNULL_RNG_OFFSET). Independent
    of panel-sampling RNG (seed + R) and negctrl RNG (seed + 999_999).
    """
    rng = np.random.default_rng(seed + FULLNULL_RNG_OFFSET)
    permuted = labels.copy()
    rng.shuffle(permuted)
    return permuted


def evaluate_cell_fullnull(cell: Cell, emb: np.ndarray,
                           real_labels: np.ndarray) -> dict:
    """Full-dataset null: both panel and test labels are permuted consistently.

    Stratification by s_max is UNCHANGED (geometry is label-independent).
    The classifier sees fully randomized labels. Any surviving gap is
    geometric artifact of the stratification operator.
    """
    perm_labels = permute_labels_fullpool(real_labels, cell.seed)

    # Panel indices are still sampled from real label distribution for
    # class balance R/2 + R/2, per original pre-reg. The *labels assigned*
    # to those indices come from the permuted vector.
    panel_idx = build_panel(real_labels, cell.R, cell.seed)
    save_panel(panel_idx, cell.R, cell.seed)
    panel_emb = emb[panel_idx]
    panel_labels = perm_labels[panel_idx]

    test_mask = np.ones(len(real_labels), dtype=bool)
    test_mask[panel_idx] = False
    test_emb = emb[test_mask]
    test_labels = perm_labels[test_mask]

    smax = compute_smax(test_emb, panel_emb)
    strata = stratify(smax)

    fn = METRIC_FNS[cell.metric]
    y_pred = fn(test_emb, panel_emb, panel_labels, cell.k)

    out = {"cell": cell.key(), "shuffle": "fullnull"}
    for name, mask in strata.items():
        n = int(mask.sum())
        underpowered = n < MIN_STRATUM_N
        if n == 0:
            out[name] = StratumResult(
                0, float("nan"), float("nan"), float("nan"),
                float("nan"), float("nan"), underpowered
            ).__dict__
            continue
        f1_point, lo, hi = bootstrap_f1_ci(
            test_labels[mask], y_pred[mask], seed=cell.seed
        )
        out[name] = StratumResult(
            n=n, f1=f1_point, precision=float("nan"), recall=float("nan"),
            f1_ci_lo=lo, f1_ci_hi=hi, underpowered=underpowered,
        ).__dict__
    return out


def iter_cells_for_scales(scales):
    for scale in scales:
        for R in PANEL_SIZES:
            for k in K_VALUES:
                for metric in METRICS:
                    for seed in SEEDS:
                        yield Cell(scale, R, k, metric, seed)


def cell_done_fullnull(cell: Cell) -> bool:
    return (RESULTS_DIR / f"fullnull_{cell.key()}.npz").exists()


def run_fullnull(scales, resume: bool = True) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    labels, _ = load_labels()
    for scale in scales:
        emb = load_embeddings(scale)
        for cell in iter_cells_for_scales((scale,)):
            if resume and cell_done_fullnull(cell):
                continue
            t0 = time.time()
            out = evaluate_cell_fullnull(cell, emb, labels)
            np.savez(RESULTS_DIR / f"fullnull_{cell.key()}.npz", **out)
            logging.info(
                "fullnull %s done in %.1fs", cell.key(), time.time() - t0
            )


def main():
    verify_prereg_hash()
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", nargs="+", default=list(SCALES),
                    choices=list(SCALES) + ["all"])
    ap.add_argument("--resume", action="store_true", default=True)
    ap.add_argument("--no-resume", dest="resume", action="store_false")
    args = ap.parse_args()
    scales = list(SCALES) if "all" in args.scale else args.scale
    # Exclude t33 until its embeddings exist.
    scales = [s for s in scales if s != "t33"]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info("full-dataset null control starting for scales: %s", scales)
    run_fullnull(scales, resume=args.resume)
    logging.info("full-dataset null control complete")


if __name__ == "__main__":
    main()
