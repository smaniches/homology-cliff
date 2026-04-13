"""Minimal deployment example: learned panel-only triplet-surrogate projection
as cliff rescue for frozen PLM biosecurity retrieval.

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC.
License: MIT.
"""
import numpy as np
import torch, torch.nn as nn, torch.optim as optim
try:
    import faiss; HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


def fit_projection(panel_emb, panel_labels, output_dim=128, n_iter=50, seed=0):
    """Fit the triplet-surrogate linear projection on panel alone, <5 CPU seconds."""
    torch.manual_seed(seed); np.random.seed(seed)
    D = panel_emb.shape[1]; output_dim = min(output_dim, D)
    X = torch.from_numpy(panel_emb.astype(np.float32))
    y = torch.from_numpy(panel_labels.astype(np.int64))
    W = nn.Parameter(torch.empty(D, output_dim)); nn.init.orthogonal_(W)
    opt = optim.Adam([W], lr=0.01)
    pos_mask, neg_mask = (y == 1), (y == 0)
    for _ in range(n_iter):
        opt.zero_grad()
        Z = X @ W; Z = Z / (Z.norm(dim=1, keepdim=True) + 1e-8)
        Zp, Zn = Z[pos_mask], Z[neg_mask]
        loss = -(Zp @ Zp.mean(0)).mean() - (Zn @ Zn.mean(0)).mean() + (Zp @ Zn.mean(0)).mean()
        loss.backward(); opt.step()
    return W.detach().numpy()


def rescue_retrieval(panel_emb, panel_labels, query_emb, k=25,
                     close_threshold=0.95, distant_threshold=0.90):
    """End-to-end rescue pipeline. Returns predictions + list of queries needing human review."""
    W = fit_projection(panel_emb, panel_labels)
    panel_proj = panel_emb @ W; panel_proj /= np.linalg.norm(panel_proj, axis=1, keepdims=True) + 1e-8
    query_proj = query_emb @ W; query_proj /= np.linalg.norm(query_proj, axis=1, keepdims=True) + 1e-8
    if HAS_FAISS:
        idx = faiss.IndexFlatIP(panel_proj.shape[1])
        idx.add(panel_proj.astype(np.float32))
        sims, nbrs = idx.search(query_proj.astype(np.float32), k)
    else:
        sims_full = query_proj @ panel_proj.T
        nbrs = np.argsort(-sims_full, axis=1)[:, :k]
        sims = np.take_along_axis(sims_full, nbrs, axis=1)
    vote_fraction = panel_labels[nbrs].mean(axis=1)
    predictions = (vote_fraction * 2 >= 1).astype(np.int64)
    sims_orig = query_emb @ panel_emb.T
    s_max = sims_orig.max(axis=1)
    stratum = np.where(s_max >= close_threshold, "close",
              np.where(s_max >= distant_threshold, "moderate", "distant"))
    route_to_human = np.where((stratum == "distant") & (predictions == 1))[0]
    return {"predictions": predictions, "vote_fraction": vote_fraction,
            "stratum": stratum, "s_max": s_max,
            "route_to_human": route_to_human.tolist(),
            "projection_matrix": W}


if __name__ == "__main__":
    np.random.seed(42)
    D, R, N = 640, 1000, 500
    panel = np.random.randn(R, D); panel /= np.linalg.norm(panel, axis=1, keepdims=True)
    panel_labels = np.random.randint(0, 2, R)
    queries = np.random.randn(N, D); queries /= np.linalg.norm(queries, axis=1, keepdims=True)
    result = rescue_retrieval(panel, panel_labels, queries, k=25)
    print(f"queries: {N}")
    print(f"strata close={sum(result['stratum']=='close')} "
          f"moderate={sum(result['stratum']=='moderate')} "
          f"distant={sum(result['stratum']=='distant')}")
    print(f"predictions positive: {result['predictions'].sum()}")
    print(f"MUST route to human: {len(result['route_to_human'])}")
    print("Rule: ALL distant-stratum positive predictions require human review")
    print("Reason: Paper 3 calibration collapse + Paper 5 cross-family mechanism")
