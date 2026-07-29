"""compute_pooled_f1.py -- reproduce pooled (whole-test-set) F1 for the cited cells.

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC.

The per-cell evidence in data/cells/main/ stores per-stratum F1 (close / moderate /
distant) only; the *pooled* F1 (computed over the whole test set, all strata combined)
that several headline numbers reference -- the Paper 1 rescue table's pooled column,
the abstract's "wins pooled F1 in 16 of 18 groups" / "F1 = 0.891", and the Paper 2
whitening comparison -- is committed for cosine/mahalanobis/learned/cascade in the
cascade cells (data/cells/cascade/*.npz) but not for the Fisher-Rao metric, and not in
a single consolidated summary. This script regenerates pooled F1 (plus per-stratum and
the close-distant gap) for every cited (scale, R, k, metric) cell directly from the
committed embeddings + seeds, using the *same* harness machinery as run_cliff.py /
run_fisher.py (imported, not reimplemented), and writes:

    data/results_summaries/pooled_f1_summary.json

As an internal correctness check it also re-derives the close/moderate/distant/pooled F1
that the cascade cells already store for cosine/mahalanobis/learned/cascade and enforces
agreement within tolerance (aborting on drift, missing cascade evidence, or non-finite
values) -- so the Fisher values, which have no committed cell to check against, inherit
the same validated pipeline. Deterministic (seeded panels, exact FAISS, torch.manual_seed(0));
repo-relative; no Git-LFS-free fallback (needs `git lfs pull` + faiss, like run_cliff.py --full).

    python code/analyses/compute_pooled_f1.py            # regenerate the summary
    python code/analyses/compute_pooled_f1.py --check    # regenerate + assert vs committed summary (tolerance)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(os.environ.get("HOMOLOGY_CLIFF_REPO_ROOT",
                                Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(REPO_ROOT / "code" / "harnesses"))

import run_cliff as rc        # noqa: E402
import run_fisher as rf       # noqa: E402

OUT = REPO_ROOT / "data" / "results_summaries" / "pooled_f1_summary.json"
CASCADE_DIR = REPO_ROOT / "data" / "cells" / "cascade"

# The cited grid: rescue table (t30,1000,25), the learned-vs-cosine "16 of 18"
# factorial, and the Fisher/Mahalanobis 18-cell comparison all live inside this
# union {t6,t12,t30} x {100,500,1000} x {5,25} x {cosine,mahalanobis,fisher,learned}.
SCALES = ("t6", "t12", "t30")
RS = (100, 500, 1000)
KS = (5, 25)
METRICS = ("cosine", "mahalanobis", "fisher", "learned", "cascade")
SEEDS = tuple(range(20260410, 20260420))


def _counts(yt: np.ndarray, yp: np.ndarray) -> tuple[int, int, int]:
    tp = int(((yt == 1) & (yp == 1)).sum())
    fp = int(((yt == 0) & (yp == 1)).sum())
    fn = int(((yt == 1) & (yp == 0)).sum())
    return tp, fp, fn


def _predict(metric, test_emb, panel_emb, panel_labels, k):
    if metric == "fisher":
        return rf.knn_fisher(test_emb, panel_emb, panel_labels, k)
    return rc.METRIC_FNS[metric](test_emb, panel_emb, panel_labels, k)


def eval_cell(emb, labels, R, k, metric, seed) -> dict:
    panel_idx = rc.build_panel(labels, R, seed)
    panel_emb = emb[panel_idx]
    panel_labels = labels[panel_idx].copy()
    test_mask = np.ones(len(labels), dtype=bool)
    test_mask[panel_idx] = False
    test_emb = emb[test_mask]
    test_labels = labels[test_mask]
    strata = rc.stratify(rc.compute_smax(test_emb, panel_emb))
    if metric == "cascade":
        # cosine on the close stratum, Mahalanobis on moderate+distant (matches run_cascade.py)
        y_cos = rc.knn_cosine(test_emb, panel_emb, panel_labels, k)
        y_mah = rc.knn_mahalanobis(test_emb, panel_emb, panel_labels, k)
        y = np.where(strata["close"], y_cos, y_mah)
    else:
        y = _predict(metric, test_emb, panel_emb, panel_labels, k)
    out = {}
    for name, mask in strata.items():
        tp, fp, fn = _counts(test_labels[mask], y[mask])
        out[name] = rc._f1_from_counts(tp, fp, fn)
    tp, fp, fn = _counts(test_labels, y)
    out["pooled"] = rc._f1_from_counts(tp, fp, fn)
    out["gap"] = out["close"] - out["distant"]
    return out


# eval_cell()'s stratum names vs. the abbreviated suffixes run_cascade.py stores them
# under in the raw cells (e.g. "cosine_mod_f1", "cosine_dist_f1").
_STRATUM_TO_CELL_SUFFIX = {"close": "close_f1", "moderate": "mod_f1", "distant": "dist_f1",
                           "pooled": "pooled_f1"}


def committed_cascade_pooled() -> tuple[dict, dict]:
    """Per-stratum + pooled F1 already stored in the cascade cells (cosine/maha/learned/cascade).

    Returns (pooled, incomplete):
      pooled: {(scale, R, k, metric): {"close":..., "moderate":..., "distant":..., "pooled":...}},
        mean over whatever seed cells are actually on disk. Covers all fields eval_cell()
        produces (except "gap", which is derived as close - distant and so is implied by the
        close/distant checks) so a regression in stratification -- not just the whole-test-set
        pooled aggregate -- is caught by the cross-check.
      incomplete: {(scale, R, k): sorted list of seeds actually found}, populated only for
        groups whose on-disk seed set does not exactly equal SEEDS. A group missing even one
        of its 10 expected seed files would otherwise silently average over the seeds present
        and still count as "matched" in main()'s group-count check, hiding incomplete evidence
        behind a nine-seed mean that happens to land within tolerance.
    """
    import re
    pat = re.compile(r"cascade_(t\d+)_(\d+)_(\d+)_(\d+)\.npz")
    acc: dict = {}
    seeds_seen: dict = {}
    for f in CASCADE_DIR.glob("cascade_*.npz"):
        m = pat.match(f.name)
        if not m:
            continue
        scale, R, k, seed = m[1], int(m[2]), int(m[3]), int(m[4])
        seeds_seen.setdefault((scale, R, k), set()).add(seed)
        # cascade cells store only scalar/string arrays, so pickle is not needed
        with np.load(f, allow_pickle=False) as z:
            for met in ("cosine", "mahalanobis", "learned", "cascade"):
                key = (scale, R, k, met)
                entry = acc.setdefault(key, {fld: [] for fld in _STRATUM_TO_CELL_SUFFIX})
                for fld, suffix in _STRATUM_TO_CELL_SUFFIX.items():
                    entry[fld].append(float(z[f"{met}_{suffix}"]))
    expected_seeds = set(SEEDS)
    incomplete = {g: sorted(s) for g, s in seeds_seen.items() if s != expected_seeds}
    pooled = {key: {fld: float(np.mean(v)) for fld, v in fields.items()}
              for key, fields in acc.items()}
    return pooled, incomplete


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="regenerate and assert agreement with the committed summary (tolerance)")
    args = ap.parse_args()

    labels, _ = rc.load_labels()
    summary: dict = {}
    cas, incomplete_seed_groups = committed_cascade_pooled()
    if incomplete_seed_groups:
        print(f"FAIL: cascade cell seed set incomplete for {len(incomplete_seed_groups)} "
              f"(scale, R, k) group(s) (expected seeds {sorted(SEEDS)}):")
        for g, found in sorted(incomplete_seed_groups.items()):
            missing = sorted(set(SEEDS) - set(found))
            extra = sorted(set(found) - set(SEEDS))
            print(f"  {g}: found {found}  missing={missing}  extra={extra}")
        print("Aborting before the expensive re-derivation -- fix or regenerate the affected "
              "cascade cells first.")
        return 1
    max_drift = 0.0
    n_matched = 0
    EXPECTED_MATCHES = len(SCALES) * len(RS) * len(KS) * 4  # cosine/mahalanobis/learned/cascade
    for scale in SCALES:
        emb = rc.load_embeddings(scale)
        for R in RS:
            for k in KS:
                for metric in METRICS:
                    accs: dict = {}
                    for seed in SEEDS:
                        r = eval_cell(emb, labels, R, k, metric, seed)
                        for key, v in r.items():
                            accs.setdefault(key, []).append(v)
                    cell = {key: float(np.mean(v)) for key, v in accs.items()}
                    summary[f"{scale}_{R}_{k}_{metric}"] = cell
                    # cross-check vs committed cascade-cell evidence (cosine/maha/learned/cascade):
                    # close/moderate/distant too, not just the whole-test-set pooled aggregate, so
                    # a stratification regression can't hide behind an unchanged pooled value.
                    ck = (scale, R, k, metric)
                    if ck in cas:
                        n_matched += 1
                        for fld in ("close", "moderate", "distant", "pooled"):
                            drift = abs(cell[fld] - cas[ck][fld])
                            if not math.isfinite(drift):
                                print(f"FAIL: {scale}_{R}_{k}_{metric}.{fld}: drift is non-finite "
                                      f"(reproduced={cell[fld]!r}, committed={cas[ck][fld]!r}). Aborting.")
                                return 1
                            max_drift = max(max_drift, drift)
                            if drift > 1e-6:
                                print(f"  NOTE {scale}_{R}_{k}_{metric}.{fld}: reproduced "
                                      f"{cell[fld]:.6f} vs committed cascade {cas[ck][fld]:.6f} "
                                      f"(drift {drift:.2e})")
    print(f"cross-check vs committed cascade-cell evidence (cosine/maha/learned/cascade, "
          f"close/moderate/distant/pooled): max drift = {max_drift:.2e} over {n_matched} cells")
    if n_matched != EXPECTED_MATCHES:
        print(f"FAIL: only {n_matched}/{EXPECTED_MATCHES} cells matched committed cascade evidence "
              f"under {CASCADE_DIR} -- cascade cells are missing or incomplete, so the cross-check "
              f"did not actually validate the pipeline. Aborting.")
        return 1
    CROSS_TOL = 1e-3
    if max_drift > CROSS_TOL:
        print(f"FAIL: reproduced pooled drifted from the committed cascade cells by {max_drift:.2e} "
              f"(> {CROSS_TOL}); the pipeline does not match the committed evidence. Aborting.")
        return 1
    # Paper 2 Attempt-3: reproduce the cascade-vs-cosine pooled-F1 penalty range from this run.
    pens = [summary[f"{s}_{R}_{k}_cascade"]["pooled"] - summary[f"{s}_{R}_{k}_cosine"]["pooled"]
            for s in SCALES for R in RS for k in KS]
    if not all(math.isfinite(p) for p in pens):
        print(f"FAIL: non-finite cascade-vs-cosine penalty encountered: {pens}. Aborting.")
        return 1
    print(f"Attempt-3 cascade pooled-F1 penalty (cascade - cosine): "
          f"{min(pens):+.3f} to {max(pens):+.3f} over {len(pens)} groups (10-seed mean)")

    summary["_doc"] = ("Pooled (whole-test-set) F1 + per-stratum F1 + close-distant gap, 10-seed mean, "
                       "reproduced from committed embeddings via run_cliff/run_fisher. Keys: scale_R_k_metric. "
                       "cosine/mahalanobis/learned pooled cross-checked == committed cascade cells; fisher pooled "
                       "inherits the same validated pipeline. Regenerate with code/analyses/compute_pooled_f1.py.")

    if args.check:
        if not OUT.is_file():
            print(f"FAIL: --check requested but {OUT} does not exist.")
            return 1
        committed = json.loads(OUT.read_text(encoding="utf-8"))
        gen_keys = {k for k in summary if not k.startswith("_")}
        com_keys = {k for k in committed if not k.startswith("_")}
        if gen_keys != com_keys:
            print(f"FAIL: committed summary cell set differs from regenerated "
                  f"(missing {sorted(com_keys - gen_keys)}; extra {sorted(gen_keys - com_keys)}).")
            return 1
        worst = 0.0
        for key in gen_keys:
            # fisher uses LAPACK eigh (platform-sensitive) so gets a looser tolerance;
            # cosine/mahalanobis/learned/cascade are tightly reproducible and use the
            # same CROSS_TOL as the cascade cross-check above.
            metric = key.rsplit("_", 1)[-1]
            tol = 6e-3 if metric == "fisher" else CROSS_TOL
            for fld in ("close", "moderate", "distant", "pooled", "gap"):
                if fld not in summary[key] or fld not in committed[key]:
                    print(f"FAIL: field '{fld}' missing in cell '{key}'.")
                    return 1
                d = abs(summary[key][fld] - committed[key][fld])
                if not math.isfinite(d):
                    print(f"FAIL: {key}.{fld} drift is non-finite "
                          f"(summary={summary[key][fld]!r}, committed={committed[key][fld]!r}).")
                    return 1
                if d > tol:
                    print(f"FAIL: {key}.{fld} drift {d:.2e} exceeds tolerance {tol} "
                          f"for metric '{metric}'.")
                    return 1
                worst = max(worst, d)
        print(f"--check: worst field drift vs committed summary = {worst:.2e}")
        return 0

    OUT.write_text(json.dumps(summary, indent=1, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT} ({len([k for k in summary if not k.startswith('_')])} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
