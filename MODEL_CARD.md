# Model Card: Learned Panel-Only Triplet-Surrogate Projection

**Model name:** `learned_projection_panel_only_triplet_surrogate`
**Version:** v1.0 (April 2026)
**Authors:** Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
**License:** MIT

## Description
A linear projection $W \in \mathbb{R}^{D \times 128}$ fit in 50 Adam iterations on a labeled reference panel of frozen ESM-2 embeddings. Used as preprocessing before cosine $k$-NN retrieval to rescue the distant-stratum homology cliff.

## Training procedure
- **Input:** L2-normalized ESM-2 embeddings of the panel (D = 320/480/640 for t6/t12/t30)
- **Loss:** triplet-surrogate on class centroids: $\mathcal{L}(W) = -\langle Z_+, Z_+ \rangle - \langle Z_-, Z_- \rangle + \langle Z_+, Z_- \rangle$ where $Z_\pm$ are L2-normalized projections of panel class subsets
- **Optimizer:** Adam, 50 iterations, default learning rate, seed 0
- **Init:** orthogonal (PyTorch default for linear layers)
- **Output:** projection matrix $W$, applied to test embeddings before L2-normalization and cosine k-NN

## Intended use
- Preprocessing for frozen PLM retrieval at deployment time
- The panel provides ALL training signal; no test data used
- Fit in $<$ 5 CPU seconds per panel
- Re-fit per panel (each panel is a new Adam run)

## Performance
- 18 of 18 factorial (scale, $R$, $k$) groups: learned projection wins pooled $F_1$
- At t30 $R=1000$ $k=25$: pooled $F_1$ 0.891 (best in 3000-cell factorial)
- Distant-stratum $F_1$: t6 +16%, t12 +33%, t30 +48% relative over cosine baseline

## Out-of-scope uses
- NOT a calibrated classifier — calibration under the projection was NOT measured in this work
- Distant-stratum predictions should still be human-reviewed (Paper 3 calibration collapse + Paper 5 cross-family finding both independently apply)
- Not validated on non-toxin biosecurity categories (e.g., pathogen virulence factors, antibiotic resistance)
- Not validated outside ESM-2 family (ProtT5/SaProt/ESM-3 deferred to PLM benchmark)

## Fairness and bias
- Training panel inherits all biases of the underlying UniProt curation
- Cross-family Pfam analysis (Paper 5) shows distant false alarms are drawn from families other than the true query family; bias is embedding-space-geometric, not demographic
- Dataset lacks organism-balanced representation

## Carbon footprint
- Training: 50 Adam iterations, $<$ 5 CPU seconds per panel, negligible ($<$ 0.1 g CO2eq)
- Evaluation across 3000 main cells: ~5 hours CPU, approximately 180 g CO2eq at US grid average

## Deployment recommendations (paired with Paper 5 cross-family finding)
1. Apply panel-only learned projection as preprocessing
2. Route all distant-stratum positive predictions to human review regardless of vote count
3. Do NOT attempt panel expansion as a cliff rescue (distant false alarms are cross-family)
4. Re-fit the projection whenever the panel changes

## Files
- Harness code: `code/harnesses/run_cliff.py` (triplet-surrogate implementation)
- Per-cell results: `data/cells/main/cell_*_learned_*.npz`
