"""Mapper topology on the 24,885-protein t30 embedding manifold.

Uses the existing L2-normalized ESM-2 t30 embeddings. Computes:
  - Lens: first two principal component scores (captures global geometry)
  - Cover: 10 x 10 overlapping hypercubes, 30% overlap
  - Clustering per pre-image: DBSCAN on cosine distance, eps 0.05, min_samples 5

Output: mapper_graph.json with nodes (clusters) and edges (cluster overlaps),
plus per-node class composition (fraction positive).

Biosecurity question: do positive proteins (toxins) cluster in a small number
of Mapper nodes, or spread diffusely across the manifold? If concentrated,
targeted panel augmentation from those nodes may rescue the distant cliff.
"""
import numpy as np, json, sys
from pathlib import Path
from collections import defaultdict
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN

# run_cliff lives in ../harnesses/ relative to this file.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harnesses"))
from run_cliff import REPO_ROOT, load_labels, load_embeddings

print("loading t30 embeddings and labels...")
labels, accs = load_labels()
emb = load_embeddings("t30")
print(f"shape {emb.shape}, labels pos={int(labels.sum())}/{len(labels)}")

print("computing lens (PCA -> 2D)...")
pca = PCA(n_components=2, random_state=0)
lens = pca.fit_transform(emb)
print(f"PCA explained variance: {pca.explained_variance_ratio_.sum():.4f}")

# Cover: 10x10 overlapping bins, 30% overlap
n_bins = 10; overlap = 0.30
def bins_1d(x, n, ovl):
    lo, hi = x.min(), x.max()
    step = (hi - lo) / n
    w = step * (1 + ovl)
    edges = [(lo + i*step - w*ovl/2, lo + (i+1)*step + w*ovl/2) for i in range(n)]
    return edges

x_bins = bins_1d(lens[:, 0], n_bins, overlap)
y_bins = bins_1d(lens[:, 1], n_bins, overlap)

nodes = []
for i, (xl, xh) in enumerate(x_bins):
    for j, (yl, yh) in enumerate(y_bins):
        mask = (lens[:, 0] >= xl) & (lens[:, 0] < xh) & (lens[:, 1] >= yl) & (lens[:, 1] < yh)
        if mask.sum() < 5: continue
        sub_emb = emb[mask]
        sub_idx = np.where(mask)[0]
        # Cosine distance via 1 - inner product (L2-normalized)
        cos_dist = 1.0 - sub_emb @ sub_emb.T
        cos_dist = np.clip(cos_dist, 0.0, 2.0)
        np.fill_diagonal(cos_dist, 0.0)
        db = DBSCAN(eps=0.05, min_samples=5, metric='precomputed').fit(cos_dist)
        for cid in set(db.labels_):
            if cid == -1: continue
            cluster_mask = db.labels_ == cid
            members = sub_idx[cluster_mask].tolist()
            pos_count = int(labels[members].sum())
            nodes.append({
                'bin': (i, j), 'cluster': int(cid),
                'n': len(members), 'pos_frac': pos_count / len(members),
                'members': members[:50]  # cap to keep JSON small
            })

print(f"total nodes: {len(nodes)}")
print(f"nodes with pos_frac > 0.5: {sum(1 for n in nodes if n['pos_frac'] > 0.5)}")
print(f"nodes with pos_frac > 0.9: {sum(1 for n in nodes if n['pos_frac'] > 0.9)}")
print(f"nodes all-positive: {sum(1 for n in nodes if n['pos_frac'] == 1.0)}")
print(f"nodes all-negative: {sum(1 for n in nodes if n['pos_frac'] == 0.0)}")

# Node size distribution
sizes = [n['n'] for n in nodes]
print(f"node sizes: min={min(sizes)} median={int(np.median(sizes))} max={max(sizes)}")

# Positive-enriched nodes
pos_nodes = sorted([n for n in nodes if n['pos_frac'] > 0.5], key=lambda x: -x['n'])
print(f"\ntop 10 positive-enriched nodes (by size):")
for n in pos_nodes[:10]:
    print(f"  bin={n['bin']} cluster={n['cluster']} n={n['n']} pos_frac={n['pos_frac']:.3f}")

out_path = REPO_ROOT / "data" / "results_summaries" / "mapper_graph.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, 'w') as f:
    json.dump({
        'n_nodes': len(nodes),
        'pca_explained_var': pca.explained_variance_ratio_.tolist(),
        'lens_method': 'PCA-2',
        'cover': f'{n_bins}x{n_bins} overlap {overlap}',
        'clustering': 'DBSCAN eps=0.05 min_samples=5 cosine',
        'nodes': nodes,
    }, f, indent=1)
print(f"wrote {out_path}")
