# Compendium Verification Status

Current state of the homology-cliff research compendium.

**Version:** v1.5.3  
**Last updated:** 2026-07-30  
**Maintainer:** Santiago Maniches (ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)), TOPOLOGICA LLC.

---

## Verified by CI (every push)

| Check | Workflow | What it verifies |
|---|---|---|
| Manifest integrity | `manifest.yml` | All non-LFS file hashes match `MANIFEST.sha256.json` (9,495 entries total; LFS pointer stubs skipped) |
| Pre-registration locks | `manifest.yml` | 2 SHA256-locked pre-reg files are byte-identical to their locked state |
| Cell filename inventory | `tests.yml` | 9,360 .npz filenames present (3000 main + 3000 negctrl + 3000 fullnull + 180 cascade + 180 fisher) |
| Smoke imports | `smoke.yml` | All harnesses and analysis scripts import without error on a fresh clone |
| No hardcoded Windows paths | `smoke.yml` | No `C:\TOPOLOGICA_BIOSECURITY` references remain in `code/` |
| Evidence spot-checks | `evidence.yml` | Headline numbers from committed JSON summaries match expected values |
| Paper PDF existence | `evidence.yml` | All 5 paper PDFs exist on disk |

## Verified by local tests (requires `git lfs pull`)

| Check | Command | What it verifies |
|---|---|---|
| Cell schema | `pytest tests/ -v` | .npz files have correct `{cell, shuffle, close, moderate, distant}` schema with required keys `n, f1, f1_ci_lo, f1_ci_hi` per stratum |
| Full-null gap near zero | `pytest tests/ -v` | Sampled fullnull cells have close-distant gap indistinguishable from zero |
| Main cliff gap substantial | `pytest tests/ -v` | Sampled main cosine cells have close-distant gap materially above 0.2 |

## Requires GPU (not verified in CI or local tests)

| Extension | Scaffold | Status |
|---|---|---|
| PLM benchmark (ProtT5, SaProt, ESM-2 t33) | `code/colab_notebook/plm_benchmark.ipynb` | Not executed; awaiting GPU time |
| Adversarial phase 2 (BLOSUM-guided edits) | `code/kaggle_notebooks/adv_cell*.py` | Not executed; awaiting GPU time |
| Stratification threshold sensitivity sweep | Pre-registered but not scaffolded | Not executed |

## Open items from v1.4.5 audit

Documented in `.github/RELEASE_AUDIT_v1.4.5.md`. The documentation-only
blockers are addressed in the changelog; the scientific item (B4) is now
**resolved in v1.5.0** — the robustness harness was executed and the Mapper
rejection holds under full node membership (see the B4 row below and
`docs/MAPPER_AUGMENTATION_ROBUSTNESS.md`).

| # | Issue | Category | Status |
|---|---|---|---|
| B2 | Precision/recall fields in .npz schema always NaN | Schema | **Addressed** — disclosed at the `StratumResult` declaration and `PROBLEMS.md` item 11 as intentionally unpopulated; only F1 + bootstrap CI are pre-registered |
| B3 | "near 0.5" wording in `v3_aggregate.py` print statement | Wording | **Fixed** — banner now states the gap-near-zero criterion and that F1 collapses toward 0 under full-pool permutation |
| B4 | Mapper augmentation uses truncated node membership (50/node) | Scientific | **Resolved (v1.5.0)** — robustness harness executed: under a common-stratification control the full-membership "rescue" collapses to ≈0 (it was a stratification artifact), so the Attempt-4 null holds. A biased-panel deduplication defect was also fixed (rescue +0.0018 → −0.0080; 95% CI still includes zero; H1 still rejected). The prose-vs-script discrepancy is recorded in the Paper 2 erratum. See `docs/MAPPER_AUGMENTATION_ROBUSTNESS.md` |
| B5 | Missing `PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md` | Provenance | **Fixed** — docstring no longer references the non-existent file; states accurate provenance (no dedicated SHA256 lock; only Mahalanobis + cascade are locked) |
| B6 | README `v3_aggregate.py` recipe did not flag LFS requirement | Wording | **Fixed** — recipe step now notes `git lfs pull` is required |
| B7 | README label-rule auditability wording | Wording | **Fixed** — auditability claim now explicitly conditional on trusting the withheld label-curation rule |

## Not yet independently validated

- No third-party replication report has been filed
- No OpenTimestamps or other external timestamp proof on pre-registration files (SHA256 hash integrity is verified; absolute lock-time relies on git history)
- Cross-family Pfam partition analyzed at one seed only (20260410); 10-seed extension deferred
- Learned-projection calibration under the projection not measured
- No external PLM comparison completed (ProtT5, SaProt, ESM-3 deferred)

## Claim precision conventions used in this compendium

| Term | Meaning |
|---|---|
| "tested" | Experimental result committed as .npz with bootstrap CI |
| "reproduced" | Verified by re-running from committed artifacts; hash-stable |
| "benchmarked" | Compared across a systematic factorial with pre-committed parameters |
| "experimentally observed" | Measured in committed cells; not yet independently replicated |
| "not yet independently validated" | No third-party replication |
| "research prototype" | Code runs and produces correct results but is not production-hardened |
| "pre-registered" | Hypothesis and success criterion committed (as text file) before experiment; SHA256-locked where noted |
