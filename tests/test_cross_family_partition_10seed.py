"""Unit tests for the locked ten-seed cross-family aggregation logic.

These tests exercise only deterministic summary/decision code. They do not load
embeddings, construct panels, or execute any pre-registered experiment seed.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "code"
    / "analyses"
    / "run_cross_family_partition_10seed.py"
)
SPEC = importlib.util.spec_from_file_location("cross_family_10seed", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def _row(seed: int, statuses: list[tuple[str, str]]) -> dict:
    detail = [
        {
            "acc": acc,
            "status": status,
            "q_pfam_known": True,
            "any_nbr_pfam_known": True,
        }
        for acc, status in statuses
    ]
    return MOD.summarize_seed(seed, n_distant=len(detail) + 3, detail=detail)


def test_wilson_zero_successes_matches_locked_formula() -> None:
    low, high = MOD.wilson_interval(0, 20)
    assert low == pytest.approx(0.0)
    assert high == pytest.approx(0.16112515805281938)


def test_wilson_undefined_for_zero_denominator() -> None:
    assert MOD.wilson_interval(0, 0) is None


def test_summarize_seed_counts_only_evaluable_cases() -> None:
    detail = [
        {
            "acc": "A",
            "status": "CROSS_FAMILY",
            "q_pfam_known": True,
            "any_nbr_pfam_known": True,
        },
        {
            "acc": "B",
            "status": "WITHIN_FAMILY",
            "q_pfam_known": True,
            "any_nbr_pfam_known": True,
        },
        {
            "acc": "C",
            "status": "CROSS_FAMILY",
            "q_pfam_known": False,
            "any_nbr_pfam_known": True,
        },
    ]
    row = MOD.summarize_seed(20260410, 11, detail)
    assert row["n_distant"] == 11
    assert row["n_distant_false_positives"] == 3
    assert row["n_evaluable"] == 2
    assert row["within_family"] == 1
    assert row["cross_family"] == 1
    assert row["within_family_fraction"] == pytest.approx(0.5)
    assert row["cross_family_fraction"] == pytest.approx(0.5)
    assert row["evaluable_accessions"] == [
        {"acc": "A", "status": "CROSS_FAMILY"},
        {"acc": "B", "status": "WITHIN_FAMILY"},
    ]


def test_aggregate_uses_unweighted_seed_fractions_and_accession_histories() -> None:
    rows = [
        _row(1, [("A", "CROSS_FAMILY"), ("B", "CROSS_FAMILY")]),
        _row(2, [("A", "WITHIN_FAMILY"), ("C", "CROSS_FAMILY")]),
        _row(3, [("D", "CROSS_FAMILY")]),
    ]
    out = MOD.aggregate(rows)
    fractions = out["cross_family_fraction_across_seeds"]
    assert fractions["mean"] == pytest.approx((1.0 + 0.5 + 1.0) / 3.0)
    assert fractions["median"] == pytest.approx(1.0)
    assert fractions["min"] == pytest.approx(0.5)
    assert fractions["max"] == pytest.approx(1.0)

    accessions = out["accession_summary"]
    assert accessions["n_unique_evaluable_accessions"] == 4
    assert accessions["n_always_cross_family"] == 3
    assert accessions["n_always_within_family"] == 0
    assert accessions["n_mixed"] == 1
    assert out["decision"]["strong_robustness_claim"] is False


def test_zero_evaluable_seed_withholds_strong_claim() -> None:
    good = _row(1, [("A", "CROSS_FAMILY")])
    zero = MOD.summarize_seed(2, n_distant=4, detail=[])
    out = MOD.aggregate([good, zero])
    assert out["zero_evaluable_seeds"] == [2]
    assert out["decision"]["cross_gt_within_every_nonzero_seed"] is True
    assert out["decision"]["median_cross_family_fraction_ge_0_80"] is True
    assert out["decision"]["all_ten_seeds_nonzero_evaluable"] is False
    assert out["decision"]["strong_robustness_claim"] is False


def test_strong_rule_requires_cross_majority_and_median_threshold() -> None:
    passing = [_row(seed, [(f"A{seed}", "CROSS_FAMILY")]) for seed in range(10)]
    assert MOD.aggregate(passing)["decision"]["strong_robustness_claim"] is True

    failing = list(passing)
    failing[0] = _row(0, [("X", "WITHIN_FAMILY")])
    assert MOD.aggregate(failing)["decision"]["strong_robustness_claim"] is False
