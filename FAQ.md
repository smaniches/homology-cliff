# Frequently Asked Questions

**Author:** Santiago Maniches, Independent Researcher, TOPOLOGICA LLC (solo research lab). ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987).

Questions anticipated from reviewers, deployers, and curious readers. If your question is not here, file a GitHub Discussion.

## About the work

**Q1. Why did you stop at ESM-2 t30 instead of t33 (650M)?**
Local hardware constraint. ESM-2 t33 needs a GPU to embed 24,885 sequences in reasonable time. The current compendium was produced entirely on a 36 GB i7 CPU workstation. The t33 extension is scaffolded in `code/colab_notebook/plm_benchmark.ipynb` but has not been executed as part of the v1.6.0 evidence.

**Q2. Why the 0.95 / 0.90 stratification cuts?**
These are fixed in the main pre-registration (SHA256 `139f6012…`); public history cannot establish that it was locked before any evaluation (see `docs/ERRATUM_2026-10-15.md`). The 0.95 cut roughly separates the CD-HIT-90 near-homolog regime from genuinely novel sequences; 0.90 gives a buffer "moderate" stratum to see the cliff onset. A threshold sensitivity sweep is listed as unverified in `PROBLEMS.md`.

**Q3. Why percentile bootstrap and not BCa?**
BCa requires a jackknife per cell, which is O(n) extra computation. With 9,360 cells the additional cost is nontrivial. Percentile is the standard fallback. For individual headline numbers in the papers, BCa confidence intervals can be computed on demand from the committed .npz files.

**Q4. Why 10 seeds? Isn't 30-50 the standard?**
Ten seeds were a computational tradeoff across 9,360 experimental cells. The preregistered seed-variance gate flags groups whose across-seed distant-stratum $F_1$ standard deviation exceeds the observed close–distant gap. Passing this gate does not establish equivalent precision or statistical power to a 30–50-seed study. Additional seeds and external replication are still needed to assess broader stability.

**Q5. Cosine and Euclidean are equivalent on the unit sphere. Why report both?**
As a numerical-correctness check. Paper 1 proves the equivalence formally and Paper 4 verifies it to 4 decimal places in 75 of 75 cells. This is a cheap sanity check that FAISS IndexFlatIP and IndexFlatL2 are returning identical neighbor sets on L2-normalized embeddings.

**Q6. The learned projection is a centroid-triplet surrogate, not a proper triplet loss with hard negative mining. Doesn't a stronger baseline exist?**
Yes, and we acknowledge this in the Paper 1 limitations and Paper 4 methods. The centroid surrogate was chosen because it fits in 5 CPU seconds on a panel of 1000 and requires no hard-negative mining infrastructure. A proper FaceNet-style triplet loss with semi-hard mining likely works equally well or better. The choice is about deployability, not optimality.

**Q7. What is the TOPOLOGICA "v7 seed-variance gate"?**
A pre-committed void rule from earlier TOPOLOGICA work on GO annotation pipelines. It states: if across-seed standard deviation of the distant-stratum F1 exceeds the observed close-distant gap, the group is voided. The rule is a screening check for one form of seed variability, not a general statistical uncertainty bound. All 300 main groups passed the stated rule.

**Q8. Why did the panel-only shuffle null fail its pre-registered criterion?**
The pre-registration required "distant F1 at chance = 0.5" under the null. But shuffling only the panel labels (while leaving test labels intact) preserves the 28.7% test class prior, and chance F1 in this class-imbalanced regime is not 0.5. This was caught within the session. A corrected pre-registration (the full-pool permutation null) was written and SHA256-locked for the stricter test, which passed 300/300. Public history cannot establish that this lock preceded the run (see `docs/ERRATUM_2026-10-15.md`).

**Q9. What does the cross-family result mean, exactly?**
At the original t30 R=1000 k=25 cosine seed 20260410, 41 distant-stratum proteins were false positives and 20 were evaluable under the Pfam annotation rule; all 20 were cross-family. That historical 20/20 result was then tested prospectively under a SHA256-locked ten-seed panel-composition protocol. Across seeds 20260410-20260419, cross-family false alarms predominated in every seed; the per-seed cross-family fraction had median 1.000, mean 0.994, and range 0.962-1.000, and all ten seeds had nonzero evaluable denominators, so the preregistered strong robustness criterion passed. This means the predominance is robust to the tested reference-panel draws. It does not mean every error is cross-family: two within-family appearances occurred, both for the same accession, and Pfam is a coarse family definition.

**Q10. Does cross-family = cross-CATH? Cross-InterPro? Cross-fold?**
Only cross-Pfam as of v1.3.1. Pfam is a coarse family definition. A finer-grained analysis using InterPro superfamily or CATH fold could reveal distant-family-but-shared-superfamily relationships the Pfam test misses. This is in `PROBLEMS.md` as deferred.

## About the authorship

**Q11. What was the role of AI tools, and what evidence can be checked?**
Santiago Maniches is the sole scientific author. AI tools supported implementation, experiment orchestration, writing, and internal critique, as described in `ACKNOWLEDGMENTS.md`. Three preregistrations are SHA-256 locked and CI-verified, the 9,360 committed `.npz` cells are indexed by `MANIFEST.sha256.json`, and `PROBLEMS.md` documents corrections. `pytest tests/` and the procedures in `REVIEWER.md` check specified artifacts and results. These checks are not independent peer review; independent reconstruction of class labels requires separate curation.

**Q12. What is TOPOLOGICA LLC?**
TOPOLOGICA LLC is Santiago Maniches's registered solo research lab. It is not a company with employees; it is a legal structure under which one independent researcher conducts research. The scientific research is single-author work. AI-assisted tools contributed to development and internal review, while scientific direction, hypotheses, experimental design, interpretation, and publication decisions remain Santiago's. Third-party software and data retain their own credit.

**Q13. Has this work been peer-reviewed?**
Not yet externally. `REFEREES.md` records internal, AI-assisted adversarial review passes, not reports from independent referees. External review and third-party replication remain separate future steps.

## About reproducibility

**Q14. How long does it take to reproduce the entire factorial from scratch?**
Approximately 28 hours wall-time on a 36 GB i7 workstation with FAISS CPU. Main factorial (3000 cells) alone takes ~6 hours. Full-null (3000 cells) takes ~5 hours. Panel-shuffle null takes ~5 hours. Cascade and Fisher 180-cell factorials take ~2 hours each. Analyses and aggregation take minutes.

**Q15. Can I reproduce a single cell quickly?**
The harness regenerates one *scale* at a time, not an individual cell: `python code/harnesses/run_cliff.py --scale t6 --dry-run` previews the smallest-scale (8M) cells and `python code/harnesses/run_cliff.py --scale t6` recomputes them. (There are no per-cell `--R/--k/--metric/--seed` flags — the CLI iterates R, k, metric, and seed internally; `--scale` selects the scale and `--dry-run` previews.) To re-run or verify one specific (scale, R, k, metric, seed) cell, follow `reproducibility/PROTOCOL.md`; every committed cell carries a SHA-256 in `MANIFEST.sha256.json`, so you can confirm a cell without recomputing.

**Q16. I get different numbers when I re-run. What's wrong?**
Check: (a) are you using the committed embeddings? They are LFS-tracked; `git lfs pull` is required. (b) Are you L2-normalizing? The pipeline assumes normalized embeddings. (c) Are you using `numpy.random.default_rng(seed)`? Older `numpy.random.RandomState` gives different streams. (d) Are you on Python 3.11+ with numpy ≥1.26? Earlier versions have different bit-exact arithmetic in edge cases.

**Q17. The pytest suite fails on my machine.**
File a reproducibility_failure issue. Include Python version, numpy version, FAISS version, OS, and the exact pytest output.

## About deployment

**Q18. Can I use this in production tomorrow?**
Not as a validated biosecurity screen. The panel-fitted projection is implemented and evaluated within the recorded experimental protocol (`deployment_example/`), but its calibration and external deployment performance have not been established. `MODEL_CARD.md` documents these limits; distant-stratum positives require human review. If your use case has a false-positive cost (panel expansion, human review capacity) we are happy to discuss.

**Q19. Can you come consult on our biosecurity screen?**
Open a GitHub Discussion or email santiago at topologica dot ai. TOPOLOGICA LLC is the legal vehicle for such engagements.

**Q20. The GPU benchmark extension (ProtT5, SaProt, ESM-3) isn't done. When will it be?**
When someone runs the Colab notebook. Either Santiago does it on Colab Pro, or a community contributor does and submits a PR per `BENCHMARK.md`. The blocking constraint is GPU time, not implementation effort.

## About the repository

**Q21. Why five papers instead of one?**
Each paper has a distinct scientific claim targeting a distinct audience. Paper 1 is the main ML/bio paper. Paper 2 is a null-results paper for the metric-learning community. Paper 3 is a calibration-under-shift paper for the reliability community. Paper 4 is a methods paper for researchers wanting the pre-registration template. Paper 5 is a topology/bioinformatics paper for the cross-family finding. Splitting allows each to be cited independently.

**Q22. Why not submit as one paper?**
Length. One paper covering all five would be 50+ pages, which is outside most journals' limits. Separate papers are also easier to iterate on; we can update Paper 5 (cross-family) without touching Papers 1–4.

**Q23. What comes next?**
The preregistered 10-seed cross-family panel-composition extension is complete. Next priorities are external submission of Papers 1 and 5, third-party replication, and the external-PLM / stronger-metric extensions (ProtT5, SaProt, ESM-3, Foldseek, and proper hard-negative triplet learning).
