# Known Problems, Things We Got Wrong, Things Deferred

## Things we got wrong in v0 (caught and corrected before v1.0)

1. **"Mahalanobis reduces the cliff by +0.376" framing** — technically true as a gap number, but misleading about mechanism. Mahalanobis closes the gap by collapsing close-stratum F1 (0.866 down to 0.456 at t30 R=1000 k=25), not by rescuing distant (0.120 down to 0.087, actually worse). Caught by running the pre-registered stratified cascade experiment, which decisively rejected the implied "Mahalanobis is a rescue" hypothesis. Early session drafts used the wrong framing; v1.0 corrects it throughout.

2. **Stratification thresholds quoted from memory** — I described 0.40/0.90 cuts in early session drafts. Source code says 0.95/0.90. Caught by reading `run_cliff.py`. All papers in v1.0 use the correct cuts.

3. **F1 vs accuracy terminology** — early drafts said "accuracy gap" when the npz schema is F1. Caught when the actual schema was inspected.

4. **Panel-only shuffle null failed its own criterion** — we registered "distant F1 at chance (0.5)" but panel-only shuffle preserves the test class prior and cannot achieve that. Caught within session; addendum pre-registration for full-pool permutation was locked BEFORE running the stricter null, not after seeing partial results.

5. **Pfam fetch v1 used accession:X OR accession:Y queries** that returned HTTP 400. Fixed by switching to UniProt ID-mapping API, then again by batch-50 search when the ID-mapping had limited coverage.

6. **Duplicate fullnull process** — launched the detached runner twice by accident, two processes raced on identical filenames. Caught by log timestamp interleaving. No data corruption (deterministic RNG), 15 minutes of redundant CPU only.

## Things not yet verified

1. **t33 (650M) scale** — committed in the pre-registration but requires GPU embedding. Colab notebook provided; user must execute.
2. **Per-paper TikZ figures** — Paper 1 has 3 tables but no figures yet. Deferred to v1.1.
3. **Stratification threshold sensitivity sweep** — pre-registered but not yet run.
4. **Adversarial phase 2** — only 3 target proteins exist (precision-not-recall finding); BLOSUM-edit attack needs GPU for ESM re-embedding. Kaggle notebook provided.
5. **Learned-projection calibration** — main factorial measured F1 only; calibration of the learned metric on distant stratum is unmeasured.
6. **Cross-family (Pfam-partitioned) analysis** — Pfam annotations now cover most of 24,885 accessions via v3 fetch; partition analysis pending.

## Things deferred to v1.1+

- TikZ figures for all five papers
- Full 300-group fullnull table as LaTeX supplementary appendix (currently in `data/results_summaries/v3_final.txt`)
- Zenodo deposit with DOI
- Adversarial phase 2 BLOSUM-edit results
- PLM benchmark (ProtT5, SaProt, ESM-3) via Colab
- Stronger learned-metric baselines (proper triplet loss, margin-based contrastive, prototype networks)

## Honest epistemic statement

This compendium has six pre-registered experiments, four SHA256-locked pre-registrations, 9,360 per-cell bootstrap-CI results, five compiled papers, and one decisively-confirmed main claim (the cliff is real, is not a stratification artifact, and is rescuable by a 5-second supervised projection). It also has five null results properly owned, three factual corrections to early session prose, and documented deferrals. It is not perfect. It is, I believe, honest.
