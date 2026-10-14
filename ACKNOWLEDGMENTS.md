# Acknowledgments

**Scientific author:** Santiago Maniches. The tools, sources, and internal review assistance acknowledged here supported the work but are not scientific coauthors or independent external reviewers.

## Infrastructure

- **FAISS** (Meta AI Research) — every k-NN operation in this compendium runs on FAISS IndexFlatIP / IndexFlatL2. The scale of the factorial (9,360 cells) is feasible on CPU only because of FAISS.
- **scikit-learn** — Ledoit-Wolf shrinkage estimator, DBSCAN clustering, PCA lens for Mapper.
- **HuggingFace ESM-2** (Lin et al. 2023) — frozen protein language model embeddings for three scales, no fine-tuning used.
- **UniProt** — sequence identifiers, Pfam annotations, taxonomy.
- **NumPy / SciPy** — bootstrap CIs, covariance estimation, linear algebra.
- **MiKTeX** — LaTeX compilation on Windows.
- **Git + Git LFS** — version control for both the small and the large.
- **Anthropic Claude** — AI-assisted coding and critical discussion during the April 11–12 development session. Helped challenge early interpretations of the Mahalanobis-rescue and panel-shuffle-null results, and executed MCP-driven file and process operations during factorial orchestration. Santiago Maniches directed the research and is responsible for the methods, interpretation, and published claims.

## Interpretation of negative results

The panel-only label-shuffle control failed its original criterion because the test-set class prior was preserved, motivating the full-pool null. The stratified cascade, Fisher-Rao, and Mapper-augmentation experiments did not support their preregistered rescue hypotheses under the evaluated controls. The observed improvement under the learned projection should be interpreted alongside these negative controls and its remaining calibration and generalization limits.

## Priors

- TOPOLOGICA **DR-010** (Fisher info geometry harms GO annotation) — replicated here in a different task.
- TOPOLOGICA **v7 seed-variance gate** — pre-committed void rule adopted from prior work.
- TOPOLOGICA **pre-registration discipline** (prior pre-regs v1-v6 on different questions) — the habit of locking hypotheses before running experiments is older than this work.

## Scope

This is not a validated operational biosecurity retrieval system. At t30 R=1000 k=25, the learned projection improves distant $F_1$ from 0.120 to 0.177, which remains low. Calibration of that projection and external deployment performance have not been established, so distant-stratum positives require human review. The cross-family finding has been checked across ten fixed panel seeds under the Pfam definition, but cross-model, cross-ontology, and third-party validation remain open. The external PLM benchmark and second adversarial phase are not completed.
