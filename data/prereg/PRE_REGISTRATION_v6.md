# PRE_REGISTRATION_v6.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987)
**Date locked:** April 8, 2026
**Prior art:** v1-v5 pre-registrations, v5 leakage audit
**Motivation for v6 (honest):** The v5 pre-registration locked `CalibratedClassifierCV(method='isotonic', cv=5)` as the calibration wrapper. Post-hoc leakage audit (`pipeline_25k_v5_audit.py`) revealed that the `cv=5` internal splitting pattern on the same training data that the base classifier was also fit on produces inflated test-split metrics. The audit's leakage-proof manual prefit isotonic calibration produced Moderate ΔF1 = +0.0537 (CI [+0.0388, +0.0694]) versus the original v5's +0.2250 — an order-of-magnitude gap. The audit itself was not pre-registered. v6 locks the leakage-proof prefit pattern on a **fresh** test split derived from a new seed, so this is a genuinely unseen evaluation, not a re-run of already-observed results.

## Hypothesis

A gradient-boosted per-query metric selector with manually-held-out prefit isotonic calibration on an independent 20% calibration set and class-weighted training, evaluated on a fresh stratified 60/20/20 split with seed 20260409 (distinct from v4/v5 seed 20260408), achieves Moderate ΔF1 ≥ +0.05 with 95% bootstrap CI excluding zero on the positive side.

## Data source (identical to v4/v5)

- S1, S2, S3 at `results_25k_t12/S{1,2,3}_*.npy`
- smax, gap, d_int at `results_25k_t12/{smax,gap,d_int}.npy`
- test_labels, ref_labels at `results_25k_t12/{test,ref}_labels.npy`
- 24,885 proteins, 7,133 positive / 17,752 negative

## Split (FRESH — different seed from v4/v5)

**Random seed: 20260409** (distinct from v4/v5's 20260408)

Stratified by `test_labels`:
- 60% train → 14,930 proteins
- 20% calibration → 4,977 proteins (used for prefit isotonic calibration only)
- 20% test → 4,978 proteins (locked, evaluation-only)

Note: v6 does NOT use the v4/v5 train/val/test split. A new split is computed with seed 20260409 and saved to disk at `results_25k_t12_v6/split_indices.npz` BEFORE classifier fitting. The v4/v5 test split (under seed 20260408) is not touched by v6 at all.

## Features (identical to v5 — 39-dim)

1. S1_top10 (10)
2. S2_top10 (10)
3. S3_top10 with -inf → finite floor (10)
4. S2 mean, std, skew (3)
5. S3 mean, std, skew over finite entries (3)
6. gap, smax, d_int (3)

Total: 39 dimensions. Identical feature construction to v5.

## Labels for selector

Identical to v4/v5: per-query best-of-3 with cosine default. m*(q) computed from training split labels only.

## Classifier (LEAKAGE-PROOF PREFIT PATTERN)

**Step 1: Fit base classifier on TRAIN split only**

```python
base = HistGradientBoostingClassifier(
    max_iter=500, max_leaf_nodes=31, learning_rate=0.05,
    min_samples_leaf=20, l2_regularization=0.1,
    random_state=20260409, early_stopping=True, validation_fraction=0.2,
)
# class weights computed from train split labels only
cw = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
base.fit(X_train, y_train, sample_weight=train_sample_weights)
```

**Step 2: Manual per-class isotonic calibration on CALIBRATION split**

```python
raw_proba_calib = base.predict_proba(X_calibration)
for ci, cls in enumerate(base.classes_):
    y_cls = (y_calibration == cls).astype(int)
    iso = IsotonicRegression(out_of_bounds='clip', y_min=0.0, y_max=1.0)
    iso.fit(raw_proba_calib[:, ci], y_cls)
    calibrators[cls] = iso
```

**Step 3: At test time, apply calibration + renormalize**

```python
raw = base.predict_proba(X_test)
for ci, cls in enumerate(base.classes_):
    cal[:, ci] = calibrators[cls].predict(raw[:, ci])
cal = cal / cal.sum(axis=1, keepdims=True)
```

The calibration set is never touched by the base classifier. The test set is never touched by either. This is the unambiguous prefit pattern with no sklearn CV internals.

## Prediction rule (tie-break to cosine)

For each test query, take argmax of calibrated probabilities. If the top-2 probabilities differ by less than 0.05, default to class 1 (cosine). Identical rule to v5.

## Primary endpoint (locked, identical to v2/v3/v4/v5)

**Moderate stratum ΔF1 ≥ +0.05 AND 95% bootstrap CI excluding zero on the positive side.**

## Controls

1. Baseline cosine on test split (identical to v4/v5 baselines on this new split)
2. Oracle 2 (smax-gated spectral) on test split — stratum-level ceiling
3. Per-query oracle on test split — label-access upper bound
4. v4/v5 direct comparison NOT possible because test splits differ

## Leakage gates (explicit)

1. Test split labels never used to fit base classifier
2. Test split labels never used to fit calibrators
3. Calibration split never used to fit base classifier
4. Calibration split never used to compute m*
5. Features constructed only from similarity matrices (no label access)
6. Single fit, single predict, single evaluate
7. No hyperparameter tuning on test split
8. If primary endpoint fails, reported as failure — NO re-running with different seeds

## Expected outcomes (from v5 audit)

- The v5 audit on the v4/v5 test split (different seed, different split, but same data pool) produced Moderate ΔF1 = +0.0537
- v6 uses a different split of the same data pool → point estimate likely in [+0.04, +0.07] range
- If point estimate falls below +0.05, the primary endpoint fails
- If point estimate falls above +0.05 AND CI lower bound excludes zero positively, the primary endpoint passes

## Lock

- Split seed: 20260409
- Classifier random_state: 20260409
- Bootstrap seed: 43
- Tie-break threshold: 0.05
- Pre-registration SHA-256 computed and saved to `PRE_REGISTRATION_v6.md.sha256` BEFORE running pipeline_25k_v6.py
- pipeline_25k_v6.py asserts the SHA on load to prove temporal precedence
