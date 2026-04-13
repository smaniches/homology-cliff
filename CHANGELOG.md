# Changelog

All notable changes to the Homology Cliff compendium. Format: [Keep A Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

**Author:** Santiago Maniches, Independent Researcher (ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)). **Lab:** TOPOLOGICA LLC (solo research lab, single-person operation).

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
