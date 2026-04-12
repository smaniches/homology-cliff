# PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987)
**Date locked:** April 12, 2026
**Status:** Addendum to PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md (hash
139f60129d4e73dfb13444c360cc80c5b48c217d9bc87b1bf4b48b06515bcc06).
Original pre-reg is not modified. This file is hashed at end and
registered BEFORE run_cliff_fullnull.py is executed.

## Rationale

The original pre-reg (Section "Ablations item 5") specified a shuffled-
reference-panel-labels negative control with the criterion "distant F1
on shuffled labels must be at chance (0.5 +/- bootstrap CI)". Execution
of that control across 3000 cells produced shuffled-label gaps in the
range +0.20 to +0.44, and stratum F1 values well above 0.5, in direct
violation of the stated criterion.

Investigation of run_cliff.py evaluate_cell() shows the implemented
"shuffled-label" control permutes ONLY the panel labels while leaving
test labels at their real values. Because the test set retains its
28.7% positive class prior (7,133 of 24,885) and the stratification
operator by s_max produces strata that are themselves class-imbalanced,
the panel-only shuffle does not eliminate information carried by the
prior and by the geometry.

## Hypothesis

**H1_addendum:** When labels are permuted across the FULL 24,885-protein
pool (panel plus test, single permutation per seed), the close-distant
F1 gap vanishes within seed variance for every (scale, R, k, metric)
cell. If this holds, the original panel-only shuffle is not a valid
null for the homology cliff hypothesis, the cliff claim is defensible,
and the geometric-versus-semantic decomposition
(main_gap = fullnull_gap_small + label_signal_gap_dominant) becomes
the correct framing.

**H0_addendum:** Under full-pool permutation, gaps persist above seed
variance, indicating the stratification operator itself induces an
apparent cliff independent of label signal. In this case the original
cliff claim requires substantial reframing as a geometric property of
the ESM-2 embedding manifold under the s_max stratification, not as a
failure of label prediction.

## Falsification criterion

H1_addendum is supported iff, for every (scale, R, k, metric) cell in
the factorial, the absolute value of the full-null close-distant F1
gap is less than 2 * (seed-std of main close-distant gap). Equivalently,
the full-null gap's 95% bootstrap CI across 10 seeds includes zero.

H0_addendum is retained otherwise.

## Method

### Permutation

Permute the full 24,885-entry labels vector once per seed using NumPy
Generator default_rng(seed + 7_777_777). Offset chosen distinct from
panel-sampling (seed + R) and original panel-shuffle (seed + 999_999)
streams. Fully deterministic and reproducible.

### Stratification

Unchanged from original pre-reg. Stratification is computed on
geometric s_max from real embeddings; it does not see labels at all.

### Classifier

Unchanged. Cosine, Euclidean, Mahalanobis (Ledoit-Wolf), learned k-NN
all operate on the permuted panel labels.

### Cells

Full factorial across scales t6, t12, t30, panel sizes {50, 100, 250,
500, 1000}, k in {1, 3, 5, 10, 25}, metrics {cosine, euclidean,
mahalanobis, learned}, seeds 20260410 through 20260419. Total 3000
cells. t33 excluded pending Kaggle embedding.

### Output

Writes fullnull_{scale}_{R}_{k}_{metric}_{seed}.npz in the existing
results/ directory. Same schema as main cells and negctrl cells. The
"shuffle" field is the string "fullnull" rather than False or True.

## Relation to original pre-reg criterion

The original pre-reg stated distant F1 must be near 0.5 under the null.
Under H1_addendum that prediction becomes testable: we predict close,
moderate, and distant F1 all approach 0.5 under full-pool permutation,
and the gap approaches 0 within seed variance. The existing
panel-only-shuffle data from negctrl_*.npz is retained as a second
control that isolates label-signal-carried-by-panel-labels from
label-signal-carried-by-test-prior.

## Cross-reference

- Original harness: run_cliff.py, SHA256 hash locked in v1 pre-reg.
- Addendum harness: run_cliff_fullnull.py (imports from run_cliff.py;
  does not modify it).
- Launcher: _launch_fullnull_detached.py.

## No selective reporting

All 3000 cells will be reported. Failure of H1_addendum will be
reported as the main finding. Paper framing will follow the data.

Santiago Maniches, TOPOLOGICA LLC. April 12, 2026.
