"""Mapper panel augmentation: does oversampling from positive-enriched Mapper
nodes rescue the distant cliff beyond uniform random sampling?

Compare two panels of R=1000 each:
  A. UNIFORM: R/2 positive + R/2 negative sampled uniformly (baseline, as in main pre-reg).
  B. MAPPER-BIASED: R/2 positive drawn from the top-N positive-enriched Mapper nodes,
     R/2 negative drawn uniformly. The biased panel over-represents the
     geometric neighborhood where positives concentrate.

Measure distant-stratum F1 under cosine kNN at k=25 for each panel, 10 seeds,
t30. Bootstrap 95% CI on the rescue: F1_biased - F1_uniform.

Pre-reg: PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md
H1: mapper-biased panel distant F1 > uniform distant F1 by at least +0.02
    with 95% CI excluding zero across 10 seeds.
"""
import json, numpy as np, sys, time
from pathlib import Path
sys.path.insert(0, r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\_experiments\homology_cliff")
from run_cliff import load_labels, load_embeddings, compute_smax, stratify, knn_cosine, bootstrap_f1_ci

MAPPER = Path(r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\_experiments\homology_cliff\mapper_graph.json")
OUT = Path(r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\_experiments\homology_cliff\mapper_augmentation_results.json")

with open(MAPPER, 'r') as f:
    mg = json.load(f)
# Top positive-enriched nodes
pos_nodes = sorted([n for n in mg['nodes'] if n['pos_frac'] > 0.5], key=lambda x: (-x['pos_frac'], -x['n']))
# Use top N nodes whose total member count >= 1000 so we can sample 500 positives from them
top_members = []
for n in pos_nodes:
    top_members.extend(n['members'])
    if len(top_members) >= 3000: break
print(f"biased pool size: {len(top_members)} from top {pos_nodes.index(pos_nodes[pos_nodes.index({x:y for x,y in pos_nodes[0].items()})])+1} nodes")

labels, accs = load_labels()
emb = load_embeddings("t30")

def build_biased_panel(R, seed, biased_pool_idx):
    """R/2 positive from biased_pool_idx (if positive there), R/2 negative uniform."""
    rng = np.random.default_rng(seed + R)
    biased_pool = np.array([i for i in biased_pool_idx if labels[i] == 1], dtype=int)
    neg_idx = np.where(labels == 0)[0]
    half = R // 2
    if len(biased_pool) < half:
        # fall back by padding with uniform positives
        other_pos = np.setdiff1d(np.where(labels == 1)[0], biased_pool)
        extra = rng.choice(other_pos, size=half - len(biased_pool), replace=False)
        pos_sample = np.concatenate([biased_pool, extra])
    else:
        pos_sample = rng.choice(biased_pool, size=half, replace=False)
    neg_sample = rng.choice(neg_idx, size=half, replace=False)
    return np.concatenate([pos_sample, neg_sample])

def build_uniform_panel(R, seed):
    rng = np.random.default_rng(seed + R)
    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    half = R // 2
    return np.concatenate([rng.choice(pos_idx, half, replace=False),
                           rng.choice(neg_idx, half, replace=False)])

R = 1000; k = 25
results = {'uniform': [], 'biased': []}
for seed in range(20260410, 20260420):
    for mode in ['uniform', 'biased']:
        if mode == 'uniform':
            panel = build_uniform_panel(R, seed)
        else:
            panel = build_biased_panel(R, seed, top_members)
        pe = emb[panel]; pl = labels[panel]
        tm = np.ones(len(labels), dtype=bool); tm[panel] = False
        te = emb[tm]; tl = labels[tm]
        smax = compute_smax(te, pe)
        st = stratify(smax)
        yp = knn_cosine(te, pe, pl, k)
        dist_mask = st['distant']
        n_dist = int(dist_mask.sum())
        if n_dist > 0:
            f1, lo, hi = bootstrap_f1_ci(tl[dist_mask], yp[dist_mask], n_boot=10000, seed=seed)
        else:
            f1, lo, hi = float('nan'), float('nan'), float('nan')
        # also close for context
        cf1, _, _ = bootstrap_f1_ci(tl[st['close']], yp[st['close']], n_boot=10000, seed=seed)
        results[mode].append({'seed': seed, 'dist_f1': f1, 'close_f1': cf1, 'n_dist': n_dist})
        print(f"  {mode:<8} seed={seed}  n_dist={n_dist:>5}  distant_F1={f1:.4f}  close_F1={cf1:.4f}")

uni_dist = [r['dist_f1'] for r in results['uniform']]
bia_dist = [r['dist_f1'] for r in results['biased']]
import random
random.seed(20260412)
diffs = [np.mean([random.choice(bia_dist) for _ in range(10)]) - np.mean([random.choice(uni_dist) for _ in range(10)]) for _ in range(5000)]
diffs.sort()
print(f"\nDistant F1 uniform mean: {np.mean(uni_dist):.4f}")
print(f"Distant F1 biased mean:  {np.mean(bia_dist):.4f}")
print(f"Rescue = biased - uniform: {np.mean(bia_dist)-np.mean(uni_dist):+.4f}")
print(f"95% CI on rescue: [{diffs[125]:+.4f}, {diffs[4875]:+.4f}]")

with open(OUT, 'w') as f:
    json.dump({'R': R, 'k': k, 'scale': 't30', 'results': results,
               'rescue_mean': float(np.mean(bia_dist)-np.mean(uni_dist)),
               'rescue_ci_lo': float(diffs[125]), 'rescue_ci_hi': float(diffs[4875])}, f, indent=1)
print(f"wrote {OUT}")
