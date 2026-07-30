# Reviewer Quick-Start Guide

Five commands to verify the compendium's central claims, plus one optional
full single-command reproduction. Estimated time: 15 minutes (clone + LFS
pull + tests), plus 2-10 minutes per spot-check.

**Maintainer:** Santiago Maniches (ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)), TOPOLOGICA LLC.

---

## 1. Clone and verify integrity

```bash
git clone https://github.com/smaniches/homology-cliff.git
cd homology-cliff
git lfs pull                              # ~188 MB of binary evidence
pip install numpy scipy scikit-learn pytest

python scripts/ci/verify_manifest.py      # 9,492 manifest entries
python scripts/ci/verify_prereg_locks.py  # 2 SHA256-locked pre-registrations
```

Expected: all manifest entries verified (0 missing, 0 mismatches); both
pre-registration hashes match.

## 2. Run tests

```bash
pytest tests/ -v
```

Expected with LFS pulled: 84 passed, 0 failed. Without LFS: 80 passed,
4 skipped (three data-dependent cell tests in `test_cell_schema.py` plus
one real-cascade-evidence shape test in `test_pooled_f1_seed_integrity.py`
skip cleanly when the relevant .npz files are LFS pointer stubs; every
other test, including the verifier, cell-inventory, and the synthetic-
fixture cascade seed-integrity tests, does not need LFS payload).

## 3. Reproduce the headline cliff gap

```bash
python -c "
import numpy as np
d = np.load('data/cells/main/cell_t30_1000_25_cosine_20260410.npz', allow_pickle=True)
c, di = d['close'].item(), d['distant'].item()
print(f\"close F1: {c['f1']:.3f}  distant F1: {di['f1']:.3f}  gap: {c['f1']-di['f1']:.3f}\")
"
```

Expected: close F1 approximately 0.866, distant F1 approximately 0.120,
gap approximately 0.745. Paper 1 reports +0.745 as the 10-seed group mean.

## 4. Verify the full-null passes

```bash
python -c "
import numpy as np
d = np.load('data/cells/fullnull/fullnull_t30_1000_25_cosine_20260410.npz', allow_pickle=True)
gap = d['close'].item()['f1'] - d['distant'].item()['f1']
print(f'full-null gap: {gap:.4f}  (should be near zero)')
"
```

Expected: gap near zero (magnitude less than 0.05). The full-pool
permutation null randomizes labels across all 24,885 proteins; the
close-distant gap should vanish.

## 5. Regenerate the aggregate table

```bash
python code/analyses/v3_aggregate.py | head -80
```

Expected: 300 main groups, 300 negctrl groups, 300 fullnull groups. The
MAIN gap table shows the cliff growing with model scale and panel size.

## 6. Full single-command reproduction (optional; needs LFS + faiss)

```bash
python reproduce.py --full
```

Re-runs everything above plus a bit-for-bit re-derivation of the two summary
artifacts that depend on the k-NN + bootstrap pipeline. `calibration_results.json`
must be exactly byte-identical (SHA256) to the committed file. **This is not
true of `mapper_augmentation_results.json` across platforms**: FAISS/BLAS
threshold behavior can produce bounded floating-point drift in its contextual
`close_f1` values between platforms -- observed once at 6.156e-05 on a
Windows/Python 3.13 run against a Linux-committed artifact -- so it is instead
checked field-aware (exact schema, seeds, seed ordering, n_dist, `dist_f1`,
and rescue mean/CI to 1e-12; `close_f1` alone to 1e-4; see `reproduce.py`'s
`mapper_results_match()`). A drift within tolerance is expected and does not
indicate a problem; either way, the regenerated file is restored to its
committed bytes afterward, so `git status` should be empty when `--full`
finishes regardless of outcome.

---

## Verify headline numbers without LFS

These checks use committed JSON summary files (not LFS-tracked):

```bash
# ECE and calibration (Paper 3):
python -c "import json; d=json.load(open('data/results_summaries/calibration_results.json')); print(f\"ECE close={d['close']['ECE']} distant={d['distant']['ECE']} ratio={d['ece_distant_to_close_ratio']:.2f}x\")"

# Cross-family partition (Paper 5):
python -c "import json; d=json.load(open('data/results_summaries/cross_family_partition.json')); print(f\"within={d['within_family']} cross={d['cross_family']} evaluable={d['n_evaluable']}\")"
```

---

## Where to look for deeper verification

| Document | What it covers |
|---|---|
| `docs/CLAIMS_TO_EVIDENCE.md` | Every headline number mapped to artifact, command, and tolerance |
| `PROBLEMS.md` | Self-audited errors and corrections |
| `STATUS.md` | Current verification state and open items |
| `.github/RELEASE_AUDIT_v1.4.5.md` | Five open blockers with proposed resolutions |
| `DATA_CARD.md` | Dataset provenance, public vs. withheld boundary |
| `MODEL_CARD.md` | Learned projection deployment scope and limitations |
| `SECURITY.md` | Dual-use policy and biosecurity disclosure process |
| `REFEREES.md` | Self-adversarial review passes per paper |

## What is externally verifiable vs. trust-dependent

| Layer | Verifiable? | How |
|---|---|---|
| Cell .npz schema and counts | Yes | `pytest tests/` |
| SHA256 manifest integrity | Yes | `python scripts/ci/verify_manifest.py` |
| Pre-registration hash locks | Yes | `python scripts/ci/verify_prereg_locks.py` |
| Headline numbers from cells | Yes (requires LFS) | Commands above |
| Aggregate statistics | Yes (requires LFS) | `python code/analyses/v3_aggregate.py` |
| Calibration and cross-family JSON | Yes (no LFS needed) | JSON spot-checks above |
| Label-curation rule | Trust-dependent | Held per dual-use guidance; see `DATA_CARD.md` |
| Pre-registration lock-time | Trust-dependent | Git history; no external timestamp anchor yet |

## Contact

Santiago Maniches · santiago at topologica dot ai · ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)
