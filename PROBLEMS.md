# Known Problems, Things We Got Wrong, Things Deferred

## Things we got wrong in v0 (caught and corrected before v1.0)

1. **"Mahalanobis reduces the cliff by +0.376" framing** — technically true as a gap number, but misleading about mechanism. Mahalanobis closes the gap by collapsing close-stratum F1 (0.866 down to 0.456 at t30 R=1000 k=25), not by rescuing distant (0.120 down to 0.087, actually worse). Caught by running the pre-registered stratified cascade experiment, which decisively rejected the implied "Mahalanobis is a rescue" hypothesis. Early session drafts used the wrong framing; v1.0 corrects it throughout.

2. **Stratification thresholds quoted from memory** — I described 0.40/0.90 cuts in early session drafts. Source code says 0.95/0.90. Caught by reading `run_cliff.py`. All papers in v1.0 use the correct cuts.

3. **F1 vs accuracy terminology** — early drafts said "accuracy gap" when the npz schema is F1. Caught when the actual schema was inspected.

4. **Panel-only shuffle null failed its own criterion** — we registered "distant F1 at chance (0.5)" but panel-only shuffle preserves the test class prior and cannot achieve that. Caught within session; addendum pre-registration for full-pool permutation was locked BEFORE running the stricter null, not after seeing partial results.

5. **Pfam fetch v1 used accession:X OR accession:Y queries** that returned HTTP 400. Fixed by switching to UniProt ID-mapping API, then again by batch-50 search when the ID-mapping had limited coverage.

6. **Duplicate fullnull process** — launched the detached runner twice by accident, two processes raced on identical filenames. Caught by log timestamp interleaving. No data corruption (deterministic RNG), 15 minutes of redundant CPU only.

7. **TikZ figures for all five papers** — COMPLETED in v1.3.1. Initially deferred when papers were drafted with tables only; figures were added across Papers 1-5 in v1.3.1.

8. **Hardcoded Windows paths in 11 analysis/harness scripts** — caught in the pre-public deep-audit pass and fixed in v1.4.4. Scripts (`run_cliff.py`, `run_cliff_fullnull.py`, `run_cascade.py`, `run_fisher.py`, `run_calibration.py`, `run_adversarial_phase1.py`, `run_mapper.py`, `run_mapper_augmentation.py`, `fetch_pfam_v3.py`, plus the Kaggle and Colab notebooks) now resolve everything via `Path(__file__).resolve().parents[N]` (overridable with `HOMOLOGY_CLIFF_REPO_ROOT` env var) and accept both the shipped data filename and the pre-reg-locked working ID. Previous releases (v1.4.0-v1.4.3) shipped harnesses that only ran on the original Windows workstation. The cells, papers, and headline numbers were not affected; only the ability of a fresh clone to re-run the experiments. Apologies; this should have been caught earlier.

9. **Calibration script - figure binning mismatch** — caught in the same audit pass and fixed in v1.4.4. The earlier `run_calibration.py` used 10 equal-width bins via `np.linspace(0,1,11)`, but Paper 3's published figure uses six unequal-width bins ($\{0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0\}$). The script now uses the figure's binning, computes ECE on that binning, and writes `data/results_summaries/calibration_results.json`. Paper 3's headline values (ECE 0.069 close, 0.294 distant; 3/44 distant pos-pred precision; 4.3x ratio) now exist as a committed JSON artifact rather than only in paper text.

10. **Overclaim softening across Papers 1, 2, 3, 5** — caught in the same audit pass and fixed in v1.4.4. Phrases like "ruling out within-family distant-homology as the mechanism", "Panel expansion is not a rescue", "rules out the within-family hypothesis entirely", and "panel augmentation is ruled out" overstated the evidence given the n=20 evaluable sample size (Wilson 95\% CI lower bound on the population within-family rate is approximately 83\%, not 100\%). Replaced with consistent "consistent with / inconsistent with / disfavors / Wilson 95\% CI [0\%, 17\%]" framing throughout. The empirical observation (20 of 20 evaluable cases cross-family) is unchanged; only the inferential strength is calibrated.

## Things not yet verified

1. **t33 (650M) scale** — committed in the pre-registration but requires GPU embedding. Colab notebook provided; user must execute.
2. **Stratification threshold sensitivity sweep** — pre-registered but not yet run.
3. **Adversarial phase 2** — only 3 target proteins exist (precision-not-recall finding); BLOSUM-edit attack needs GPU for ESM re-embedding. Kaggle notebook provided.
4. **Learned-projection calibration** — main factorial measured F1 only; calibration of the learned metric on distant stratum is unmeasured.
5. ~~Cross-family (Pfam-partitioned) analysis~~ — COMPLETED v1.0.1. Result: 100% of evaluable distant false alarms are cross-family (zero Pfam overlap with voters). Paper 5 updated from v0.9 stub to full v1.0 with this result.

## Things deferred to v1.1+

- Full 300-group fullnull table as LaTeX supplementary appendix (currently in `data/results_summaries/v3_final.txt`)
- Zenodo deposit with DOI
- Adversarial phase 2 BLOSUM-edit results
- PLM benchmark (ProtT5, SaProt, ESM-3) via Colab
- Stronger learned-metric baselines (proper triplet loss, margin-based contrastive, prototype networks)
- Independent third-party timestamp anchor (e.g., OpenTimestamps proof on Bitcoin) on the four pre-registration files. The cryptographic property `verify_prereg_hash()` enforces (file is byte-identical to its hashed state) is preserved; what's not externally provable in the current repo is the absolute claim "lock-time was April 10, 2026 before any results existed." A reviewer must trust the lock-time is honest. An OpenTimestamps proof would convert this trust step into independent verification. Cost: 5 minutes per pre-reg file. Deferred but noted.

## Honest epistemic statement

This compendium has six pre-registered experiments, four SHA256-locked pre-registrations, 9,360 per-cell bootstrap-CI results, five compiled papers, and one decisively-confirmed main claim (the cliff is real, is not a stratification artifact, and is rescuable by a 5-second supervised projection). It also has five null results properly owned, three factual corrections to early session prose, and documented deferrals. It is not perfect. It is, I believe, honest.
