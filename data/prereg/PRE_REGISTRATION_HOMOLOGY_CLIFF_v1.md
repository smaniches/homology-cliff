# PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987)
**Date locked:** April 10, 2026
**Status:** Pre-registered. Hash computed at end of file. Any edit after hashing voids the registration.
**Relationship to prior work:** PARALLEL to PRE_REGISTRATION_v1 through v6. Those pre-regs evaluate whether a calibrated metric-selector IMPROVES downstream classification. This pre-reg asks a different question: does the underlying embedding space support classification at all on the slice that matters for biosecurity (proteins with no close homolog in the reference panel). Different hypothesis, different seed, independent pipeline.

## Hypothesis

**H1 (alternative):** Frozen ESM-2 embeddings fail on the distant-stratum slice that matters for biosecurity. Specifically, F1 on the distant stratum (smax < 0.90 to any protein in a fixed reference panel) is lower than F1 on the close stratum (smax ≥ 0.95), and the difference exceeds the variance induced by reference-panel composition.

**H0 (null):** Distant-stratum F1 lies within the 95% bootstrap confidence interval of close-stratum F1. There is no cliff; performance is homogeneous across similarity strata within sampling noise.

## Falsification criterion

H1 is supported if and only if the distant-stratum F1 95% bootstrap CI upper bound is below the close-stratum F1 95% bootstrap CI lower bound, AND this gap survives the seed-variance gate (clause below).

H0 is retained otherwise.

## Data source

Fixed to the existing beyond_sequence_v2 25k dataset:
- Proteins: `_data/data_25k/experiment2_proteins_25k_filtered.json` (24,885 proteins, 7,133 positive, 17,752 negative)
- Sequences: `_data/data_25k/experiment2_sequences_25k_filtered.json`
- Existing embeddings: `_embeddings/embeddings_25k_t12/` (ESM-2 t12 layer) and `_embeddings/embeddings_t30/` (ESM-2 t30 layer)

No new UniProt fetch. Real data, no synthetic. Labels inherited from the existing filtered set.

## Reference panel construction (locked BEFORE any evaluation)

Random seed: **20260410** (distinct from v4/v5's 20260408 and v6's 20260409).

For each reference panel size R in {50, 100, 250, 500, 1000}:
1. Sample R/2 positive and R/2 negative proteins uniformly without replacement from the full 24,885 pool using seed 20260410 + R.
2. Save panel indices to `_experiments/homology_cliff/panels/panel_R{R}_seed{seed}.npz` BEFORE any test evaluation.
3. The remaining 24,885 - R proteins form the test pool for that panel size.

For the seed-variance gate, an additional 9 panels per size are constructed with seeds 20260411 through 20260419, total 10 panels per size.

## Stratification

For each (R, panel) pair and each test protein, compute smax = max cosine similarity to any protein in the panel (same embedding space). Assign stratum:
- close: smax ≥ 0.95
- moderate: 0.90 ≤ smax < 0.95
- distant: smax < 0.90

Report stratum population counts per panel. If the distant stratum contains fewer than 100 proteins in any configuration, that cell is flagged as underpowered and excluded from the pooled analysis but still reported individually.

## Classifier

Per stratum, k-nearest-neighbor classification in the embedding space against the reference panel. No learned layer. Majority vote.

## Ablations (ALL reported, no selective reporting)

1. **Model scale:** ESM-2 t6 (8M), t12 (35M, already embedded), t30 (150M, already embedded), t33 (650M). t6 and t33 computed as part of this experiment; t12 and t30 reused from disk.
2. **Reference panel size:** R in {50, 100, 250, 500, 1000} (5 values).
3. **k:** k in {1, 3, 5, 10, 25} (5 values).
4. **Metric:** cosine k-NN, Euclidean k-NN, Mahalanobis with pooled panel covariance, learned metric via contrastive fine-tuning on the training pool only (no test leakage).
5. **Negative control:** shuffled reference-panel labels. Distant-stratum F1 on shuffled labels must be at chance (0.5 +/- bootstrap CI). If it is not, the pipeline has a leak and all results are voided.
6. **Seed-variance gate (v7 lesson enforced):** For each (scale, R, k, metric) cell, compute distant-stratum F1 across 10 reference-panel seeds. Report mean, std, and 95% CI of the std. If the std of distant F1 across panels exceeds the claimed effect size (close-F1 minus distant-F1), the effect is declared reference-panel variance and H1 is NOT considered supported for that cell.

Total cells: 4 scales x 5 R x 5 k x 4 metrics x 10 seeds = 4000 evaluations. Plus 4 x 5 x 5 x 4 = 400 negative-control evaluations on shuffled labels.

## Metrics reported per cell

F1, precision, recall, per stratum (close, moderate, distant), with 10000-sample bootstrap 95% CI.

## Analysis plan

Primary: close vs distant F1 difference, with both bootstrap CI and panel-variance gate applied.

Secondary: does any single axis (scale, R, k, metric) rescue the distant stratum? Reported as heatmaps and marginal plots.

Tertiary: is there an interaction (e.g., large R + large scale closes the cliff) that no single axis captures? Reported as ablation tables.

## Stopping rules

The experiment runs to completion. No early stopping. No peeking at the distant-stratum F1 before all 4000 cells are computed. If any cell fails the shuffled-label negative control, the entire pipeline is voided, the leak is fixed, and the run is restarted with a new seed.

## Decision rules for the paper

- H1 supported across all or most ablation cells: paper is submitted as a strong negative result on frozen PLM embeddings for biosecurity-critical slices.
- H1 supported only under specific conditions: paper is submitted as a bounded positive result with those conditions stated explicitly in the abstract.
- H1 falsified (distant F1 within close F1 CI): paper is submitted as a falsification of the cliff hypothesis, with the explanation of why the March 2026 paper observed the effect (likely small-sample variance in the original 66-protein distant stratum).

## Output artifacts

- `_experiments/homology_cliff/results/` with per-cell .npz results
- `_deliverables/homology_cliff_paper.tex` populated from real results only, no PENDING cells at submission time
- `_deliverables/homology_cliff_figures/` with all heatmaps and marginal plots

## Title

"The Homology Cliff: Why Protein Language Model Embeddings Fail Where Biosecurity Needs Them Most"

Submitted as negative, bounded-positive, or falsification paper depending on the actual result per the decision rules above.

## No em dashes, no fabricated numbers, no cherry-picking

Per delivery and reproduction mandate. Every number in the final paper comes from same-session script execution against real data. Pre-reg hash below locks this document before any cell is computed.

---

**SHA256 hash of this document computed at lock time and stored at PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md.sha256**
