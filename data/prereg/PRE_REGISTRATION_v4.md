# PRE_REGISTRATION_v4.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987)
**Date locked:** April 8, 2026
**Project:** Beyond Cosine — per-query learned metric selector
**Prior art:** PRE_REGISTRATION.md (v1), PRE_REGISTRATION_v2.md (v2)
**Status of v2 at lock time:** Primary endpoint met on n=870 t12 (+0.069 Moderate),
failed at n=24,885 scale-up (+0.022 Moderate, CI [+0.011, +0.033]).
**Status of v3 at lock time:** Post-hoc stratum-distribution T_gap calibration,
failed at same magnitude as v2.
**Status of oracle analysis at lock time:** smax-gated-spectral ceiling at +0.023;
per-query cheating oracle at +0.398; 17× dynamic range available to a learning rule.

## Motivation

The oracle ceiling analysis (Section 8.1 of BEYOND_COSINE.pdf) proved that
no stratum-level gating rule with a single alternative metric can exceed
+0.023 Moderate ΔF1 at n=24,885 on ESM-2 t12_35M embeddings for GO:0090729.
The cheating oracle (per-query best-of-3 with label access) achieves
+0.398 Moderate ΔF1 with 3,707 of 5,231 cosine-wrong queries rescuable
by at least one alternative metric (70.9%). The signal exists at the
per-query level but is not accessible through any single scalar gating
feature. The v4 protocol tests whether a learned per-query classifier
on the similarity vectors themselves can bridge this gap.

## Hypothesis

A supervised classifier trained on per-query similarity features can
select the correct metric (cosine, spectral, or Fermat) at a rate
sufficient to produce Moderate stratum ΔF1 ≥ +0.05 on a held-out test
split at n ≈ 20,000, thereby meeting the pre-registered primary
endpoint that v2 and v3 failed at scale.

## Data source

Fixed. No new data is fetched.
- S1, S2, S3 similarity matrices at `results_25k_t12/S{1,2,3}_*.npy`
  (shape 24,885 × 100, dtype float32)
- smax, gap, d_int at `results_25k_t12/{smax,gap,d_int}.npy`
- test_labels at `results_25k_t12/test_labels.npy`
- ref_labels at `results_25k_t12/ref_labels.npy`
- 24,885 total test proteins, 7,133 positive / 17,752 negative

## Split

Fixed random seed: 20260408.
Stratified by true_label.
- **Train split:** 60% of n=24,885 = 14,931 proteins (4,280 pos / 10,651 neg expected)
- **Validation split:** 20% = 4,977 proteins (used only for early stopping / hyperparameter selection if applicable)
- **Test split:** 20% = 4,977 proteins (locked, used only for final endpoint evaluation)

The train/val/test split is computed BEFORE any classifier fitting,
saved as `results_25k_t12_v4/split_indices.npz`, and hash-locked.

## Features

For each query q, the feature vector φ(q) ∈ ℝ^18 is constructed as:
- `S1_top5[q]` ∈ ℝ^5: top-5 cosine similarities to references (descending, FAISS top-k)
- `S2_top5[q]` ∈ ℝ^5: top-5 spectral similarities (negative distances, descending)
- `S3_top5[q]` ∈ ℝ^5: top-5 Fermat similarities (negative distances, descending)
- `gap[q]` ∈ ℝ: persistence gap (s1 - s5) / s1 from cosine
- `smax[q]` ∈ ℝ: max cosine similarity (=S1_top5[0])
- `d_int[q]` ∈ ℝ: local TwoNN intrinsic dimension

All features are computed from arrays already on disk. No re-embedding,
no re-cascade, no new Dijkstra runs. The feature construction is
deterministic from the cached similarity matrices.

## Labels for the selector

For each query q, the per-query oracle target m*(q) ∈ {1, 2, 3} is defined as:
- If cosine prediction (via k=1 NN on S1) matches true_label[q]: m*(q) = 1
- Else if spectral prediction matches true_label[q]: m*(q) = 2
- Else if Fermat prediction matches true_label[q]: m*(q) = 3
- Else (all three wrong): m*(q) = 1 (default to cosine when unrecoverable)

This is the "per-query best-of-3 with default" labeling used in the
cheating oracle analysis. m*(q) is computed only from the TRAINING SPLIT
labels. Test split labels are not used to construct m*.

## Classifier family

Fixed choice: **Gradient-boosted decision trees** via scikit-learn's
`HistGradientBoostingClassifier`. This is chosen because:
1. It handles the 18-dim feature vector without scaling
2. It is interpretable (feature importances) which matters for a patent-facing deliverable
3. It is deterministic given a fixed random_state
4. It is not a neural network (no GPU, no training instability)

Hyperparameters locked in advance:
- `max_iter=500`
- `max_leaf_nodes=31`
- `learning_rate=0.05`
- `min_samples_leaf=20`
- `l2_regularization=0.1`
- `random_state=20260408`
- `early_stopping=True` with `validation_fraction=0.2` internal split on training data
  (NOTE: this is internal to sklearn and uses training-split queries only; the
  20% validation split reserved outside is separate and untouched during fitting)

## Evaluation procedure

1. Fit selector on train split (14,931 proteins) with m*(q) labels
2. Predict selector on test split (4,977 proteins) to get m̂(q)
3. For each test query, read prediction from cascade using m̂(q):
   - If m̂(q) = 1: use classify(S1[q], ref_labels, k=1)
   - If m̂(q) = 2: use classify(S2[q], ref_labels, k=1)
   - If m̂(q) = 3: use classify(S3[q], ref_labels, k=1)
4. Compute F1 on test split overall and per stratum (Close/Moderate/Distant)
5. Compute baseline cosine F1 on same test split
6. Compute ΔF1 = v4 - baseline on overall and per stratum
7. Stratified paired bootstrap 1000 resamples seed=43 for 95% CIs

## Primary endpoint (locked)

**Moderate stratum ΔF1 ≥ +0.05 AND 95% bootstrap CI excluding zero on positive side**

Same threshold as v2 and v3. Identical statistical test. Only the
classifier input changes.

## Secondary endpoints (descriptive, not gates)

- Overall ΔF1 and 95% CI
- Close ΔF1 and 95% CI
- Distant ΔF1 and 95% CI
- Classifier accuracy on m*(q) on test split
- Confusion matrix of m̂(q) vs m*(q)
- Feature importances (for mechanistic reporting)

## Controls

1. **Always-cosine knockoff:** replace selector output with constant m̂(q) = 1
   → should reproduce baseline exactly
2. **Random-selector knockoff:** draw m̂(q) uniformly from {1, 2, 3}
   → expected Moderate ΔF1 ≈ 0 with wide CI
3. **Oracle upper bound on test split:** compute ΔF1 using true m*(q)
   → absolute ceiling of what any selector on this feature set could achieve
4. **Stratum-level lower bound on test split:** apply Oracle 2 (smax-gated spectral)
   → reproduces the +0.023 ceiling on the test split specifically

## Leakage gates

1. Test split labels are NEVER used to fit the selector or compute m*
2. Validation split labels are NEVER used to fit the selector
3. Feature computation uses ONLY the similarity matrices (no label access)
4. The selector is fit once, predicted once, evaluated once
5. No hyperparameter tuning on the test split
6. If the primary endpoint fails, the result is reported as failure — the
   classifier family, hyperparameters, feature set, and split seed are
   NOT changed and re-run

## Expected outcomes (bounds from oracle analysis)

- **Lower bound (stratum-level ceiling):** Moderate ΔF1 ≈ +0.023
  (any reasonable selector that at least distinguishes Close from NonClose
  should match this, because it reproduces Oracle 2)
- **Upper bound (per-query cheating oracle):** Moderate ΔF1 ≈ +0.398
  (only achievable with label access, bounds what ANY selector on
  these features could possibly do)
- **Pre-registered threshold:** Moderate ΔF1 ≥ +0.05

A selector that captures ~9% of the dynamic range between +0.023 and
+0.398 meets the primary endpoint. A selector that matches the Oracle 2
ceiling (+0.023) fails by the same margin as v2. A selector that
significantly beats +0.023 without reaching +0.05 is a descriptive
positive that falls short of the threshold and will be reported honestly
as such.

## Output artifacts

- `results_25k_t12_v4/split_indices.npz` — train/val/test indices
- `results_25k_t12_v4/features.npy` — 24,885 × 18 feature matrix
- `results_25k_t12_v4/m_star.npy` — per-query oracle targets
- `results_25k_t12_v4/selector.joblib` — fitted classifier
- `results_25k_t12_v4/predictions.npz` — selector predictions and cascade predictions on test split
- `results_25k_t12_v4/summary_v4.json` — all endpoints, CIs, confusion matrices
- `results_25k_t12_v4/feature_importances.json` — mechanistic readout

## Lock

This pre-registration is committed to disk at
`C:\TOPOLOGICA_BIOSECURITY\beyond_sequence_v2\PRE_REGISTRATION_v4.md`
BEFORE any selector fitting. The SHA-256 hash of this file is computed
and saved alongside the file. The hash appears in summary_v4.json as
`prereg_sha256` to prove temporal precedence.

Random seed: 20260408
Split seed: 20260408
Classifier random_state: 20260408
Bootstrap seed: 43
