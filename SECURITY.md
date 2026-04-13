# Security and Dual-Use Policy

This repository documents a failure mode of frozen protein language model retrieval on biosecurity-relevant proteins. The underlying dataset contains toxin-labeled protein sequences. Responsible disclosure and dual-use awareness are explicit obligations here.

**Maintainer:** Santiago Maniches, Independent Researcher, TOPOLOGICA LLC (solo research lab). ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987).

## Reporting a security or biosecurity concern

If you identify any of the following, **do not open a public issue**. Contact santiago at topologica dot ai directly:

- A leak of the label-curation rule that could enable untrained users to generate new toxin-label training sets
- An attack that uses this compendium's findings to evade a biosecurity screen in a way not already discussed in the papers
- A deployment mistake that could cause a real biosecurity screen to be miscalibrated against novel threats
- Any reproducibility result that contradicts a paper claim in a way that has safety implications

Disclosure timeline: I will acknowledge within 5 business days and work toward public disclosure or mitigation within 90 days unless the concern warrants faster or slower action. Coordinated disclosure is preferred over immediate public disclosure.

## Dual-use statement

This compendium follows the spirit of [Urbina et al. 2022, *Dual use of artificial-intelligence-powered drug discovery*](https://www.nature.com/articles/s42256-022-00465-9):

1. **Sequences and accessions are redistributed** under UniProt terms. They are already publicly available from UniProt.
2. **Pfam annotations are redistributed** as they are publicly available.
3. **Embeddings are redistributed** because frozen ESM-2 is open-weights and any competent researcher can reproduce them from sequences in ~8 hours of GPU time.
4. **The label curation rule is NOT published.** Which proteins are labeled positive (toxin-relevant) vs negative was decided via a TOPOLOGICA internal procedure. That procedure is not in this repository. A researcher with their own curation rule can reproduce the methodology on their own labeled set; a bad actor wanting to bypass a screen cannot easily recreate the label set from this repository alone.

## What this repository is NOT

- Not a biosecurity screening system
- Not a trained toxin classifier ready for deployment
- Not a guide to evading biosecurity filters
- Not an inventory of toxins or their mechanisms

## What this repository IS

- A characterization of a failure mode in frozen PLM retrieval
- Evidence that panel expansion cannot rescue the failure (Paper 5)
- Evidence that one cheap projection-based intervention can partially rescue it (Paper 1)
- A call to route distant-stratum positive predictions to human review regardless of metric (Papers 3 and 5)

## Legitimate researcher access

Academic and industrial researchers working on PLM retrieval, biosecurity screening, or metric learning are welcome to use this compendium under CC-BY-4.0 (papers) and MIT (code). Cite as in `CITATION.cff`.

Institutional review board or biosecurity review board reviewers: feel free to contact the maintainer with questions about the label curation rule under appropriate confidentiality.
