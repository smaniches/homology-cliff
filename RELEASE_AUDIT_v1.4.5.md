# Release Audit: v1.4.5 — Blocker Verification

## Scope

Blocker verification before public adversarial-review outreach. No scientific
result changed. No experiments rerun. No tag created. No main push.

This audit is a verification pass against current `origin/main` (HEAD
`b38698b`, post-v1.4.4). Of the seven reviewer-facing blockers identified,
**two were addressed in v1.4.4**, **one is now treated as a residual
documentation clarification**, and **five remain open** for maintainer
decision.

### Reconciliation History

This audit was originally drafted against repository state at commit
`6d63798a` (v1.3.2 README commit, April 12, 2026). Between that draft and
this PR, `main` advanced through v1.4.3 and v1.4.4, with substantial fixes
shipped on April 26, 2026.

Of the seven blockers identified in the original audit:

- Blocker 1 (calibration artifact) was addressed in v1.4.4 (Defect W).
- Blocker 6 instance 1 (`run_cliff.py` docstring typo) was addressed in
  v1.4.4 (Defect X).
- Blocker 6 instance 2 is now treated as a residual documentation
  clarification, not as one of the five remaining blockers, because v1.4.4
  made `code/analyses/v3_aggregate.py` repo-relative and cross-platform.
  The remaining question is whether README wording should further qualify
  expected output and LFS requirements.
- Five blockers remain open against current `origin/main` `b38698b` and are
  documented below as maintainer-decision pending: B2, B3, B4, B5, and B7.

This audit therefore serves as a forward-looking reconciliation record
rather than a complete pre-public-release blocker list.

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
| 1 | Calibration artifact/script mismatch | **ADDRESSED IN v1.4.4** |
| 2 | Precision/recall schema overclaim | **STILL OPEN — maintainer-decision pending** |
| 3 | Stale full-null / chance-F1 wording | **STILL OPEN — maintainer-decision pending** |
| 4 | Mapper augmentation truncated membership | **STILL OPEN — maintainer-decision pending** |
| 5 | Missing PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md | **STILL OPEN — maintainer-decision pending** |
| 6 | Reviewer-facing CLI commands that do not match | **ADDRESSED IN v1.4.4 (instance 1) / RESIDUAL DOCUMENTATION CLARIFICATION (instance 2)** |
| 7 | Dataset label-rule auditability overclaim | **STILL OPEN — maintainer-decision pending** |

Five-blocker open count (excluding the v1.4.4-addressed and the residual
documentation clarification): B2, B3, B4, B5, B7.

---

### Blocker 1: Calibration artifact/script mismatch

**Status:** ADDRESSED IN v1.4.4 (Defect W).

**Evidence on origin/main `b38698b`:**

- `CHANGELOG.md` v1.4.4 entry, line 14: "Calibration script — figure binning
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

**Status:** STILL OPEN — maintainer-decision pending.

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

**Fix path:** Maintainer decision pending (see S2 in Maintainer-Decision
Blocks below).

**Committed in this PR:** None.

---

### Blocker 3: Stale full-null / chance-F1 wording

**Status:** STILL OPEN — maintainer-decision pending.

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

**Fix path:** Maintainer decision pending (see S3 in Maintainer-Decision
Blocks below).

**Committed in this PR:** None.

---

### Blocker 4: Mapper augmentation using truncated node membership

**Status:** STILL OPEN — maintainer-decision pending.

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

**Fix path:** Maintainer decision pending (see S4 in Maintainer-Decision
Blocks below).

**Committed in this PR:** None.

---

### Blocker 5: Missing PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md

**Status:** STILL OPEN — maintainer-decision pending.

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

**Fix path:** Maintainer decision pending (see S5 in Maintainer-Decision
Blocks below). Creating a post-hoc pre-registration file is forbidden.

**Committed in this PR:** None.

---

### Blocker 6: Reviewer-facing CLI commands that do not match

**Status:** ADDRESSED IN v1.4.4 (instance 1) / RESIDUAL DOCUMENTATION
CLARIFICATION (instance 2).

**Evidence on origin/main `b38698b`:**

Instance 1 — ADDRESSED IN v1.4.4:
- `code/harnesses/run_cliff.py:21` (docstring): `python run_cliff.py --negative-control`
- argparse flag matches docstring.
- The CHANGELOG v1.4.4 entry "`run_cliff.py` factorial-cell-count docstring
  fix (Defect X)" reflects the broader v1.4.4 docstring overhaul; the
  `--negative-control-only` typo is no longer present.
- **No action needed in this PR for Instance 1.**

Instance 2 — RESIDUAL DOCUMENTATION CLARIFICATION (follow-up wording
decision pending):
- `README.md` advertises `python code/analyses/v3_aggregate.py` as a
  reproducibility recipe step.
- `code/analyses/v3_aggregate.py` was refactored to repo-relative paths
  in v1.4.4 (Defect R/T/U), so the script now runs cross-platform.
- The remaining question is whether README wording should further qualify
  expected output and LFS requirements (e.g., "regenerates the headline
  numbers table" presumes LFS-pulled cells).
- This is a documentation-wording question, not a code question. It is
  excluded from the five-open-blockers count.

**Fix path (Instance 1):** Already done upstream. **No action.**

**Fix path (Instance 2):** Maintainer decision pending (see S6 in
Maintainer-Decision Blocks below). The hard scope of v1.4.5 forbids
README edits; this is flagged for a follow-up PR.

**Committed in this PR:** None.

---

### Blocker 7: Dataset label-rule auditability overclaim

**Status:** STILL OPEN — maintainer-decision pending.

**Evidence on origin/main `b38698b`:**

- `README.md:39`: "Every number in every paper has an artifact on disk."
- `DATA_CARD.md` acknowledges that the label-curation rule is held as
  TOPOLOGICA internal per Urbina et al. 2022 dual-use guidance.
- Recent commit on origin/main `b38698b` ("fix: stale numbers in README
  trust statement") addressed adjacent issues but did not qualify the
  label-rule auditability claim.

**Impact:** The README's auditability promise is unconditional in the
relevant section, but the most fundamental input to the experimental
pipeline — the label-curation rule — is explicitly withheld. Reviewers
will note this contradiction.

**Fix path:** Maintainer decision pending (see S7 in Maintainer-Decision
Blocks below).

**Committed in this PR:** None.

---

## Maintainer-Decision Blocks

Maintainer-decision options are documented inline in this audit file and
will be summarized in the PR body. The audit file is the canonical
reference for option text; the PR body cross-references it.

### S1: Calibration artifact policy

S1: Calibration artifact policy — RESOLVED IN v1.4.4 (Defect W). No
further action required from this PR.

---

### S2: Precision/recall schema policy

**Addresses:** Blocker 2.

**Current evidence:** `code/harnesses/run_cliff.py:124–125` declares the
fields; lines 451–454 always set them to `float("nan")` with a TODO
comment at line 452. `tests/test_cell_schema.py` does not validate them.

**Candidate fix paths:**

- **Option 2A — remove fields from schema** in a future code/schema PR.
  Trade-off: cleanest match between schema and reality. Cost: requires a
  separate code-changing PR (out of v1.4.5 scope), and would technically
  alter the future `.npz` write contract (existing committed cells already
  have the NaN fields and remain unchanged).
- **Option 2B — document precision/recall as intentionally unpopulated/NaN**
  in current committed cells, via a comment at `run_cliff.py:124–125`,
  the `# TODO` at line 452, and a note in `PROBLEMS.md`. Trade-off: zero
  schema risk, lowest-friction fix; preserves the placeholder for a future
  populated-fields PR. Cost: schema "fields exist but are NaN" remains
  technically true but is now explicitly disclosed.
- **Option 2C — compute precision/recall in the harness.**
  **Forbidden in v1.4.5; requires explicit maintainer approval** because
  it changes future output semantics (newly-written cells would carry
  populated values; older committed cells would not, creating a
  pre/post-fix discontinuity).

**Recommendation:** Option 2B is the lowest-friction, in-scope-style fix
for a follow-up documentation PR, paired with eventually scheduling 2A or
2C as a separate decision.

---

### S3: Full-null / chance-F1 wording

**Addresses:** Blocker 3.

**Current evidence:** `code/analyses/v3_aggregate.py:39` prints "Should
ALL be near 0.5 per addendum pre-reg if cliff is real." The addendum's
operationalized criterion is gap-near-zero across 10 seeds (lines 47–50);
actual full-null F1 collapses toward 0, not toward 0.5. The pre-reg files
themselves are SHA256-locked and cannot be edited (harness-verified at
`run_cliff.py:135–159`).

**Candidate fix paths:**

- **Option 3A — replace the print statement** at `v3_aggregate.py:39`
  with wording that matches the operationalized criterion and repository
  terminology. In-scope as a documentation-style code change in a
  follow-up PR. Does not modify any SHA256-locked pre-registration file.
- **Option 3B — leave unchanged and add a `PROBLEMS.md` note** explaining
  the inherited 0.5 framing. Lower-friction but leaves the misleading
  print intact.

**Recommendation:** Option 3A. The pre-reg file remains untouched; only
the downstream aggregator text is corrected.

[PROPOSED-WORDING-PENDING-APPROVAL]

Replacement for `code/analyses/v3_aggregate.py:39`:

`print("   Per addendum pre-reg, operationalized criterion is gap-near-zero across 10 seeds; per-stratum F1 collapses toward 0 under full-pool permutation, not toward 0.5 (the 0.5 framing was inherited from the deprecated v1 panel-shuffle null).")`

[/PROPOSED-WORDING-PENDING-APPROVAL]

---

### S4: Mapper augmentation truncation

**Addresses:** Blocker 4.

**Current evidence:** `code/analyses/run_mapper.py:67` truncates per-node
member lists to 50 (`members[:50]`). The downstream
`run_mapper_augmentation.py` therefore samples from a 50-per-node pool
rather than from full positive-enriched neighborhoods. Paper 2 abstract
item (iv) and `README.md` `rescues_rejected` cite the +0.0018 / CI
[−0.027, +0.029] result as a pre-registered rejection.

**Candidate fix paths:**

- **Option 4A — rerun Mapper augmentation with full membership.**
  Requires removing the `[:50]` cap, regenerating `mapper_graph.json`
  (~1–2 min CPU, needs LFS-pulled embeddings), and re-running
  `run_mapper_augmentation.py` (10 seeds × 2 panels). The H1 result MAY
  change. **Out of v1.4.5 scope; requires explicit maintainer approval.**
  Trade-off: preserves the strong "pre-registered rejection of panel
  augmentation" framing if confirmed, at the cost of new experiment time
  and risk that the result flips.
- **Option 4B — downgrade Mapper augmentation claim to exploratory.**
  Documentation only. Updates Paper 2 abstract item (iv), the README
  machine-readable index `rescues_rejected` list, and
  `run_mapper_augmentation.py:13`'s pre-reg reference (overlaps with S5).
  Trade-off: faster and safer; reframes the result as exploratory under a
  truncated input rather than a pre-registered rejection. Weakens the
  "panel augmentation cannot rescue" framing slightly but matches the
  reproducibility evidence on disk.

**Recommendation:** Option 4B for v1.4.5-style follow-up; 4A only if the
maintainer wants to preserve the strong rejection claim and is willing to
authorize a new-experiment PR.

[PROPOSED-WORDING-PENDING-APPROVAL]

Paper 2 abstract item (iv) replacement:

`(iv) A Mapper-biased panel drawn from positive-enriched topological regions of the upstream Mapper graph (per-node member lists truncated to 50 by the graph generator at code/analyses/run_mapper.py:67; see RELEASE_AUDIT_v1.4.5.md Blocker 4) yields a distant-F1 rescue of +0.0018, 95% CI [-0.027, +0.029], consistent with no rescue under the truncated input. We treat this as exploratory rather than as a pre-registered rejection of panel augmentation; rerunning under full membership is deferred.`

README machine-readable index update (line range containing
`rescues_rejected`):

`"rescues_rejected": ["mahalanobis", "fisher_rao", "cascade"],
"rescues_exploratory_inconclusive_under_truncation": ["mapper_augmentation"],`

[/PROPOSED-WORDING-PENDING-APPROVAL]

---

### S5: Missing Mapper preregistration file

**Addresses:** Blocker 5.

**Current evidence:** `run_mapper_augmentation.py:13` references
`PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md`, which is absent from
`data/prereg/` and from `MANIFEST.sha256.json`. Paper 2 abstract claims
"We pre-register and reject four"; line 19 narrows the SHA256-lock claim
to Mahalanobis and cascade only.

**Candidate fix paths:**

- **Option 5A — locate and commit a genuine pre-existing preregistration
  file** if and only if it verifiably existed before execution (e.g., in
  a TOPOLOGICA private archive with a pre-experiment timestamp). If
  located, place it in `data/prereg/` and add to `MANIFEST.sha256.json`.
- **Option 5B — reframe Mapper augmentation as exploratory or
  non-preregistered.** Documentation only. Updates
  `run_mapper_augmentation.py:13`, Paper 2 abstract phrase "pre-register
  and reject four", and any other reference. Overlaps with S4 Option 4B.
- **FORBIDDEN — fabricate a post-hoc preregistration file.** Creating a
  new file claiming to have been locked before execution is explicitly
  not an option.

**Recommendation:** Option 5B unless 5A's pre-existing file can be
verified.

[PROPOSED-WORDING-PENDING-APPROVAL]

`code/analyses/run_mapper_augmentation.py:13` replacement (under S5
Option 5B):

`Exploratory analysis (no pre-registration; complements Paper 5 Mapper topology).`

Paper 2 abstract first sentence replacement (under S5 Option 5B,
overlapping with S4 Option 4B):

`We pre-register and reject three (Mahalanobis, Fisher-Rao, cascade) and run one exploratory test (Mapper augmentation) which is also negative under the truncated input documented in RELEASE_AUDIT_v1.4.5.md Blocker 4.`

[/PROPOSED-WORDING-PENDING-APPROVAL]

---

### S6: README v3_aggregate.py recipe — residual documentation clarification

**Addresses:** Blocker 6 instance 2. **Classification: residual
documentation clarification, not one of the five open blockers.**

**Current evidence:** v1.4.4 made `code/analyses/v3_aggregate.py`
repo-relative and cross-platform; the script now runs from a clean clone
on Linux/macOS/Windows. `README.md` advertises it as a 15-minute
reproducibility step but does not explicitly state that the headline
numbers regeneration requires LFS-pulled `.npz` cells.

**Candidate fix paths:**

- **Option 6A — qualify the README recipe** with a one-line note that
  `git lfs pull` is required for `v3_aggregate.py` to produce non-empty
  output. Documentation only. Deferred to a follow-up README PR
  (this PR forbids README edits).
- **Option 6B — leave unchanged.** The existing recipe also says
  `git lfs pull` earlier in the same block; the v3_aggregate.py
  qualification is implicit.

**Recommendation:** Option 6A in a follow-up PR.

[PROPOSED-WORDING-PENDING-APPROVAL]

For a future README follow-up PR, suffix the
`python code/analyses/v3_aggregate.py` line in the 15-minute recipe with:

`(requires `git lfs pull` to have completed; otherwise the .npz cells
are LFS-pointer placeholders and the regeneration is empty)`

[/PROPOSED-WORDING-PENDING-APPROVAL]

---

### S7: Dataset label-rule auditability wording

**Addresses:** Blocker 7.

**Current evidence:** `README.md:39` claims "Every number in every paper
has an artifact on disk." The label-curation rule is held as TOPOLOGICA
internal per Urbina et al. 2022 dual-use guidance, per `DATA_CARD.md`.
The auditability promise at line 39 is unconditional and conflicts with
the disclosed opacity of the upstream label rule.

**Candidate fix paths:**

- **Option 7A — soften the auditability claim** at `README.md:39` to
  acknowledge that auditability is conditional on trusting the committed
  labels. Documentation only. Deferred to a follow-up README PR (this
  PR forbids README edits).
- **Option 7B — leave unchanged.** The "Honest limitations" section of
  the README and `DATA_CARD.md` already disclose the gap; reviewers can
  reconcile.

**Recommendation:** Option 7A in a follow-up PR.

[PROPOSED-WORDING-PENDING-APPROVAL]

For a future README follow-up PR, replace the final sentence of
`README.md:39` ("Every number in every paper has an artifact on disk.")
with:

`Every numeric claim in every paper is reproducible from a committed artifact on disk, conditional on the committed labels being trusted. The label-curation rule that maps UniProt entries to positive/negative is held as TOPOLOGICA internal per Urbina et al. 2022 dual-use guidance (see DATA_CARD.md and PROBLEMS.md); independent re-derivation requires an approved researcher applying their own curation.`

[/PROPOSED-WORDING-PENDING-APPROVAL]

---

### S8: Fisher-Rao docstring/implementation discrepancy

S8: Fisher-Rao docstring/implementation discrepancy — tracked separately,
not touched in this PR.

---

## What Was Committed

1. `RELEASE_AUDIT_v1.4.5.md` (this file) — new file in this PR.
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

## Maintainer-Decision Options Location

Maintainer-decision options are documented in this audit file (see the
Maintainer-Decision Blocks section above) and will be summarized in the
PR body. This audit file is the canonical reference for option text; the
PR body cross-references it.

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
