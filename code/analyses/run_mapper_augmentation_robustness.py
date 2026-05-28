"""Robustness re-run of the Mapper panel-augmentation attempt (Paper 2, Attempt 4).

Motivation
----------
The committed Mapper-augmentation result (`mapper_augmentation_results.json`:
rescue +0.0018, 95% CI [-0.027, +0.029], H1 rejected) was produced from a biased
pool assembled from Mapper-node member lists that `run_mapper.py` truncates to 50
entries per node (`members[:50]`). Audit blocker B4 concerns whether the H1
rejection is an artifact of that truncation.

A separate discrepancy was identified during the audit: Paper 2, Attempt 4
describes the biased pool as drawn from a single top positive-enriched Mapper node
(1,131 positives available, bin (7,4), pos_frac=0.885), whereas the committed
`run_mapper_augmentation.py` accumulates members across multiple positive-enriched
nodes until the pool reaches 3,000 entries. The published description and the
committed implementation therefore specify different sampling methods.

Method (non-destructive)
------------------------
The Mapper graph is regenerated in memory with full node membership (no 50-entry
cap), replicating the lens, cover, and clustering of `run_mapper.py` exactly. The
augmentation is then evaluated under three configurations:

  1. truncated-multinode  cap=50, multi-node accumulation to 3,000. Reproduces the
                          committed pipeline and serves as a self-consistency
                          check against `mapper_augmentation_results.json`.
  2. full-multinode       no cap, multi-node accumulation to 3,000. Tests the
                          robustness of the committed method to truncation.
  3. full-single-node     no cap, single node with the most positives.
                          Corresponds to the method described in Paper 2's prose.

Each configuration runs the same 10-seed (20260410-20260419) cosine-kNN comparison
(k=25, R=1000, t30) of a Mapper-biased panel against a uniform panel, using the
same 5,000-resample rescue confidence interval as the committed harness.

Output (new files only; committed artifacts are never modified):
  data/results_summaries/mapper_augmentation_robustness.json

H1 (per configuration): biased distant F1 exceeds uniform distant F1 by at least
+0.02, with a 95% confidence interval excluding zero across the 10 seeds. This is
a post-hoc robustness check, not a pre-registration.

Requirements: `git lfs pull` must have fetched data/embeddings/embeddings_t30.npy
and data/sequences/proteins_25k_sequences.json. The procedure is deterministic
(PCA random_state=0, DBSCAN, numpy default_rng, fixed random seed), so re-runs are
byte-stable.
"""
import json
import random
import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA

# run_cliff lives in ../harnesses/ relative to this file. Reuse the exact same
# data loaders and metric/stratification/bootstrap functions as the committed
# harnesses so the comparison is apples-to-apples.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harnesses"))
from run_cliff import (  # noqa: E402
    REPO_ROOT,
    bootstrap_f1_ci,
    compute_smax,
    knn_cosine,
    load_embeddings,
    load_labels,
    stratify,
)

OUT = REPO_ROOT / "data" / "results_summaries" / "mapper_augmentation_robustness.json"
COMMITTED = REPO_ROOT / "data" / "results_summaries" / "mapper_augmentation_results.json"

R = 1000
K = 25
SEEDS = list(range(20260410, 20260420))
POOL_TARGET = 3000  # multi-node accumulation target, matches run_mapper_augmentation.py
N_BOOT_CI = 5000    # rescue CI resamples, matches run_mapper_augmentation.py


def build_nodes(emb, labels, member_cap):
    """Replicate run_mapper.py's Mapper graph, with a configurable member cap.

    member_cap=None keeps full membership; member_cap=50 reproduces the committed
    graph. Returns a list of node dicts with true `n`/`pos_frac` and a `members`
    list of global indices (capped only if member_cap is not None).
    """
    pca = PCA(n_components=2, random_state=0)
    lens = pca.fit_transform(emb)

    n_bins, overlap = 10, 0.30

    def bins_1d(x, n, ovl):
        lo, hi = x.min(), x.max()
        step = (hi - lo) / n
        w = step * (1 + ovl)
        return [(lo + i * step - w * ovl / 2, lo + (i + 1) * step + w * ovl / 2) for i in range(n)]

    x_bins = bins_1d(lens[:, 0], n_bins, overlap)
    y_bins = bins_1d(lens[:, 1], n_bins, overlap)

    nodes = []
    for i, (xl, xh) in enumerate(x_bins):
        for j, (yl, yh) in enumerate(y_bins):
            mask = (lens[:, 0] >= xl) & (lens[:, 0] < xh) & (lens[:, 1] >= yl) & (lens[:, 1] < yh)
            if mask.sum() < 5:
                continue
            sub_emb = emb[mask]
            sub_idx = np.where(mask)[0]
            cos_dist = 1.0 - sub_emb @ sub_emb.T
            cos_dist = np.clip(cos_dist, 0.0, 2.0)
            np.fill_diagonal(cos_dist, 0.0)
            db = DBSCAN(eps=0.05, min_samples=5, metric="precomputed").fit(cos_dist)
            for cid in set(db.labels_):
                if cid == -1:
                    continue
                cluster_mask = db.labels_ == cid
                members = sub_idx[cluster_mask].tolist()
                pos_count = int(labels[members].sum())
                stored = members if member_cap is None else members[:member_cap]
                nodes.append({
                    "bin": (i, j),
                    "cluster": int(cid),
                    "n": len(members),
                    "pos_frac": pos_count / len(members),
                    "members": stored,
                })
    return nodes


def pool_multinode(nodes, target):
    """Committed method: accumulate members from positive-enriched nodes
    (sorted by -pos_frac, -n) until the pool reaches `target` entries."""
    pos_nodes = sorted([n for n in nodes if n["pos_frac"] > 0.5], key=lambda x: (-x["pos_frac"], -x["n"]))
    pool, used = [], 0
    for n in pos_nodes:
        pool.extend(n["members"])
        used += 1
        if len(pool) >= target:
            break
    return pool, used


def pool_singlenode(nodes):
    """Paper-2 prose method: the single positive-enriched node with the most
    positives (pos_frac * n), using its full member list."""
    pos_nodes = [n for n in nodes if n["pos_frac"] > 0.5]
    top = max(pos_nodes, key=lambda x: x["pos_frac"] * x["n"])
    return list(top["members"]), top


def build_uniform_panel(labels, R, seed):
    rng = np.random.default_rng(seed + R)
    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    half = R // 2
    return np.concatenate([rng.choice(pos_idx, half, replace=False),
                           rng.choice(neg_idx, half, replace=False)])


def build_biased_panel(labels, R, seed, biased_pool_idx):
    rng = np.random.default_rng(seed + R)
    biased_pool = np.array([i for i in biased_pool_idx if labels[i] == 1], dtype=int)
    neg_idx = np.where(labels == 0)[0]
    half = R // 2
    if len(biased_pool) < half:
        other_pos = np.setdiff1d(np.where(labels == 1)[0], biased_pool)
        extra = rng.choice(other_pos, size=half - len(biased_pool), replace=False)
        pos_sample = np.concatenate([biased_pool, extra])
    else:
        pos_sample = rng.choice(biased_pool, size=half, replace=False)
    neg_sample = rng.choice(neg_idx, size=half, replace=False)
    return np.concatenate([pos_sample, neg_sample])


def evaluate(emb, labels, biased_pool_idx):
    """Run the 10-seed uniform-vs-biased comparison; return per-seed rows and
    the rescue mean + 95% CI (5,000 resamples, matching the committed harness)."""
    results = {"uniform": [], "biased": []}
    for seed in SEEDS:
        for mode in ("uniform", "biased"):
            if mode == "uniform":
                panel = build_uniform_panel(labels, R, seed)
            else:
                panel = build_biased_panel(labels, R, seed, biased_pool_idx)
            pe, pl = emb[panel], labels[panel]
            tm = np.ones(len(labels), dtype=bool)
            tm[panel] = False
            te, tl = emb[tm], labels[tm]
            st = stratify(compute_smax(te, pe))
            yp = knn_cosine(te, pe, pl, K)
            dist_mask = st["distant"]
            n_dist = int(dist_mask.sum())
            if n_dist > 0:
                f1, _, _ = bootstrap_f1_ci(tl[dist_mask], yp[dist_mask], n_boot=10000, seed=seed)
            else:
                f1 = float("nan")
            cf1, _, _ = bootstrap_f1_ci(tl[st["close"]], yp[st["close"]], n_boot=10000, seed=seed)
            results[mode].append({"seed": seed, "dist_f1": f1, "close_f1": cf1, "n_dist": n_dist})

    uni = [r["dist_f1"] for r in results["uniform"]]
    bia = [r["dist_f1"] for r in results["biased"]]
    random.seed(20260412)
    diffs = sorted(
        np.mean([random.choice(bia) for _ in range(10)]) - np.mean([random.choice(uni) for _ in range(10)])
        for _ in range(N_BOOT_CI)
    )
    lo_i, hi_i = int(0.025 * N_BOOT_CI), int(0.975 * N_BOOT_CI)
    rescue = float(np.mean(bia) - np.mean(uni))
    ci_lo, ci_hi = float(diffs[lo_i]), float(diffs[hi_i])
    h1_supported = bool(rescue >= 0.02 and ci_lo > 0)
    return {
        "uniform_distant_f1_mean": float(np.mean(uni)),
        "biased_distant_f1_mean": float(np.mean(bia)),
        "rescue_mean": rescue,
        "rescue_ci_lo": ci_lo,
        "rescue_ci_hi": ci_hi,
        "h1_supported": h1_supported,
        "results": results,
    }


def main():
    print("Loading t30 embeddings and labels (requires git lfs pull)...")
    labels, _ = load_labels()
    emb = load_embeddings("t30")
    print(f"  shape {emb.shape}, positives {int(labels.sum())}/{len(labels)}")

    summary = {"R": R, "k": K, "scale": "t30", "n_boot_ci": N_BOOT_CI, "configs": {}}

    print("\nRegenerating Mapper graph at cap=50 (reproduces committed pipeline)...")
    nodes_trunc = build_nodes(emb, labels, member_cap=50)
    pool_t, used_t = pool_multinode(nodes_trunc, POOL_TARGET)
    print(f"  biased pool {len(pool_t)} members from {used_t} nodes")
    summary["configs"]["truncated_multinode"] = {
        "description": "cap=50, multi-node accumulation to 3000 (committed method)",
        "biased_pool_size": len(pool_t),
        "nodes_used": used_t,
        **evaluate(emb, labels, pool_t),
    }

    print("\nRegenerating Mapper graph at full membership (no cap)...")
    nodes_full = build_nodes(emb, labels, member_cap=None)

    pool_fm, used_fm = pool_multinode(nodes_full, POOL_TARGET)
    print(f"  full-multinode biased pool {len(pool_fm)} members from {used_fm} nodes")
    summary["configs"]["full_multinode"] = {
        "description": "no cap, multi-node accumulation to 3000 (robustness of committed method)",
        "biased_pool_size": len(pool_fm),
        "nodes_used": used_fm,
        **evaluate(emb, labels, pool_fm),
    }

    pool_sn, top = pool_singlenode(nodes_full)
    print(f"  full-single-node biased pool {len(pool_sn)} members "
          f"(bin {top['bin']}, pos_frac={top['pos_frac']:.3f}, ~{int(top['pos_frac'] * top['n'])} positives)")
    summary["configs"]["full_single_node"] = {
        "description": "no cap, single node with the most positives (Paper 2 prose method)",
        "biased_pool_size": len(pool_sn),
        "top_node_bin": list(top["bin"]),
        "top_node_pos_frac": top["pos_frac"],
        "top_node_positives": int(top["pos_frac"] * top["n"]),
        **evaluate(emb, labels, pool_sn),
    }

    # Self-check against the committed result.
    if COMMITTED.is_file():
        committed = json.loads(COMMITTED.read_text())
        repro = summary["configs"]["truncated_multinode"]
        drift = abs(repro["rescue_mean"] - committed.get("rescue_mean", float("nan")))
        summary["reproduction_check"] = {
            "committed_rescue_mean": committed.get("rescue_mean"),
            "regenerated_rescue_mean": repro["rescue_mean"],
            "abs_drift": drift,
            "reproduced": bool(drift < 1e-6),
        }
        print(f"\nReproduction check: committed={committed.get('rescue_mean'):.6f} "
              f"regenerated={repro['rescue_mean']:.6f} drift={drift:.2e} "
              f"{'OK' if drift < 1e-6 else 'DRIFT — investigate'}")

    OUT.write_text(json.dumps(summary, indent=1))
    print(f"\nwrote {OUT}")
    print("\n=== SUMMARY (rescue = biased distant F1 - uniform distant F1) ===")
    for name, cfg in summary["configs"].items():
        print(f"  {name:<22} rescue={cfg['rescue_mean']:+.4f} "
              f"CI=[{cfg['rescue_ci_lo']:+.4f}, {cfg['rescue_ci_hi']:+.4f}] "
              f"H1={'SUPPORTED' if cfg['h1_supported'] else 'rejected'}")


if __name__ == "__main__":
    main()
