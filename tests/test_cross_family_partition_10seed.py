"""Unit tests for the locked ten-seed cross-family aggregation logic.

These tests exercise deterministic summary/decision code and the input-integrity
preflight. They do not load the real embeddings, construct panels, or execute
any pre-registered experiment seed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
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


def _locked_input_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    paths = {
        "emb": tmp_path / "data" / "embeddings" / "embeddings_t30.npy",
        "seqs": tmp_path / "data" / "sequences" / "proteins_25k_sequences.json",
        "pfam": tmp_path / "data" / "annotations" / "proteins_25k_pfam.json",
    }
    payloads = {
        "emb": b"synthetic-test-bytes-for-integrity-only",
        "seqs": b'{"test_set": []}\n',
        "pfam": b'{"test_set": []}\n',
    }
    for key, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payloads[key])

    manifest = {}
    for path in paths.values():
        payload = path.read_bytes()
        manifest[path.relative_to(tmp_path).as_posix()] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }
    manifest_path = tmp_path / "MANIFEST.sha256.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr(MOD, "REPO", tmp_path)
    monkeypatch.setattr(MOD, "MANIFEST", manifest_path)
    monkeypatch.setattr(MOD, "EMB", paths["emb"])
    monkeypatch.setattr(MOD, "SEQS", paths["seqs"])
    monkeypatch.setattr(MOD, "PFAM", paths["pfam"])
    emb_payload = paths["emb"].read_bytes()
    monkeypatch.setattr(MOD, "PREREG_T30_SHA256", hashlib.sha256(emb_payload).hexdigest())
    monkeypatch.setattr(MOD, "PREREG_T30_BYTES", len(emb_payload))
    return paths


def test_wilson_zero_successes_matches_locked_formula() -> None:
    low, high = MOD.wilson_interval(0, 20)
    assert low == pytest.approx(0.0)
    assert high == pytest.approx(0.16112515805281938)


def test_wilson_undefined_for_zero_denominator() -> None:
    assert MOD.wilson_interval(0, 0) is None


def test_summarize_seed_counts_only_evaluable_cases_and_retains_full_detail() -> None:
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
    assert row["detail"] == detail
    assert row["evaluable_accessions"] == [
        {"acc": "A", "status": "CROSS_FAMILY"},
        {"acc": "B", "status": "WITHIN_FAMILY"},
    ]


def test_verify_locked_inputs_accepts_exact_hydrated_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _locked_input_fixture(tmp_path, monkeypatch)
    verified = MOD.verify_locked_inputs()
    for path in paths.values():
        rel = path.relative_to(tmp_path).as_posix()
        payload = path.read_bytes()
        assert verified[rel] == {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }


def test_verify_locked_inputs_rejects_manifest_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _locked_input_fixture(tmp_path, monkeypatch)
    paths["seqs"].write_bytes(paths["seqs"].read_bytes() + b"tampered")
    with pytest.raises(RuntimeError, match="Locked input mismatch"):
        MOD.verify_locked_inputs()


def test_verify_locked_inputs_rejects_unresolved_lfs_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _locked_input_fixture(tmp_path, monkeypatch)
    pointer = (
        b"version https://git-lfs.github.com/spec/v1\n"
        b"oid sha256:15d6e3656b46729a2483b7fbc603e49a61f25206e3854676bc2e528164608fd6\n"
        b"size 63705728\n"
    )
    paths["emb"].write_bytes(pointer)

    manifest_path = tmp_path / "MANIFEST.sha256.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rel = paths["emb"].relative_to(tmp_path).as_posix()
    manifest[rel] = {
        "sha256": hashlib.sha256(pointer).hexdigest(),
        "bytes": len(pointer),
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(MOD, "PREREG_T30_SHA256", hashlib.sha256(pointer).hexdigest())
    monkeypatch.setattr(MOD, "PREREG_T30_BYTES", len(pointer))

    with pytest.raises(RuntimeError, match="unresolved Git LFS pointer"):
        MOD.verify_locked_inputs()


def test_verify_locked_inputs_rejects_prereg_embedding_lock_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _locked_input_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(MOD, "PREREG_T30_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="Pre-registration t30 lock mismatch"):
        MOD.verify_locked_inputs()


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


def test_committed_confirmatory_result_matches_locked_summary() -> None:
    """The archived result must continue to support exactly the preregistered claim."""
    path = Path(__file__).resolve().parents[1] / "data" / "results_summaries" / "cross_family_partition_10seed.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    assert [row["seed"] for row in d["per_seed"]] == list(MOD.SEEDS)
    assert len(d["per_seed"]) == 10
    assert all(row["n_evaluable"] > 0 for row in d["per_seed"])
    assert all(row["cross_family"] > row["within_family"] for row in d["per_seed"])

    s = d["cross_family_fraction_across_seeds"]
    assert s["mean"] == pytest.approx(0.9941130298273156)
    assert s["median"] == pytest.approx(1.0)
    assert s["min"] == pytest.approx(25 / 26)
    assert s["max"] == pytest.approx(1.0)

    assert d["zero_evaluable_seeds"] == []
    assert d["decision"] == {
        "cross_gt_within_every_nonzero_seed": True,
        "median_cross_family_fraction_ge_0_80": True,
        "all_ten_seeds_nonzero_evaluable": True,
        "strong_robustness_claim": True,
    }
    a = d["accession_summary"]
    assert a["n_unique_evaluable_accessions"] == 102
    assert a["n_always_cross_family"] == 101
    assert a["n_always_within_family"] == 1
    assert a["n_mixed"] == 0
