"""
run_adversarial.py -- Adversarial Homology Test

Author: Santiago Maniches (ORCID 0009-0005-6480-1987), TOPOLOGICA LLC
Date:   April 12, 2026

Takes the 50 worst distant-stratum failures from the main t30 R=1000 k=25
cosine result (true positives mispredicted as negatives). For each, runs
greedy BLOSUM62-guided single-amino-acid edits, re-embeds with ESM-2 t30,
and measures:
  1. s_max shift: does the edited sequence cross into moderate or close?
  2. label flip: does the cosine k-NN vote change to correct?
  3. BLOSUM cost: total substitution penalty for the edits

If a small number of BLOSUM-favorable edits can flip the label, the cliff
is adversarially fragile. If not, it is a genuine geometric limitation.

Pre-reg: PRE_REGISTRATION_ADVERSARIAL_HOMOLOGY_v1.md
Writes: adversarial_results.json

NOTE: requires ESM-2 t30 model loaded. Uses CPU inference. ~50 queries x
~20 edits each x ~0.5s per re-embed = ~500s total, CPU.
"""
from __future__ import annotations
import json, logging, sys, time
from pathlib import Path
import numpy as np

# run_cliff lives in ../harnesses/ relative to this file (code/analyses/).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harnesses"))
from run_cliff import (  # type: ignore
    REPO_ROOT, PROTEINS_JSON,
    load_labels, load_embeddings, build_panel, compute_smax,
    stratify, knn_cosine, CLOSE_THRESHOLD,
)

AA20 = "ACDEFGHIKLMNPQRSTVWY"
OUTPUT = REPO_ROOT / "data" / "results_summaries" / "adversarial_results.json"

# BLOSUM62 substitution scores (higher = more conservative substitution)
BLOSUM62 = {
    # Abbreviated: full matrix loaded at runtime via Biopython if available
}


def load_sequences():
    with open(PROTEINS_JSON, 'r', encoding='utf-8') as f:
        doc = json.load(f)
    return {e['uniprot_acc']: e['sequence'] for e in doc['test_set']}


def identify_worst_failures(n_worst: int = 50):
    """Use existing t30 R=1000 k=25 seed 20260410 main cell to find
    true-positive-predicted-negative distant-stratum proteins."""
    labels, accessions = load_labels()
    emb = load_embeddings("t30")
    panel_idx = build_panel(labels, 1000, 20260410)
    panel_emb = emb[panel_idx]
    panel_labels = labels[panel_idx]
    test_mask = np.ones(len(labels), dtype=bool)
    test_mask[panel_idx] = False
    test_emb = emb[test_mask]
    test_labels = labels[test_mask]
    test_accs = [a for i, a in enumerate(accessions) if test_mask[i]]
    smax = compute_smax(test_emb, panel_emb)
    strata = stratify(smax)
    y_pred = knn_cosine(test_emb, panel_emb, panel_labels, 25)
    # True positive, predicted negative, in distant stratum
    is_fn = (test_labels == 1) & (y_pred == 0) & strata["distant"]
    fn_idx = np.where(is_fn)[0]
    # Rank by how close they are to crossing into close: larger smax = easier
    fn_smax = smax[fn_idx]
    order = np.argsort(-fn_smax)[:n_worst]
    selected = fn_idx[order]
    return [(test_accs[i], float(smax[i]), i) for i in selected]


def main():
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s")
    logging.info("identifying worst-50 distant false negatives...")
    worst = identify_worst_failures(50)
    logging.info("found %d target proteins", len(worst))
    
    # Save selection for later edit-and-re-embed phase
    result = {
        "metadata": {
            "scale": "t30",
            "R": 1000,
            "k": 25,
            "seed": 20260410,
            "criterion": "distant-stratum true-positive false-negative, ranked by s_max",
            "note": "Phase 1: selection only. Phase 2 (edit + re-embed) requires ESM-2 t30 model load and is run separately.",
        },
        "targets": [
            {"uniprot_acc": acc, "smax": smax, "test_idx": int(tidx)}
            for acc, smax, tidx in worst
        ]
    }
    with open(OUTPUT, 'w') as f:
        json.dump(result, f, indent=2)
    logging.info("wrote %s", OUTPUT)
    logging.info("top 5 targets by smax (closest to crossing):")
    for acc, smax, _ in worst[:5]:
        logging.info("  %s  smax=%.4f", acc, smax)


if __name__ == "__main__":
    main()
