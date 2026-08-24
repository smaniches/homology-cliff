# Changelog

All notable changes to the Homology Cliff compendium. Format: [Keep A Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

**Author:** Santiago Maniches, Independent Researcher (ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)). **Lab:** TOPOLOGICA LLC (solo research lab, single-person operation).

## [Unreleased]

## [v1.6.0] — 2026-08-24

### Added
- **Preregistered ten-seed cross-family confirmation executed and archived (2026-08-24).** The SHA256-locked protocol in `data/prereg/PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md` was executed once from `main` via GitHub Actions run `32692013434`. Seed 20260410 reproduced the pre-existing single-seed artifact before continuation. Across all ten fixed panel seeds, CROSS_FAMILY > WITHIN_FAMILY; median per-seed cross-family fraction = 1.000, mean = 0.994, range = 0.962-1.000, and every seed had a nonzero evaluable denominator, so the preregistered strong robustness criterion passed. The exact sealed output is `data/results_summaries/cross_family_partition_10seed.json` (SHA256 `332b939622ac2a174124f5378d74d2df074d66561654c7b84e55002608677b7d`). Recurring accession appearances are not pooled into a binomial interval because the panel seed is the locked robustness unit.
- **Executable confirmatory cross-family runner** at `code/analyses/run_cross_family_partition_10seed.py`, implementing the already-locked ten-seed protocol without executing it. The runner is import-safe, reproduces seed 20260410 against the committed single-seed detail before continuing, reports the locked per-seed Wilson intervals and unweighted seed-level aggregate, retains full per-accession evaluable histories, withholds the strong claim on any zero-evaluable seed, and refuses to write a result if the existing seed does not reproduce. `tests/test_cross_family_partition_10seed.py` covers only deterministic summary, interval, accession-history, and decision-rule logic; no additional panel seed is run by CI or by this change.
- **Confirmatory 10-seed cross-family pre-registration** locked at `data/prereg/PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md` (SHA256 `204953ef...9a7a6804`, LF bytes), with its companion digest stored beside it at `data/prereg/PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md.sha256`. It fixes, before any additional panel seed is run, a robustness extension of the single-seed cross-family Pfam partition (`code/analyses/run_cross_family_partition.py`, committed at `data/results_summaries/cross_family_partition.json`) across the ten already-fixed panel seeds 20260410-20260419. The protocol is held identical (t30, R=1000, k=25, cosine via `faiss.IndexFlatIP`, distant `smax < 0.90`, positive majority at k=25, distant false positives only, unchanged Pfam WITHIN/CROSS partition and evaluable definition) and locks: per-seed distant / distant-FP / evaluable / WITHIN_FAMILY / CROSS_FAMILY counts and fractions with a per-seed Wilson 95% interval for the within-family fraction; the unweighted mean, median, min and max of the per-seed cross-family fraction over seeds with a nonzero evaluable denominator; a secondary cross-seed accession summary; and a decision rule (CROSS_FAMILY > WITHIN_FAMILY in every nonzero-evaluable seed AND median per-seed cross-family fraction >= 0.80, with the strong claim withheld if any seed has zero evaluable observations). The seed is the robustness unit; no pooled Wilson interval is computed over recurring accessions. The eventual result will be written to the new `data/results_summaries/cross_family_partition_10seed.json`; the existing `cross_family_partition.json` is untouched. No experiment is run here and no scientific result, paper, README claim, threshold, classifier, or family definition changes.
- **Restored companion `data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md.sha256`** promised by the body of `PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md` ("stored at PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md.sha256") but previously absent from the tree. It carries the already-canonical digest `139f6012...515bcc06` (recomputed here under the same LF normalization CI uses, exact match required before writing) that `scripts/ci/verify_prereg_locks.py` and `run_cliff.py` already enforce. The SHA256-locked `.md` itself is byte-identical and unchanged.

### Changed
- **Scientific reporting updated after the confirmatory result.** Papers 1 and 5, README, website, claims-to-evidence ledger, FAQ, reviewer/referee guidance, status, model/deployment documentation, and Zenodo metadata now distinguish the original 20/20 seed result from the preregistered ten-seed confirmation. Paper 5's title is softened from categorical "cross-family, not within-family" wording to "cross-family predominance" because two within-family appearances are present in the complete confirmatory result. The result itself and all preregistration bytes remain unchanged.
- **Evidence CI now checks the ten-seed committed result semantically**, including the ten exact seeds, seed-level decision booleans, mean/median/min/max, accession-summary counts, and frozen protocol metadata. A no-LFS pytest regression test checks the committed confirmatory summary as well.
- **`scripts/ci/verify_prereg_locks.py`**: the `EXPECTED` map grows from two entries to three, adding the new 10-seed pre-registration's SHA256 lock so CI fails on any byte-level edit to it. The two existing hashes are unchanged. The new entry is a CI-only lock (not cited by any paper and not verified by a runtime harness), so the "two SHA256-locked pre-registrations" provenance descriptor of the published compendium in `README.md`, `STATUS.md`, `REVIEWER.md`, `PROBLEMS.md`, and the paper sources is intentionally left unchanged.
- **Manifest entry-count references bumped to 9,495** in `README.md`, `STATUS.md`, and `REVIEWER.md`, reflecting the three new tracked files above. `MANIFEST.sha256.json` regenerated via `python scripts/update_manifest.py` (9,492 -> 9,495: 130 real-file hashes, 9,365 LFS pointer stubs preserved, 0 missing, 0 mismatches). No existing result artifact is modified. The historical `[v1.5.x]` changelog entries that record earlier manifest counts are left unchanged.

## [v1.5.3] — 2026-07-30

Reproducibility-tooling hardening for the pooled-F1 provenance added in v1.5.2 (addresses automated-review feedback on PR #32 and PR #33). No paper, result, or conclusion change; all raw evidence cells (`data/cells/`) and every other result summary are byte-identical to v1.5.0 -- the sole exception is `data/results_summaries/pooled_f1_summary.json` itself, which this release deliberately expands (see below).

### Changed -- code/analyses/compute_pooled_f1.py
- The cross-check against the committed cascade cells is now **enforced**: if the reproduced cosine/Mahalanobis/learned/cascade pooled F1 drifts from the committed cascade evidence by more than 1e-3, the script aborts (previously it only printed a note, so a real pipeline drift could still pass). It also now aborts if fewer than the expected 72 cells actually matched committed cascade evidence (previously an empty/incomplete cascade directory would silently report zero drift without validating anything), and if any drift or cascade-vs-cosine penalty value is non-finite (previously a NaN could pass silently).
- The cross-check now compares **close/moderate/distant F1 as well as pooled** against the raw cascade cells (previously pooled-only, so a stratification regression could hide behind an unchanged whole-test-set aggregate).
- `--check` now **fails** if the committed `pooled_f1_summary.json` is missing, and verifies the regenerated cell set matches the committed one exactly (previously a missing file silently regenerated and passed, and dropped cells were skipped). The per-field tolerance is now applied per-metric (tight for cosine/mahalanobis/learned/cascade, looser only for Fisher-Rao's platform-sensitive LAPACK eigh) instead of one blanket tolerance for every metric, and rejects non-finite field drifts explicitly.
- Added the **cascade** metric so the script reproduces the Paper 2 Attempt-3 pooled-F1 penalty range (-0.046 to -0.236) cited in the v1.5.2 erratum, and prints that range. `pooled_f1_summary.json` expands from 72 to 90 cells (the 18 cascade cells).
- `np.load(..., allow_pickle=False)` for the cascade cells (they store only scalar/string arrays).
- **Cascade seed-set completeness is now validated**: `committed_cascade_pooled()` tracks the exact seeds found on disk per `(scale, R, k)` group and aborts before the expensive re-derivation if any group's seed set does not equal the 10 expected `SEEDS` exactly (previously the cross-check only counted matched `(scale, R, k, metric)` groups, so one missing seed file out of ten would still count as "matched" and silently average over fewer seeds).
- **Duplicate cascade seed files are now rejected**: filenames are tracked per `(scale, R, k, seed)` instead of just seed values, so a duplicate or misnamed file (e.g. zero-padded) that parses to an already-seen seed integer is caught explicitly, even though the seed-*set* completeness check alone cannot see it (the duplicate seed collapses into the set while its values still accumulate into the mean).
- **Exact cascade-file inventory gate**: before loading any cascade evidence, the new `cascade_inventory_mismatch()` compares the on-disk `cascade_*.npz` filename set (a raw string comparison, not the per-file regex parser) against the canonical 180-name grid and aborts on any missing or unexpected filename, printing both lists explicitly. This is full filename matching, not prefix matching: the per-file regex parser (`pat.match()`, which has no `$`/fullmatch anchor) would otherwise silently `continue` past a malformed or noncanonical name -- a stray suffix, a zero-padded duplicate, a typo -- that still matches the `cascade_*.npz` glob, leaving it invisible to every check below. The seed-completeness and duplicate-seed-file checks above are retained as defense in depth against a bug in this gate.
- **Embedded-identity cross-check**: each cascade cell's `(scale, R, k, seed)` fields, written by `run_cascade.py` alongside the F1 values, are now compared against the identity parsed from its filename; a mismatch (e.g. a file overwritten with another seed's payload) is rejected and excluded from the pooled means -- a case the inventory gate above cannot catch, since it only ever compares filenames, never file content.
- **Unexpected-group check**: a fully-populated, duplicate-free cascade group whose `(scale, R, k)` key falls outside the expected grid entirely is now rejected explicitly (also caught by the inventory gate above; retained as defense in depth).
- Corrected the `_doc` field written into `pooled_f1_summary.json`: it previously said only "cosine/mahalanobis/learned pooled cross-checked", omitting cascade and the close/moderate/distant fields the cross-check above actually covers; it now states accurately that cosine/mahalanobis/learned/cascade close/moderate/distant/pooled fields are all cross-checked within tolerance.
- Added `tests/test_pooled_f1_seed_integrity.py`: permanent regression coverage (synthetic fixtures, numpy-only, no LFS/faiss/torch required) for every check above, plus a real-data shape assertion (exactly 180 files across 18 groups, every check clean) that runs whenever the LFS payload is hydrated and skips cleanly otherwise. Real committed cascade evidence is exactly 180 files across 18 groups with zero duplicates, zero incomplete groups, zero unexpected groups, and zero embedded-identity mismatches.

### Changed -- reproduce.py
- The pooled check now also asserts the cascade penalty range (18 groups, all negative, bounded at both endpoints: min ~= -0.236, max ~= -0.046) against the exact expected pre-registered group set (3 scales x 3 panel sizes x 2 neighbor counts), and rejects non-finite penalty values.
- `--full` now **fails** (non-zero exit, no "COMPLETE" claim) if `faiss` is not importable, instead of silently skipping the bit-for-bit re-derivation and reporting that phase as passed. `--full` explicitly promises to re-derive the summary artifacts from committed evidence; being unable to do so is an incomplete reproduction, not a pass. Missing `torch` and an unhydrated Git-LFS payload were already handled correctly without a special case: `knn_learned`'s lazy `import torch` and `run_cliff.load_embeddings()`'s LFS-pointer-stub check both raise inside the re-derivation subprocesses this launches, which `_run()` already reports as FAIL via a non-zero exit code.
- **`mapper_augmentation_results.json`'s `--full` check is now field-aware instead of SHA256-identical.** A hydrated Windows/Python 3.13 `--full` run completed every computation correctly but failed on SHA256 mismatch: `results.uniform[2].close_f1` drifted by 6.1563885830229204e-05 from the Linux-committed value (FAISS/BLAS threshold behavior differs across platforms), while every seed, `n_dist`, `dist_f1`, and the rescue mean/CI were exactly identical and the Mapper H1 decision was unchanged -- a portability-only verification mismatch, not a computational one. The new `mapper_results_match()` requires exact schema/key sets, exact `R`/`k`/`scale`, exact arm names, exact result-list lengths, exact seed values *and ordering* (entries are compared positionally), exact `n_dist`, `dist_f1`/`rescue_mean`/`rescue_ci_lo`/`rescue_ci_hi` within 1e-12 (float round-trip noise only), and `close_f1` alone within 1e-4; any non-finite value anywhere a float comparison is expected fails outright. `calibration_results.json` is unchanged: still strict SHA256 byte-identity.
- **Both re-derived artifacts are now always restored to their committed bytes after `--full`'s comparison**, via a new `_preserved()` context manager, regardless of whether the comparison passed, failed, or raised, and regardless of whether the re-derivation subprocess itself crashed partway through a write. Previously a non-identical (but now potentially tolerance-passing, for Mapper) regenerated file could be left sitting in the working tree; `--full` must leave `git status` clean either way.
- Added `tests/test_reproduce_mapper_tolerance.py` (35 tests): the exact observed 6.156e-05 `close_f1` drift passing; a drift above 1e-4 failing; a boundary-exact 1e-4 drift passing; every structural/seed-ordering/`n_dist`/`dist_f1`/rescue-statistic/non-finite violation failing; and artifact restoration after a passing comparison, a failing comparison, a raised exception during comparison, and a crashed re-derivation subprocess.
- `_preserved()` also **removes** an artifact that did not exist on entry but was created inside its block (a re-derivation writing a fresh file when its committed copy is absent), rather than only restoring ones that already existed. Without this, `--full` run from a checkout missing one of the two committed artifacts would leave a new untracked file behind, making the "never leaves the working tree modified" contract only conditionally true; a clean checkout is unaffected either way, since both artifacts are committed.
- Two now-inaccurate labels corrected: the missing-`faiss` abort message no longer says "bit-for-bit re-derivation" (it is only bit-for-bit for calibration), and the reproduction-summary key is `--full artifact agreement` rather than `--full bit-for-bit`.

### Changed -- code/analyses/run_mapper_augmentation.py
- Writes `mapper_augmentation_results.json` with explicit `encoding='utf-8', newline='\n'` instead of the platform default, so a Windows re-derivation no longer emits CRLF line endings into a file whose committed form is LF. The committed artifact itself is unchanged by this fix -- only future re-derivations write consistently.

### Fixed — documentation consistency
- **Manifest entry-count references corrected to 9,490** in `README.md`, `STATUS.md`, and `REVIEWER.md`. The v1.5.2 release added two tracked artifacts (`code/analyses/compute_pooled_f1.py` and `data/results_summaries/pooled_f1_summary.json`), taking `MANIFEST.sha256.json` from 9,488 to 9,490 entries, but the current-state count in these three documents was not refreshed at the time. Verified with `python scripts/ci/verify_manifest.py` (9,490 entries: 125 real-file hashes matched, 9,365 LFS pointer stubs skipped, 0 missing, 0 mismatches). The historical v1.5.0/v1.5.1 changelog entries, which correctly record 9,488 for those releases, are left unchanged.
- **Paper 3 reference count corrected to 7** in the README `Honest limitations` section (was 8). `papers/03_calibration_collapse/paper.tex` cites seven unique references and the compiled `paper.pdf` bibliography contains seven entries; the same count method reproduces the stated 24/25/17/4 counts for Papers 1, 2, 4, and 5 exactly.
- **`code/kaggle_notebooks/adv_cell1_setup.py`: replaced the removed `Bio.SubsMat.MatrixInfo` import** with `Bio.Align.substitution_matrices`. `Bio.SubsMat` was deleted in Biopython 1.80 (2022), so the adversarial phase-2 scaffold would fail at import on any modern Biopython the cell installs. The replacement loads the same BLOSUM62 matrix via the current API; the returned `Array` supports `blosum62.get((a, b), default)` identically, so `adv_cell2_edits.py` is unchanged. Verified against Biopython 1.87 that the scaffold's exact `blosum62.get((a,b), blosum62.get((b,a), -99))` expression returns identical scores (A/R = -1, W/W = 11, symmetric, non-alphabet pairs hit the -99 default).
- **README read-order note corrected from "three additional rescues" to "four rescues"** (Paper 2 documents all four: Mahalanobis, Fisher-Rao, cascade, Mapper-augmentation), matching the paper's title and abstract. Added a note that the `papers/02_three_failed_rescues/` directory retains its original name (three rescues; a fourth was pre-registered and added later) as a stable identifier matching the archived Zenodo deposit.
- **Manifest entry-count references bumped again to 9,491** in `README.md`, `STATUS.md`, and `REVIEWER.md`, reflecting the addition of `tests/test_pooled_f1_seed_integrity.py` above.
- **`REVIEWER.md`'s documented `pytest tests/` totals corrected** from 40 passed (LFS) / 37 passed + 3 skipped (no LFS) to 53 passed (LFS) / 49 passed + 4 skipped (no LFS), reflecting the 13 tests `tests/test_pooled_f1_seed_integrity.py` now contains and its one LFS-conditional real-data test.
- **Release date corrected to 2026-07-30** in `CITATION.cff`, `codemeta.json`, `README.md`, `STATUS.md`, and this file's `[v1.5.3]` heading. The original 2026-06-16 date recorded when this release's first commit landed, not when its review-hardening was actually finished and the tree went final; `[v1.5.2]`'s own 2026-06-16 date is a distinct, earlier release and is unchanged.
- **This `[Unreleased]` section is now empty**: every entry that was sitting above the `[v1.5.3]` boundary while already being part of the released v1.5.3 tree (the four documentation-consistency fixes and the five `Changed` items below) has been moved into this section, where it belongs. Resolves the open PR #33 review thread on this exact inconsistency.
- **Manifest entry-count references bumped again to 9,492** in `README.md`, `STATUS.md`, and `REVIEWER.md`, reflecting the addition of `tests/test_reproduce_mapper_tolerance.py` above. `REVIEWER.md`'s documented `pytest tests/` totals corrected again, to 88 passed (LFS) / 84 passed + 4 skipped (no LFS); it also gains a new "Full single-command reproduction" section documenting the `--full` command and the Mapper field-aware-tolerance caveat below.
- **No document claims universal bit-for-bit identity for `mapper_augmentation_results.json` across platforms any more.** README.md's "Deterministic seeds" trust-architecture point now states that re-running is byte-identical on the *same* platform, and explains why `--full` checks Mapper field-aware instead of via SHA256 (cross-platform FAISS/BLAS drift in `close_f1`, bounded and documented, `dist_f1` and the rescue conclusion unaffected). `reproduce.py`'s module docstring, `--full`'s `--help` text, and `reproduce_full()`/`mapper_results_match()`'s docstrings were rewritten to match; none of them claimed this incorrectly before as a defect, `reproduce.py` simply enforced strict SHA256 identity for Mapper until this release, which is the behavior this round of hardening reconsiders in light of the real cross-platform run described above.

### Changed
- Refreshed stale current-version labels from `v1.5.0` to `v1.5.2`: the README `Honest limitations` opening line and the `STATUS.md` version header. Historical `v1.5.0` references that record when a specific item was resolved are unchanged.
- `.github/dependabot.yml`: moved the `pip` and `github-actions` update cadence from monthly to weekly and grouped each ecosystem's updates into a single batched PR (`groups: "*"`). Weekly cadence surfaces a CVE in the verification toolchain (which includes `pip-audit` and `bandit`) within a week rather than up to a month while the repository is under active external review; grouping matches the maintainer's existing practice of landing dependency bumps as one batch. No runtime dependency is added or unpinned; the GPU floors in `pyproject.toml` are untouched.
- `requirements-lock.txt`: `coverage` 7.14.3 -> 7.15.0, `ruff` 0.15.20 -> 0.15.21, `mypy` 2.1.0 -> 2.2.0 (Dependabot verification-toolchain group, PR #46). `MANIFEST.sha256.json` re-sealed to match (single entry, `requirements-lock.txt`; count unchanged at 9,490 at that time) -- Dependabot cannot run `scripts/update_manifest.py` itself, so its PRs always fail `manifest-verify` on the file they touch; this is the same land-manually-and-supersede pattern used for PRs #24-#30, #34-#40. Runtime pins (`numpy`, `scipy`, `scikit-learn`) and GPU floors are untouched. Re-validated against the new toolchain: `ruff check .`, `mypy` (--strict), `bandit`, `pip-audit` (0 known vulnerabilities), `pytest tests/` (37 passed / 3 skipped, coverage 15.91% > 15% floor), and `python reproduce.py` (all 7 phases pass, headline numbers unchanged) all green. Supersedes #46.
- `requirements-lock.txt`: `ruff` 0.15.21 -> 0.15.22, `mypy` 2.2.0 -> 2.3.0, `coverage` 7.15.0 -> 7.15.2 (Dependabot verification-toolchain group, PR #48). `MANIFEST.sha256.json` re-sealed to match (single entry, `requirements-lock.txt`; count unchanged at 9,490 at that time) -- Dependabot cannot run `scripts/update_manifest.py` itself, so its PRs always fail `manifest-verify` on the file they touch; this is the same land-manually-and-supersede pattern used for PRs #24-#30, #34-#40, #46. Runtime pins (`numpy`, `scipy`, `scikit-learn`) and GPU floors are untouched. Re-validated against the new toolchain: `ruff check .`, `mypy` (--strict), `bandit`, `pip-audit` (0 known vulnerabilities), `pytest tests/` (37 passed / 3 skipped, coverage 15.91% > 15% floor), and `python reproduce.py` (all 7 phases pass, headline numbers unchanged) all green. Supersedes #48.
- `version` 1.5.2 -> 1.5.3 (CITATION.cff, codemeta.json, README.md, pyproject.toml); `figures/cliff_summary.png` version label refreshed.
- `MANIFEST.sha256.json` regenerated a final time (9,492 entries) once every other edit in this release landed.

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
