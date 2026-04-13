# Deployment Example

Minimal self-contained example for applying the Homology Cliff rescue (Paper 1) in production.

**Contents:**
- `deploy_cliff_rescue.py` — fit projection on your panel, retrieve k-NN, stratify, flag distant-stratum positives for human review

## Usage

```python
from deploy_cliff_rescue import rescue_retrieval
import numpy as np

# Your panel and queries, L2-normalized ESM-2 (or compatible PLM) embeddings
panel_emb = np.load("my_panel.npy")       # shape (R, D)
panel_labels = np.load("my_labels.npy")   # shape (R,), binary 0/1
query_emb = np.load("my_queries.npy")     # shape (N, D)

result = rescue_retrieval(panel_emb, panel_labels, query_emb, k=25)

# Deployment policy (MANDATORY per Papers 3 and 5):
for i in result["route_to_human"]:
    print(f"Query {i}: distant-stratum positive prediction, requires human review")
```

## Why "route to human" is mandatory for distant-stratum positives

Paper 3 shows distant-stratum Expected Calibration Error is 4x higher than close-stratum, and that the highest-confidence distant bin had 3 predictions, 0 correct. Paper 5 shows 100% of evaluable distant false alarms are cross-family, meaning panel expansion cannot fix them. No confidence threshold can be trusted on the distant stratum. Human review is the correct intervention.

## Dependencies

numpy, torch, faiss-cpu (optional; falls back to dense matmul if not installed).

## Limitations (paired with `MODEL_CARD.md`)

- Projection is fit per-panel; changing the panel requires refitting (5 CPU seconds)
- Calibration of the learned metric is unmeasured (Paper 1 L4)
- Not validated outside ESM-2 family PLMs; see `BENCHMARK.md`
- Not a trained biosecurity classifier; this is a cliff rescue, not a complete screen

## License

MIT. See `LICENSE-code.txt` in the repo root.
