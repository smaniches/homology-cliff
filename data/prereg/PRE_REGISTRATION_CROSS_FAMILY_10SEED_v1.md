# PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md

**Author:** Santiago Maniches (ORCID 0009-0005-6480-1987)
**Status:** Pre-registered. Locked BEFORE any additional panel seed is run. Hash computed at end of file and stored in the companion `.sha256`. Any byte-level edit after hashing voids the registration.
**Relationship to prior work:** CONFIRMATORY robustness extension of the existing single-seed cross-family Pfam partition analysis in `code/analyses/run_cross_family_partition.py`, whose result is committed at `data/results_summaries/cross_family_partition.json` (seed 20260410: 41 distant false positives, 20 evaluable, within_family = 0, cross_family = 20). This document does not introduce a new model, metric, threshold, neighbor count, annotation source, or family ontology. It only asks whether that single-seed observation survives changes to reference-panel composition across the ten already-fixed panel seeds. No existing result artifact is modified by this registration, and `cross_family_partition.json` is left byte-identical.

## Lock timestamp

Recorded immediately before the SHA256 hash of this document was computed, so that the public git commit timestamp cannot introduce date ambiguity:

- **Local:** 2026-08-18 01:49:08 (timezone Etc/UTC, UTC+0000)
- **UTC:** 2026-08-18T01:49:08Z

The lock environment's local timezone is UTC (`Etc/UTC`), so the local and UTC wall-clock readings coincide. There is no cross-midnight or cross-day ambiguity between them.

## Question

Does the cross-family predominance observed among evaluable distant-stratum false positives persist across the ten already-fixed panel seeds?

The single-seed run (seed 20260410) found that every evaluable distant false positive was CROSS_FAMILY (20 of 20; within_family = 0). This registration tests whether that predominance is a stable property of the distant-stratum failure mode or an artifact of one particular reference-panel draw.

## Scope

Only robustness to reference-panel composition. This is a confirmatory replication of one analysis across the ten pre-registered panel seeds and nothing else. It introduces:

- No new model. The embedding is the existing frozen ESM-2 t30 layer.
- No new metric. Similarity is cosine via `faiss.IndexFlatIP` on L2-normalized embeddings, exactly as in the existing script.
- No new threshold. The distant stratum is `smax < 0.90`.
- No new neighbor count. k = 25, positive-majority vote.
- No new annotation source. Pfam identifiers are read from `data/annotations/proteins_25k_pfam.json`.
- No new family ontology. Family membership is Pfam-ID intersection, unchanged.

## Fixed protocol (locked before any additional seed is run)

Held identical to `code/analyses/run_cross_family_partition.py` in every respect except that the analysis is repeated once per panel seed:

- Reference panel size: R = 1000.
- Neighbor count: k = 25.
- Embedding scale: t30 (ESM-2 150M layer), L2-normalized per row.
- Similarity: cosine via `faiss.IndexFlatIP`.
- Stratification: for each test protein, `smax` = maximum cosine similarity to any panel member; distant stratum is `smax < 0.90`.
- Prediction: k = 25 nearest panel neighbors; predicted label is 1 when the positive votes satisfy `votes.sum() * 2 >= k` (positive majority at k = 25), matching the existing script exactly.
- Unit of analysis: distant false positives only, i.e. test proteins with `distant == True`, predicted label 1, and true label 0.

### Pfam partition (unchanged)

For each distant false positive, take the union of Pfam identifiers over its positive-voting panel neighbors (the neighbors that voted for label 1) and intersect with the query's own Pfam identifiers:

- **WITHIN_FAMILY:** the query Pfam set intersects the union of Pfam IDs from the positive-voting neighbors (intersection non-empty).
- **CROSS_FAMILY:** the intersection is empty.

### Evaluable case definition (unchanged)

A distant false positive is evaluable only when BOTH of the following hold:

- the query has at least one known Pfam ID, and
- at least one positive-voting neighbor has at least one known Pfam ID.

Cases where the query has no known Pfam ID, or where no positive-voting neighbor has a known Pfam ID, are recorded but excluded from the WITHIN/CROSS denominators, exactly as in the single-seed analysis.

## Panel seeds (already fixed by the original homology-cliff pre-registration)

The ten panel seeds are inherited verbatim from `data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md` and are NOT chosen by this document:

```
20260410
20260411
20260412
20260413
20260414
20260415
20260416
20260417
20260418
20260419
```

Seed 20260410 is the already-executed single-seed run; it is re-derived here under identical code so that the ten-seed table is internally consistent, and its committed value must reproduce.

## Panel construction (identical for every seed)

For each seed in the list above, the reference panel is constructed exactly as in the existing script and pre-registration:

```
rng = numpy.random.default_rng(seed + R)          # R = 1000
positives = rng.choice(pos_idx, 500, replace=False)   # 500 positives, without replacement
negatives = rng.choice(neg_idx, 500, replace=False)   # 500 negatives, without replacement
panel = concatenate([positives, negatives])           # positives first, then negatives
```

The remaining `24885 - 1000` proteins that are not in the panel form the test pool for that seed. Panel and test-pool construction are byte-for-byte identical to the single-seed run for seed 20260410; only the seed integer changes across the ten panels.

## Inputs (must remain, unchanged)

- `data/embeddings/embeddings_t30.npy`
- `data/sequences/proteins_25k_sequences.json`
- `data/annotations/proteins_25k_pfam.json`

The t30 embedding Git-LFS object is pinned at:

- sha256: `15d6e3656b46729a2483b7fbc603e49a61f25206e3854676bc2e528164608fd6`
- size: 63705728 bytes

No new UniProt fetch, no new embedding computation, no relabeling. Real data only; no synthetic results.

## Per-seed outputs

For each of the ten seeds, the following are reported (no selective reporting, no omission):

- n distant (size of the distant stratum in the test pool)
- n distant false positives
- n evaluable (distant false positives satisfying the evaluable definition)
- n WITHIN_FAMILY (among evaluable)
- n CROSS_FAMILY (among evaluable)
- cross-family fraction (CROSS_FAMILY / evaluable), reported only when evaluable > 0
- within-family fraction (WITHIN_FAMILY / evaluable), reported only when evaluable > 0
- Wilson 95% confidence interval for the within-family fraction when the evaluable denominator > 0

### Wilson interval method (locked)

For a seed with evaluable denominator n > 0 and within-family count w, let p = w / n and z = 1.959963984540054 (the two-sided 95% normal quantile). The Wilson score interval is:

```
center = (p + z^2 / (2n)) / (1 + z^2 / n)
half   = (z / (1 + z^2 / n)) * sqrt( p(1 - p)/n + z^2 / (4 n^2) )
CI     = [center - half, center + half]
```

The interval is clipped to [0, 1]. When n = 0 the within-family fraction and its interval are undefined and are reported as null, not as zero.

## Across-seed aggregation

The per-seed cross-family fraction is the robustness observable. Across the ten seeds, and restricted to seeds with a nonzero evaluable denominator, report:

- unweighted mean of the per-seed cross-family fraction
- median of the per-seed cross-family fraction
- minimum of the per-seed cross-family fraction
- maximum of the per-seed cross-family fraction

"Unweighted" means each qualifying seed contributes one value regardless of how many evaluable cases it carried; seeds are not weighted by evaluable count.

### The seed is the robustness unit

The reference panel seed is the unit of robustness. Each seed yields one cross-family fraction, and the ten fractions are the sample.

Do NOT compute a single pooled Wilson interval over all evaluable appearances across the ten seeds. The same accession can be sampled into the test pool of multiple panel seeds and can appear as a distant false positive in several of them; those appearances are not independent Bernoulli trials, so a pooled binomial interval would understate uncertainty and misrepresent the design. Per-seed Wilson intervals are reported for within-seed precision only; the cross-seed claim rests on the distribution of the ten per-seed fractions, not on a pooled proportion.

## Secondary cross-seed accession summary

As a descriptive secondary analysis (not a hypothesis test), summarize how individual accessions behave across the seeds in which they are evaluable:

- count of unique evaluable accessions (union over the ten seeds)
- count always CROSS_FAMILY (evaluable in one or more seeds and CROSS_FAMILY in every seed where evaluable)
- count always WITHIN_FAMILY (evaluable in one or more seeds and WITHIN_FAMILY in every seed where evaluable)
- count mixed (evaluable in two or more seeds with both statuses observed)
- for every unique evaluable accession, the full per-seed record of (seed, status) for the seeds in which it was evaluable

This summary is descriptive context for the primary seed-level result and does not feed the decision rule.

## Decision rule

The original single-seed observation is called robust to panel composition only if BOTH of the following hold:

1. CROSS_FAMILY > WITHIN_FAMILY in every seed that has a nonzero evaluable denominator, AND
2. the median per-seed cross-family fraction (over seeds with nonzero evaluable denominator) is >= 0.80.

If any of the ten seeds has zero evaluable observations, the strong robustness claim is NOT made for the complete ten-seed experiment. Any per-seed result that fails either clause is reported in full; a partial or seed-restricted robustness statement, if warranted, is made explicitly and is not presented as the strong claim above.

## Stopping rules and retention

- No early stopping. All ten seeds are run to completion before the result is read.
- No peeking. The per-seed cross-family fractions are not inspected to decide whether to continue.
- All ten seeds are reported. No seed is dropped for being unfavorable.
- Unfavorable results are retained and reported. A result that fails the decision rule is a valid, publishable outcome of this confirmatory extension.

## Output artifact

The ten-seed analysis, when eventually executed under this locked protocol, writes its result to the NEW file:

- `data/results_summaries/cross_family_partition_10seed.json`

This file does not exist yet and is intentionally NOT created by this registration; it is produced only when the confirmatory experiment is run. The existing single-seed artifact:

- `data/results_summaries/cross_family_partition.json`

must remain untouched and byte-identical. The single-seed value for seed 20260410 in the ten-seed table must reproduce the committed single-seed artifact.

## What remains untouched until the result is in

No paper result, abstract, conclusion, README scientific claim, deployment recommendation, threshold, classifier, family definition, or existing pre-registration text is changed by this registration. Paper and README claims about the cross-family partition remain as they are until the ten-seed result is executed, independently checked, scientifically adjudicated, and explicitly approved. This document only fixes the protocol in advance.

## No em dashes, no fabricated numbers, no cherry-picking

Per the compendium delivery and reproduction mandate. Every number in the eventual ten-seed result comes from same-session script execution against the real committed inputs above. The pre-registration hash below locks this document before any additional seed is computed.

---

**SHA256 hash of this document is computed over its exact LF-normalized UTF-8 bytes at lock time and stored in the companion file `PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md.sha256`. Any edit after hashing voids the registration.**
