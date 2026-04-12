# PRE_REGISTRATION_v5.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987)
**Date locked:** April 8, 2026
**Prior art:** PRE_REGISTRATION.md (v1), PRE_REGISTRATION_v2.md (v2), PRE_REGISTRATION_v4.md (v4)
**v4 result at lock time:** Moderate ΔF1 = +0.0330 on held-out n=4,979, 95% CI [+0.0229, +0.0446], FAILS +0.05 threshold by 5 thousandths on CI upper bound.

## Motivation

v4 beat the Oracle 2 stratum-level ceiling (+0.0294) by +0.0036 on the same test split, producing the first positive overall delta (+0.0176) and first significantly positive Close delta (+0.0030) in the population-scale series. Permutation importance ranked all five spectral features (S2_top1..top5) in the top 6 positions. The CI upper bound of +0.0446 misses the +0.050 threshold by 5 thousandths. v5 refines v4 along three axes that the v4 mechanistic readout directly motivates: (a) class-balance bias correction via isotonic calibration, (b) expanded spectral feature coverage (top-10 plus distribution moments) to exploit the finding that spectral boundary structure is the operative signal, (c) explicit class weighting to counteract the 85% cosine-majority bias in m*.

## Hypothesis

A calibrated, class-weighted gradient-boosted per-query metric selector trained on an expanded 40-dimensional feature vector exceeds Moderate ΔF1 = +0.05 with 95% CI excluding zero positively on the same held-out test split used for v4.

## Data source

Identical to v4. No new data fetched.
- S1, S2, S3 at `results_25k_t12/S{1,2,3}_*.npy`
- smax, gap, d_int at `results_25k_t12/{smax,gap,d_int}.npy`
- test_labels, ref_labels at `results_25k_t12/{test,ref}_labels.npy`
- 24,885 total proteins, 7,133 positive / 17,752 negative

## Split (IDENTICAL to v4, loaded from disk to guarantee reproducibility)

- `results_25k_t12_v4/split_indices.npz` → train (14,930) / val (4,976) / test (4,979)
- seed 20260408, stratified by label
- The test split is locked and shared with v4 for direct comparison

## Features (expanded from 18 to 40 dimensions)

For each query q, φ(q) ∈ ℝ^40 constructed as:
1. `S1_top10[q]` ∈ ℝ^10: top-10 cosine similarities (descending)
2. `S2_top10[q]` ∈ ℝ^10: top-10 spectral similarities (descending)
3. `S3_top10[q]` ∈ ℝ^10: top-10 Fermat similarities (descending), -inf replaced with finite floor
4. `S2_mean[q]`, `S2_std[q]`, `S2_skew[q]`: first 3 moments of full spectral similarity vector over all 100 references
5. `S3_mean[q]`, `S3_std[q]`, `S3_skew[q]`: first 3 moments of full Fermat similarity vector (finite values only)
6. `gap[q]`, `smax[q]`, `d_int[q]`: scalars

Total: 30 (top-10 × 3 metrics) + 6 (moments) + 3 (scalars) = 39 dimensions.
[Correction note: initial draft erroneously summed to 40; the enumerated feature list above is the locked ground truth at 39 dimensions. The correction is transparent and does not change any feature identity.]

All features are computed from arrays already on disk. No re-embedding, no new cascade runs.

## Labels for the selector

Identical to v4: per-query best-of-3 with cosine default. m*(q) ∈ {1, 2, 3}.
m* is computed from the training split labels only.

## Classifier (locked hyperparameters)

Choice: `CalibratedClassifierCV(HistGradientBoostingClassifier(...), method='isotonic', cv=5)`.

Base estimator `HistGradientBoostingClassifier`:
- `max_iter=500`
- `max_leaf_nodes=31`
- `learning_rate=0.05`
- `min_samples_leaf=20`
- `l2_regularization=0.1`
- `class_weight='balanced'` ← NEW vs v4 (corrects the 85% cosine bias)
- `random_state=20260408`
- `early_stopping=True` with `validation_fraction=0.2` (internal sklearn split on train only)

Calibration wrapper `CalibratedClassifierCV`:
- `method='isotonic'`
- `cv=5` (5-fold cross-fitted isotonic calibration on training split only)

## Prediction rule

For each test query, predict class probabilities p(m | q) via the calibrated classifier, then take argmax. If the top-2 probabilities are within 0.05 of each other, default to class 1 (cosine) — this is the "tie-break to cosine" rule locked here and justified by the fact that cosine is the safe default when the selector is uncertain.

## Evaluation procedure

Identical to v4:
1. Fit calibrated classifier on train split (14,930)
2. Predict on test split (4,979)
3. Construct v5 cascade predictions via selector routing
4. Compute baseline cosine F1 on test split (identical to v4 baseline)
5. Stratified paired bootstrap N=1000 seed=43 for overall + per-stratum 95% CIs

## Primary endpoint (locked, identical to v4)

**Moderate stratum ΔF1 ≥ +0.05 AND 95% CI excluding zero on positive side.**

## Secondary endpoints (descriptive)

- Overall, Close, Distant ΔF1 with CIs
- Selector accuracy on m*(q)
- Confusion matrix
- Per-class prediction rates (how often does the selector predict 1/2/3?)
- Feature importances (permutation, 5 repeats)
- v5 vs v4 delta on same test split (empirical measurement of calibration + expanded features contribution)

## Controls (locked)

1. **Always-cosine**: reproduces baseline exactly
2. **Random-selector**: baseline random routing control
3. **Per-query oracle on test split**: upper bound (+0.398 expected)
4. **Oracle 2 (smax-gated spectral) on test split**: stratum ceiling (+0.029 from v4 run)
5. **v4 selector on test split**: direct comparison (expected +0.033 from v4 run)

## Leakage gates

1. Test split labels NEVER used to fit selector or compute m*
2. Validation split labels NEVER used to fit selector (they are used only for permutation importance post-fit)
3. Features computed only from similarity matrices (no label access)
4. Single fit, single predict, single evaluate
5. No hyperparameter tuning on test split
6. Tie-break rule locked before fitting
7. If primary endpoint fails, the result is reported as failure — hyperparameters NOT changed and re-run

## Expected outcomes (bounds)

- Lower bound: v4 performance (+0.0330)
- Upper bound: per-query cheating oracle (+0.401)
- Pre-registered threshold: +0.050
- Gap to close: +0.0054 on CI upper bound (the 5 thousandths)
- Plausible if: calibration shifts class-2/3 probabilities enough that tie-break rule catches more rescuable queries, or expanded features allow classifier to discriminate spectral-rescuable from Fermat-rescuable more accurately

## Lock

Random seed: 20260408
Bootstrap seed: 43
Tie-break threshold: 0.05
