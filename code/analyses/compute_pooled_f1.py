"""compute_pooled_f1.py -- reproduce pooled (whole-test-set) F1 for the cited cells.

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC.

The per-cell evidence in data/cells/main/ stores per-stratum F1 (close / moderate /
distant) only; the *pooled* F1 (computed over the whole test set, all strata combined)
that several headline numbers reference -- the Paper 1 rescue table's pooled column,
the abstract's "wins pooled F1 in 16 of 18 groups" / "F1 = 0.891", and the Paper 2
whitening comparison -- is committed for cosine/mahalanobis/learned/cascade in the
cascade cells (data/cells/cascade/*.npz) but not for the Fisher-Rao metric, and not in
a single consolidated summary. This script regenerates pooled F1 (plus per-stratum and
the close-distant gap) for every cited (scale, R, k, metric) cell directly from the
committed embeddings + seeds, using the *same* harness machinery as run_cliff.py /
run_fisher.py (imported, not reimplemented), and writes:

    data/results_summaries/pooled_f1_summary.json

As an internal correctness check it also re-derives the pooled F1 that the cascade cells
already store for cosine/mahalanobis/learned and asserts byte-level agreement -- so the
Fisher values, which have no committed cell to check against, inherit the same validated
pipeline. Deterministic (seeded panels, exact FAISS, torch.manual_seed(0)); repo-relative;
no Git-LFS-free fallback (needs `git lfs pull` + faiss, like run_cliff.py --full).

    python code/analyses/compute_pooled_f1.py            # regenerate the summary
    python code/analyses/compute_pooled_f1.py --check    # regenerate + assert vs committed summary (tolerance)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(os.environ.get("HOMOLOGY_CLIFF_REPO_ROOT",
                                Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(REPO_ROOT / "code" / "harnesses"))

import run_cliff as rc        # noqa: E402
import run_fisher as rf       # noqa: E402

OUT = REPO_ROOT / "data" / "results_summaries" / "pooled_f1_summary.json"
CASCADE_DIR = REPO_ROOT / "data" / "cells" / "cascade"

# The cited grid: rescue table (t30,1000,25), the learned-vs-cosine "16 of 18"
# factorial, and the Fisher/Mahalanobis 18-cell comparison all live inside this
# union {t6,t12,t30} x {100,500,1000} x {5,25} x {cosine,mahalanobis,fisher,learned}.
SCALES = ("t6", "t12", "t30")
RS = (100, 500, 1000)
KS = (5, 25)
METRICS = ("cosine", "mahalanobis", "fisher", "learned")
SEEDS = tuple(range(20260410, 20260420))


def _counts(yt: np.ndarray, yp: np.ndarray) -> tuple[int, int, int]:
    tp = int(((yt == 1) & (yp == 1)).sum())
    fp = int(((yt == 0) & (yp == 1)).sum())
    fn = int(((yt == 1) & (yp == 0)).sum())
    return tp, fp, fn


def _predict(metric, test_emb, panel_emb, panel_labels, k):
    if metric == "fisher":
        return rf.knn_fisher(test_emb, panel_emb, panel_labels, k)
    return rc.METRIC_FNS[metric](test_emb, panel_emb, panel_labels, k)


def eval_cell(emb, labels, R, k, metric, seed) -> dict:
    panel_idx = rc.build_panel(labels, R, seed)
    panel_emb = emb[panel_idx]
    panel_labels = labels[panel_idx].copy()
    test_mask = np.ones(len(labels), dtype=bool)
    test_mask[panel_idx] = False
    test_emb = emb[test_mask]
    test_labels = labels[test_mask]
    strata = rc.stratify(rc.compute_smax(test_emb, panel_emb))
    y = _predict(metric, test_emb, panel_emb, panel_labels, k)
    out = {}
    for name, mask in strata.items():
        tp, fp, fn = _counts(test_labels[mask], y[mask])
        out[name] = rc._f1_from_counts(tp, fp, fn)
    tp, fp, fn = _counts(test_labels, y)
    out["pooled"] = rc._f1_from_counts(tp, fp, fn)
    out["gap"] = out["close"] - out["distant"]
    return out


def committed_cascade_pooled() -> dict:
    """Mean pooled F1 already stored in the cascade cells (cosine/maha/learned)."""
    import re
    pat = re.compile(r"cascade_(t\d+)_(\d+)_(\d+)_(\d+)\.npz")
    acc: dict = {}
    for f in CASCADE_DIR.glob("cascade_*.npz"):
        m = pat.match(f.name)
        if not m:
            continue
        scale, R, k = m[1], int(m[2]), int(m[3])
        with np.load(f, allow_pickle=True) as z:
            for met in ("cosine", "mahalanobis", "learned"):
                acc.setdefault((scale, R, k, met), []).append(float(z[f"{met}_pooled_f1"]))
    return {key: float(np.mean(v)) for key, v in acc.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="regenerate and assert agreement with the committed summary (tolerance)")
    args = ap.parse_args()

    labels, _ = rc.load_labels()
    summary: dict = {}
    cas = committed_cascade_pooled()
    max_drift = 0.0
    for scale in SCALES:
        emb = rc.load_embeddings(scale)
        for R in RS:
            for k in KS:
                for metric in METRICS:
                    accs: dict = {}
                    for seed in SEEDS:
                        r = eval_cell(emb, labels, R, k, metric, seed)
                        for key, v in r.items():
                            accs.setdefault(key, []).append(v)
                    cell = {key: float(np.mean(v)) for key, v in accs.items()}
                    summary[f"{scale}_{R}_{k}_{metric}"] = cell
                    # cross-check vs committed cascade-cell pooled (cosine/maha/learned)
                    ck = (scale, R, k, metric)
                    if ck in cas:
                        drift = abs(cell["pooled"] - cas[ck])
                        max_drift = max(max_drift, drift)
                        if drift > 1e-6:
                            print(f"  NOTE {scale}_{R}_{k}_{metric}: reproduced pooled "
                                  f"{cell['pooled']:.6f} vs committed cascade {cas[ck]:.6f} (drift {drift:.2e})")
    print(f"cross-check vs committed cascade-cell pooled (cosine/maha/learned): "
          f"max drift = {max_drift:.2e} over {sum(1 for k in summary if any(k.endswith(m) for m in ('cosine','mahalanobis','learned')))} cells")

    summary["_doc"] = ("Pooled (whole-test-set) F1 + per-stratum F1 + close-distant gap, 10-seed mean, "
                       "reproduced from committed embeddings via run_cliff/run_fisher. Keys: scale_R_k_metric. "
                       "cosine/mahalanobis/learned pooled cross-checked == committed cascade cells; fisher pooled "
                       "inherits the same validated pipeline. Regenerate with code/analyses/compute_pooled_f1.py.")

    if args.check and OUT.is_file():
        committed = json.loads(OUT.read_text(encoding="utf-8"))
        worst = 0.0
        for key, cell in summary.items():
            if key.startswith("_") or key not in committed:
                continue
            for fld in ("close", "moderate", "distant", "pooled", "gap"):
                if fld in cell and fld in committed[key]:
                    worst = max(worst, abs(cell[fld] - committed[key][fld]))
        tol = 6e-3  # fisher uses LAPACK eigh (platform-sensitive); cosine/maha/learned are tighter
        print(f"--check: worst field drift vs committed summary = {worst:.2e} (tol {tol})")
        return 0 if worst <= tol else 1

    OUT.write_text(json.dumps(summary, indent=1, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT} ({len([k for k in summary if not k.startswith('_')])} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
