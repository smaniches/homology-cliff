# Acknowledgments

With maximum humility.

## Infrastructure

- **FAISS** (Meta AI Research) — every k-NN operation in this compendium runs on FAISS IndexFlatIP / IndexFlatL2. The scale of the factorial (9,360 cells) is feasible on CPU only because of FAISS.
- **scikit-learn** — Ledoit-Wolf shrinkage estimator, DBSCAN clustering, PCA lens for Mapper.
- **HuggingFace ESM-2** (Lin et al. 2023) — frozen protein language model embeddings for three scales, no fine-tuning used.
- **UniProt** — sequence identifiers, Pfam annotations, taxonomy.
- **NumPy / SciPy** — bootstrap CIs, covariance estimation, linear algebra.
- **MiKTeX** — LaTeX compilation on Windows.
- **Git + Git LFS** — version control for both the small and the large.
- **Anthropic Claude** — pair-research interlocutor throughout the April 11-12 session. Caught several of my own early errors via the adversarial-referee pattern (especially the Mahalanobis-rescue framing and the panel-shuffle-null criterion mismatch). Executed MCP-driven file and process operations to orchestrate the four parallel factorials.

## Epistemology

Every null result in this compendium is a teacher. The panel-only shuffle failing its own criterion taught the class-prior mechanism. The stratified cascade failing 18/18 taught that Mahalanobis is not a rescue. The Fisher-Rao result replicating DR-010 in a new domain taught that within-class covariance on frozen PLMs carries class signal. The Mapper-augmentation null taught that panel composition is not the lever. The one positive finding (learned projection) is interpretable only against the backdrop of these four failed hypotheses; absent the nulls the positive claim would be an unfalsified guess.

## Priors

- TOPOLOGICA **DR-010** (Fisher info geometry harms GO annotation) — replicated here in a different task.
- TOPOLOGICA **v7 seed-variance gate** — pre-committed void rule adopted from prior work.
- TOPOLOGICA **pre-registration discipline** (prior pre-regs v1-v6 on different questions) — the habit of locking hypotheses before running experiments is older than this work.

## What this compendium is not

It is not a complete biosecurity retrieval solution. The learned projection achieves distant F1 = 0.177 at t30 R=1000 k=25, an improvement from 0.120 but still far from useful. The calibration collapse (ECE 0.294 on distant) means all distant-stratum hits still require human review. The cross-family question is unresolved. The PLM comparison is unfinished. The adversarial attack is unfinished. v1.0 is a real step, not a destination.
