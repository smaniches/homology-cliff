# Homology Cliff in Frozen Protein Language Models — Research Compendium

**Author:** Santiago Maniches (ORCID: [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987))
**Affiliation:** TOPOLOGICA LLC
**Date:** April 12, 2026
**License:** Papers under CC BY 4.0, code under MIT. See `LICENSE-papers.txt` and `LICENSE-code.txt`.

## What this is

A five-paper research compendium characterizing the **homology cliff** in frozen ESM-2 biosecurity-relevant retrieval: a systematic F₁ collapse on test proteins distant in embedding space from the reference panel. All five papers share a single 24,885-protein test set, a single factorial harness, and four pre-registered experiments with SHA256 hash locks.

## The papers

| # | Title | Kind | Claim |
|---|---|---|---|
| 1 | **Homology Cliff and Its Rescue** | Main | Cliff confirmed across 3000 cells; not a stratification artifact (3000-cell full-null). A cheap panel-only learned projection rescues it (+48% distant F₁ at t30). |
| 2 | **Three Failed Rescue Attempts** | Null-results companion | Mahalanobis, Fisher-Rao, stratified cascade, and Mapper-biased panel augmentation all fail to rescue. |
| 3 | **Calibration Collapse** | Short report | ECE rises 4× from close (0.069) to distant (0.294); distant positive-prediction precision is 0.068 (3 true positives of 44 predictions). |
| 4 | **Methods & Pre-Registrations** | Methods paper | Documents the 4000-cell factorial harness, four pre-registrations (SHA256 locked), seed-variance gate, reproducibility infrastructure. |
| 5 | **Cross-Family Partition & Mapper Topology** | Topology paper | 149 Mapper nodes, 6 all-positive; positive class spatially localized. Pfam-partitioned distant-stratum analysis (pending full Pfam coverage). |

## Headline numbers

- Cliff at t30 R=1000 k=25 cosine: close F₁ = 0.866, distant F₁ = 0.120, gap = +0.745
- Full-null criterion passed: 300 of 300 groups, gap ∈ [−0.027, +0.038], CI includes zero
- Learned projection wins 18/18 factorial groups; t30 pooled F₁ = 0.891 (best in factorial)
- Distant-stratum positive-prediction precision under cosine: 0.068 (3/44)
- Mahalanobis, Fisher, cascade, Mapper-augmentation: all rejected at H1

## Pre-registrations (SHA256 locked)

- `PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md` — hash `139f60129d4e73df…` (main factorial)
- `PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md` — hash `f3864d097a0c611d…` (full-pool permutation null)
- `PRE_REGISTRATION_STRATIFIED_CASCADE_v1.md` (cascade rescue)
- `PRE_REGISTRATION_FISHER_CLIFF_v1.md` (Fisher whitening rescue)

## Reproducing

All 9,360 per-cell `.npz` results are on local disk (not committed, too large). See `reproducibility/PROTOCOL.md` for the exact execution order. Total compute: ~28 hours on a single 36 GB i7 CPU with FAISS; no GPU needed for the main experiments. GPU is needed only for the PLM benchmark extension (Colab notebook in `code/colab_notebook/`).

## Repo layout

```
homology_cliff_repo/
├── README.md                 (this file)
├── LICENSE-papers.txt        CC-BY-4.0
├── LICENSE-code.txt          MIT
├── papers/
│   ├── references.bib
│   ├── 01_homology_cliff_and_rescue/
│   ├── 02_three_failed_rescues/
│   ├── 03_calibration_collapse/
│   ├── 04_methods_and_preregistrations/
│   └── 05_cross_family_and_mapper/
├── code/
│   ├── harnesses/            run_cliff.py, run_cliff_fullnull.py, run_cascade.py, run_fisher.py
│   ├── analyses/             calibration, mapper, adversarial, aggregation
│   ├── kaggle_notebooks/     alternative GPU cells
│   └── colab_notebook/       ipynb for PLM benchmark extension
├── data/
│   ├── prereg/               four pre-registrations with SHA256
│   └── results_summaries/    JSON + text summaries of all 9,360 per-cell outputs
└── reproducibility/
    └── PROTOCOL.md           exact re-run instructions
```

## Citation

```
@software{maniches_homology_cliff_2026,
  author = {Maniches, Santiago},
  title = {Homology Cliff in Frozen Protein Language Models: Research Compendium},
  year = {2026}, month = {4},
  orcid = {0009-0005-6480-1987},
  url = {https://github.com/USER/homology_cliff_repo}
}
```
