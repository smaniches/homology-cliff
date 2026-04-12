"""Calibration analysis on main-factorial cells: per-stratum k-NN vote-fraction
reliability. For each test point, its panel-voted probability of positive is
(n_pos_among_k_neighbors) / k. Bin into 10 equal-width bins, compute observed
positive rate per bin per stratum. A well-calibrated classifier: bin mean
predicted == bin observed rate. The adversarial phase 1 finding suggests the
distant stratum is over-confident in POSITIVE predictions (false alarms); this
confirms or refutes at scale."""
import numpy as np, glob, os, re
from collections import defaultdict

# Need to regenerate y_pred + y_true + stratum masks from a single cell.
# Use t30 R=1000 k=25 cosine seed 20260410 as the representative case.
import sys
sys.path.insert(0, r"C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\_experiments\homology_cliff")
from run_cliff import load_labels, load_embeddings, build_panel, compute_smax, stratify
import faiss

labels, accs = load_labels()
emb = load_embeddings("t30")
panel_idx = build_panel(labels, 1000, 20260410)
panel_emb = emb[panel_idx]
panel_labels = labels[panel_idx]
test_mask = np.ones(len(labels), dtype=bool); test_mask[panel_idx] = False
test_emb = emb[test_mask]; test_labels = labels[test_mask]
smax = compute_smax(test_emb, panel_emb)
strata = stratify(smax)

# Cosine k=25 vote fractions
index = faiss.IndexFlatIP(panel_emb.shape[1])
index.add(np.ascontiguousarray(panel_emb, dtype=np.float32))
_, I = index.search(np.ascontiguousarray(test_emb, dtype=np.float32), 25)
vote_frac = (panel_labels[I] == 1).mean(axis=1)  # proportion positive in k=25 neighbors

# Reliability per stratum
bins = np.linspace(0, 1, 11)
print("Reliability (observed P(y=1) given vote_fraction) per stratum, t30 R=1000 k=25 cosine")
print(f"{'bin':<12} {'close':>10} {'moderate':>12} {'distant':>10}  {'n_close':>8} {'n_mod':>8} {'n_dist':>8}")
for i in range(10):
    lo, hi = bins[i], bins[i+1]
    row = f"[{lo:.1f},{hi:.1f})"
    cells = []
    counts = []
    for name, mask in [('close', strata['close']),('moderate',strata['moderate']),('distant',strata['distant'])]:
        b_mask = mask & (vote_frac >= lo) & (vote_frac < hi + (1e-9 if i==9 else 0))
        n = int(b_mask.sum())
        if n == 0:
            cells.append("   -   "); counts.append(0)
        else:
            rate = float(test_labels[b_mask].mean())
            cells.append(f"{rate:.4f}")
            counts.append(n)
    print(f"{row:<12} {cells[0]:>10} {cells[1]:>12} {cells[2]:>10}  {counts[0]:>8d} {counts[1]:>8d} {counts[2]:>8d}")

# Summary: expected calibration error per stratum (ECE)
print("\nExpected Calibration Error per stratum (lower is better):")
for name, mask in [('close',strata['close']),('moderate',strata['moderate']),('distant',strata['distant'])]:
    ece = 0.0; n_total = int(mask.sum())
    for i in range(10):
        lo, hi = bins[i], bins[i+1]
        b_mask = mask & (vote_frac >= lo) & (vote_frac < hi + (1e-9 if i==9 else 0))
        n = int(b_mask.sum())
        if n == 0: continue
        conf = vote_frac[b_mask].mean()
        acc = test_labels[b_mask].mean()
        ece += (n / n_total) * abs(conf - acc)
    print(f"  {name:<10} ECE = {ece:.4f}  (n={n_total})")

# Over-confidence diagnostic: for vote_frac > 0.5 (predicted positive), how often is it correct?
print("\nPositive-prediction precision per stratum (vote_frac >= 0.5):")
for name, mask in [('close',strata['close']),('moderate',strata['moderate']),('distant',strata['distant'])]:
    pred_pos = mask & (vote_frac >= 0.5)
    n_pp = int(pred_pos.sum())
    if n_pp == 0:
        print(f"  {name:<10} no positive predictions")
        continue
    tp = int(test_labels[pred_pos].sum())
    precision = tp/n_pp
    print(f"  {name:<10} predicted_positive_n={n_pp:>6d}  tp={tp:>5d}  precision={precision:.4f}")
