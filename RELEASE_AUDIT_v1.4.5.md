# Release Audit: v1.4.5 — Blocker Verification

## Scope

Blocker verification before public adversarial-review outreach. No scientific
result changed. No experiments rerun. No tag created. No main push.

This audit is a verification pass against current `origin/main` (HEAD
`b38698b`, post-v1.4.4). Of the seven reviewer-facing blockers identified,
**two were already fixed in v1.4.4** and **five remain open** for maintainer
decision.

## Verification Date

2026-05-07

## Branch

`v1.4.5/blocker-verification` (created from `origin/main`)

## Base Commit

`b38698b` (origin/main HEAD: "fix: stale numbers in README trust statement")

## Pre-Registration Integrity Check

Both SHA256-locked pre-registration files verified against on-disk content:

- `data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md`:
  `139f60129d4e73dfb13444c360cc80c5b48c217d9bc87b1bf4b48b06515bcc06` —
  matches `PREREG_HASH` constant at `code/harnesses/run_cliff.py:51`.
- `data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md`:
  `f3864d097a0c611d790e6fb15a42e7efb36b2d1b103be4ec1c4f28f99d1004dc` —
  matches reference in addendum line 6 and Paper 1 text.

---

## Blockers Audited (Reconciled Against origin/main b38698b)

### Summary Table

| # | Blocker | Status against origin/main |
|---|---|---|
| 1 | Calibration artifact/script mismatch | **ALREADY FIXED in v1.4.4** |
| 2 | Precision/recall schema overclaim | **STILL OPEN** — maintainer-decision pending |
| 3 | Stale full-null / chance-F1 wording | **STILL OPEN** — maintainer-decision pending |
| 4 | Mapper augmentation truncated membership | **STILL OPEN** — maintainer-decision pending |
| 5 | Missing PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md | **STILL OPEN** — maintainer-decision pending |
| 6 | Reviewer-facing CLI commands that do not match | **PARTIALLY FIXED** — instance 1 already done; instance 2 still open |
| 7 | Dataset label-rule auditability overclaim | **STILL OPEN** — maintainer-decision pending |

---

### Blocker 1: Calibration artifact/script mismatch

**Status:** ALREADY FIXED in v1.4.4 (Defect W).

**Evidence on origin/main `b38698b`:**

- `CHANGELOG.md` v1.4.4 entry, line 14: "Calibration script - figure binning
  reconciliation (Defect W): `run_calibration.py` rewritten to use the six
  unequal-width bins shown in Paper 3's published figure ... Output
  `data/results_summaries/calibration_results.json` now contains the
  per-stratum reliability table, ECE values, and positive-prediction
  precision counts that Paper 3 cites — previously these numbers lived only
  in Paper 3's prose."
- `data/results_summaries/calibration_results.json` is now committed.
- `code/analyses/run_calibration.py` now writes the JSON artifact.

**Action required:** None. Closing the blocker in this audit.

**Committed in this PR:** None.

---

### Blocker 2: Precision/recall schema overclaim

**Status:** STILL OPEN. Maintainer-decision pending.

**Evidence on origin/main `b38698b`:**

- `code/harnesses/run_cliff.py:124–125` declares `precision: float` and
  `recall: float` in the `StratumResult` dataclass.
- `code/harnesses/run_cliff.py:451–454` always sets both to `float("nan")`
  with comment `# TODO: add precision_recall_ci helper` (line 452).
- `tests/test_cell_schema.py` validates `n`, `f1`, `f1_ci_lo`, `f1_ci_hi`
  but does NOT validate `precision` or `recall` fields.

**Impact:** The `.npz` cell schema declares fields that are never populated.
Downstream consumers who trust the schema find only NaN. The test suite
does not catch this discrepancy.

**Fix path:** Maintainer decision pending (see PR body for options 2A/2B).

**Committed in this PR:** None.

---

### Blocker 3: Stale full-null / chance-F1 wording

**Status:** STILL OPEN. Maintainer-decision pending.

**Evidence on origin/main `b38698b`:**

- `code/analyses/v3_aggregate.py:39` prints:
  `"Should ALL be near 0.5 per addendum pre-reg if cliff is real."`
- Actual full-null F1 values are ~0.015–0.025 across strata (not ~0.5).
  Under full-pool label permutation the classifier has no signal; F1
  collapses toward 0, not toward 0.5.
- The addendum pre-reg's *operationalized* criterion
  (`PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md:47–50`) is:
  "the full-null gap's 95% bootstrap CI across 10 seeds includes zero."
  The data satisfies this criterion (300/300 groups pass).
- The "0.5" wording is inherited from the deprecated v1 panel-shuffle null
  criterion (`PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md:59`). The addendum
  itself (lines 14–16) describes this original criterion as "in direct
  violation of the stated criterion."
- Pre-reg files cannot be edited: SHA256-locked, harness-verified at
  `run_cliff.py:135–159`, aborts on hash mismatch.

**Fix path:** Maintainer decision pending (see PR body for proposed wording
for `v3_aggregate.py:39`).

**Committed in this PR:** None.

---

### Blocker 4: Mapper augmentation using truncated node membership

**Status:** STILL OPEN. Maintainer-decision pending.

**Evidence on origin/main `b38698b`:**

- `code/analyses/run_mapper.py:67`:
  `'members': members[:50]  # cap to keep JSON small`
- `code/analyses/run_mapper_augmentation.py` reads from these truncated
  lists in `data/results_summaries/mapper_graph.json`.
- The buggy print statement in `run_mapper_augmentation.py` was fixed in
  v1.4.4 (CHANGELOG line 15), but the underlying *truncation* of node
  membership in the upstream Mapper graph itself is unchanged.
- The pre-registered H1 rejection (rescue +0.0018, CI [−0.027, +0.029])
  is cited in:
  - Paper 2 abstract item (iv).
  - `README.md` machine-readable index `rescues_rejected:
    [..., "mapper_augmentation"]`.

**Impact:** The "biased pool" was not drawn from the full positive-enriched
neighborhoods but from a 50-per-node truncated sample. The H1 rejection may
be invalid if the full membership would have produced a different result.

**Fix path:** Maintainer decision pending (see PR body for Mapper-A rerun
vs Mapper-B exploratory downgrade). Both options involve scientific framing
changes and are not committed in this PR.

**Committed in this PR:** None.

---

### Blocker 5: Missing PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md

**Status:** STILL OPEN. Maintainer-decision pending.

**Evidence on origin/main `b38698b`:**

- `code/analyses/run_mapper_augmentation.py:13`:
  `Pre-reg: PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md`
- `data/prereg/` directory listing on `origin/main` does NOT contain
  `PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md`.
- `MANIFEST.sha256.json` does not list this file.
- Paper 2 abstract states "We pre-register and reject four." Paper 2 line 19
  narrows the explicit SHA256-lock claim to "Pre-registrations for
  Mahalanobis and cascade locked via SHA256 before execution." The Mapper
  augmentation is not among those explicitly claimed as SHA256-locked.

**Fix path:** Maintainer decision pending (see PR body for options 5A locate
vs 5B reframe). Creating a post-hoc pre-registration file is forbidden.

**Committed in this PR:** None.

---

### Blocker 6: Reviewer-facing CLI commands that do not match

**Status:** PARTIALLY FIXED.

**Evidence on origin/main `b38698b`:**

Instance 1 (already fixed in v1.4.4):
- `code/harnesses/run_cliff.py:21` (docstring): `python run_cliff.py --negative-control`
- argparse flag matches docstring.
- The CHANGELOG v1.4.4 entry "`run_cliff.py` factorial-cell-count docstring
  fix (Defect X)" reflects the broader v1.4.4 docstring overhaul; the
  `--negative-control-only` typo is no longer present.
- **No action needed in this PR for Instance 1.**

Instance 2 (still open):
- `README.md` advertises `python code/analyses/v3_aggregate.py` as a
  reproducibility recipe step.
- `code/analyses/v3_aggregate.py` was refactored to repo-relative paths
  in v1.4.4 (Defect R/T/U), so the script now runs cross-platform.
  However, the README's wording around this command and its expected
  output may still need a minor clarification depending on whether
  the maintainer wants to qualify what "regenerates the headline numbers
  table" means in the absence of LFS-pulled cells.
- This is a documentation-wording question, not a code question.

**Fix path (Instance 1):** Already done upstream. **No action.**

**Fix path (Instance 2):** Maintainer decision pending. The hard scope of
v1.4.5 forbids README edits; this is flagged for a follow-up PR.

**Committed in this PR:** None.

---

### Blocker 7: Dataset label-rule auditability overclaim

**Status:** STILL OPEN. Maintainer-decision pending.

**Evidence on origin/main `b38698b`:**

- `README.md:39` (or equivalent — origin/main has been edited but the
  unconditional auditability claim wording remains): "Every number in every
  paper has an artifact on disk."
- `DATA_CARD.md` acknowledges that the label-curation rule is held as
  TOPOLOGICA internal per Urbina et al. 2022 dual-use guidance.
- Recent commit on origin/main `b38698b` ("fix: stale numbers in README
  trust statement") addressed adjacent issues but did not qualify the
  label-rule auditability claim.

**Impact:** The README's auditability promise is unconditional in the
relevant section, but the most fundamental input to the experimental
pipeline — the label-curation rule — is explicitly withheld. Reviewers
will note this contradiction.

**Fix path:** Maintainer decision pending (see PR body for proposed
softened wording).

**Committed in this PR:** None.

---

## What Was Committed

1. `RELEASE_AUDIT_v1.4.5.md` (this file) — new file.
2. `CHANGELOG.md` — appended `[v1.4.5]` section under the existing
   Keep-A-Changelog format. The pre-existing v1.0.x–v1.4.4 entries are
   not modified.

## What Was NOT Committed

- `code/harnesses/run_cliff.py` was NOT edited. The `--negative-control-only`
  docstring typo was already fixed upstream in v1.4.4. The previously-staged
  one-line docstring fix is therefore redundant and was dropped.
- No edits to README.md, DATA_CARD.md, PROBLEMS.md, papers, tests, workflows,
  MANIFEST.sha256.json, pyproject.toml, CITATION.cff, codemeta.json, or any
  analysis script.
- No path-portability changes (already done in v1.4.4).
- No code-behavior changes.

## What Was Staged in PR Body for Maintainer Approval

- S2: Blocker 2 precision/recall schema policy (options 2A/2B).
- S3: Blocker 3 proposed wording for `v3_aggregate.py:39`.
- S4: Blocker 4 Mapper rerun (4A) vs exploratory downgrade (4B).
- S5: Blocker 5 locate pre-reg file (5A) vs reframe (5B).
- S6: Blocker 6 instance 2 — proposed wording for the README
  `v3_aggregate.py` reproducibility recipe (deferred to follow-up PR per
  v1.4.5 hard limits).
- S7: Blocker 7 proposed wording softening at README's auditability claim
  (deferred to follow-up PR per v1.4.5 hard limits).
- S8: Fisher-Rao docstring/implementation discrepancy from prior audit; not
  touched in this PR; tracked separately.

## LFS-Dependent Validation

LFS-dependent validation was not completed in this session. CI may not
fully validate LFS-dependent artifacts unless Git LFS checkout/pull is
configured. This PR does not claim full artifact validation.

## What Was Not Done

- No tag (no `v1.4.5` git tag, no any tag).
- No main-branch push.
- No GitHub Release.
- No Zenodo deposit or DOI-triggering action.
- No paper edits, no paper consolidation, no paper moves.
- No edits to `papers/01_*/paper.tex` through `papers/05_*/paper.tex`.
- No README edits.
- No DATA_CARD edits.
- No PROBLEMS edits.
- No metadata edits (`pyproject.toml`, `CITATION.cff`, `codemeta.json`).
- No `MANIFEST.sha256.json` update.
- No CI / workflow / LFS-config changes.
- No path-portability changes.
- No code-behavior changes.
- No new experiments or harness reruns.
- No fabricated or post-hoc preregistration files.
- No unilateral scientific-judgment calls.
