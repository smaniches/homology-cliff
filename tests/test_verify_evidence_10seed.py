"""Regression tests for the hardened ten-seed evidence check.

`scripts/ci/verify_evidence.py::check_cross_family_10seed` must derive every
per-seed fraction, across-seed aggregate, and decision boolean independently
from the raw per-seed counts and reject any file whose stored derived fields
disagree -- in particular a file where a per-seed count was altered while the
stale aggregate/decision fields were left unchanged.

The tests start from the sealed confirmatory result (read-only), write
tampered copies to tmp_path, and assert the check fails closed. The sealed
file itself is never modified.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFIER = REPO_ROOT / "scripts" / "ci" / "verify_evidence.py"
SEALED = (
    REPO_ROOT / "data" / "results_summaries" / "cross_family_partition_10seed.json"
)


def _load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_evidence_under_test", VERIFIER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load_verifier()


def _sealed() -> dict[str, Any]:
    return json.loads(SEALED.read_text(encoding="utf-8"))


def _write(tmp_path: Path, doc: dict[str, Any]) -> Path:
    path = tmp_path / "cross_family_partition_10seed.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _seed_row(doc: dict[str, Any], seed: int) -> dict[str, Any]:
    for row in doc["per_seed"]:
        if row["seed"] == seed:
            return row
    raise AssertionError(f"seed {seed} not found")


def test_sealed_result_passes() -> None:
    """The committed confirmatory result satisfies the hardened check."""
    assert MOD.check_cross_family_10seed() is True


def test_sealed_copy_passes(tmp_path: Path) -> None:
    """A byte-equivalent copy passes via the explicit path parameter."""
    assert MOD.check_cross_family_10seed(_write(tmp_path, _sealed())) is True


def test_altered_count_with_stale_derived_fields_rejected(tmp_path: Path) -> None:
    """The late-review scenario: a per-seed count is edited so the counts stay
    internally consistent, but every stored derived field (per-row fraction,
    aggregates, decision) is left stale. The check must reject it."""
    doc = _sealed()
    row = _seed_row(doc, 20260412)  # sealed: cross=48, within=1, n_evaluable=49
    row["within_family"] = 0
    row["cross_family"] = 49
    assert MOD.check_cross_family_10seed(_write(tmp_path, doc)) is False


def test_internally_inconsistent_counts_rejected(tmp_path: Path) -> None:
    """cross_family + within_family != n_evaluable must fail."""
    doc = _sealed()
    _seed_row(doc, 20260410)["cross_family"] += 1
    assert MOD.check_cross_family_10seed(_write(tmp_path, doc)) is False


def test_stale_per_row_fraction_rejected(tmp_path: Path) -> None:
    """A stored per-row fraction that disagrees with cross/n_evaluable fails."""
    doc = _sealed()
    _seed_row(doc, 20260415)["cross_family_fraction"] = 0.5
    assert MOD.check_cross_family_10seed(_write(tmp_path, doc)) is False


def test_stale_aggregate_mean_rejected(tmp_path: Path) -> None:
    """A stored across-seed mean that disagrees with the derived mean fails."""
    doc = _sealed()
    doc["cross_family_fraction_across_seeds"]["mean"] += 1e-6
    assert MOD.check_cross_family_10seed(_write(tmp_path, doc)) is False


def test_stale_decision_booleans_rejected(tmp_path: Path) -> None:
    """Counts edited so cross no longer beats within, while the stored decision
    object still claims strong robustness, must fail."""
    doc = _sealed()
    row = _seed_row(doc, 20260410)  # sealed: cross=20, within=0, n_evaluable=20
    row["cross_family"] = 0
    row["within_family"] = 20
    row["cross_family_fraction"] = 0.0
    assert doc["decision"]["strong_robustness_claim"] is True  # left stale
    assert MOD.check_cross_family_10seed(_write(tmp_path, doc)) is False


def test_stale_zero_evaluable_seed_list_rejected(tmp_path: Path) -> None:
    """A seed zeroed out while zero_evaluable_seeds and the decision object
    remain stale must fail."""
    doc = _sealed()
    row = _seed_row(doc, 20260417)
    row["cross_family"] = 0
    row["within_family"] = 0
    row["n_evaluable"] = 0
    row["cross_family_fraction"] = None
    assert doc["zero_evaluable_seeds"] == []  # left stale
    assert MOD.check_cross_family_10seed(_write(tmp_path, doc)) is False
