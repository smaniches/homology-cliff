# Changelog

All notable changes to the Homology Cliff compendium. Format: [Keep A Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

**Author:** Santiago Maniches, Independent Researcher (ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)). **Lab:** TOPOLOGICA LLC (solo research lab, single-person operation).

## [v1.4.4] — 2026-04-26
### Fixed (raised-bar pre-public audit)
- **Hardcoded Windows paths in 11 scripts** (Defects R/T/U from the deep-audit pass): `code/harnesses/run_cliff.py`, `run_cliff_fullnull.py`, `run_cascade.py`, `run_fisher.py`, `code/analyses/run_calibration.py`, `run_adversarial_phase1.py`, `run_mapper.py`, `run_mapper_augmentation.py`, `fetch_pfam_v3.py`, and both notebooks. Every script now resolves paths via `Path(__file__).resolve().parents[N]` (with an `HOMOLOGY_CLIFF_REPO_ROOT` env-var override for CI/notebook contexts). The master harness `run_cliff.py` exposes named output directories (`RESULTS_DIR`, `NEGCTRL_DIR`, `FULLNULL_DIR`, `CASCADE_DIR`, `FISHER_DIR`) that map to the public-release `data/cells/{main,negctrl,fullnull,cascade,fisher}/` layout. Previous releases (1.4.0-1.4.3) shipped harnesses that ran only on the author's original workstation; the README's "rerun any single harness" claim was materially false until this fix.
- **Dataset filename mismatch** (Defect S): the pre-registration locks `experiment2_proteins_25k_filtered.json` (working ID); the repo ships `proteins_25k_sequences.json` (descriptive name). Code now accepts either path; `DATA_CARD.md` and Paper 1 §Data already disclosed the rename.
- **Pre-reg verification path fix** (Defect U): `verify_prereg_hash()` now reads from `data/prereg/`, not the historical Windows `_prereg/`. Cryptographic guarantee (harness aborts if pre-reg file is byte-edited) now actually executes on a public clone.
- **Bootstrap CI docstring fix** (Defect V): `run_cliff.py` docstring claimed BCa; implementation has always been 10,000-resample percentile (matching Paper 4). Docstring corrected.
- **`run_cliff.py` factorial-cell-count docstring fix** (Defect X): "4000-cell" -> "9,360-cell" (3,000 main + 3,000 negctrl + 3,000 fullnull + 180 cascade + 180 fisher).
- **Calibration script - figure binning reconciliation** (Defect W): `run_calibration.py` rewritten to use the six unequal-width bins ($\{0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0\}$) shown in Paper 3's published figure, replacing the previous 10-equal-width-bin scheme that did not match the figure. Output `data/results_summaries/calibration_results.json` now contains the per-stratum reliability table, ECE values, and positive-prediction precision counts that Paper 3 cites - previously these numbers lived only in Paper 3's prose.
- **Buggy print statement in `run_mapper_augmentation.py`** (lines 28-34): replaced `pos_nodes.index(pos_nodes[pos_nodes.index({x:y for x,y in pos_nodes[0].items()})])` (which always returns 0) with explicit `n_nodes_used` counter that reports the actual number of Mapper nodes contributing to the biased pool.

### Changed (raised-bar epistemic calibration)
- **Soften overclaim language across Papers 1, 2, 3, 5**: replaced "ruling out within-family distant-homology as the mechanism" / "Panel expansion is not a rescue" / "rules out the within-family hypothesis entirely" / "panel augmentation is ruled out" with consistent "consistent with / inconsistent with / disfavors / Wilson 95\% CI $[0\%, 17\%]$" framing. The empirical 20-of-20 cross-family observation is unchanged; only the inferential strength is calibrated to what n=20 supports under Wilson interval estimation. Paper 3 abstract additionally clarifies that the calibration-guarantees-vanish framing is per Ovadia et al. 2019 (cited result, not newly demonstrated here).
- **Paper 3 §Limitations L2** now correctly describes the binning as six bins with boundaries $\{0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0\}$ rather than "6-bin uniform" (the bins are unequal width).
- **Paper 5 §"What this rules out"** -> §"What this disfavors" (header change matches the softened conclusions).

### Added
- `data/results_summaries/calibration_results.json` -- committed JSON evidence for every Paper 3 headline number; reproducible by `python code/analyses/run_calibration.py`.
- `PROBLEMS.md` items 8, 9, 10 documenting the v1.4.4 audit fixes; updated "deferred" list to include OpenTimestamps third-party-anchor proof for the pre-registration files (cryptographic lock holds; absolute lock-time relies on author attestation in the current repo).

## [v1.4.3] — 2026-04-25
### Fixed
- Dataset filename mismatch: Paper 1 §Data and `DATA_CARD.md` now reference the actual shipped file `data/sequences/proteins_25k_sequences.json` (working ID `experiment2_proteins_25k_filtered` retained for provenance)
- DOI badge URL replaced with `shields.io` "DOI: pending" placeholder until first Zenodo deposit (previous URL `zenodo.org/badge/latestdoi/<owner>/<repo>.svg` was structurally invalid — Zenodo uses numeric repo IDs)
- Metadata version normalization to v1.4.3 across `CITATION.cff`, `codemeta.json`, `README.md`

## [v1.4.2] — 2026-04-25
### Fixed
- Paper 4: pre-existing `! Double subscript.` LaTeX error in seed-variance gate equation (`F_1^{distant}_s` → `F_{1,s}^{distant}`)

## [v1.4.1] — 2026-04-25
### Fixed
- Pre-release audit defects A–J: hardcoded Windows path in `code/analyses/v3_aggregate.py`; version drift across `CITATION.cff`/`codemeta.json`/`README.md`; missing DOI badge; Paper 4 title (4000-Cell → 9{,}360-Cell); Paper 5 date marker; PDF/source drift; manifest staleness; PROBLEMS.md duplicate

## [v1.4.0] — 2026-04-12
### Added
- `CHANGELOG.md` (this file)
- `CONTRIBUTING.md` with issue and PR templates
- `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)
- `SECURITY.md` with dual-use biosecurity disclosure policy
- `BENCHMARK.md` defining the cliff-gap leaderboard
- `FAQ.md` answering 20+ anticipated reviewer questions
- `REFEREES.md` logging adversarial-review passes per paper
- `deployment_example/` with a 30-line Python example for production use
- Badge row in README (license, CI, DOI placeholder, Python version, paper count)
- `.github/ISSUE_TEMPLATE/` bug_report, data_issue, reproducibility_failure

### Changed
- README restructured with audience-specific entry points

## [v1.3.2] — 2026-04-12
### Added
- Full narrative README with motivation, who-this-is-for, trust section for solo-researcher-with-AI authorship, machine-readable JSON index, reproducibility one-liners

## [v1.3.1] — 2026-04-12
### Fixed
- Papers 2/3/4/5 compiled with TikZ figures (was: 0 figures in Papers 4/5, 1 figure in Papers 2/3)
- Paper 5 bibliography populated (was: empty due to missing `\cite` calls)
- Figure rendering on pgfplots symbolic-x-coords axes (Paper 1 reliability diagram)
- Citations across Papers 2/3/4/5: 25/8/17/4 bibliography entries respectively

## [v1.3.0] — 2026-04-12
### Added
- `DATA_CARD.md` for the 24,885-protein test set with dual-use ethics statement
- `MODEL_CARD.md` for the learned-projection rescue
- `reproducibility/GPU_EXECUTION_GUIDE.md` with Colab Pro A100 and Kaggle T4 paths

## [v1.2.0] — 2026-04-12
### Added
- Papers 2, 3, 4 v1.1 with figures, expanded references, full related-work sections

## [v1.1.0] — 2026-04-12
### Added
- Paper 1 v1.1 at arXiv-submittable level: 3 TikZ figures, 24 bibliography entries, related-work section, cross-family section, deployment recommendations, full methods

## [v1.0.1] — 2026-04-12
### Added
- Cross-family Pfam partition analysis: 100% of evaluable distant false alarms are cross-family (0 of 20 within-family)
- Paper 5 upgraded from v0.9 stub to v1.0 with the cross-family result as headline
- `code/analyses/run_cross_family_partition.py`
- `data/results_summaries/cross_family_partition.json`

### Changed
- Pfam coverage raised from 425/24,885 (v1 fetch) to 21,615/24,885 = 86.9% (v3 batch-50 search)

## [v1.0.0] — 2026-04-12
### Initial release
- Five compiled papers at v1.0 baseline
- 9,360 per-cell bootstrap-CI `.npz` results across main/negctrl/fullnull/cascade/fisher experiments
- 3 ESM-2 embedding arrays (t6/t12/t30) via Git LFS
- 4 SHA256-locked pre-registrations
- `MANIFEST.sha256.json` covering 9,445 files
- Production infrastructure: pyproject.toml, CITATION.cff, codemeta.json, pytest harness, GitHub Actions CI, LICENSE (CC-BY-4.0 papers / MIT code)
- `PROBLEMS.md` with self-audited error log
- `ACKNOWLEDGMENTS.md` with max-humility attribution

### Known errors caught before v1.0.0 release
- "Mahalanobis rescues the cliff by +0.376" framing corrected: Mahalanobis closes the gap only by collapsing close-stratum F1, not by rescuing distant
- Stratification thresholds corrected from 0.40/0.90 (memory) to 0.95/0.90 (source code)
- F1 vs accuracy terminology corrected to match .npz schema
- Panel-only shuffle null diagnosed as class-prior retention; full-pool permutation null pre-registered before stricter test
