"""Resolve Paper 5's two descriptive filter counts from immutable per-case data.

The original v1.6.0 manuscript and Zenodo deposit are not rewritten;
the dated erratum defines the corrected count predicates explicitly.
No embeddings, sequences, positive labels, or LFS payloads are loaded.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "data/results_summaries/cross_family_partition.json"
CONFIRMATION = ROOT / "data/results_summaries/cross_family_partition_10seed.json"
ERRATUM = ROOT / "docs/ERRATUM_2026-10-15.md"


def _counts(detail: list[dict]) -> dict[str, int]:
    known_query = [item for item in detail if item["q_pfam_known"]]
    known_voter = [item for item in detail if item["any_nbr_pfam_known"]]
    evaluable = [
        item for item in detail
        if item["q_pfam_known"] and item["any_nbr_pfam_known"]
    ]
    return {
        "false_positives": len(detail),
        "query_known": len(known_query),
        "voter_known": len(known_voter),
        "evaluable": len(evaluable),
        "within_family": sum(item["status"] == "WITHIN_FAMILY" for item in evaluable),
        "cross_family": sum(item["status"] == "CROSS_FAMILY" for item in evaluable),
    }


def test_paper5_filter_counts_are_supported_by_both_archived_results() -> None:
    """Direct row-level counts agree with the original and ten-seed summary."""
    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    confirm = json.loads(CONFIRMATION.read_text(encoding="utf-8"))
    same_seed = next(row for row in confirm["per_seed"] if row["seed"] == 20260410)
    expected = {
        "false_positives": 41,
        "query_known": 20,
        "voter_known": 41,
        "evaluable": 20,
        "within_family": 0,
        "cross_family": 20,
    }
    assert original["seed"] == 20260410
    assert original["R"] == 1000 and original["k"] == 25
    assert _counts(original["detail"]) == expected
    assert _counts(same_seed["detail"]) == expected
    assert original["n_distant_FP"] == same_seed["n_distant_false_positives"] == 41
    assert original["n_evaluable"] == same_seed["n_evaluable"] == 20
    assert original["within_family"] == same_seed["within_family"] == 0
    assert original["cross_family"] == same_seed["cross_family"] == 20


def test_erratum_explicitly_records_the_correct_filter_predicates() -> None:
    text = ERRATUM.read_text(encoding="utf-8")
    assert "correction from archived per-case fields" in text
    assert "| Query Pfam known | `q_pfam_known` is true | **20** |" in text
    assert "| At least one positive-voter Pfam known | `any_nbr_pfam_known` is true | **41** |" in text
    assert "| Evaluable (both Pfam sets known) | both flags true | **20** |" in text
    assert "original **36** should not be cited" in text
