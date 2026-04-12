# PRE_REGISTRATION_FISHER_CLIFF_v1.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
**Date locked:** April 12, 2026
**Status:** Parallel to v1 cliff pre-reg and to stratified-cascade pre-reg.

## Hypothesis

**H1_fisher:** Fisher-Rao-whitening k-NN (within-class pooled covariance inverse) reduces the close-distant F1 gap beyond Ledoit-Wolf pooled-covariance Mahalanobis at scale t30, panel R=1000, k=25, with 95% bootstrap CI on the reduction excluding zero.

**H0_fisher:** The Fisher-whitened gap is within sampling noise of the Mahalanobis gap.

## Rationale

For two-class Gaussian class-conditional density with shared covariance, the Fisher information matrix on the class-conditional embedding reduces to the within-class pooled covariance inverse. This is geometrically distinct from Ledoit-Wolf pooled-all-points Mahalanobis: pooled covariance captures total variance including between-class shifts; within-class covariance captures only noise around class means.

DR-010 found Fisher embedding hurt GO annotation with Shapley -0.128. That was categorical enrichment with many classes. This is binary classification with stratification; Fisher may behave differently.

## Design

Factorial: scales {t6, t12, t30}, R in {100, 500, 1000}, k in {5, 25}, seeds 20260410..20260419. 180 cells total. Write fisher_{scale}_{R}_{k}_{seed}.npz. Compare against existing Mahalanobis cells at same (scale, R, k, seed).

Shrinkage 0.05 toward diag for numerical stability; this is a hyperparameter locked pre-hoc.

## Falsification

Per-cell reduction = (mahalanobis_gap - fisher_gap) aggregated over 10 seeds. Bootstrap 5000 resamples. H1_fisher supported at scale t30 R=1000 k=25 iff 95% CI of reduction excludes zero AND the mean is positive.

## No selective reporting

All 180 cells reported. If Fisher fails at t30 but wins at t6 or t12, that is reported as-is.
