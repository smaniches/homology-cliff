# Referees Log

Self-adversarial review passes applied to each paper before public release. This log exists because this compendium is authored by one person, Santiago Maniches (Independent Researcher, TOPOLOGICA LLC), with AI-collaboration support. Absent external peer review, the discipline is to simulate hostile referees from multiple angles and document what they caught. See `PROBLEMS.md` for the complete error log.

The five adversarial-referee personas used, per the TOPOLOGICA `adversarial-manuscript-referee` protocol:

1. **Logical structure referee** — is the argument valid even if the numbers are right?
2. **Mathematical rigor referee** — do the proofs/derivations hold?
3. **Empirical honesty referee** — are the numbers real, traceable, and honestly framed?
4. **Literature positioning referee** — is the related work adequate and are credits correct?
5. **Presentation clarity referee** — can a competent reader follow and reproduce?

## Paper 1 — Homology Cliff and Its Rescue

| Pass | Persona | Findings | Resolution |
|------|---------|----------|------------|
| 1 | Logical structure | Earlier draft framed Mahalanobis as "partial rescue because gap shrinks by +0.376." This is invalid: the gap shrinks because close F1 collapses, not because distant F1 improves. | Reframed in v1.0. Pooled F1 now reported alongside gap, making the close-collapse visible. Documented as error #1 in `PROBLEMS.md`. |
| 2 | Mathematical rigor | Proposition (cosine ≡ Euclidean on S^(d-1)) trivial but needs stated in paper. Also: bootstrap CI should cite a reference, not stand as unsupported. | Proposition included with proof in Paper 1 §5. Bootstrap implementation cites percentile-bootstrap tradition (see Paper 4 for detailed justification). |
| 3 | Empirical honesty | Seed-variance gate originally described without numbers. Reviewer: "does ANY group pass?" | Paper 1 now states "all 300 main groups passed." Full-null passing "300/300" is now explicit. |
| 4 | Literature positioning | v1.0 cited only 2 references (unacceptable). Missing ESM-2, ProtT5, Foldseek, CD-HIT, calibration literature, metric-learning literature, pre-registration literature, dual-use guidance. | v1.1 expanded to 24 references in 8 subsections of a proper related-work section. |
| 5 | Presentation clarity | v1.0 had no figures. A paper claiming a "cliff" without showing the cliff shape is weak. | v1.1 adds 3 TikZ figures: cliff surface (gap vs panel size, 3 scales), reliability diagram (close vs distant), rescue bar chart (distant F1 by metric and scale). |

**Residual concerns deferred to v1.2+:**
- Figures are single-panel; multi-panel publication-quality figures deferred
- Related work still short of 40+ refs target for a top-tier venue

## Paper 2 — Four Failed Rescue Attempts

| Pass | Persona | Findings | Resolution |
|------|---------|----------|------------|
| 1 | Logical structure | Earlier drafts merged 3 rescue rejections into one paper. Reviewer: "is this really one paper or three short papers?" | Justification: each rejection is short (2-3 pages), collectively they form a coherent "what doesn't work" narrative, splitting would fragment. Kept as one. |
| 2 | Mathematical rigor | Fisher-Rao "within-class whitening" terminology was ambiguous. Which covariance exactly? | Paper 4 methods section specifies: within-class scatter matrix $S_W = \sum_c \sum_{x \in c} (x - \mu_c)(x - \mu_c)^\top$, whitened via pseudoinverse. |
| 3 | Empirical honesty | Mapper-augmentation rescue +0.0018 CI [-0.027, +0.029]. Reviewer: "this is essentially zero. Does the paper honestly state that?" | Yes, Paper 2 Attempt 4 explicitly reports "rescue +0.0018 indistinguishable from zero, H1 rejected." |
| 4 | Literature positioning | Weinberger 2009 (LMNN) should be cited for metric learning baseline context. | Added to Paper 2 §7. |
| 5 | Presentation clarity | Needs at least one visual summary table of "what was tried, what happened." | Paper 2 §6 "Synthesis" table added. |

## Paper 3 — Calibration Collapse

| Pass | Persona | Findings | Resolution |
|------|---------|----------|------------|
| 1 | Logical structure | Highest-confidence bin on distant has 3 predictions, 0 correct. Reviewer: "is n=3 really enough for a claim?" | Explicit acknowledgment: the claim is not "ECE=0.294 is statistically precise" but "in the bin that a downstream filter would route to automation, the classifier is 0/3. This is the deployment-critical fact." |
| 2 | Mathematical rigor | 6-bin uniform ECE is known to be sensitive to binning. | `PROBLEMS.md` flags this as L2. Adaptive binning or Brier score deferred. |
| 3 | Empirical honesty | Paper 3 is short. Could be expanded with temperature scaling as a rescue attempt. | Scope-limited: Paper 3 documents the calibration failure; rescue attempts belong in a follow-up. Explicitly stated in limitations. |
| 4 | Literature positioning | Guo 2017 and Ovadia 2019 are the canonical references. Both cited. | Done. |
| 5 | Presentation clarity | Reliability diagram is essential. | TikZ reliability diagram included in v1.1. |

## Paper 4 — Methods and Pre-Registrations

| Pass | Persona | Findings | Resolution |
|------|---------|----------|------------|
| 1 | Logical structure | The seed-variance gate is novel but not motivated against alternatives (e.g., multiple-testing correction). | Paper 4 discusses it as a pre-commitment rule orthogonal to BH/Bonferroni; both can be applied. A dedicated methodology paper comparing them is future work. |
| 2 | Mathematical rigor | Ledoit-Wolf shrinkage intensity not specified. | Paper 4 methods: "scikit-learn default, optimal-under-Frobenius selected via Ledoit-Wolf lemma 1." Reference cited. |
| 3 | Empirical honesty | "All 300 main groups passed" is a strong claim. Reviewer: "show me the one that barely passed." | The `v3_final.txt` committed file lists every group's (gap, std) pair. Readers can inspect directly. |
| 4 | Literature positioning | Pre-registration references needed. Nosek 2018, Forde 2019 are key. | Cited. |
| 5 | Presentation clarity | The 4000-cell vs actual 3000-cell count should be reconciled. | v1.3.1 reconciles: t33 was pre-registered and is pending GPU; main factorial at 3000 cells covers t6/t12/t30. |

## Paper 5 — Cross-Family and Mapper Topology

| Pass | Persona | Findings | Resolution |
|------|---------|----------|------------|
| 1 | Logical structure | 20/20 cross-family is striking. Reviewer: "but n=20 is small." | Paper 5 explicitly acknowledges: result at one seed, 10-seed extension deferred. The binary result (0 within-family) is what matters, not the precision of the "100%". |
| 2 | Mathematical rigor | Mapper parameters not justified. Why PCA-2? Why 10x10? Why DBSCAN? | Standard Mapper defaults per Singh-Mémoli-Carlsson 2007. Cited. |
| 3 | Empirical honesty | 13.1% of accessions lack Pfam. Excluded from partition. Could this bias the cross-family rate? | Yes, possibly. Documented as L2 in Paper 5 limitations. |
| 4 | Literature positioning | v1.0 had 0 bibliography entries. Unacceptable. | v1.3.1 cites Singh, Carlsson, Edelsbrunner, Lin (ESM-2). 4 entries. Still thin but coherent. |
| 5 | Presentation clarity | v1.0 had no figures. | v1.3.1 adds Mapper 2D scatter figure showing positive-enriched bins. |

## Policy on future referee passes

External peer review via arXiv + journal submission is the next stage. The self-adversarial passes above are not a substitute. They are a lower bound on the rigor applied before public release.

When external reviewers file critiques, this document will be updated with their findings and our resolutions, with attribution.
