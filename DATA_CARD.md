# Data Card: Homology Cliff 25k Protein Test Set

**Dataset name:** working ID `experiment2_proteins_25k_filtered`; shipped as `data/sequences/proteins_25k_sequences.json`
**Version:** v1.0 (April 2026)
**Maintainer:** Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
**License:** UniProt-sourced accessions and sequences are redistributed under UniProt terms (CC-BY-4.0 for UniProt data, 2026).

## Composition
- **Size:** 24,885 proteins
- **Class balance:** 7,133 positive (28.7%) / 17,752 negative (71.3%)
- **Source:** UniProtKB Swiss-Prot (reviewed) entries, filtered for biosecurity-relevant categories
- **Sequence length distribution:** median 344 aa, max truncated to 1022 for ESM-2 compatibility
- **Redundancy:** Each accession distinct at primary UniProt ID level; no explicit CD-HIT pre-clustering

## Annotations
- **Pfam coverage:** 21,615 / 24,885 (86.9%) via UniProt ID-mapping + search batch-50 (April 12, 2026)
- **Organism / taxonomy:** committed with Pfam annotations
- **Positive label source:** curated biosecurity-relevance list; exact curation rule documented in TOPOLOGICA internal registry

## Collection
- UniProt programmatic REST API, April 2026
- Accessions retrieved as primary IDs; secondary/obsolete IDs excluded
- Sequences retrieved as canonical FASTA

## Intended use
- Benchmarking frozen protein language model retrieval at biosecurity-relevant scale
- Pre-registered factorial experiments on metric selection and panel composition
- NOT intended as a deployment-grade biosecurity classifier training set

## Known limitations
- 28.7% positive prior does not reflect real-world screening distributions (which are far more imbalanced)
- Label curation rule is TOPOLOGICA internal and not published alongside the data
- 13.1% of accessions lack Pfam annotations; partition analyses exclude these
- Single-chain proteins only; multi-domain behavior not tested
- Redundancy filter relies on UniProt's built-in Swiss-Prot curation, not explicit sequence identity clustering

## Ethical considerations (dual-use)
Following Urbina et al. 2022 on AI-powered drug discovery dual-use concerns, we redistribute public-domain UniProt accessions and sequences only. We do not publish the label curation rule that identifies toxin-relevant proteins from the general UniProt pool; the curation logic is a TOPOLOGICA internal artifact. This restricts downstream misuse while preserving reproducibility for approved researchers who can apply their own curation.

## Public vs. withheld (external verifiability boundary)

| Component | Public? | Externally verifiable? | Notes |
|---|---|---|---|
| Protein accessions and sequences | Yes | Yes | Redistributed from UniProt (CC-BY-4.0) |
| Binary labels (positive/negative) | Yes | Conditional | Labels are committed; the curation rule that produced them is withheld |
| Label-curation rule | **No** | **No** | Held as TOPOLOGICA internal per Urbina et al. 2022 dual-use guidance |
| ESM-2 embeddings (t6/t12/t30) | Yes | Yes | Reproducible from sequences using open-weights ESM-2 |
| Pfam annotations | Yes | Yes | Retrievable from UniProt ID-mapping API |
| Per-cell .npz results (9,360 cells) | Yes | Yes | Reproducible from embeddings + labels using committed harness code |
| Aggregate JSON summaries | Yes | Yes | Reproducible from per-cell .npz files using committed analysis scripts |
| Pre-registration files | Yes | Yes (hash-locked) | SHA256 verified by CI and by harness at runtime |
| SHA256 manifest | Yes | Yes | Verified by CI on every push |

**Which claims require trust in the committed labels:**

All claims about absolute F1, precision, ECE values, and the cross-family partition depend on the committed labels being correct. The label-curation rule is not published; a reviewer who does not trust the labels can still verify:
- That the .npz schema and cell counts are correct
- That the full-null permutation eliminates the gap (labels permuted, geometric stratification preserved)
- That the aggregation arithmetic is correct from cells to tables
- That the pre-registration hashes match
- That the cross-family partition logic is correct given Pfam annotations

An independent researcher who applies their own curation rule to the same UniProt accessions can reproduce the entire methodology on their own labeled set. See `SECURITY.md` for the dual-use rationale.

## Files in this repository
- `data/sequences/proteins_25k_sequences.json` (8.2 MB) — accessions, sequences, lengths, labels
- `data/annotations/proteins_25k_pfam.json` (13.5 MB) — Pfam IDs, organism, lineage, taxonomy
- `data/embeddings/embeddings_t6.npy` (30.4 MB), `embeddings_t12.npy` (45.6 MB), `embeddings_t30.npy` (60.8 MB) — ESM-2 mean-pooled L2-normalized embeddings
