# PRE_REGISTRATION_STRATIFIED_CASCADE_v1.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
**Date locked:** April 12, 2026
**Status:** Parallel to PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md. Independent experiment, different hypothesis, different registration.

## Hypothesis

**H1:** Per-stratum metric selection (cosine for close, Mahalanobis for moderate+distant) produces higher pooled-test F1 than any single-metric baseline on the same 24,885-protein beyond_sequence_v2 test set. Specifically, the stratified cascade's pooled F1 exceeds cosine-only pooled F1 and Mahalanobis-only pooled F1 by at least +0.02 with 95% bootstrap CI excluding zero.

**H0:** The stratified cascade performs within sampling noise of the better single-metric baseline.

## Design

For each seed s in {20260410..20260419}, each R in {100, 500, 1000}:
1. Sample class-balanced panel (same panel RNG as v1 pre-reg: seed + R).
2. Compute smax per test protein using cosine similarity against panel.
3. Stratify by locked thresholds: close >= 0.95, moderate [0.90, 0.95), distant < 0.90.
4. Compute three single-metric F1s pooled across strata: cosine-only, mahalanobis-only, learned-only.
5. Compute stratified-cascade F1: close predictions from cosine, moderate+distant from mahalanobis.
6. Record pooled F1 + per-stratum F1 + bootstrap CI per cell.

k values: {5, 25}. Metrics: cosine, mahalanobis, and cascade. Ten seeds. Three R values. 60 cells per scale × 3 scales = 180 cells.

## Gating

Pre-registered test: cascade_pooled_F1 minus max(cos_pooled_F1, mah_pooled_F1) > +0.02 with 95% CI excluding zero (5000-resample bootstrap across 10 seeds).

## Deliverable

Companion paper to v3 homology cliff, ~6-8 pages. If H1 supported, the result is directly operationalizable in biosecurity retrieval pipelines.

## Hash

SHA256 locked at end of file by _hash_cascade.py before execution.
