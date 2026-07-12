# Changelog

All notable changes to the Homology Cliff compendium. Format: [Keep A Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

**Author:** Santiago Maniches, Independent Researcher (ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)). **Lab:** TOPOLOGICA LLC (solo research lab, single-person operation).

## [Unreleased]

### Fixed — documentation consistency
- **Manifest entry-count references corrected to 9,490** in `README.md`, `STATUS.md`, and `REVIEWER.md`. The v1.5.2 release added two tracked artifacts (`code/analyses/compute_pooled_f1.py` and `data/results_summaries/pooled_f1_summary.json`), taking `MANIFEST.sha256.json` from 9,488 to 9,490 entries, but the current-state count in these three documents was not refreshed at the time. Verified with `python scripts/ci/verify_manifest.py` (9,490 entries: 125 real-file hashes matched, 9,365 LFS pointer stubs skipped, 0 missing, 0 mismatches). The historical v1.5.0/v1.5.1 changelog entries, which correctly record 9,488 for those releases, are left unchanged.
- **Paper 3 reference count corrected to 7** in the README `Honest limitations` section (was 8). `papers/03_calibration_collapse/paper.tex` cites seven unique references and the compiled `paper.pdf` bibliography contains seven entries; the same count method reproduces the stated 24/25/17/4 counts for Papers 1, 2, 4, and 5 exactly.
- **`code/kaggle_notebooks/adv_cell1_setup.py`: replaced the removed `Bio.SubsMat.MatrixInfo` import** with `Bio.Align.substitution_matrices`. `Bio.SubsMat` was deleted in Biopython 1.80 (2022), so the adversarial phase-2 scaffold would fail at import on any modern Biopython the cell installs. The replacement loads the same BLOSUM62 matrix via the current API; the returned `Array` supports `blosum62.get((a, b), default)` identically, so `adv_cell2_edits.py` is unchanged. Verified against Biopython 1.87 that the scaffold's exact `blosum62.get((a,b), blosum62.get((b,a), -99))` expression returns identical scores (A/R = -1, W/W = 11, symmetric, non-alphabet pairs hit the -99 default).
- **README read-order note corrected from "three additional rescues" to "four rescues"** (Paper 2 documents all four: Mahalanobis, Fisher-Rao, cascade, Mapper-augmentation), matching the paper's title and abstract. Added a note that the `papers/02_three_failed_rescues/` directory retains its original name (three rescues; a fourth was pre-registered and added later) as a stable identifier matching the archived Zenodo deposit.

### Changed
- Refreshed stale current-version labels from `v1.5.0` to `v1.5.2`: the README `Honest limitations` opening line and the `STATUS.md` version header (now dated 2026-07-06). Historical `v1.5.0` references that record when a specific item was resolved are unchanged.
- `.github/dependabot.yml`: moved the `pip` and `github-actions` update cadence from monthly to weekly and grouped each ecosystem's updates into a single batched PR (`groups: "*"`). Weekly cadence surfaces a CVE in the verification toolchain (which includes `pip-audit` and `bandit`) within a week rather than up to a month while the repository is under active external review; grouping matches the maintainer's existing practice of landing dependency bumps as one batch. No runtime dependency is added or unpinned; the GPU floors in `pyproject.toml` are untouched.
- `MANIFEST.sha256.json`: refreshed the LF-committed hashes for the edited `README.md`, `STATUS.md`, `REVIEWER.md`, `.github/dependabot.yml`, and this `CHANGELOG.md`. No entries added or removed; the count remains 9,490.
- `requirements-lock.txt`: `coverage` 7.14.3 -> 7.15.0, `ruff` 0.15.20 -> 0.15.21, `mypy` 2.1.0 -> 2.2.0 (Dependabot verification-toolchain group, PR #46). `MANIFEST.sha256.json` re-sealed to match (single entry, `requirements-lock.txt`; count unchanged at 9,490) -- Dependabot cannot run `scripts/update_manifest.py` itself, so its PRs always fail `manifest-verify` on the file they touch; this is the same land-manually-and-supersede pattern used for PRs #24-#30, #34-#40. Runtime pins (`numpy`, `scipy`, `scikit-learn`) and GPU floors are untouched. Re-validated against the new toolchain: `ruff check .`, `mypy` (--strict), `bandit`, `pip-audit` (0 known vulnerabilities), `pytest tests/` (37 passed / 3 skipped, coverage 15.91% > 15% floor), and `python reproduce.py` (all 7 phases pass, headline numbers unchanged) all green. Supersedes #46.

## [v1.5.2] — 2026-06-16

Pooled-F1 provenance + Paper 2 Attempt-2 correction. No conclusion changes; all evidence cells and result summaries are byte-identical to v1.5.0.

### Added
- `code/analyses/compute_pooled_f1.py` + `data/results_summaries/pooled_f1_summary.json`: reproduce pooled (whole-test-set) F1, per-stratum F1, and the close-distant gap for the cited cells directly from the committed embeddings (via `run_cliff`/`run_fisher`). The cosine/mahalanobis/learned pooled values cross-check against the committed cascade cells to a maximum drift of 8.8e-6; the script supplies the one pooled value (Fisher-Rao) that no committed cell stored. `reproduce.py` now asserts the rescue-table pooled row (default mode) and re-derives it under `--full`.

### Fixed — Paper 2 Attempt-2 (Fisher-Rao), erratum 2026-06-16
- The prior text claimed Fisher-Rao "underperforms Mahalanobis" with a "+0.015 to +0.285 pooled-F1 penalty" and is "strictly worse than Mahalanobis." Reproduction from the committed cells shows the opposite sign: Fisher attains **higher** pooled F1 than Mahalanobis in all 18 cells (its close-stratum collapse is milder). The pre-registered result is unchanged: Fisher's close-distant **gap** exceeds Mahalanobis's in 17 of 18 cells (H1 rejected), and at the R=1000 deployment regime neither whitening lifts distant-stratum F1 to the cosine baseline, so Attempt 2 remains a failed rescue.
- `fig:whitening` now plots **distant-stratum F1** (the safety-critical metric, reproducible from the committed cells: cosine > Fisher > Mahalanobis at R=500 and 1000) instead of pooled F1; the prior figure plotted Fisher below Mahalanobis, which the pooled data does not support.
- Attempt-2 factorial description corrected to "3 panels x 2 k-values" (was "2 panels x 3 k-values"; the run is R in {100,500,1000} x k in {5,25}).

### Fixed — Paper 2 Attempt-3 (cascade), Paper 1 rescue table
- Attempt-3 cascade pooled-F1 penalty range corrected to **-0.046 to -0.236** (10-seed mean, from the committed cascade cells; the prior **-0.310** overstated the maximum). The "rejected in 18 of 18 cells" conclusion is unchanged.
- Paper 1 rescue-table Fisher-Rao row brought into exact agreement with the committed Fisher cells: close 0.478->0.484, distant 0.094->0.099, pooled 0.461->0.462 (the cosine/Mahalanobis/learned rows already matched).

### Changed
- `version` 1.5.1 -> 1.5.2 in `CITATION.cff`, `codemeta.json`, `README.md`, `pyproject.toml`; Papers 1 and 2 PDFs rebuilt; `figures/cliff_summary.png` version label updated; `MANIFEST.sha256.json` refreshed.

## [v1.5.1] — 2026-06-16

Figure-erratum and citation-metadata patch. No result, table, or conclusion changes; all evidence cells and result summaries are byte-identical to v1.5.0.

### Fixed — figure erratum (2026-06-16)
- **Paper 1, Figure 1 (`fig:cliff_surface`) and Figure 3 (`fig:rescue`)** are now plotted directly from the committed MAIN gap table (`data/results_summaries/v3_final.txt`). The previously plotted values at interior panel sizes and at the t6/t12 scales had been hand-entered and diverged from the committed data; the `R=1000` endpoints, the t30 column, the data tables, and the +16/+33/+47% relative-improvement figures were already correct. The corrected figures show the same monotonic cliff and the same rescue ordering (learned > cosine > Mahalanobis at every scale); the y-axis of Figure 3 was widened and Figure 1's caption now notes that the scale ordering is established for panels `R≥100`. The reliability figure (Figure 2) was already correct (verified against `calibration_results.json`) and is unchanged.
- **Paper 5, `fig:mapper`** is now generated directly from the committed Mapper graph (`data/results_summaries/mapper_graph.json`): it plots the dominant node per occupied PCA lens bin, colored by positive fraction, and the caption is corrected accordingly. The previously plotted points were hand-entered and did not all match the committed graph. The Pfam-partition results are unchanged.
- `scripts/build_summary_figure.py` / `figures/cliff_summary.png` regenerated (all panels are parsed from the committed summaries; version label updated; content unchanged).

### Fixed — citation metadata
- Corrected the Zenodo DOI references. `CITATION.cff`, `README.md`, and `codemeta.json` previously cited `10.5281/zenodo.20143143` as the "concept DOI." That identifier is the **v1.4.7 version DOI**; the **concept DOI is `10.5281/zenodo.20143142`** (it resolves to the latest version) and is now the canonical citation DOI. For the record, the version DOIs are v1.4.7 → 10.5281/zenodo.20143143 and v1.5.0 → 10.5281/zenodo.20719001.

### Changed
- `version` 1.5.0 → 1.5.1 and dates → 2026-06-16 in `CITATION.cff`, `codemeta.json`, `README.md`, and `pyproject.toml`.
- `MANIFEST.sha256.json`: refreshed hashes for the edited paper PDFs and `.tex` sources, the citation-metadata files, and the regenerated summary figure (entry count unchanged at 9,488).

## [v1.5.0] — 2026-06-15

This release adds externally-verifiable engineering quality gates and a transparent **erratum**: a stale committed artifact and a code defect — neither affecting any core finding — were corrected after a full write-free reproduction audit in which the headline homology-cliff result reproduced bit-for-bit from the committed embeddings and seeds.

### Engineering / CI
- `.github/workflows/lint.yml` — ruff (pyflakes + syntax-error rules), mypy `--strict` (scoped to `scripts/ci/`), bandit (intentional checks skipped via `[tool.bandit]`), and pip-audit, on the pinned verification toolchain.
- `.github/workflows/tests.yml` — pytest now collects coverage with an honest `fail_under` floor over the LFS-free unit-test surface.
- `tests/test_numerics_known_answer.py` — 28 known-answer tests pinning the published-number functions (F1, majority vote, stratify, panel construction, bootstrap CI, ECE, reliability, positive-prediction precision, full-pool label permutation) to hand-computed reference values.
- `requirements-lock.txt` (CI verification-toolchain lock, explicitly not a GPU-artifact-environment lock), `.github/dependabot.yml`, `.github/CODEOWNERS`.
- `pyproject.toml` — `[tool.ruff]`, `[tool.mypy]`, `[tool.bandit]`, `[tool.coverage]`; PEP 639 SPDX `license` expression + `license-files` (build requirement raised to `setuptools>=77`).
- `scripts/update_manifest.py` — now hashes the LF-committed form of text files (CRLF→LF iff the working-tree EOL is `crlf` and the path is not Git-LFS-tracked) and writes the manifest with LF newlines, so a manifest regenerated on a Windows checkout is byte-identical to one from Linux. Verified to reproduce all prior entries exactly.

### Fixed — erratum (reproduction audit, 2026-06-15)
- **`data/results_summaries/calibration_results.json` (Paper 3) was stale.** It predated a `build_panel` change and did not reproduce from the current pipeline (its `_provenance` note falsely claimed byte-stability); it has been regenerated from the script. Corrected close/moderate positive-prediction precision are **0.788** and **0.347** (previously 0.891 and 0.467); close/moderate stratum sizes are **22,198** and **1,533** (previously 22,090 and 1,641). The headline distant precision (3/44 = 0.068) and all three ECEs (0.069 / 0.154 / 0.294) reproduce **unchanged**. The reliability figures in Papers 1 and 3 are now plotted from the script-computed reliability table rather than hand-entered diagram read-offs. Papers 1 and 3 updated; all conclusions unchanged.
- **Mapper biased-panel deduplication (Paper 2 Attempt 4; resolves audit blocker B4).** In `code/analyses/run_mapper_augmentation.py` and `run_mapper_augmentation_robustness.py`, the 30%-overlapping Mapper cover let boundary proteins recur across node member lists, and `rng.choice(replace=False)` removes positions, not values, so the biased arm held fewer than 500 unique positives. Pools are now deduplicated (`np.unique`). The corrected rescue is **−0.0080** (was +0.0018), 95% CI **[−0.035, +0.018]**; the CI still spans zero, **H1 remains rejected, and the null conclusion is unchanged and reinforced**. `mapper_augmentation_results.json` and `mapper_augmentation_robustness.json` regenerated; Paper 2 updated. The committed +0.0018 null reproduced bit-for-bit before the fix.
- **Mapper full-membership robustness (audit blocker B4) executed and resolved.** The robustness re-run (`run_mapper_augmentation_robustness.py`, now run for the first time) showed that, under a *naive per-arm stratification*, full node membership appears to support H1 (rescue +0.084 multi-node, +0.172 single-node). This is a **stratification artifact**: a cluster-concentrated biased panel enlarges its own distant stratum (biased/uniform `n_dist` ratio up to 1.16), pushing easier points into a larger "distant" set. A **common-stratification control** (both arms scored on the same distant queries, now committed in the robustness harness and JSON as `controlled_rescue_*`) collapses the rescue to ≈0 (−0.004 multi-node, −0.006 single-node; the truncated arm's controlled rescue is +0.016), every CI spanning zero — consistent with the committed truncated result under its own stratification (−0.008, H1 also rejected). **The Attempt-4 null is robust to full membership; the "four failed rescues" result stands.** Documented in `docs/MAPPER_AUGMENTATION_ROBUSTNESS.md` and `PROBLEMS.md`.

### Reproduction audit (2026-06-15)
- Write-free reproduction of every published claim from the committed embeddings + seeds: the main factorial (Paper 1) reproduces bit-exact for cosine/euclidean and to a 5th-decimal cross-platform LAPACK tolerance for mahalanobis; the `v3_final.txt` gap tables and the `cross_family_partition.json` counts reproduce exactly; the null controls (negctrl, fullnull) reproduce and the "fullnull gap ≈ 0" claim holds (mean +0.004 vs negctrl +0.33 vs main +0.57). The core homology-cliff finding is solid.

### Added
- `reproduce.py` — single-command reproduction and verification entry point. Default mode (no Git-LFS payload required) runs the verification chain (pre-registration SHA256 locks, manifest integrity, smoke imports, evidence spot-checks, schema + known-answer tests) and asserts each headline number from the committed summaries against its expected range; `--full` re-derives `calibration_results.json` and `mapper_augmentation_results.json` and asserts byte-identity (SHA256) to the committed artifacts. Repo-relative paths; exit 0 iff every phase passes.
- `REVIEWER.md` — orientation guide for external adversarial reviewers (PRs #5–#7).
- `docs/CLAIMS_TO_EVIDENCE.md` — claim-to-evidence traceability map linking each headline number to its committed artifact (PRs #5–#7).
- `.github/workflows/evidence.yml` + `scripts/ci/verify_evidence.py` — CI spot-checks that headline numbers in the committed JSON summaries match expected values and that all five paper PDFs and the claims doc exist (PRs #5–#7).
- `code/analyses/run_mapper_augmentation_robustness.py` + `docs/MAPPER_AUGMENTATION_ROBUSTNESS.md` — non-destructive full-membership robustness re-run of the Mapper panel-augmentation attempt (Paper 2 Attempt 4 / audit blocker B4). Executed 2026-06-15; results committed in `data/results_summaries/mapper_augmentation_robustness.json`. Resolves blocker B4 (see the erratum entry above).
- `tests/test_verify_manifest.py` — eight focused regression tests for `scripts/ci/verify_manifest.py` covering exact-byte match, CRLF text fallback, binary exact-bytes-only, missing-file failure, gitignored-artifact skip, LFS-pointer-stub skip, and bad-format-entry failure. Raises that module's line+branch coverage to 92%. Uses `tmp_path` fixtures only; needs no LFS payload.

### Changed
- `scripts/ci/verify_manifest.py`: made CRLF-robust for text files, mirroring `verify_prereg_locks.py`. The manifest stores the LF-committed hash of each text file; on a Windows checkout with `core.autocrlf=true` the working tree carries CRLF endings, which previously produced 105 spurious mismatches and exit code 1 locally even with no content edited. The verifier now retries a failed text-file match against the LF-normalized content; binary files (`.npz/.npy/.png/.pdf/...`) are never normalized and still require an exact raw-byte match. The committed manifest hashes are unchanged; Linux/CI behavior is unchanged.
- `MANIFEST.sha256.json`: added the entry for the new `tests/test_verify_manifest.py` and refreshed entries for the edited `scripts/ci/verify_manifest.py`, `README.md`, `REVIEWER.md`, `STATUS.md`, and this `CHANGELOG.md` (LF-committed hashes), added `data/results_summaries/mapper_augmentation_robustness.json` plus the new CI-governance and known-answer test files, and removed `bandit-baseline.json`. Total manifest entries after v1.5.0: 9,488.
- `README.md`, `REVIEWER.md`, `STATUS.md`: manifest entry-count references updated to 9,488; `REVIEWER.md` test-count expectations updated for the new tests (40 passed with LFS; 37 passed / 3 skipped without LFS).
- `code/analyses/v3_aggregate.py` (audit blocker B3): corrected the full-null print banner that claimed per-stratum F1 should be "near 0.5". Under full-pool label permutation F1 collapses toward 0; the addendum's operationalized criterion is gap-near-zero across 10 seeds. The "0.5" framing was inherited from the deprecated v1 panel-shuffle null.
- `README.md` (audit blockers B6, B7): softened the unconditional "every number has an artifact on disk" statement to state explicitly that reproducibility is conditional on trusting the withheld label-curation rule; qualified the `v3_aggregate.py` 15-minute recipe step to note it requires `git lfs pull`.
- `code/harnesses/run_cliff.py` (audit blocker B2): documented at the `StratumResult` declaration that `precision`/`recall` are intentionally unpopulated (NaN) in every committed cell — only F1 and its bootstrap CI are pre-registered.
- `code/analyses/run_mapper_augmentation.py` (audit blocker B5): corrected the docstring's dangling reference to a non-existent `PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md`; the docstring now states accurate provenance (follows Paper 1's pre-registered factorial; only Mahalanobis and cascade are SHA256-locked).
- PEP 8 formatting pass; CodeQL alert resolution (workflow permissions, Python syntax); `scripts/update_manifest.py` chunked hashing and CI boundary check (PRs #5–#7).
- `pyproject.toml`: discoverability and build-robustness metadata. Added `keywords`, trove `classifiers` (Intended Audience :: Science/Research; Topic :: Scientific/Engineering :: Bio-Informatics and :: Artificial Intelligence; Programming Language :: Python :: 3 / 3.11; Operating System :: OS Independent), and `[project.urls]` Repository / Documentation (GitHub Pages) / Changelog entries (previously Homepage only). Pinned `[tool.setuptools] packages = []` alongside `py-modules = []` so flat-layout auto-discovery cannot treat `code/`, `data/`, `papers/`, etc. as importable across setuptools versions (the build requirement is raised to `setuptools>=77` for PEP 639, recorded under Engineering / CI above). Addresses automated-review feedback on PRs #20–#21.
- `scripts/ci/verify_manifest.py`: the binary-suffix guard now lowercases the path before matching `BINARY_SUFFIXES`, so uppercase extensions (`.PNG`, `.PDF`, `.NPZ`) are still treated as exact-bytes-only and never LF-normalized.

### Notes
- The 9,360-cell main/negctrl/fullnull/cascade/fisher evidence base (the `.npz` cells) is **byte-identical to v1.4.7** and reproduces bit-for-bit from the committed embeddings and seeds. No SHA256-locked pre-registration file was touched. The v1.5.0 erratum regenerated only two derived summary artifacts (`calibration_results.json`, `mapper_augmentation_*.json`) and the papers that cite them.
- Blocker B4 (whether the Mapper rejection is robust to full node membership) is **resolved**: the full-membership robustness re-run was executed and the biased-panel deduplication defect was fixed. The Mapper rejection holds (corrected rescue −0.0080, 95% CI includes zero). The previously-noted prose/code discrepancy (Paper 2 §Attempt 4 single-top-node prose vs multi-node accumulation in code) is recorded in the v1.5.0 erratum above.

## [v1.4.7] — 2026-05-12
### Added
- **Zenodo DOI**: first permanent archive minted at [10.5281/zenodo.20143143](https://doi.org/10.5281/zenodo.20143143) after the v1.4.7 GitHub Release triggered the Zenodo webhook. README badge resolves; concept DOI tracks all future versions.
- `.zenodo.json`: deposit metadata (title, description, creator + ORCID, license, keywords, `isSupplementTo` repo link) so each Zenodo record gets clean fields instead of only the repo's auto-extracted surface metadata. Originally added in PR #3; this entry records its arrival in the changelog.

### Changed
- `README.md`: header version stamp bumped `v1.4.4 -> v1.4.7`, date `April 12, 2026 -> May 12, 2026`, added `DOI: 10.5281/zenodo.20143143` link to the header line, Machine-Readable Index JSON (`doi`, `doi_url`, `zenodo_metadata` keys), and BibTeX block. "Honest limitations" intro bumped to `v1.4.7` and the *"Zenodo DOI deposit ... pending"* bullet removed. `## Zenodo DOI (optional)` section renamed to `## Zenodo DOI` and rewritten to document the live DOI (concept-vs-version DOI distinction). The DOI badge URL itself was already swapped from the `shields.io` placeholder to the real Zenodo SVG in PR #3 / v1.4.7 release boundary; this PR does not touch the badge line.
- `CITATION.cff`: `version: 1.4.4 -> 1.4.7`, `date-released: 2026-04-12 -> 2026-05-12`, added `doi: "10.5281/zenodo.20143143"`.
- `codemeta.json`: `version: 1.4.4 -> 1.4.7`, `dateModified: 2026-04-12 -> 2026-05-12`, added `identifier: https://doi.org/10.5281/zenodo.20143143`.
- `MANIFEST.sha256.json`: refreshed entries for `README.md`, `CITATION.cff`, `codemeta.json`, `CHANGELOG.md` to match the metadata bump.

### Not changed
- No code-behavior changes. No experiments rerun. No paper, harness, test, or workflow edits. No data file edits. The 9,360-cell evidence base is identical to v1.4.5.

## [v1.4.6] — 2026-05-10
### Added
- GitHub Release tag `v1.4.6` cut from the v1.4.5 merge commit (`263e2fe`) as the first public tag. No code/content changes versus v1.4.5; the tag preceded the Zenodo wiring landing on `main`, so this release did not result in a Zenodo deposit. v1.4.7 is the first version with a minted DOI.

## [v1.4.5] — 2026-05-07
### Added
- `.github/RELEASE_AUDIT_v1.4.5.md` — blocker-verification audit before public
  adversarial-review outreach. Seven reviewer-facing blockers were re-checked
  against current `origin/main` (post-v1.4.4). Two were confirmed already fixed
  in v1.4.4 (B1 calibration artifact, B6 instance 1 `run_cliff.py` docstring).
  Five remain open and are documented inline as maintainer-decision pending:
  B2 precision/recall NaN schema fields,
  B3 stale "F1 near 0.5" wording in `code/analyses/v3_aggregate.py`,
  B4 Mapper augmentation truncated node membership,
  B5 missing `PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md`,
  B7 dataset label-rule auditability overclaim.

### Not changed
- No code-behavior changes in this version entry. No experiments rerun. No
  `README.md`, `DATA_CARD.md`, `PROBLEMS.md`, paper, test, workflow, or
  metadata edits. The five open blockers are deferred to follow-up PRs after
  maintainer decisions on framing.

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
- 4 pre-registrations committed (2 SHA256-locked and harness/CI-verified; cascade and Fisher committed without a runtime hash check)
- `MANIFEST.sha256.json` covering 9,445 files
- Production infrastructure: pyproject.toml, CITATION.cff, codemeta.json, pytest harness, GitHub Actions CI, LICENSE (CC-BY-4.0 papers / MIT code)
- `PROBLEMS.md` with self-audited error log
- `ACKNOWLEDGMENTS.md` with max-humility attribution

### Known errors caught before v1.0.0 release
- "Mahalanobis rescues the cliff by +0.376" framing corrected: Mahalanobis closes the gap only by collapsing close-stratum F1, not by rescuing distant
- Stratification thresholds corrected from 0.40/0.90 (memory) to 0.95/0.90 (source code)
- F1 vs accuracy terminology corrected to match .npz schema
- Panel-only shuffle null diagnosed as class-prior retention; full-pool permutation null pre-registered before stricter test
