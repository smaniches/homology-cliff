# Mapper Augmentation — Robustness Re-run (audit blocker B4)

**Status:** **EXECUTED (v1.5.0, 2026-06-15).** The B4 question is resolved; see
the `## Resolution` section below. Full results are committed in
`data/results_summaries/mapper_augmentation_robustness.json`.

## Question under test

Paper 2's fourth rescue attempt (Mapper-biased panel augmentation) originally
reported a distant-stratum rescue of **+0.0018, 95% CI [−0.027, +0.029]**
(pre-deduplication), with H1 rejected — oversampling the panel from
positive-enriched Mapper nodes does not beat uniform sampling. After the
deduplication fix described in the Resolution section, the committed value is
**−0.0080, 95% CI [−0.035, +0.018]**, H1 still rejected. The committed evidence is
`data/results_summaries/mapper_augmentation_results.json`.

That result was produced from a biased pool built out of Mapper-node member
lists that `code/analyses/run_mapper.py:67` **truncates to 50 entries per node**
(`members[:50]  # cap to keep JSON small`). Audit blocker B4 asks: **is the H1
rejection an artifact of that truncation, or does it hold under full node
membership?**

## Methodological discrepancy: published prose vs. committed code

While preparing this re-run we found that Paper 2 §Attempt 4 and the committed
script describe **different sampling methods**:

- **Paper 2 prose** (`papers/02_three_failed_rescues/paper.tex`, §"Attempt 4"
  and Limitation L3): the biased pool is drawn from *"the top positive-enriched
  Mapper node (1,512 positives available in bin (7,4), pos_frac=0.885)"* — a
  **single node**.
- **Committed script** (`code/analyses/run_mapper_augmentation.py:28–37`):
  positive-enriched nodes (`pos_frac > 0.5`) are sorted and their members are
  **accumulated across many nodes** until the pool reaches 3,000 entries — and
  each node contributes at most 50 members because of the upstream truncation.

These are not the same experiment. The committed `.json` reflects the
multi-node code path, not the single-node prose. Both interpretations are
therefore tested below.

## Method

`code/analyses/run_mapper_augmentation_robustness.py` is **non-destructive**: it
regenerates the Mapper graph *in memory* (replicating `run_mapper.py`'s PCA-2
lens, 10×10 cover at 30% overlap, DBSCAN `eps=0.05 min_samples=5`) and never
overwrites `mapper_graph.json` or `mapper_augmentation_results.json`. It
evaluates three configurations under the identical 10-seed (20260410–20260419)
cosine-kNN comparison (R=1000, k=25, t30, 10,000-resample F1 CI per cell,
5,000-resample rescue CI):

| Config | Cap | Pool construction | Purpose |
|---|---|---|---|
| `truncated_multinode` | 50 | multi-node → 3,000 | reproduces the committed pipeline (self-check) |
| `full_multinode` | none | multi-node → 3,000 | robustness of the committed method to truncation |
| `full_single_node` | none | single node with the most positives | matches Paper 2's prose method |

The `truncated_multinode` arm is a **reproduction check**: its `rescue_mean`
should match `mapper_augmentation_results.json` to ~1e-6 (the pipeline is
deterministic). The harness asserts this and reports drift.

H1 for each arm: biased distant F1 > uniform distant F1 by **≥ +0.02** with a
95% CI excluding zero. This is a **post-hoc robustness check, not a
pre-registration** — the original analysis has no dedicated SHA256-locked
pre-registration file (only Mahalanobis and cascade are locked; see
`run_mapper_augmentation.py` and audit blocker B5).

## How to run

```bash
git lfs pull --include="data/embeddings/embeddings_t30.npy,data/sequences/proteins_25k_sequences.json"
python -m pip install numpy scikit-learn      # if not already present
python code/analyses/run_mapper_augmentation_robustness.py
```

Output: `data/results_summaries/mapper_augmentation_robustness.json` (new file).
Wall time is dominated by the Mapper regeneration (full membership) and 60
kNN evaluations; expect a few minutes of CPU. Re-running is byte-stable.

## Interpretation

- **If both `full_*` arms still reject H1** (rescue near zero, CI spans zero):
  the published Paper 2 conclusion is **robust** to the truncation, and the
  prose can be reconciled to the multi-node method with a one-line correction.
  No scientific claim changes.
- **If a `full_*` arm now supports H1** (rescue ≥ +0.02, CI above zero): the
  published rejection was **truncation-dependent**, and Paper 2's Attempt-4
  conclusion requires revision (text, PDF recompilation, and a new Zenodo
  version). This is a substantive scientific correction, not an editorial one.

Both outcomes are recorded here and in `PROBLEMS.md`. The purpose of the re-run
is to determine empirically whether the rejection holds under full node
membership, independent of the committed result.

## Resolution (2026-06-15, v1.5.0)

The harness was executed with the LFS payload available. Two findings.

1. **Deduplication defect (fixed).** The biased pool concatenated members across
   the 30%-overlapping Mapper cover without deduplication, and
   `rng.choice(replace=False)` removes positions, not values, so the biased arm
   held fewer than 500 unique positives. Fixed with `np.unique` in both
   `run_mapper_augmentation.py` and this harness. The `truncated_multinode` arm
   reproduces the committed result to `<1e-9` before the fix and gives
   **−0.0080** after (95% CI [−0.035, +0.018]; includes zero; H1 rejected).

2. **The truncation is not the limiting factor — a stratification confound is.**
   Under the published *per-arm* stratification, full node membership appears to
   support H1: `full_multinode` rescue **+0.084** (CI [+0.052, +0.114]),
   `full_single_node` **+0.172** (CI [+0.117, +0.228]). This is a
   **stratification artifact**, not a rescue: a cluster-concentrated biased
   panel enlarges its *own* distant stratum (biased/uniform `n_dist` ratio 1.09
   and 1.16 respectively), pushing easier points into a larger "distant" set.
   The harness now also computes a **common-stratification control**
   (`controlled_rescue_*`): both arms scored on the same test points using a
   single distant stratum defined by the uniform panel. Under that control the
   rescue collapses to **≈0** (−0.004 multi-node, −0.006 single-node; the
   truncated arm's controlled rescue is +0.016), every CI spanning zero —
   consistent with the committed truncated result under its own stratification
   (−0.008, H1 also rejected).

**Conclusion — first Interpretation branch above.** The Paper 2 Attempt-4 null
is **robust to full node membership** once the stratification confound is
controlled; the biased panel does not help the same distant queries. The "four
failed rescues" result stands. Both the prose method (`full_single_node`) and
the committed multi-node code (`full_multinode`) reject H1 under the controlled
comparison. No published conclusion changes; this is recorded in `CHANGELOG.md`
(v1.5.0), `PROBLEMS.md` (item 6, resolved), and the Paper 2 erratum.

## Provenance note

This is a follow-up robustness analysis. It does not alter the committed
`.npz`/`.json` evidence base, the SHA256-locked pre-registrations, or the paper
PDFs. See `CHANGELOG.md` (`[v1.5.0]`), `STATUS.md`, and
`.github/RELEASE_AUDIT_v1.4.5.md` (blocker B4) for the surrounding context.
