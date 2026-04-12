# PRE-REGISTRATION v2: Cosine→Fermat Gap-Gated Cascade

**Author:** Santiago Maniches (ORCID: 0009-0005-6480-1987)
**Affiliation:** Independent Researcher / TOPOLOGICA LLC
**Date:** 2026-04-07
**Status:** LOCKED before any v2 cascade computation
**Predecessor:** PRE_REGISTRATION.md (v1, SHA256 7d99a0254da5b9c4484c3c0d60475c18fb55acb14629973f7be946fdf95f7036)

## 1. v1 outcome that motivates v2

The locked v1 cascade (Cosine / Spectral / Fermat with intrinsic-dimension
gating) failed both the primary and secondary endpoints in PRE_REGISTRATION
v1 Section 9. Quantitative summary, fully documented in `results/`:

- Overall F1 delta: -0.0204, paired bootstrap 95% CI [-0.0378, -0.0051],
  CI excludes zero on the negative side. v1 cascade is significantly *worse*
  than baseline overall.
- Moderate stratum F1 delta: -0.0007, 95% CI [-0.0708, +0.0662], CI
  straddles zero. v1 cascade is statistically indistinguishable from
  baseline on the primary endpoint stratum.
- Permutation test (1000 perms, ref-label shuffle, seed=42):
  cascade overall z=6.985, Moderate z=4.664. Cascade carries signal,
  just less than baseline.
- Knockoff control (random orthogonal rotation): overall F1 0.657,
  Moderate F1 0.349. Pipeline structurally sound; v1 failure is due
  to the gating rule, not the cascade machinery.

### v1 ablation findings (Tier 1, 7 cells)

- Cell 3 (Fermat alone): overall F1 0.874735 — **statistical tie with cosine**.
  Identical Close (0.9032 vs 0.9030). +0.109 absolute on Distant (0.909 vs 0.800).
- Cell 2 (Spectral alone): F1 0.846 — uniformly worse on every stratum.
  Destroys Distant (0.526 vs 0.800).
- Cell 6 (Spectral+Fermat, no Stage 1): the only cell beating cosine on
  Moderate (+0.0100), but worse overall.

### v1 Shapley decomposition (Tier 3)

| Stage | Overall φ | Moderate φ |
|---|---|---|
| Cosine | 0.2930 | 0.2320 |
| Spectral | **0.2681** (lowest) | **0.2261** (lowest) |
| Fermat | **0.2939** (highest) | **0.2361** (highest) |

## 2. Diagnostic conclusions (data-grounded)

1. **Spectral with d=32 on n=100 references is structurally underpowered.**
   The graph Laplacian eigenbasis is unstable at this sample/dimension ratio.
   Spectral is dropped from v2.

2. **Fermat on the Euclidean kNN graph (p=2) is a valid metric on this manifold.**
   It ties cosine globally, ties cosine on Close, ties cosine on Moderate
   (within noise), and beats cosine on Distant by a meaningful margin
   (n=33, underpowered for significance but striking direction).

3. **Intrinsic dimension is the wrong gating axis.** ESM-2 t6_8M on the
   toxin manifold has global d_int ~ 9, so the locked thresholds (4 / 8)
   route 614/631 Close-stratum queries away from cosine, where cosine
   is in fact strong. The damage is concentrated on the Close stratum,
   not the Moderate stratum.

4. **Persistence gap (cosine top-1 confidence) is the right gating axis.**
   It is the natural measure of "where cosine is uncertain" — exactly the
   regime where an alternative metric has room to help. Gate on the
   actual axis of cosine's failure mode, not on a proxy.

## 3. v2 architecture (LOCKED)

Two stages. No spectral.

### Stage 1: Cosine (default)
Identical to baseline. FAISS IndexFlatIP on L2-normalized ESM-2 t6_8M
embeddings. k=1, strict majority, ties to negative.

### Stage 2: Fermat
Approximate Fermat distance via shortest path on the joint kNN graph
(reference + test) with edge weights ||x_i - x_j||^p, p=2. Computed by
Dijkstra FROM the n_ref reference points, exploiting D_F symmetry.
Hyperparameters identical to v1 Stage 3:
  k_graph = 15
  fermat_p = 2.0
  edge weights = Euclidean distance on the unit sphere

### Gating: persistence gap
For each test query q, compute:
  s_1(q) = top-1 cosine similarity to any reference
  s_5(q) = top-5 cosine similarity to any reference
  gap(q) = (s_1(q) - s_5(q)) / s_1(q)

Decision rule:
  if gap(q) >= T_gap: use Stage 1 (cosine)
  else:               use Stage 2 (Fermat)

T_gap is calibrated by leave-one-reference-out (LORO) on the reference
panel BEFORE any test set evaluation. Procedure in Section 4.

## 4. T_gap calibration procedure (LORO, no test leakage)

For each i in 0..99:
  - Remove reference[i] from the reference panel.
  - Treat reference[i] as a test query against the remaining 99 references.
  - Compute its top-1 cosine similarity s_1, top-5 cosine s_5, gap.
  - Predict its label by 1-NN over the 99 remaining references.
  - Record (gap_i, correct_i, true_label_i, predicted_label_i).

After all 100 LORO trials:
  - Sort the (gap, correct) pairs by gap descending.
  - For each candidate threshold T in {0.001, 0.002, ..., 0.20}:
    - Compute LORO accuracy on subset {gap >= T}: this is "where cosine is
      confident". Higher is better.
    - Compute LORO accuracy on subset {gap < T}: this is "where cosine is
      uncertain". This is where Fermat will be used.
  - Select T* as the smallest T such that LORO accuracy on {gap >= T}
    is at least 0.95. This is the "cosine is sufficiently confident" zone.
  - If no T satisfies this, fall back to T* = median(gap) over LORO trials.

T_gap is computed and committed to the protocol BEFORE the test set is
touched. The chosen T_gap value is recorded in the calibration output JSON.

The calibration uses ONLY the 100 reference embeddings and their 100
labels. It does not touch the 870 test embeddings or labels in any way.
Verified by code review against the calibration script.

## 5. Locked baseline (frozen from v1 reproduction)

| metric              | value      |
|---------------------|------------|
| overall F1 (k=1)    | 0.875536   |
| Close F1            | 0.902985   |
| Moderate F1         | 0.694915   |
| Distant F1          | 0.800000   |
| TP / FP / FN / TN   | 408 / 77 / 39 / 346 |

These numbers are the immutable comparator. Any v2 result is a delta
against these.

## 6. Primary endpoint (LOCKED, identical to v1)

F1 at k=1 on the **Moderate stratum** (smax in [0.85, 0.95) by baseline cosine).
Baseline value: 0.694915.

**v2 success** requires:
  Delta F1 >= +0.05 on Moderate
  AND paired bootstrap 95% CI on Moderate delta excludes zero on the positive side.

## 7. Secondary endpoints (LOCKED)

- Overall F1 at k=1: must not be significantly worse than baseline.
  Bootstrap 95% CI on overall delta must not exclude zero on the
  negative side. Improvement of any magnitude is positive but not required.
- Close F1: same constraint (must not significantly degrade).
- Distant F1: directional check only (n=33 underpowered).
- Per-protein flip analysis on each stratum.
- Stage assignment distribution: how many queries route to Fermat under
  the calibrated T_gap.

## 8. Pre-registered failure modes

v2 will be reported as **failed** if:
  - Moderate F1 delta < +0.05
  - OR Moderate bootstrap CI fails to exclude zero on positive side
  - OR overall F1 bootstrap CI excludes zero on negative side

v2 will be reported as **partial success** if:
  - Moderate F1 delta in [+0.02, +0.05) with positive CI
  - AND no significant overall degradation

v2 will be reported as **success** if:
  - Moderate F1 delta >= +0.05 with positive CI
  - AND no significant overall degradation
  - AND knockoff control shows the gain is real

## 9. Verification gate (per Santiago verification gate)

1. Interpolator check: no stage uses k=1 nearest neighbor with zero
   smoothing as a regression target. k=1 classification is allowed.
2. Correction audit: T_gap is calibrated on reference panel only. The
   cascade gating uses query-local cosine similarity, never the test label.
3. Derivative inheritance: paired bootstrap CIs on the same test indices.
4. Provenance: every reported number carries its method label and seed.

## 10. Reporting

The v2 results table is added as a section to the private deliverable
("BEYOND COSINE", internal codename). The public revision of the BlueDot
paper does not mention v2 or v1 — only the three error corrections noted
in PRE_REGISTRATION v1 Section 10.

Document timestamp: 2026-04-07
SHA256 (computed at lock time): see hash_v2_prereg.py output
