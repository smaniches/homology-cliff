"""Cross-family Pfam partition of distant-stratum failures.

For each distant-stratum false-positive (predicted 1, actually 0) at t30 R=1000
k=25 cosine seed 20260410, check whether the top-25 NN panel members share any
Pfam identifier with the query. Partition into:
  WITHIN_FAMILY  : at least one shared Pfam ID with a voting neighbor
  CROSS_FAMILY   : zero shared Pfam IDs

This distinguishes correctable (panel-expansion) failures from uncorrectable
(novel-mechanism) failures. Pre-reg hash locked before running.
"""
import json, numpy as np, sys, faiss
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
EMB = REPO / "data" / "embeddings" / "embeddings_t30.npy"
PFAM = REPO / "data" / "annotations" / "proteins_25k_pfam.json"
SEQS = REPO / "data" / "sequences" / "proteins_25k_sequences.json"
OUT = REPO / "data" / "results_summaries" / "cross_family_partition.json"

with open(SEQS) as f: seqs_doc = json.load(f)
with open(PFAM) as f: pfam_doc = json.load(f)
entries = seqs_doc['test_set']
pfam_by_acc = {e['uniprot_acc']: set(e.get('pfam_ids', [])) for e in pfam_doc['test_set']}
labels = np.array([e['true_label'] for e in entries], dtype=np.int64)
accs = [e['uniprot_acc'] for e in entries]
emb = np.load(EMB)
emb /= (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8)
print(f"N={len(entries)}  pfam_coverage={sum(1 for a in accs if pfam_by_acc.get(a))}/{len(accs)}")

R, k, seed = 1000, 25, 20260410
rng = np.random.default_rng(seed + R)
pos_idx = np.where(labels == 1)[0]; neg_idx = np.where(labels == 0)[0]
panel = np.concatenate([rng.choice(pos_idx, R//2, replace=False), rng.choice(neg_idx, R//2, replace=False)])
panel_labels = labels[panel]
test_mask = np.ones(len(labels), dtype=bool); test_mask[panel] = False
test_idx = np.where(test_mask)[0]
pe = emb[panel]; te = emb[test_idx]

# stratify
idx = faiss.IndexFlatIP(pe.shape[1]); idx.add(pe.astype(np.float32))
sims, _ = idx.search(te.astype(np.float32), 1); smax = sims[:,0]
distant = smax < 0.90
print(f"distant stratum: {int(distant.sum())}")

# kNN and vote
sims_k, nbrs = idx.search(te.astype(np.float32), k)
votes = panel_labels[nbrs]
preds = (votes.sum(1) * 2 >= k).astype(np.int64)
true_labels = labels[test_idx]

# distant false positives: predicted 1, actual 0
fp_mask = distant & (preds == 1) & (true_labels == 0)
tp_mask = distant & (preds == 1) & (true_labels == 1)
print(f"distant FP (false alarms): {int(fp_mask.sum())}")
print(f"distant TP (correct): {int(tp_mask.sum())}")

# Partition
within, cross = 0, 0
detail = []
for ti in np.where(fp_mask)[0]:
    q_acc = accs[test_idx[ti]]
    q_pfam = pfam_by_acc.get(q_acc, set())
    # find positive-voting neighbors (those voting for label 1)
    pos_voters = [panel[nbrs[ti, j]] for j in range(k) if panel_labels[nbrs[ti, j]] == 1]
    nbr_pfams = set()
    for pi in pos_voters:
        nbr_pfams |= pfam_by_acc.get(accs[pi], set())
    shared = q_pfam & nbr_pfams
    if shared: within += 1; status = "WITHIN_FAMILY"
    else: cross += 1; status = "CROSS_FAMILY"
    detail.append({"acc": q_acc, "q_pfam": sorted(q_pfam), "nbr_pfam_union": sorted(nbr_pfams),
                   "shared": sorted(shared), "status": status,
                   "q_pfam_known": bool(q_pfam), "any_nbr_pfam_known": bool(nbr_pfams)})

# Only count when BOTH query and at least one neighbor have Pfam
eval_detail = [d for d in detail if d['q_pfam_known'] and d['any_nbr_pfam_known']]
within_e = sum(1 for d in eval_detail if d['status'] == 'WITHIN_FAMILY')
cross_e = sum(1 for d in eval_detail if d['status'] == 'CROSS_FAMILY')
print(f"\nEvaluable (both q and nbr have Pfam): {len(eval_detail)}/{len(detail)}")
print(f"  WITHIN_FAMILY: {within_e} ({100*within_e/max(1,len(eval_detail)):.1f}%)")
print(f"  CROSS_FAMILY:  {cross_e} ({100*cross_e/max(1,len(eval_detail)):.1f}%)")

with open(OUT, 'w') as f:
    json.dump({"R": R, "k": k, "seed": seed, "scale": "t30",
               "n_distant_FP": int(fp_mask.sum()),
               "n_evaluable": len(eval_detail),
               "within_family": within_e, "cross_family": cross_e,
               "detail": detail}, f, indent=1)
print(f"wrote {OUT}")
