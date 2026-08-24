"""Confirmatory ten-seed cross-family Pfam partition.

Implements the protocol locked in
``data/prereg/PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md``.  This module is
import-safe: importing it does not load the experiment data or execute any
seed.  Running the file first verifies the three locked experiment inputs,
then executes all ten fixed seeds, verifies that seed 20260410 reproduces the
committed single-seed artifact, and only then writes
``data/results_summaries/cross_family_partition_10seed.json``.

Do not change protocol constants without creating and locking a new
pre-registration.  In particular, do not pool recurring accessions across
seeds for a binomial confidence interval: the panel seed is the robustness
unit.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "MANIFEST.sha256.json"
EMB = REPO / "data" / "embeddings" / "embeddings_t30.npy"
PFAM = REPO / "data" / "annotations" / "proteins_25k_pfam.json"
SEQS = REPO / "data" / "sequences" / "proteins_25k_sequences.json"
SINGLE_SEED_RESULT = REPO / "data" / "results_summaries" / "cross_family_partition.json"
OUT = REPO / "data" / "results_summaries" / "cross_family_partition_10seed.json"

R = 1000
K = 25
SCALE = "t30"
DISTANT_THRESHOLD = 0.90
SEEDS = tuple(range(20260410, 20260420))
Z_95 = 1.959963984540054

# Independent lock written into the pre-registration.  The runtime preflight
# checks this in addition to the repository manifest so a later manifest edit
# cannot silently redefine the frozen t30 input.
PREREG_T30_SHA256 = "15d6e3656b46729a2483b7fbc603e49a61f25206e3854676bc2e528164608fd6"
PREREG_T30_BYTES = 63705728
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def _repo_relative(path: Path) -> str:
    """Return a stable repository-relative POSIX path for audit metadata."""
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"Locked input is outside repository root: {path}") from exc


def _hash_real_file(path: Path, rel_path: str) -> tuple[str, int]:
    """Hash one hydrated input and reject Git-LFS pointer stubs explicitly."""
    if not path.is_file():
        raise RuntimeError(f"Locked input is missing: {rel_path}")

    digest = hashlib.sha256()
    total = 0
    with open(path, "rb") as fh:
        first = fh.read(64)
        if first.startswith(LFS_PREFIX):
            raise RuntimeError(
                f"Locked input {rel_path} is an unresolved Git LFS pointer; "
                "hydrate Git LFS before any confirmatory seed is run."
            )
        digest.update(first)
        total += len(first)
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
    return digest.hexdigest(), total


def verify_locked_inputs() -> dict[str, dict[str, Any]]:
    """Fail closed unless all three pre-registered inputs match their locks.

    The repository manifest is the canonical lock for all three inputs.  The
    embedding additionally has an explicit SHA256 and byte count in the locked
    ten-seed pre-registration, so both sources must agree with the actual
    hydrated file before ``load_inputs`` is allowed to run.
    """
    if not MANIFEST.is_file():
        raise RuntimeError("MANIFEST.sha256.json is missing; refusing confirmatory run.")
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Could not read MANIFEST.sha256.json; refusing confirmatory run.") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError("MANIFEST.sha256.json has an invalid top-level format.")

    verified: dict[str, dict[str, Any]] = {}
    for path in (EMB, SEQS, PFAM):
        rel_path = _repo_relative(path)
        expected = manifest.get(rel_path)
        if not isinstance(expected, dict):
            raise RuntimeError(f"Manifest has no lock record for required input: {rel_path}")
        expected_sha = expected.get("sha256")
        expected_bytes = expected.get("bytes")
        if not isinstance(expected_sha, str) or not isinstance(expected_bytes, int):
            raise RuntimeError(f"Manifest lock record is malformed for required input: {rel_path}")

        actual_sha, actual_bytes = _hash_real_file(path, rel_path)
        if actual_sha != expected_sha or actual_bytes != expected_bytes:
            raise RuntimeError(
                f"Locked input mismatch for {rel_path}: "
                f"manifest sha256={expected_sha}, bytes={expected_bytes}; "
                f"actual sha256={actual_sha}, bytes={actual_bytes}. "
                "Refusing to run any confirmatory seed."
            )

        if path == EMB and (
            actual_sha != PREREG_T30_SHA256 or actual_bytes != PREREG_T30_BYTES
        ):
            raise RuntimeError(
                f"Pre-registration t30 lock mismatch for {rel_path}: "
                f"expected sha256={PREREG_T30_SHA256}, bytes={PREREG_T30_BYTES}; "
                f"actual sha256={actual_sha}, bytes={actual_bytes}. "
                "Refusing to run any confirmatory seed."
            )

        verified[rel_path] = {"sha256": actual_sha, "bytes": actual_bytes}

    return verified


def wilson_interval(within: int, n: int) -> list[float] | None:
    """Locked two-sided 95% Wilson interval for the within-family fraction."""
    if n == 0:
        return None
    if within < 0 or within > n:
        raise ValueError("within must satisfy 0 <= within <= n")
    p = within / n
    z2 = Z_95 * Z_95
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    half = (Z_95 / denom) * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))
    return [max(0.0, center - half), min(1.0, center + half)]


def summarize_seed(seed: int, n_distant: int, detail: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the pre-registered per-seed summary from distant-FP detail rows."""
    evaluable = [d for d in detail if d["q_pfam_known"] and d["any_nbr_pfam_known"]]
    within = sum(d["status"] == "WITHIN_FAMILY" for d in evaluable)
    cross = sum(d["status"] == "CROSS_FAMILY" for d in evaluable)
    n_eval = len(evaluable)
    within_fraction = within / n_eval if n_eval else None
    cross_fraction = cross / n_eval if n_eval else None
    return {
        "seed": seed,
        "n_distant": int(n_distant),
        "n_distant_false_positives": len(detail),
        "n_evaluable": n_eval,
        "within_family": within,
        "cross_family": cross,
        "within_family_fraction": within_fraction,
        "cross_family_fraction": cross_fraction,
        "within_family_wilson_95": wilson_interval(within, n_eval),
        # Retain every distant false positive, including non-evaluable cases.
        # This is the audit trail promised by the locked protocol; denominators
        # still use only evaluable rows above.
        "detail": detail,
        "evaluable_accessions": [
            {"acc": d["acc"], "status": d["status"]} for d in evaluable
        ],
    }


def aggregate(per_seed: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the locked seed-level aggregate and descriptive accession summary."""
    qualifying = [s for s in per_seed if s["n_evaluable"] > 0]
    fractions = np.asarray([s["cross_family_fraction"] for s in qualifying], dtype=float)
    zero_evaluable = [s["seed"] for s in per_seed if s["n_evaluable"] == 0]

    if len(fractions):
        seed_fraction_summary: dict[str, float | None] = {
            "mean": float(np.mean(fractions)),
            "median": float(np.median(fractions)),
            "min": float(np.min(fractions)),
            "max": float(np.max(fractions)),
        }
    else:
        seed_fraction_summary = {"mean": None, "median": None, "min": None, "max": None}

    records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for seed_row in per_seed:
        for row in seed_row["evaluable_accessions"]:
            records[row["acc"]].append({"seed": seed_row["seed"], "status": row["status"]})

    accession_rows = []
    always_cross = always_within = mixed = 0
    for acc in sorted(records):
        acc_records = sorted(records[acc], key=lambda r: r["seed"])
        statuses = {r["status"] for r in acc_records}
        if statuses == {"CROSS_FAMILY"}:
            always_cross += 1
        elif statuses == {"WITHIN_FAMILY"}:
            always_within += 1
        elif len(acc_records) >= 2 and statuses == {"CROSS_FAMILY", "WITHIN_FAMILY"}:
            mixed += 1
        else:
            raise RuntimeError(f"Unexpected status set for {acc}: {statuses}")
        accession_rows.append({"acc": acc, "records": acc_records})

    all_nonzero_cross_majority = bool(qualifying) and all(
        s["cross_family"] > s["within_family"] for s in qualifying
    )
    median_cross = seed_fraction_summary["median"]
    median_at_least_080 = median_cross is not None and median_cross >= 0.80
    strong_robust = not zero_evaluable and all_nonzero_cross_majority and median_at_least_080

    return {
        "cross_family_fraction_across_seeds": seed_fraction_summary,
        "zero_evaluable_seeds": zero_evaluable,
        "accession_summary": {
            "n_unique_evaluable_accessions": len(accession_rows),
            "n_always_cross_family": always_cross,
            "n_always_within_family": always_within,
            "n_mixed": mixed,
            "accessions": accession_rows,
        },
        "decision": {
            "cross_gt_within_every_nonzero_seed": all_nonzero_cross_majority,
            "median_cross_family_fraction_ge_0_80": median_at_least_080,
            "all_ten_seeds_nonzero_evaluable": not zero_evaluable,
            "strong_robustness_claim": strong_robust,
        },
    }


def run_seed(
    seed: int,
    labels: np.ndarray,
    accs: list[str],
    emb: np.ndarray,
    pfam_by_acc: dict[str, set[str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Execute one fixed panel seed under the locked single-seed algorithm."""
    import faiss

    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    rng = np.random.default_rng(seed + R)
    panel = np.concatenate(
        [
            rng.choice(pos_idx, R // 2, replace=False),
            rng.choice(neg_idx, R // 2, replace=False),
        ]
    )
    panel_labels = labels[panel]
    test_mask = np.ones(len(labels), dtype=bool)
    test_mask[panel] = False
    test_idx = np.where(test_mask)[0]
    pe = emb[panel]
    te = emb[test_idx]

    index = faiss.IndexFlatIP(pe.shape[1])
    index.add(pe.astype(np.float32))
    sims, _ = index.search(te.astype(np.float32), 1)
    distant = sims[:, 0] < DISTANT_THRESHOLD

    _, nbrs = index.search(te.astype(np.float32), K)
    votes = panel_labels[nbrs]
    preds = (votes.sum(1) * 2 >= K).astype(np.int64)
    true_labels = labels[test_idx]
    fp_mask = distant & (preds == 1) & (true_labels == 0)

    detail: list[dict[str, Any]] = []
    for ti in np.where(fp_mask)[0]:
        q_acc = accs[test_idx[ti]]
        q_pfam = pfam_by_acc.get(q_acc, set())
        pos_voters = [
            panel[nbrs[ti, j]] for j in range(K) if panel_labels[nbrs[ti, j]] == 1
        ]
        nbr_pfams: set[str] = set()
        for pi in pos_voters:
            nbr_pfams |= pfam_by_acc.get(accs[pi], set())
        shared = q_pfam & nbr_pfams
        detail.append(
            {
                "acc": q_acc,
                "q_pfam": sorted(q_pfam),
                "nbr_pfam_union": sorted(nbr_pfams),
                "shared": sorted(shared),
                "status": "WITHIN_FAMILY" if shared else "CROSS_FAMILY",
                "q_pfam_known": bool(q_pfam),
                "any_nbr_pfam_known": bool(nbr_pfams),
            }
        )

    return summarize_seed(seed, int(distant.sum()), detail), detail


def verify_single_seed_reproduction(summary: dict[str, Any], detail: list[dict[str, Any]]) -> None:
    """Require the re-derived first seed to reproduce the committed artifact exactly."""
    with open(SINGLE_SEED_RESULT, encoding="utf-8") as fh:
        committed = json.load(fh)
    expected = {
        "seed": committed["seed"],
        "n_distant_false_positives": committed["n_distant_FP"],
        "n_evaluable": committed["n_evaluable"],
        "within_family": committed["within_family"],
        "cross_family": committed["cross_family"],
    }
    observed = {key: summary[key] for key in expected}
    if observed != expected or detail != committed["detail"]:
        raise RuntimeError(
            "Seed 20260410 failed to reproduce the committed single-seed artifact; "
            "refusing to continue or write a ten-seed result."
        )


def load_inputs() -> tuple[np.ndarray, list[str], np.ndarray, dict[str, set[str]]]:
    with open(SEQS, encoding="utf-8") as fh:
        seqs_doc = json.load(fh)
    with open(PFAM, encoding="utf-8") as fh:
        pfam_doc = json.load(fh)
    entries = seqs_doc["test_set"]
    pfam_by_acc = {
        e["uniprot_acc"]: set(e.get("pfam_ids", [])) for e in pfam_doc["test_set"]
    }
    labels = np.asarray([e["true_label"] for e in entries], dtype=np.int64)
    accs = [e["uniprot_acc"] for e in entries]
    emb = np.load(EMB).astype(np.float32, copy=True)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8
    return labels, accs, emb, pfam_by_acc


def main() -> int:
    verified_inputs = verify_locked_inputs()
    labels, accs, emb, pfam_by_acc = load_inputs()
    per_seed: list[dict[str, Any]] = []

    for seed in SEEDS:
        summary, detail = run_seed(seed, labels, accs, emb, pfam_by_acc)
        if seed == SEEDS[0]:
            verify_single_seed_reproduction(summary, detail)
        per_seed.append(summary)

    result = {
        "protocol": {
            "preregistration": "data/prereg/PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md",
            "R": R,
            "k": K,
            "scale": SCALE,
            "distant_threshold": DISTANT_THRESHOLD,
            "seeds": list(SEEDS),
            "robustness_unit": "panel_seed",
            "pooled_binomial_interval": False,
        },
        "input_integrity": {
            "manifest": "MANIFEST.sha256.json",
            "verified_inputs": verified_inputs,
        },
        "per_seed": per_seed,
        **aggregate(per_seed),
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
