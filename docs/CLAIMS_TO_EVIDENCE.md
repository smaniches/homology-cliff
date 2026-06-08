# Claims to Evidence

Systematic traceability from every headline number in the compendium to its
committed artifact, reproducing command, and limitations.

**Maintainer:** Santiago Maniches (ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987)), TOPOLOGICA LLC.

## How to use this document

Each entry maps a claim made in the README or papers to:
1. The artifact file(s) on disk that constitute the evidence
2. A command to reproduce or verify the number
3. The expected output (with tolerance where applicable)
4. Any caveat or limitation

All paths are repo-relative. All commands assume a fresh clone with
`git lfs pull` completed unless noted otherwise.

---

## Headline Numbers (from README Machine-Readable Index)

### 1. cliff_gap_t30_R1000_k25_cosine = 0.745

| Field | Value |
|---|---|
| Claim | Close-distant F1 gap of +0.745 at ESM-2 t30, R=1000, k=25, cosine metric |
| Papers | Paper 1 abstract and Section 3 |
| Source artifact | `data/cells/main/cell_t30_1000_25_cosine_*.npz` (10 seeds, 20260410-20260419) |
| Aggregate artifact | `data/results_summaries/v3_final.txt` (MAIN gap table, row t30/1000/25/cosine) |
| Reproducing command | `python -c "import numpy as np; d=np.load('data/cells/main/cell_t30_1000_25_cosine_20260410.npz', allow_pickle=True); print('close F1:', d['close'].item()['f1'], 'distant F1:', d['distant'].item()['f1'])"` |
| Expected output | close F1 approximately 0.866, distant F1 approximately 0.120; gap approximately 0.745 |
| Tolerance | The 0.745 is the 10-seed group mean. Individual seeds vary within the bootstrap CI stored in each .npz. |
| Requires LFS | Yes |

### 2. learned_projection_pooled_f1_t30 = 0.891

| Field | Value |
|---|---|
| Claim | Learned linear projection achieves pooled F1 of 0.891 at t30 |
| Papers | Paper 1 abstract, Section 4 |
| Source artifact | `data/cells/cascade/cascade_t30_1000_25_*.npz` (10 seeds), field `learned_pooled_f1` (the global confusion-matrix F1; the per-stratum `data/cells/main/*` cells do not store a pooled value) |
| Reproducing command | `python -c "import numpy as np, glob; fs=sorted(glob.glob('data/cells/cascade/cascade_t30_1000_25_*.npz')); assert fs, 'Git LFS files not pulled - run: git lfs pull'; vals=[float(np.load(f, allow_pickle=True)['learned_pooled_f1']) for f in fs]; print(f'pooled F1 (10-seed mean): {sum(vals)/len(vals):.4f}')"` |
| Expected output | pooled F1 (10-seed mean): 0.8905 |
| Tolerance | 0.8905 is the 10-seed group mean; individual seeds vary within the stored bootstrap CI |
| Requires LFS | Yes |

### 3. distant_precision_t30_cosine = 0.068

| Field | Value |
|---|---|
| Claim | Positive-prediction precision in the distant stratum is 3/44 = 0.068 |
| Papers | Paper 3, Section 2 |
| Source artifact | `data/results_summaries/calibration_results.json` |
| Reproducing command | `python -c "import json; d=json.load(open('data/results_summaries/calibration_results.json')); pp=d['distant']['positive_prediction']; print(f\"tp={pp['tp']} n={pp['n_predicted_positive']} precision={pp['precision']}\")"` |
| Expected output | tp=3, n_predicted_positive=44, precision=0.068 |
| Tolerance | Exact (single seed 20260410, deterministic) |
| Requires LFS | No |

### 4. ECE_close = 0.069

| Field | Value |
|---|---|
| Claim | Expected Calibration Error on the close stratum is 0.069 |
| Papers | Paper 3, abstract and Section 2 |
| Source artifact | `data/results_summaries/calibration_results.json` |
| Reproducing command | `python -c "import json; d=json.load(open('data/results_summaries/calibration_results.json')); print('ECE close:', d['close']['ECE'])"` |
| Expected output | ECE close: 0.069 |
| Tolerance | Exact from committed artifact |
| Requires LFS | No |

### 5. ECE_distant = 0.294

| Field | Value |
|---|---|
| Claim | Expected Calibration Error on the distant stratum is 0.294 |
| Papers | Paper 3, abstract and Section 2 |
| Source artifact | `data/results_summaries/calibration_results.json` |
| Reproducing command | `python -c "import json; d=json.load(open('data/results_summaries/calibration_results.json')); print('ECE distant:', d['distant']['ECE'])"` |
| Expected output | ECE distant: 0.294 |
| Tolerance | Exact from committed artifact |
| Requires LFS | No |

### 6. ECE ratio close-to-distant = 4.3x

| Field | Value |
|---|---|
| Claim | ECE rises 4.3x from close to distant stratum |
| Papers | Paper 3 abstract; README figure caption |
| Source artifact | `data/results_summaries/calibration_results.json` |
| Reproducing command | `python -c "import json; d=json.load(open('data/results_summaries/calibration_results.json')); print(f\"ratio: {d['ece_distant_to_close_ratio']:.2f}x\")"` |
| Expected output | ratio: 4.26x (reported as approximately 4.3x) |
| Tolerance | Rounded to one decimal place in papers |
| Requires LFS | No |

### 7. fullnull_groups_passing_criterion = 300/300

| Field | Value |
|---|---|
| Claim | All 300 full-pool permutation null groups pass the gap-near-zero criterion |
| Papers | Paper 1, Section 3.2 |
| Source artifact | 3,000 .npz files in `data/cells/fullnull/` |
| Aggregate artifact | `data/results_summaries/v3_final.txt` (FULL-NULL table) |
| Reproducing command | Group count: `python code/analyses/v3_aggregate.py 2>/dev/null \| grep "^fullnull groups:"`. Gap-near-zero criterion: `pytest tests/test_cell_schema.py::test_fullnull_gap_near_zero -v` (requires LFS). |
| Expected output | `fullnull groups: 300  cells: 3000`, and the pytest passes (every fullnull group's mean gap is near zero). |
| Tolerance | Per addendum pre-registration: 95% bootstrap CI on the 10-seed mean gap includes zero |
| Requires LFS | Yes (for individual cell verification) |

### 8. main_groups_passing_seed_variance_gate = 300/300

| Field | Value |
|---|---|
| Claim | All 300 main factorial groups pass the seed-variance gate |
| Papers | Paper 1, Section 3.1; Paper 4, Section 2 |
| Source artifact | `data/results_summaries/v3_final.txt` (MAIN gap table, "up" column) |
| Reproducing command | `python code/analyses/v3_aggregate.py 2>/dev/null \| awk '/=== MAIN gap table/{f=1;next} /^=== /{f=0} f && /^t[0-9]/{print $NF}' \| sort -u` (scopes to the MAIN gap table, whose last column is the per-group "up" count; a bare `grep "^t[0-9]"` also matches the FULL-NULL and NEGATIVE CONTROL tables, whose last columns are not the up count) |
| Expected output | `0` (the only distinct value; every one of the 300 main groups has up=0) |
| Requires LFS | Yes |

### 9. cross_family_fraction = 20/20

| Field | Value |
|---|---|
| Claim | 20 of 20 evaluable distant false alarms are cross-family (zero Pfam overlap) |
| Papers | Paper 5, abstract and Section 2 |
| Source artifact | `data/results_summaries/cross_family_partition.json` |
| Reproducing command | `python -c "import json; d=json.load(open('data/results_summaries/cross_family_partition.json')); print(f\"within={d['within_family']} cross={d['cross_family']} evaluable={d['n_evaluable']}\")"` |
| Expected output | within=0 cross=20 evaluable=20 |
| Tolerance | Exact (single seed 20260410, deterministic) |
| Limitation | Analyzed at one seed only; 10-seed extension deferred. 21 of 41 distant FPs lack Pfam annotation on query or voters, hence n_evaluable=20 not 41. |
| Requires LFS | No |

### 10. rescues_rejected: Mahalanobis, Fisher-Rao, cascade, Mapper augmentation

| Field | Value |
|---|---|
| Claim | Four rescue hypotheses pre-registered and rejected at H1 |
| Papers | Paper 2 (all four); Paper 1 Section 4 (Mahalanobis) |
| Source artifacts | `data/cells/cascade/` (180 .npz), `data/cells/fisher/` (180 .npz), `data/results_summaries/mapper_augmentation_results.json` |
| Limitation (Mapper) | Mapper augmentation used truncated node membership (50 per node); see `.github/RELEASE_AUDIT_v1.4.5.md` Blocker 4. The missing `PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md` is documented in Blocker 5. |
| Limitation (Mahalanobis/Fisher) | SHA256-locked pre-registrations exist only for the main cliff and full-null; cascade and Fisher pre-registrations are committed but without hashes claimed in paper abstracts. |
| Requires LFS | Yes (for per-cell verification of cascade/fisher) |

### 11. rescues_accepted: learned linear projection (panel-only)

| Field | Value |
|---|---|
| Claim | Learned projection wins pooled F1 in 16 of 18 factorial groups (12/12 at t12 and t30; the two misses are at the smallest t6/8M scale at k=5) |
| Papers | Paper 1, Section 4; MODEL_CARD.md |
| Source artifact | `data/cells/cascade/cascade_*.npz` (3 scales x 6 (R,k) pairs x 10 seeds), fields `learned_pooled_f1` and `cosine_pooled_f1` (global confusion-matrix F1; the per-stratum `data/cells/main/*` cells do not store a pooled value) |
| Reproducing command | `python -c "import numpy as np, glob, collections; files=glob.glob('data/cells/cascade/cascade_*.npz'); assert files, 'Git LFS files not pulled - run: git lfs pull'; g=collections.defaultdict(lambda:[[],[]]); [ (lambda d: (g[(str(d['scale']),int(d['R']),int(d['k']))][0].append(float(d['learned_pooled_f1'])), g[(str(d['scale']),int(d['R']),int(d['k']))][1].append(float(d['cosine_pooled_f1']))))(np.load(f, allow_pickle=True)) for f in files]; wins=sum(1 for k in g if np.mean(g[k][0])>np.mean(g[k][1])); print(f'learned wins {wins}/{len(g)} groups')"` |
| Expected output | learned wins 16/18 groups |
| Tolerance | "16/18" means: for each of the 18 (scale, R, k) groups, the 10-seed mean of `learned_pooled_f1` exceeds the 10-seed mean of `cosine_pooled_f1`. The two non-winning groups (cosine higher) are t6 R=100 k=5 (0.8200 vs 0.8262) and t6 R=1000 k=5 (0.8773 vs 0.8792). |
| Requires LFS | Yes |

### 12. Distant F1 relative improvement 47% at t30

| Field | Value |
|---|---|
| Claim | Learned projection improves distant-stratum F1 by 47% relative at t30 R=1000 k=25 |
| Papers | Paper 1 abstract, Section 4, figure caption; README body; MODEL_CARD.md; docs/index.html |
| Source artifact | `data/cells/cascade/cascade_t30_1000_25_*.npz`, fields `learned_dist_f1` and `cosine_dist_f1` |
| Reproducing command | `python -c "import numpy as np, glob; fs=sorted(glob.glob('data/cells/cascade/cascade_t30_1000_25_*.npz')); L=np.mean([float(np.load(f, allow_pickle=True)['learned_dist_f1']) for f in fs]); C=np.mean([float(np.load(f, allow_pickle=True)['cosine_dist_f1']) for f in fs]); print(f'learned={L:.4f} cosine={C:.4f} relative=+{100*(L-C)/C:.1f}%')"` |
| Computation | Full-precision 10-seed means: learned distant F1 = 0.1770, cosine distant F1 = 0.1203; (0.1770 - 0.1203) / 0.1203 = 0.471, i.e. 47.1% relative, reported as 47%. |
| Note | The rounded table values (0.177, 0.120) give 47.5%; the full-precision committed value is 47.1%. All artifacts state 47%. |

---

## Pre-Registration Integrity

| File | Expected SHA256 | CI-verified | Verify command |
|---|---|---|---|
| `data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md` | `139f60129d4e73df...` | Yes | `python scripts/ci/verify_prereg_locks.py` |
| `data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md` | `f3864d097a0c611d...` | Yes | `python scripts/ci/verify_prereg_locks.py` |
| `data/prereg/PRE_REGISTRATION_STRATIFIED_CASCADE_v1.md` | Not hash-locked in CI | No | File committed; no runtime hash check |
| `data/prereg/PRE_REGISTRATION_FISHER_CLIFF_v1.md` | Not hash-locked in CI | No | File committed; no runtime hash check |

---

## Limitations of This Traceability

1. **Label-curation rule withheld.** The rule that maps UniProt entries to
   positive/negative is held as TOPOLOGICA internal per Urbina et al. 2022
   dual-use guidance. All claims are verifiable conditional on trusting the
   committed labels. See `DATA_CARD.md` and `SECURITY.md`.

2. **Pre-registration lock-time.** The SHA256 hashes prove byte-identity
   with the locked file, but the absolute claim "locked before experiments
   ran" depends on trusting the git history. An external timestamp anchor
   (e.g., OpenTimestamps) is listed as deferred in `PROBLEMS.md`.

3. **Mapper augmentation truncation.** The Mapper graph generator truncates
   per-node member lists to 50 (`code/analyses/run_mapper.py:67`). The
   downstream augmentation test used this truncated pool. See
   `.github/RELEASE_AUDIT_v1.4.5.md` Blocker 4.

4. **Missing Mapper pre-registration.** `run_mapper_augmentation.py`
   references `PRE_REGISTRATION_MAPPER_AUGMENTATION_v1.md` which is absent
   from `data/prereg/`. See `.github/RELEASE_AUDIT_v1.4.5.md` Blocker 5.

5. **Cross-family partition at one seed.** The 20/20 result is from seed
   20260410 only. A 10-seed extension is deferred.

6. **Precision/recall fields.** The .npz schema declares precision and
   recall fields but they are always NaN in committed cells. See
   `.github/RELEASE_AUDIT_v1.4.5.md` Blocker 2.
