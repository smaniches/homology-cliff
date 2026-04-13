# Frequently Asked Questions

**Author:** Santiago Maniches, Independent Researcher, TOPOLOGICA LLC (solo research lab). ORCID [0009-0005-6480-1987](https://orcid.org/0009-0005-6480-1987).

Questions anticipated from reviewers, deployers, and curious readers. If your question is not here, file a GitHub Discussion.

## About the work

**Q1. Why did you stop at ESM-2 t30 instead of t33 (650M)?**
Local hardware constraint. ESM-2 t33 needs a GPU to embed 24,885 sequences in reasonable time. The current compendium was produced entirely on a 36 GB i7 CPU workstation. The t33 extension is scaffolded via the Colab notebook in `code/colab_notebook/plm_benchmark.ipynb` and expected in v1.5.

**Q2. Why the 0.95 / 0.90 stratification cuts?**
These were locked in the main pre-registration (SHA256 `139f6012…`) before any evaluation. The 0.95 cut roughly separates the CD-HIT-90 near-homolog regime from genuinely novel sequences; 0.90 gives a buffer "moderate" stratum to see the cliff onset. A threshold sensitivity sweep is listed as unverified in `PROBLEMS.md`.

**Q3. Why percentile bootstrap and not BCa?**
BCa requires a jackknife per cell, which is O(n) extra computation. With 9,360 cells the additional cost is nontrivial. Percentile is the standard fallback. For individual headline numbers in the papers, BCa confidence intervals can be computed on demand from the committed .npz files.

**Q4. Why 10 seeds? Isn't 30-50 the standard?**
Cost tradeoff. 10 seeds at the current factorial size is already 9,360 cells. Doubling seeds doubles compute and storage. The pre-committed seed-variance gate compensates: any cell where across-seed std exceeds the claimed gap is voided, which ensures 10-seed claims are not inflated relative to what 30 seeds would support.

**Q5. Cosine and Euclidean are equivalent on the unit sphere. Why report both?**
As a numerical-correctness check. Paper 1 proves the equivalence formally and Paper 4 verifies it to 4 decimal places in 75 of 75 cells. This is a cheap sanity check that FAISS IndexFlatIP and IndexFlatL2 are returning identical neighbor sets on L2-normalized embeddings.

**Q6. The learned projection is a centroid-triplet surrogate, not a proper triplet loss with hard negative mining. Doesn't a stronger baseline exist?**
Yes, and we acknowledge this in the Paper 1 limitations and Paper 4 methods. The centroid surrogate was chosen because it fits in 5 CPU seconds on a panel of 1000 and requires no hard-negative mining infrastructure. A proper FaceNet-style triplet loss with semi-hard mining likely works equally well or better. The choice is about deployability, not optimality.

**Q7. What is the TOPOLOGICA "v7 seed-variance gate"?**
A pre-committed void rule from earlier TOPOLOGICA work on GO annotation pipelines. It states: if across-seed standard deviation of the distant-stratum F1 exceeds the observed close-distant gap, the group is voided. The rule protects against claiming a cliff that is actually seed noise. All 300 main groups passed.

**Q8. Why did the panel-only shuffle null fail its pre-registered criterion?**
The pre-registration required "distant F1 at chance = 0.5" under the null. But shuffling only the panel labels (while leaving test labels intact) preserves the 28.7% test class prior, and chance F1 in this class-imbalanced regime is not 0.5. This was caught within the session. A corrected pre-registration (the full-pool permutation null) was SHA256-locked before running the stricter test, and passed 300/300.

**Q9. What does "100% cross-family" mean, exactly?**
At t30 R=1000 k=25 cosine seed 20260410: 41 distant-stratum proteins received a positive prediction while the true label was negative. Of those, 20 had both a Pfam annotation on the query and at least one Pfam annotation on the positive-voting panel members. In all 20 cases, the intersection of the query's Pfam set with the union of its positive-voters' Pfam sets was empty. Not one of those 20 failures was caused by within-family confusion.

**Q10. Does cross-family = cross-CATH? Cross-InterPro? Cross-fold?**
Only cross-Pfam as of v1.3.1. Pfam is a coarse family definition. A finer-grained analysis using InterPro superfamily or CATH fold could reveal distant-family-but-shared-superfamily relationships the Pfam test misses. This is in `PROBLEMS.md` as deferred.

## About the authorship

**Q11. You are one researcher working with AI tools. How do I trust this work?**
See the "How we addressed the solo researcher with AI trust concern" section of the README, and `PROBLEMS.md` for self-audited errors caught during authoring. The architectural trust arguments: SHA256-locked pre-registrations that the running code verifies, every cell committed as .npz with bootstrap CI, deterministic seeds, git history, self-audited errors. Run `pytest tests/`, pick any committed cell, rerun its harness, confirm the .npz hash matches `MANIFEST.sha256.json`.

**Q12. What is TOPOLOGICA LLC?**
TOPOLOGICA LLC is Santiago Maniches's registered solo research lab. It is not a company with employees; it is a legal structure under which one independent researcher conducts research. Work is single-author. AI collaboration tools are used to accelerate execution; scientific direction, hypothesis formation, experimental design, and final judgment are Santiago's.

**Q13. Has this work been peer-reviewed?**
Not yet externally. The `REFEREES.md` document logs the self-adversarial review passes applied to each paper. External peer review is pending arXiv / journal submission.

## About reproducibility

**Q14. How long does it take to reproduce the entire factorial from scratch?**
Approximately 28 hours wall-time on a 36 GB i7 workstation with FAISS CPU. Main factorial (3000 cells) alone takes ~6 hours. Full-null (3000 cells) takes ~5 hours. Panel-shuffle null takes ~5 hours. Cascade and Fisher 180-cell factorials take ~2 hours each. Analyses and aggregation take minutes.

**Q15. Can I reproduce a single cell quickly?**
Yes. Pick any cell from `data/cells/main/`, note its filename (encodes scale, R, k, metric, seed). Run `python code/harnesses/run_cliff.py --scale <scale> --R <R> --k <k> --metric <metric> --seed <seed>`. Expected time: 20-40 seconds. The output .npz should have a SHA256 matching `MANIFEST.sha256.json`.

**Q16. I get different numbers when I re-run. What's wrong?**
Check: (a) are you using the committed embeddings? They are LFS-tracked; `git lfs pull` is required. (b) Are you L2-normalizing? The pipeline assumes normalized embeddings. (c) Are you using `numpy.random.default_rng(seed)`? Older `numpy.random.RandomState` gives different streams. (d) Are you on Python 3.11+ with numpy ≥1.26? Earlier versions have different bit-exact arithmetic in edge cases.

**Q17. The pytest suite fails on my machine.**
File a reproducibility_failure issue. Include Python version, numpy version, FAISS version, OS, and the exact pytest output.

## About deployment

**Q18. Can I use this in production tomorrow?**
The learned projection is deployable in the sense that it is code that runs. See `deployment_example/`. But `MODEL_CARD.md` documents important out-of-scope uses: calibration under the projection is unmeasured, so distant-stratum predictions still need human review. If your use case has a false-positive cost (panel expansion, human review capacity) we are happy to discuss.

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
v1.5 target: PLM benchmark extension, 10-seed cross-family extension, arXiv submission for Papers 1 and 5. v2.0 target: external PLM comparison (ProtT5, SaProt, ESM-3, Foldseek) and a stronger learned metric using proper triplet loss with hard negative mining.
