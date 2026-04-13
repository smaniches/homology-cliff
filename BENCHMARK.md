# Homology Cliff Leaderboard

A public benchmark for frozen protein language model retrieval on biosecurity-relevant proteins. This is the leaderboard; to submit, see **How to submit** below.

**Maintainer:** Santiago Maniches, Independent Researcher, TOPOLOGICA LLC.

## The benchmark

**Test set:** 24,885 proteins from UniProt, 28.7% positive prior (see `DATA_CARD.md`).
**Protocol:** cosine k-NN retrieval on L2-normalized frozen embeddings. Panel class-balanced. 10 seeds (20260410–20260419). Stratification by $s_{\max}$ to the panel: close ≥0.95, moderate [0.90, 0.95), distant <0.90. F1 with bootstrap 10,000-resample percentile CI per stratum per cell. Pre-registered seed-variance void rule.

**Primary metric:** **cliff gap** = close-stratum F1 − distant-stratum F1 at $R=1000$, $k=25$, cosine metric. Lower is better (smaller cliff = PLM encodes function better independent of sequence homology).

**Secondary metrics:** distant-stratum F1 (higher better), pooled F1 (higher better), distant-stratum precision at positive prediction (higher better), ECE on distant stratum (lower better).

## Current leaderboard

| rank | PLM | params | cliff gap ↓ | distant F1 ↑ | pooled F1 ↑ | distant ECE ↓ | submitter |
|------|-----|--------|-------------|--------------|-------------|---------------|-----------|
| 1 | ESM-2 t6 | 8M | **+0.585** | 0.297 | 0.873 | — | Maniches 2026 (this repo) |
| 2 | ESM-2 t12 | 35M | +0.710 | 0.173 | 0.881 | — | Maniches 2026 (this repo) |
| 3 | ESM-2 t30 | 150M | +0.745 | 0.120 | 0.848 | 0.294 | Maniches 2026 (this repo) |
| — | ESM-2 t33 | 650M | _pending GPU_ | _pending_ | _pending_ | _pending_ | _open_ |
| — | ProtT5 XL | 3B | _pending GPU_ | _pending_ | _pending_ | _pending_ | _open_ |
| — | SaProt 650M | 650M | _pending GPU_ | _pending_ | _pending_ | _pending_ | _open_ |
| — | ESM-3 open | varies | _not tested_ | _pending_ | _pending_ | _pending_ | _open_ |

**Observation:** within the ESM-2 family, larger models have **larger** cliff gaps, not smaller. The counterintuitive scaling is one of this compendium's findings. External PLMs may or may not follow the same trend; the leaderboard will tell us.

## Rescue leaderboard (at t30 R=1000 k=25)

| rank | method | distant F1 ↑ | pooled F1 ↑ | wins factorial | submitter |
|------|--------|--------------|-------------|----------------|-----------|
| 1 | **Learned linear projection (panel-only triplet-surrogate)** | **0.177** | **0.891** | **18 / 18** | Maniches 2026 |
| 2 | Cosine baseline | 0.120 | 0.848 | — | Maniches 2026 |
| 3 | Fisher-Rao whitening | 0.094 | 0.461 | 0 / 18 | Maniches 2026 (rejected) |
| 4 | Mahalanobis Ledoit-Wolf | 0.087 | 0.435 | 0 / 18 | Maniches 2026 (rejected) |
| 5 | Cosine+Mahalanobis cascade | 0.074 | 0.538 | 0 / 18 | Maniches 2026 (rejected) |
| 6 | Mapper-biased panel augmentation | 0.122 (+0.002) | 0.850 | 0 / 18 | Maniches 2026 (rejected) |

## How to submit

1. Clone this repository. Install dependencies from `pyproject.toml`.
2. Embed the 24,885 test proteins with your PLM. L2-normalize. Save as `data/embeddings/embeddings_<YOUR_PLM>.npy`.
3. Run `python code/harnesses/run_cliff.py --scale <YOUR_PLM> --resume`. This produces 1500 per-cell .npz files in `data/cells/main/`.
4. Run `python code/analyses/v3_aggregate.py`. Your row appears in the output table.
5. Open a pull request with:
   - The .npy file (LFS tracked)
   - The new .npz cells (LFS tracked)
   - A one-paragraph description of your PLM, its parameter count, training data, and pooling method
   - Updated `MANIFEST.sha256.json`
   - Updated `CHANGELOG.md` under `[Unreleased]`

## Rules

- **Frozen embeddings only.** No fine-tuning on the panel or test set. No task-specific supervision during embedding.
- **Mean pooling required** unless the PLM is architecturally incompatible with mean pooling (document this).
- **10 seeds required** (20260410–20260419). Pre-committed seed-variance gate applies.
- **Bootstrap CI required** (10,000 resamples, percentile) per stratum per cell.
- **Pre-registration is NOT required for leaderboard submission** but is strongly encouraged if you propose a new rescue.

## Hall of rejections

We explicitly track rescues that DO NOT work. This is how the field learns. See Paper 2 for four pre-registered rejections. If your submitted method fails to beat the cosine baseline at distant F1, that is still a valid and publishable result; we will list it.
