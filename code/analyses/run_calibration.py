"""run_calibration.py -- Calibration analysis for Paper 3.

Computes per-stratum reliability and Expected Calibration Error (ECE) for
the t30 R=1000 k=25 cosine baseline at seed 20260410. Reproduces every
number reported in Paper 3 (`papers/03_calibration_collapse/paper.tex`):

    close-stratum ECE   = 0.069
    moderate-stratum ECE = 0.154
    distant-stratum ECE = 0.294
    distant pos-pred precision = 3 / 44 = 0.068
    close pos-pred precision   = 0.891
    moderate pos-pred precision = 0.467

Reliability binning matches the published figure exactly:
    [0.0, 0.1)  [0.1, 0.3)  [0.3, 0.5)  [0.5, 0.7)  [0.7, 0.9)  [0.9, 1.0]
This is six unequal-width bins, the standard tight-tails wide-middle scheme
used in the calibration-under-shift literature (Guo et al. 2017 use a
similar non-uniform scheme to absorb the dense low-confidence predictions
without smearing the diagnostic high-confidence tail).

Output: data/results_summaries/calibration_results.json with the full
per-stratum, per-bin reliability table plus aggregate ECEs and pos-pred
precisions. Headline values are read off this file by Paper 3's TeX
source (no number lives only in prose).

Repo-relative paths via REPO_ROOT (overridable with HOMOLOGY_CLIFF_REPO_ROOT).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

# Defer faiss import; raise a clear message if missing.
try:
    import faiss  # type: ignore
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "faiss is required for run_calibration.py. Install with "
        "`pip install faiss-cpu` (CPU build is sufficient)."
    ) from e

# run_cliff lives in ../harnesses/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harnesses"))
from run_cliff import (  # type: ignore
    REPO_ROOT,
    load_labels, load_embeddings, build_panel,
    compute_smax, stratify,
)


# ---------------------------------------------------------------------------
# Reliability binning. SIX UNEQUAL-WIDTH BINS to match Paper 3's published
# figure. The first and last bins are width 0.1 (tight tails for the
# zero-prediction and full-confidence regions); the middle four are width
# 0.2 each. Boundaries: 0.0 0.1 0.3 0.5 0.7 0.9 1.0.
# ---------------------------------------------------------------------------

BIN_EDGES = (0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0001)  # +eps so 1.0 falls in last bin
BIN_LABELS = ("[0.0,0.1)", "[0.1,0.3)", "[0.3,0.5)",
              "[0.5,0.7)", "[0.7,0.9)", "[0.9,1.0]")


def bin_index(vote_frac: np.ndarray) -> np.ndarray:
    """Map vote-fraction to bin index in [0, 5]."""
    # np.digitize returns bin index in [1, len(edges)]; subtract 1 to get [0, ...]
    idx = np.digitize(vote_frac, BIN_EDGES) - 1
    return np.clip(idx, 0, len(BIN_LABELS) - 1)


def reliability_table(vote_frac: np.ndarray, y_true: np.ndarray
                      ) -> list[dict]:
    """Per-bin n, mean predicted, mean observed."""
    bidx = bin_index(vote_frac)
    rows = []
    for b in range(len(BIN_LABELS)):
        m = bidx == b
        n = int(m.sum())
        if n == 0:
            rows.append(dict(bin=BIN_LABELS[b], n=0,
                             mean_pred=float("nan"),
                             mean_obs=float("nan")))
        else:
            rows.append(dict(
                bin=BIN_LABELS[b], n=n,
                mean_pred=float(vote_frac[m].mean()),
                mean_obs=float(y_true[m].mean()),
            ))
    return rows


def expected_calibration_error(rows: list[dict]) -> float:
    """ECE = sum_b (n_b/N) * |mean_pred_b - mean_obs_b| over non-empty bins."""
    n_total = sum(r["n"] for r in rows)
    if n_total == 0:
        return float("nan")
    ece = 0.0
    for r in rows:
        if r["n"] == 0:
            continue
        ece += (r["n"] / n_total) * abs(r["mean_pred"] - r["mean_obs"])
    return ece


def positive_prediction_precision(vote_frac: np.ndarray, y_true: np.ndarray,
                                  threshold: float = 0.5) -> dict:
    """Precision when the classifier predicts positive (vote_frac >= threshold)."""
    pred_pos = vote_frac >= threshold
    n_pp = int(pred_pos.sum())
    tp = int(y_true[pred_pos].sum()) if n_pp else 0
    return dict(
        n_predicted_positive=n_pp,
        tp=tp,
        fp=n_pp - tp,
        precision=(tp / n_pp) if n_pp else float("nan"),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(scale: str = "t30", R: int = 1000, k: int = 25,
         seed: int = 20260410) -> dict:
    labels, accessions = load_labels()
    emb = load_embeddings(scale)

    panel_idx = build_panel(labels, R, seed)
    panel_emb = emb[panel_idx]
    panel_labels = labels[panel_idx]
    test_mask = np.ones(len(labels), dtype=bool)
    test_mask[panel_idx] = False
    test_emb = emb[test_mask]
    test_labels = labels[test_mask]

    smax = compute_smax(test_emb, panel_emb)
    strata = stratify(smax)

    # Cosine k-NN vote fractions
    index = faiss.IndexFlatIP(panel_emb.shape[1])
    index.add(np.ascontiguousarray(panel_emb, dtype=np.float32))
    _, neighbors = index.search(np.ascontiguousarray(test_emb, dtype=np.float32), k)
    vote_frac = (panel_labels[neighbors] == 1).mean(axis=1)

    out: dict = dict(
        scale=scale, R=R, k=k, seed=seed, metric="cosine",
        n_test=int(test_mask.sum()),
        bin_scheme="six_unequal: 0.0 0.1 0.3 0.5 0.7 0.9 1.0",
    )
    for sname in ("close", "moderate", "distant"):
        mask = strata[sname]
        n = int(mask.sum())
        rows = reliability_table(vote_frac[mask], test_labels[mask])
        ece = expected_calibration_error(rows)
        ppp = positive_prediction_precision(vote_frac[mask], test_labels[mask])
        out[sname] = dict(
            n=n,
            reliability=rows,
            ECE=ece,
            positive_prediction=ppp,
        )

    # Aggregate diagnostics
    if not (np.isnan(out["close"]["ECE"]) or np.isnan(out["distant"]["ECE"])):
        out["ece_distant_to_close_ratio"] = (
            out["distant"]["ECE"] / out["close"]["ECE"]
        )

    return out


if __name__ == "__main__":
    result = main()
    out_path = REPO_ROOT / "data" / "results_summaries" / "calibration_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    print(f"wrote {out_path}")

    # Stdout summary mirrors Paper 3's tabulated headline values.
    print()
    print(f"{'stratum':<10} {'n':>8} {'ECE':>8} {'pos-pred prec':>15}")
    for sname in ("close", "moderate", "distant"):
        s = result[sname]
        ppp = s["positive_prediction"]
        print(f"{sname:<10} {s['n']:>8d} {s['ECE']:>8.4f} "
              f"{ppp['tp']:>3}/{ppp['n_predicted_positive']:<3} "
              f"= {ppp['precision']:.4f}")
    if "ece_distant_to_close_ratio" in result:
        print(f"\ndistant/close ECE ratio: {result['ece_distant_to_close_ratio']:.2f}x")
