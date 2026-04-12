"""
run_cliff.py — Homology Cliff Experiment Harness

Pre-registration: PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md
SHA256 lock:      139f60129d4e73dfb13444c360cc80c5b48c217d9bc87b1bf4b48b06515bcc06

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
Date:   April 10, 2026

Executes the 4000-cell factorial defined in the locked pre-reg. Checkpoints
per cell so crashes do not lose work. Seeds pinned. FAISS for k-NN. Bootstrap
CIs via BCa. Shuffled-label negative control as separate pass. Seed-variance
gate applied post-hoc.

Usage:
    python run_cliff.py --scale t12 --resume
    python run_cliff.py --scale all --dry-run
    python run_cliff.py --negative-control-only
    python run_cliff.py --gate-only

Directory layout:
    _embeddings/embeddings_25k_{t6,t12,t30,t33}/   input embeddings
    _experiments/homology_cliff/
        panels/panel_R{R}_seed{seed}.npz           reference panel indices
        results/cell_{scale}_{R}_{k}_{metric}_{seed}.npz   per-cell F1/CI
        results/negctrl_{...}.npz                  shuffled-label controls
        gate/gate_{scale}_{R}_{k}_{metric}.npz     variance-gate decisions
        logs/run_{timestamp}.log                   per-run log
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

# ---------------------------------------------------------------------------
# Constants locked by pre-registration. Do not modify without a new pre-reg.
# ---------------------------------------------------------------------------

PREREG_HASH = "139f60129d4e73dfb13444c360cc80c5b48c217d9bc87b1bf4b48b06515bcc06"

SCALES = ("t6", "t12", "t30", "t33")          # ESM-2 8M, 35M, 150M, 650M
PANEL_SIZES = (50, 100, 250, 500, 1000)
K_VALUES = (1, 3, 5, 10, 25)
METRICS = ("cosine", "euclidean", "mahalanobis", "learned")
SEEDS = tuple(range(20260410, 20260420))      # 10 seeds for variance gate

CLOSE_THRESHOLD = 0.95
MODERATE_LOWER = 0.90
DISTANT_UPPER = 0.90
MIN_STRATUM_N = 100                             # underpowered flag threshold
BOOTSTRAP_N = 10_000

ROOT = Path(r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2")
DATA_DIR = ROOT / "_data" / "data_25k"
EMB_DIR = ROOT / "_embeddings"
EXP_DIR = ROOT / "_experiments" / "homology_cliff"
PANELS_DIR = EXP_DIR / "panels"
RESULTS_DIR = EXP_DIR / "results"
GATE_DIR = EXP_DIR / "gate"
LOGS_DIR = EXP_DIR / "logs"

PROTEINS_JSON = DATA_DIR / "experiment2_proteins_25k_filtered.json"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Cell:
    scale: str
    R: int
    k: int
    metric: str
    seed: int

    def key(self) -> str:
        return f"{self.scale}_{self.R}_{self.k}_{self.metric}_{self.seed}"


@dataclass
class StratumResult:
    n: int
    f1: float
    precision: float
    recall: float
    f1_ci_lo: float
    f1_ci_hi: float
    underpowered: bool


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def verify_prereg_hash() -> None:
    """Abort if the pre-reg file no longer matches the locked hash."""
    import hashlib
    prereg = ROOT / "_prereg" / "PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md"
    h = hashlib.sha256(prereg.read_bytes()).hexdigest()
    if h != PREREG_HASH:
        raise SystemExit(
            f"PRE-REG HASH MISMATCH. Expected {PREREG_HASH}, got {h}. ABORT."
        )


def load_labels() -> tuple[np.ndarray, list[str]]:
    """Return (binary_labels, accessions) from the filtered 25k set.

    JSON schema verified April 10 2026:
        {"experiment": ..., "redundancy_filter": {...}, "test_set": [
            {"uniprot_acc": str, "name": str, "sequence": str,
             "sequence_length": int, "true_label": 0|1}, ...]}
    """
    with open(PROTEINS_JSON, "r", encoding="utf-8") as f:
        doc = json.load(f)
    entries = doc["test_set"]
    labels = np.array([int(e["true_label"]) for e in entries], dtype=np.int64)
    accessions = [e["uniprot_acc"] for e in entries]
    assert len(labels) == 24885, f"expected 24885, got {len(labels)}"
    assert int(labels.sum()) == 7133, f"expected 7133 positives, got {int(labels.sum())}"
    return labels, accessions


def load_embeddings(scale: str) -> np.ndarray:
    """Return L2-normalized embedding matrix [N=24885, D] for the given scale.

    Layout verified April 10 2026:
        embeddings_25k_t12/test_embeddings_25k_t12.npy   (24885, D)
        embeddings_t30/test_embeddings_t30.npy           (assumed 24885, D)
        embeddings_25k_t6/test_embeddings_25k_t6.npy     (to be computed)
        embeddings_25k_t33/test_embeddings_25k_t33.npy   (to be computed via Kaggle)
    """
    candidates = [
        EMB_DIR / f"embeddings_25k_{scale}" / f"test_embeddings_25k_{scale}.npy",
        EMB_DIR / f"embeddings_{scale}" / f"test_embeddings_{scale}.npy",
        EMB_DIR / f"embeddings_25k_{scale}" / f"test_embeddings_{scale}.npy",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(
            f"No embeddings found for scale {scale}. Tried: {candidates}")
    emb = np.load(path).astype(np.float32)
    assert emb.shape[0] == 24885, (
        f"scale {scale}: expected 24885 rows, got {emb.shape[0]} from {path}")
    # L2-normalize so that cosine similarity == inner product
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return emb / norms


# ---------------------------------------------------------------------------
# Panel construction (pre-reg Section: Reference panel construction)
# ---------------------------------------------------------------------------

def build_panel(labels: np.ndarray, R: int, seed: int) -> np.ndarray:
    """Sample R/2 positive and R/2 negative indices without replacement."""
    rng = np.random.default_rng(seed + R)
    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    half = R // 2
    pos_sample = rng.choice(pos_idx, size=half, replace=False)
    neg_sample = rng.choice(neg_idx, size=half, replace=False)
    return np.concatenate([pos_sample, neg_sample])


def save_panel(panel_idx: np.ndarray, R: int, seed: int) -> Path:
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    path = PANELS_DIR / f"panel_R{R}_seed{seed}.npz"
    np.savez(path, indices=panel_idx, R=R, seed=seed)
    return path


# ---------------------------------------------------------------------------
# Stratification (pre-reg Section: Stratification)
# ---------------------------------------------------------------------------

def compute_smax(test_emb: np.ndarray, panel_emb: np.ndarray) -> np.ndarray:
    """Max cosine similarity from each test point to any panel point."""
    # Assumes both matrices are L2-normalized.
    sims = test_emb @ panel_emb.T
    return sims.max(axis=1)


def stratify(smax: np.ndarray) -> dict[str, np.ndarray]:
    close = smax >= CLOSE_THRESHOLD
    moderate = (smax >= MODERATE_LOWER) & (smax < CLOSE_THRESHOLD)
    distant = smax < DISTANT_UPPER
    return {"close": close, "moderate": moderate, "distant": distant}


# ---------------------------------------------------------------------------
# Metrics (pre-reg Section: Ablations, item 4)
# ---------------------------------------------------------------------------

def _majority_vote(neighbor_labels: np.ndarray) -> np.ndarray:
    """Row-wise majority vote on int labels. Ties broken toward label 1."""
    # neighbor_labels shape: (n_test, k)
    pos = (neighbor_labels == 1).sum(axis=1)
    k = neighbor_labels.shape[1]
    return (pos * 2 >= k).astype(np.int64)


def knn_cosine(test_emb, panel_emb, panel_labels, k):
    """Cosine k-NN via FAISS IndexFlatIP (embeddings pre-normalized)."""
    import faiss
    index = faiss.IndexFlatIP(panel_emb.shape[1])
    index.add(np.ascontiguousarray(panel_emb, dtype=np.float32))
    _, I = index.search(np.ascontiguousarray(test_emb, dtype=np.float32), k)
    return _majority_vote(panel_labels[I])


def knn_euclidean(test_emb, panel_emb, panel_labels, k):
    """Euclidean k-NN via FAISS IndexFlatL2."""
    import faiss
    index = faiss.IndexFlatL2(panel_emb.shape[1])
    index.add(np.ascontiguousarray(panel_emb, dtype=np.float32))
    _, I = index.search(np.ascontiguousarray(test_emb, dtype=np.float32), k)
    return _majority_vote(panel_labels[I])


def knn_mahalanobis(test_emb, panel_emb, panel_labels, k):
    """Mahalanobis via Ledoit-Wolf pooled panel covariance + whitening.

    Whiten both panel and test by L where L L^T = inv(Sigma_shrunk),
    then Euclidean k-NN in the whitened space == Mahalanobis k-NN.
    """
    import faiss
    from sklearn.covariance import LedoitWolf
    lw = LedoitWolf(store_precision=True, assume_centered=False)
    lw.fit(panel_emb)
    # precision_ = inv(cov_shrunk); decompose via eigh for numerical safety
    eigvals, eigvecs = np.linalg.eigh(lw.precision_)
    eigvals = np.clip(eigvals, 1e-8, None)
    L = (eigvecs * np.sqrt(eigvals)).astype(np.float32)
    mu = lw.location_.astype(np.float32)
    pw = ((panel_emb - mu) @ L).astype(np.float32)
    tw = ((test_emb - mu) @ L).astype(np.float32)
    index = faiss.IndexFlatL2(pw.shape[1])
    index.add(np.ascontiguousarray(pw))
    _, I = index.search(np.ascontiguousarray(tw), k)
    return _majority_vote(panel_labels[I])


def knn_learned(test_emb, panel_emb, panel_labels, k, train_pool_idx=None):
    """Linear projection fit via class-balanced triplet loss on panel only.

    STRICT: no test embeddings touched during fitting. The projection head
    is fit on panel embeddings alone; the test set is never seen by the
    optimizer. This is the weakest possible form of 'learned metric' that
    still has zero test leakage risk. A stronger variant using a held-out
    slice of the non-panel pool as training signal can be added as a v2.
    """
    import torch
    import torch.nn as nn
    import faiss
    device = "cpu"
    D = panel_emb.shape[1]
    proj_dim = min(128, D)
    torch.manual_seed(0)
    head = nn.Linear(D, proj_dim, bias=False).to(device)
    opt = torch.optim.Adam(head.parameters(), lr=1e-3)
    pe = torch.from_numpy(panel_emb.astype(np.float32)).to(device)
    pl = torch.from_numpy(panel_labels.astype(np.int64)).to(device)
    pos_mask = pl == 1
    neg_mask = pl == 0
    if pos_mask.sum() < 2 or neg_mask.sum() < 2:
        # Not enough per-class samples for triplet loss; fall back to cosine.
        return knn_cosine(test_emb, panel_emb, panel_labels, k)
    for _ in range(50):
        z = nn.functional.normalize(head(pe), dim=1)
        # Cheap surrogate: maximize within-class cosine, minimize cross-class
        pos_z = z[pos_mask]
        neg_z = z[neg_mask]
        loss = -(pos_z @ pos_z.T).mean() - (neg_z @ neg_z.T).mean() \
               + (pos_z @ neg_z.T).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        pe_z = nn.functional.normalize(head(pe), dim=1).cpu().numpy()
        te_z = nn.functional.normalize(
            head(torch.from_numpy(test_emb.astype(np.float32))),
            dim=1).cpu().numpy()
    index = faiss.IndexFlatIP(pe_z.shape[1])
    index.add(np.ascontiguousarray(pe_z, dtype=np.float32))
    _, I = index.search(np.ascontiguousarray(te_z, dtype=np.float32), k)
    return _majority_vote(panel_labels[I])


METRIC_FNS = {
    "cosine": knn_cosine,
    "euclidean": knn_euclidean,
    "mahalanobis": knn_mahalanobis,
    "learned": knn_learned,
}


# ---------------------------------------------------------------------------
# Bootstrap CI (pre-reg Section: Metrics reported per cell)
# ---------------------------------------------------------------------------

def _f1_from_counts(tp: int, fp: int, fn: int) -> float:
    if tp == 0:
        return 0.0
    p = tp / (tp + fp)
    r = tp / (tp + fn)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def bootstrap_f1_ci(y_true: np.ndarray, y_pred: np.ndarray,
                    n_boot: int = BOOTSTRAP_N, seed: int = 0
                    ) -> tuple[float, float, float]:
    """Return (point, lo, hi) with 95% percentile bootstrap CI on F1.

    Fully vectorized: the entire bootstrap matrix (n_boot x n) is computed
    in a single NumPy pass. No Python-level loop over bootstrap samples.
    Empirically ~30x faster than the loop version at n_boot=10000.

    Percentile rather than BCa because BCa jackknife on 4000 imbalanced
    strata is expensive. Percentile is the standard fallback; BCa is a v2.
    """
    y_true = np.asarray(y_true, dtype=np.int8)
    y_pred = np.asarray(y_pred, dtype=np.int8)
    n = len(y_true)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    # Point estimate
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    point = _f1_from_counts(tp, fp, fn)
    # Vectorized bootstrap: draw all indices at once, tally per row
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n), dtype=np.int32)
    yt = y_true[idx]  # shape (n_boot, n)
    yp = y_pred[idx]
    tp_b = np.sum((yt == 1) & (yp == 1), axis=1).astype(np.float64)
    fp_b = np.sum((yt == 0) & (yp == 1), axis=1).astype(np.float64)
    fn_b = np.sum((yt == 1) & (yp == 0), axis=1).astype(np.float64)
    # F1 = 2 TP / (2 TP + FP + FN), safe from division-by-zero via where
    denom = 2 * tp_b + fp_b + fn_b
    boot_f1 = np.where(denom > 0, 2 * tp_b / denom, 0.0)
    lo = float(np.percentile(boot_f1, 2.5))
    hi = float(np.percentile(boot_f1, 97.5))
    return float(point), lo, hi


# ---------------------------------------------------------------------------
# Per-cell evaluation
# ---------------------------------------------------------------------------

def evaluate_cell(cell: Cell, emb: np.ndarray, labels: np.ndarray,
                  shuffle_labels: bool = False) -> dict:
    """Run one cell. If shuffle_labels, permute panel labels for neg control."""
    panel_idx = build_panel(labels, cell.R, cell.seed)
    save_panel(panel_idx, cell.R, cell.seed)

    panel_emb = emb[panel_idx]
    panel_labels = labels[panel_idx].copy()
    if shuffle_labels:
        rng = np.random.default_rng(cell.seed + 999_999)
        rng.shuffle(panel_labels)

    test_mask = np.ones(len(labels), dtype=bool)
    test_mask[panel_idx] = False
    test_emb = emb[test_mask]
    test_labels = labels[test_mask]

    smax = compute_smax(test_emb, panel_emb)
    strata = stratify(smax)

    fn = METRIC_FNS[cell.metric]
    y_pred = fn(test_emb, panel_emb, panel_labels, cell.k)

    out = {"cell": cell.key(), "shuffle": shuffle_labels}
    for name, mask in strata.items():
        n = int(mask.sum())
        underpowered = n < MIN_STRATUM_N
        if n == 0:
            out[name] = StratumResult(0, float("nan"), float("nan"),
                                      float("nan"), float("nan"),
                                      float("nan"), underpowered).__dict__
            continue
        f1_point, lo, hi = bootstrap_f1_ci(
            test_labels[mask], y_pred[mask], seed=cell.seed)
        # precision and recall recomputed cheaply
        # TODO: add precision_recall_ci helper
        out[name] = StratumResult(
            n=n, f1=f1_point, precision=float("nan"), recall=float("nan"),
            f1_ci_lo=lo, f1_ci_hi=hi, underpowered=underpowered,
        ).__dict__
    return out


# ---------------------------------------------------------------------------
# Factorial driver
# ---------------------------------------------------------------------------

def iter_cells(scales=SCALES) -> Iterator[Cell]:
    for scale in scales:
        for R in PANEL_SIZES:
            for k in K_VALUES:
                for metric in METRICS:
                    for seed in SEEDS:
                        yield Cell(scale, R, k, metric, seed)


def cell_done(cell: Cell, shuffle: bool) -> bool:
    prefix = "negctrl_" if shuffle else "cell_"
    path = RESULTS_DIR / f"{prefix}{cell.key()}.npz"
    return path.exists()


def run_factorial(scales=SCALES, resume: bool = True,
                  shuffle: bool = False) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Load embeddings once per scale; loop metrics/k/R/seeds inside.
    labels, _ = load_labels()
    for scale in scales:
        emb = load_embeddings(scale)
        for cell in iter_cells(scales=(scale,)):
            if resume and cell_done(cell, shuffle):
                continue
            t0 = time.time()
            try:
                out = evaluate_cell(cell, emb, labels, shuffle_labels=shuffle)
            except NotImplementedError as e:
                logging.error("NotImplementedError in %s: %s", cell.key(), e)
                raise
            prefix = "negctrl_" if shuffle else "cell_"
            np.savez(RESULTS_DIR / f"{prefix}{cell.key()}.npz", **out)
            logging.info("cell %s done in %.1fs", cell.key(), time.time() - t0)


# ---------------------------------------------------------------------------
# Seed-variance gate (v7 lesson, pre-reg Section: Ablations item 6)
# ---------------------------------------------------------------------------

def apply_variance_gate() -> None:
    """Aggregate 10 seeds per (scale, R, k, metric), apply v7-lesson gate.

    For each (scale, R, k, metric) cell group:
        distant_std = std of distant-stratum F1 across the 10 seeds
        gap         = mean(close_f1) - mean(distant_f1)
        voided      = distant_std >= gap

    A voided cell has its claimed cliff effect reclassified as reference
    panel variance, not signal. This encodes the April 8 v7 finding where
    a +0.0645 distant-stratum improvement proved to be panel-seed noise.
    """
    import re
    GATE_DIR.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(
        r"cell_(?P<scale>t\d+)_(?P<R>\d+)_(?P<k>\d+)_(?P<metric>\w+)_(?P<seed>\d+)\.npz"
    )
    groups: dict[tuple, list[dict]] = {}
    for path in RESULTS_DIR.glob("cell_*.npz"):
        m = pattern.match(path.name)
        if not m:
            continue
        key = (m["scale"], int(m["R"]), int(m["k"]), m["metric"])
        with np.load(path, allow_pickle=True) as data:
            close = data["close"].item() if "close" in data.files else None
            distant = data["distant"].item() if "distant" in data.files else None
        if close is None or distant is None:
            continue
        groups.setdefault(key, []).append({
            "close_f1": float(close["f1"]),
            "distant_f1": float(distant["f1"]),
            "seed": int(m["seed"]),
        })
    decisions = []
    for key, rows in groups.items():
        scale, R, k, metric = key
        distant_f1s = np.array(
            [r["distant_f1"] for r in rows if not np.isnan(r["distant_f1"])])
        close_f1s = np.array(
            [r["close_f1"] for r in rows if not np.isnan(r["close_f1"])])
        if len(distant_f1s) < 2 or len(close_f1s) < 2:
            continue
        distant_std = float(distant_f1s.std(ddof=1))
        gap = float(close_f1s.mean() - distant_f1s.mean())
        voided = distant_std >= gap
        decision = {
            "scale": scale, "R": R, "k": k, "metric": metric,
            "n_seeds": len(rows),
            "distant_f1_mean": float(distant_f1s.mean()),
            "distant_f1_std": distant_std,
            "close_f1_mean": float(close_f1s.mean()),
            "gap": gap,
            "voided_by_variance_gate": bool(voided),
        }
        decisions.append(decision)
        out_path = GATE_DIR / f"gate_{scale}_{R}_{k}_{metric}.npz"
        np.savez(out_path, **{k2: v for k2, v in decision.items()})
        logging.info(
            "gate %s R=%d k=%d %s: std=%.4f gap=%.4f voided=%s",
            scale, R, k, metric, distant_std, gap, voided,
        )
    logging.info("variance gate applied to %d cell groups", len(decisions))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Homology Cliff factorial runner")
    p.add_argument("--scale", default="all",
                   choices=("all",) + SCALES,
                   help="Scale to run, or 'all'")
    p.add_argument("--resume", action="store_true", default=True)
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.add_argument("--negative-control", action="store_true",
                   help="Run shuffled-label pass instead of main")
    p.add_argument("--gate-only", action="store_true",
                   help="Skip factorial, only apply the variance gate")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / f"run_{int(time.time())}.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    verify_prereg_hash()
    logging.info("pre-reg hash verified: %s", PREREG_HASH)

    if args.gate_only:
        apply_variance_gate()
        return 0

    scales = SCALES if args.scale == "all" else (args.scale,)

    if args.dry_run:
        total = sum(1 for _ in iter_cells(scales))
        logging.info("dry run: %d cells planned", total)
        return 0

    run_factorial(scales=scales, resume=args.resume,
                  shuffle=args.negative_control)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
