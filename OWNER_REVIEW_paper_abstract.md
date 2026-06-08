# Owner review: Paper 1 abstract overclaim lives only in the archived PDF

**Status:** FLAG ONLY. No source file was edited to produce this note, and no
release/DOI was cut. This is a hand-off for the owner, who is the only one who
should touch `papers/**/paper.tex` and re-archive the DOI'd artifact.

**Scope:** `papers/01_homology_cliff_and_rescue/` (Paper 1, "The Homology Cliff
in Frozen ESM-2 Biosecurity Retrieval", April 12 2026, v1.1).

---

## 1. The pre-registration-count overclaim (primary)

### Where it stands now

The LaTeX **source** on `main` is already correct. It was fixed in commit
`d7e156b` (PR #18, "paper.tex 'four SHA256-locked' -> two"):

- `paper.tex:15` (abstract close):
  > "...four pre-registrations (two SHA256-locked and automatically re-verified),
  > and full code under MIT + CC-BY-4.0."
- `paper.tex:175` (Reproducibility):
  > "Four pre-registrations (two SHA256-locked and automatically re-verified),
  > 9,360 per-cell .npz results..."

This wording is accurate: of the four pre-registrations, only two are
SHA256-locked and CI-verified. `scripts/ci/verify_prereg_locks.py` enforces
exactly those two (`PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md` and
`PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md`); the cascade and
Fisher pre-registrations are committed without a hash claimed in any abstract.

### The remaining problem

The **compiled, DOI-archived PDF** (`papers/01_homology_cliff_and_rescue/paper.pdf`)
still renders the OLD, incorrect text. The PDF predates the source fix and was
not rebuilt (commit #18's own note: "the compiled paper.pdf still renders the
old text; rebuild at next release"). The PDF is the durable, citable artifact,
so the overclaim is still live for anyone who reads the archived copy.

Exact quotes from the current PDF (extracted via `pdftotext -layout`):

- Abstract close:
  > "We release 9,360 per-cell bootstrap-CI results, **four SHA256-locked
  > pre-registrations**, and full code under MIT + CC-BY-4.0."
- Section 11 (Reproducibility):
  > "Code MIT, papers CC-BY-4.0. **Four SHA256-locked pre-registrations**,
  > 9,360 per-cell .npz results with 10k-resample bootstrap CIs per stratum
  > per cell..."

**The issue:** "four SHA256-locked pre-registrations" asserts that all four
registrations carry a SHA256 lock. Only two do. Read literally it overstates
the cryptographic-integrity guarantee by 2x.

**Recommended honest wording** (already present in the source `.tex`; just needs
to reach the PDF):

> "...four pre-registrations (two SHA256-locked and automatically re-verified)..."

**Owner action:** rebuild `paper.pdf` from the corrected `.tex` and re-archive
the new PDF to Zenodo as a new version under the existing concept DOI. No
source edit is required — the `.tex` is already right.

---

## 2. Related PDF-vs-source drifts in the same abstract (secondary)

The same stale PDF also lags two other numbers that the `.tex` source on `main`
has already corrected (so a single rebuild fixes all of them at once):

| Claim | Stale PDF text | Corrected `.tex` on main | Evidence |
|---|---|---|---|
| Learned-projection win count | "wins pooled F1 in **18 of 18** factorial groups" | "wins pooled F1 in 16 of 18 factorial groups (12 of 12 at t12 and t30...)" | CLAIMS_TO_EVIDENCE #11 reproduces 16/18 from `data/cells/cascade/` |
| Distant-F1 relative improvement | "improving distant-stratum F1 by **48%** relative" | "improving distant-stratum F1 by 47% relative" | CLAIMS_TO_EVIDENCE #12 reproduces +47.1% (rounds to 47%) |

Both corrected values are the ones backed by the committed cells; the PDF's
18/18 and 48% are not reproducible from the released artifacts. Same fix:
rebuild and re-archive.

---

## 3. Cross-paper consistency flag (Paper 4, optional)

`papers/04_methods_and_preregistrations/paper.tex:11` reads:

> "Four pre-registrations with SHA256 locks (main SHA256 139f6012..., full-pool
> addendum f3864d09..., cascade, Fisher) committed before execution."

Read as a list, this can be taken to mean all four carry SHA256 locks, when only
the first two do (the cascade and Fisher are named but have no abstract-cited
hash and are not enforced by `verify_prereg_locks.py`). This is the same factual
point as item 1, on a different surface. The owner may want to align Paper 4's
phrasing with Paper 1's accurate "(two SHA256-locked...)" wording at the next
rebuild. Lower priority: Paper 4 is methods-only and less likely to be the
DOI-cited number.

---

## What was NOT done here (by design)

- No edit to any `papers/**/paper.tex` (owner-only; actively under edit).
- No edit to `FAQ.md`.
- No PDF rebuild, no Zenodo deposit, no new tag/DOI.
- No honest caveat removed anywhere.

The reproducibility-script and documentation fixes that accompany this note
(CRLF-robust pre-registration verifier, hardened LFS-stub detection in
`v3_aggregate.py`, two corrected commands in `docs/CLAIMS_TO_EVIDENCE.md`, and a
README link to that file) are in the same branch and do not touch any paper
source.
