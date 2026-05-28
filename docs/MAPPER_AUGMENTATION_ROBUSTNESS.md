# Mapper Augmentation — Robustness Re-run (audit blocker B4)

**Status:** harness authored; **not yet executed** (the authoring environment
could not fetch the t30 embeddings via `git lfs pull`). This document states the
question, the method, and how to run it. Results are appended once the harness
runs where the LFS payload is available.

## The question

Paper 2's fourth rescue attempt (Mapper-biased panel augmentation) reports a
distant-stratum rescue of **+0.0018, 95% CI [−0.027, +0.029]**, with H1
rejected — oversampling the panel from positive-enriched Mapper nodes does not
beat uniform sampling. The committed evidence is
`data/results_summaries/mapper_augmentation_results.json`.

That result was produced from a biased pool built out of Mapper-node member
lists that `code/analyses/run_mapper.py:67` **truncates to 50 entries per node**
(`members[:50]  # cap to keep JSON small`). Audit blocker B4 asks: **is the H1
rejection an artifact of that truncation, or does it hold under full node
membership?**

## A second issue: prose vs. code disagree on the method

While preparing this re-run we found that Paper 2 §Attempt 4 and the committed
script describe **different sampling methods**:

- **Paper 2 prose** (`papers/02_three_failed_rescues/paper.tex`, §"Attempt 4"
  and Limitation L3): the biased pool is drawn from *"the top positive-enriched
  Mapper node (1,131 positives available in bin (7,4), pos_frac=0.885)"* — a
  **single node**.
- **Committed script** (`code/analyses/run_mapper_augmentation.py:28–37`):
  positive-enriched nodes (`pos_frac > 0.5`) are sorted and their members are
  **accumulated across many nodes** until the pool reaches 3,000 entries — and
  each node contributes at most 50 members because of the upstream truncation.

These are not the same experiment. The committed `.json` reflects the
multi-node code path, not the single-node prose. Both interpretations are
therefore tested below.

## What the harness does

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

## How to read the result

- **If both `full_*` arms still reject H1** (rescue near zero, CI spans zero):
  the published Paper 2 conclusion is **robust** to the truncation, and the
  prose can be reconciled to the multi-node method with a one-line correction.
  No scientific claim changes.
- **If a `full_*` arm now supports H1** (rescue ≥ +0.02, CI above zero): the
  published rejection was **truncation-dependent**, and Paper 2's Attempt-4
  conclusion needs revision (text + PDF recompile + a new Zenodo version).
  Treat this as a material finding, not a copy-edit.

Either outcome is recorded honestly here and in `PROBLEMS.md`. The point of the
re-run is to find out, not to defend the existing claim.

## Provenance note

This is a follow-up robustness analysis. It does not alter the committed
`.npz`/`.json` evidence base, the SHA256-locked pre-registrations, or the paper
PDFs. See `CHANGELOG.md` (`[Unreleased]`), `STATUS.md`, and
`.github/RELEASE_AUDIT_v1.4.5.md` (blocker B4) for the surrounding context.
