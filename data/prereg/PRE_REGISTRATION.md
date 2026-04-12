# PRE-REGISTRATION: PH Cascade vs Cosine Baseline on ESM-2 Toxin Classification

**Author:** Santiago Maniches (ORCID: 0009-0005-6480-1987)
**Affiliation:** Independent Researcher / TOPOLOGICA LLC
**Date:** 2026-04-07
**Document hash:** computed at end of file
**Status:** LOCKED before any cascade computation

## 1. Purpose

This pre-registration locks the protocol for evaluating a topological similarity
cascade against the cosine k-NN baseline used in the public BlueDot deliverable
("Beyond Sequence Homology: Detecting Toxin Activity in ESM-2 Embedding Space",
Maniches 2026). The goal is to determine whether geometry-aware similarity
recovers signal that the naive cosine metric loses on the strata where
biosecurity matters most.

This document is written and committed BEFORE any cascade code is executed
on the test set. Any deviation from this protocol in the final report must
be flagged explicitly with reason.

## 2. Inputs (frozen, identical to public paper)

- Reference embeddings: `data/reference_embeddings.npy`, shape (100, 320),
  ESM-2 t6_8M mean-pooled (BOS/EOS excluded), L2-normalized.
- Test embeddings: `data/test_embeddings.npy`, shape (870, 320), same model.
- Reference labels: 50 GO:0090729-positive / 50 GO:0090729-negative.
- Test labels: 447 positive / 423 negative.
- Disjointness: verified at acc level by original paper, re-verified in audit.

## 3. Reproduced baseline (locked reference numbers)

The cosine k-NN baseline was independently reproduced from the on-disk
embeddings on 2026-04-07 in this session. All numbers below are bit-for-bit
matches against `experiment1_results.json` from the original tar.

| k  | F1       | Precision | Recall   | Accuracy | TP  | FP  | FN  | TN  |
|----|----------|-----------|----------|----------|-----|-----|-----|-----|
|  1 | 0.875536 | 0.841237  | 0.912752 | 0.866667 | 408 |  77 |  39 | 346 |
|  3 | 0.844345 | 0.845291  | 0.843400 | 0.840230 | 377 |  69 |  70 | 354 |
|  5 | 0.809578 | 0.825581  | 0.794183 | 0.808046 | 355 |  75 |  92 | 348 |
|  7 | 0.810502 | 0.827506  | 0.794183 | 0.809195 | 355 |  74 |  92 | 349 |
|  9 | 0.815909 | 0.829099  | 0.803132 | 0.813793 | 359 |  74 |  88 | 349 |
| 11 | 0.804989 | 0.816092  | 0.794183 | 0.802299 | 355 |  80 |  92 | 343 |
| 15 | 0.786127 | 0.813397  | 0.760626 | 0.787356 | 340 |  78 | 107 | 345 |

Primary baseline: k=1, F1 = 0.875536.

### 3.1 smax stratification at k=1 (cosine to nearest reference)

| Bin              | n   | TP  | FP | FN | TN  | F1       |
|------------------|-----|-----|----|----|-----|----------|
| [0.99, 1.00]     | 125 | 114 |  0 |  0 |  11 | 1.000000 |
| [0.97, 0.99)     | 295 | 183 | 27 | 12 |  73 | 0.903704 |
| [0.95, 0.97)     | 211 |  66 | 25 | 14 | 106 | 0.771930 |
| [0.90, 0.95)     | 157 |  37 | 16 |  9 |  95 | 0.747475 |
| [0.85, 0.90)     |  49 |   4 |  8 |  3 |  34 | 0.421053 |
| [0.80, 0.85)     |  24 |   2 |  1 |  1 |  20 | 0.666667 |
| [0.00, 0.80)     |   9 |   2 |  0 |  0 |   7 | 1.000000 |

Aggregated "Close" (smax >= 0.95): TP=363, FP=52, FN=26, F1=0.903.
Aggregated "Moderate" ([0.85, 0.95)): TP=41, FP=24, FN=12, F1=0.695.
Aggregated "Distant" (< 0.85): TP=4, FP=1, FN=1, F1=0.800.

### 3.2 Permutation test (1000 iterations, reference-label shuffle, seed=42)

Observed F1 = 0.875536.
Null distribution: mean = 0.5042, sd = 0.0583.
z = 6.37 (independent reproduction; original audit reported z = 6.2).
p_empirical = 0.0000.

## 4. Stronger method: PH cascade (locked specification)

The cascade is a three-stage similarity measure that replaces the cosine
inner product. Each stage operates on the same L2-normalized ESM-2
embeddings as the baseline. The cascade selects which stage to apply on
a per-query basis based on local geometric properties, not on labels.

**No label leakage.** Stage selection uses only the test query and the
reference embeddings; it never sees the test label. This is enforced by
construction in the implementation.

### Stage 1: Cosine (Euclidean on the unit sphere)
Inner product on L2-normalized vectors. Identical to the baseline.
Used as the default when local geometry is well-conditioned.

### Stage 2: Spectral distance
Distance computed on the eigenbasis of a graph Laplacian built from the
k-nearest-neighbor graph of the combined reference + query set. The
spectral distance between query q and reference r is the L2 distance of
their projections into the top-d eigenvectors of the normalized Laplacian
L_sym = I - D^(-1/2) W D^(-1/2), where W is the heat-kernel weighted
adjacency. Captures intrinsic manifold structure that ambient cosine
ignores. Used when the local cosine neighborhood is ambiguous.

### Stage 3: Fermat (density-corrected) distance
Approximate Fermat distance via shortest path on the kNN graph with
edge weights w_ij = ||x_i - x_j||^p for p > 1. Down-weights paths that
traverse low-density regions, giving distances that respect the data
density rather than the ambient metric. Used when the local cosine
neighborhood spans a density discontinuity.

### Stage selection rule (intrinsic-dimension gated)
For each query q:
  1. Compute local intrinsic dimension d_int(q) via TwoNN on the 30
     nearest neighbors in cosine.
  2. Compute persistence gap ratio: gap(q) = (s_1 - s_5) / s_1, where
     s_i is the cosine similarity to the i-th nearest reference.
  3. Decision:
     - If d_int(q) <= 4 AND gap(q) >= 0.05: use Stage 1 (cosine).
       (Well-separated, low-dimensional local neighborhood — cosine works.)
     - Elif d_int(q) <= 8: use Stage 2 (spectral).
       (Moderate dimension, structure matters — switch to manifold metric.)
     - Else: use Stage 3 (Fermat).
       (High intrinsic dimension or density discontinuity — cosine fails;
       Fermat is the only stage with stability guarantees in this regime.)

These thresholds (d_int=4, d_int=8, gap=0.05) are LOCKED here before
any cascade run on the test set. They are derived from the reference-only
geometry (Section 5).

### Hyperparameters (LOCKED)
- kNN graph for spectral / Fermat: k_graph = 15.
- Heat-kernel bandwidth for spectral: sigma = median pairwise distance
  in the kNN graph.
- Spectral embedding dimension: d_spec = 32.
- Fermat exponent: p = 2.
- TwoNN local neighborhood size: 30.
- All distances computed in float64; final classification in float32.
- Random seed: 42 (for any tie-breaking; no stochastic component otherwise).

## 5. Geometry calibration (reference-only, no test labels)

Before running the cascade on the test set, the following intrinsic-dimension
and gap statistics will be computed on the reference panel alone. The
thresholds in Section 4 are locked above; this section only verifies that
the chosen thresholds correspond to meaningful regimes in the reference
geometry. If the reference geometry is degenerate (e.g., d_int << 4 for all
points), the report will note that the cascade collapses to Stage 1 and the
result is interpreted accordingly.

Quantities to compute and report:
- TwoNN intrinsic dimension on the full reference panel (n=100).
- TwoNN intrinsic dimension on positives only (n=50).
- TwoNN intrinsic dimension on negatives only (n=50).
- MLE intrinsic dimension (Levina-Bickel) for cross-check.
- Distribution of pairwise cosine similarities (positives, negatives, mixed).
- Distribution of persistence gap (s_1 - s_5)/s_1 over reference held-out
  leave-one-out queries.

These are descriptive statistics. They do not enter the decision rule
in any way that depends on them. The thresholds in Section 4 are LOCKED.

## 6. Evaluation protocol

All metrics computed on the n=870 test set. Evaluation is strictly OOS:
the test set is disjoint from the reference panel by accession.

### Primary endpoint
F1 at k=1 on the **Moderate stratum** (smax in [0.85, 0.95)).
Baseline value: F1 = 0.695 (reproduced).
Pre-registered direction: cascade should improve over baseline.
Magnitude required for "meaningful improvement": Delta F1 >= 0.05 with
bootstrap 95 percent CI excluding zero.

Note: smax bins are computed from the BASELINE cosine similarities, not
from the cascade output. This keeps the stratification anchored to the
public paper's slicing so the comparison is interpretable.

### Secondary endpoints
- F1 at k=1 on the Close stratum (smax >= 0.95). Baseline: 0.903.
- F1 at k=1 on the Distant stratum (smax < 0.85). Baseline: 0.800
  (small n; underpowered).
- Overall F1 at k=1. Baseline: 0.875536.
- Per-protein flip analysis: which test proteins change predicted label
  between baseline and cascade, in which direction, with what stratum.
- Diphtheria toxin (P00588) sim-gap delta. Baseline: -0.0002.
  Cascade target: positive delta.

### Anti-cherry-picking enforcement
The Moderate stratum is the primary endpoint. If the cascade improves
the Close stratum but not the Moderate stratum, the report will state
that the primary endpoint was not met. There is no post-hoc reweighting.

## 7. Ablation matrix (LOCKED)

### Tier 1: Leave-one-out component contribution
Run the full cascade and seven systematic ablations:
1. Baseline cosine (Stage 1 only).
2. Spectral only (Stage 2 forced for all queries).
3. Fermat only (Stage 3 forced for all queries).
4. Cascade with Stage 1 + Stage 2 only (Stage 3 disabled).
5. Cascade with Stage 1 + Stage 3 only (Stage 2 disabled).
6. Cascade with Stage 2 + Stage 3 only (Stage 1 disabled).
7. Full cascade (all three stages with gating rule).

For each ablation report: overall F1, F1 per stratum, flip count vs baseline.

### Tier 2: Inferential validation
- Permutation test (1000 perms, ref-label shuffle, seed=42) on full
  cascade overall F1. Report null distribution, z, p_empirical.
- Bootstrap 95 percent CI on cascade overall F1 and on Moderate-stratum
  F1 (1000 resamples of test set with replacement, stratified by label).
  Report mean, 2.5 percentile, 97.5 percentile.
- Knockoff negative control: replace the cascade similarity with a
  random orthogonal rotation of the cosine similarity (preserves marginal
  but destroys local structure). Run the same cascade pipeline. Report
  F1. Expected: indistinguishable from baseline. Any improvement here
  indicates the gain is not from "any non-cosine thing" but from
  structure-preserving geometry.

### Tier 3: Shapley decomposition over the three stages
Shapley value of each stage on overall F1 and on Moderate-stratum F1,
computed by enumeration over the 2^3 = 8 stage subsets. The seven
ablations in Tier 1 cover all subsets except the empty set; F1 of the
empty set is 0.5 by majority class (or undefined; report as 0).

## 8. Verification gate (per Santiago verification gate)

Before reporting any number from the cascade run:

1. Interpolator check: no stage uses k=1 nearest neighbor with zero
   smoothing as a regression target. Classification at k=1 is allowed
   (the baseline does this) but no stage fits a kernel regression with
   bandwidth zero.
2. Correction audit: no stage is fit on data that includes the test
   point. The reference panel is the only training input. The cascade
   gating uses query-local geometry but does not use the query label.
3. Derivative inheritance: any reported delta (cascade F1 minus baseline
   F1) is on the same test indices, same stratification, same evaluation
   harness. Bootstrap CIs are paired (resample test indices once and
   recompute both metrics on the resample).
4. Provenance: every reported number carries its method label. The
   permutation test uses RNG seed 42; the bootstrap uses RNG seed 43.

## 9. Success / failure criteria

**Pre-registered success:** Full cascade improves overall F1 by at least
0.02 AND improves Moderate-stratum F1 by at least 0.05, with bootstrap
95 percent CI on the Moderate delta excluding zero, AND knockoff control
shows no comparable improvement.

**Pre-registered partial success:** Improvement on Moderate stratum >= 0.05
but overall F1 unchanged or improved by less than 0.02. Report as "cascade
recovers signal in the regime where cosine fails, at no cost to the regime
where cosine succeeds."

**Pre-registered failure:** No improvement on Moderate stratum. The report
will state that the cascade does not generalize to this dataset and the
public paper's conclusion (cosine ESM-2 has a fundamental ceiling on this
task) is reinforced.

## 10. Reporting and IP discipline

The output of this protocol is two documents:

**Public revision** of the BlueDot deliverable. Identical to the original
paper except for: (a) corrected smax-stratum aggregation explanation
(Close = smax >= 0.95, not >= 0.97), (b) corrected permutation test z =
6.37 with seed=42 reproduction note, (c) clarification that Ricin/Abrin/
Hen lysozyme sim-gap analysis is from experiment0 not experiment1. No new
methods. No mention of cascade.

**Private deliverable** ("BEYOND COSINE", internal codename). Contains
the cascade specification, the result table, the ablation matrix, the
stratified analysis, and the per-protein flip analysis. Written for 1:1
sharing with BlueDot contacts under appropriate scope. Does NOT name
TOPOLOGICA LLC. Does NOT name "drift tensor". Does NOT name any
patent-pending construction. Refers to the method as "intrinsic-dimension-
gated topological similarity cascade" — language already in the public
literature on metric selection for high-dimensional embedding spaces
(Damrich NeurIPS 2024 etc.).

The cascade implementation file (cascade.py) is local-only. It is not
included in the private deliverable's reproducibility package. The private
deliverable's reproducibility package includes: data, baseline code,
result tables, ablation tables. A reader can verify the result tables
trace from the locked baseline; they cannot reproduce the cascade itself
without access to the source.

## 11. Document hash and timestamp

This file is hashed at completion and the hash is recorded in the state
document. Any modification after the cascade run is logged with reason.

Timestamp: 2026-04-07
Author: Santiago Maniches (ORCID: 0009-0005-6480-1987)
