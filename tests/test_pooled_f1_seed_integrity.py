"""Regression tests for compute_pooled_f1.committed_cascade_pooled()'s cascade
seed-file integrity checks.

PR #33's third and fourth review-hardening rounds added two checks that
main() runs before trusting the committed cascade evidence:

  1. completeness -- every (scale, R, k) group must have exactly the 10
     expected SEEDS on disk, not a subset (a missing file would otherwise
     silently average over fewer seeds and still "match").
  2. no duplicates -- no seed within a group may be backed by more than one
     file (e.g. a zero-padded filename parsing to an already-seen seed
     integer), which the seed-*set* check alone cannot see because the
     duplicate seed value collapses into the set while its data still
     accumulates into the mean.

These tests pin that detection logic directly so a future edit cannot
regress it silently. Style matches tests/test_numerics_known_answer.py:
synthetic fixtures via tmp_path + monkeypatch, numpy-only (compute_pooled_f1
imports run_cliff/run_fisher, which defer faiss/torch to call sites, so
importing it needs no heavy dependency and no LFS data).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "code" / "harnesses"))
sys.path.insert(0, str(REPO_ROOT / "code" / "analyses"))

import compute_pooled_f1  # noqa: E402

_METRICS = ("cosine", "mahalanobis", "learned", "cascade")


def _write_cell(cascade_dir, scale, R, k, seed, *, filename=None, value=0.5):
    """Write a synthetic cascade_{scale}_{R}_{k}_{seed}.npz with all 16 scalar
    fields committed_cascade_pooled() reads (4 metrics x close/mod/dist/pooled)."""
    fields = {}
    for met in _METRICS:
        for suffix in compute_pooled_f1._STRATUM_TO_CELL_SUFFIX.values():
            fields[f"{met}_{suffix}"] = np.float64(value)
    name = filename or f"cascade_{scale}_{R}_{k}_{seed}.npz"
    np.savez(cascade_dir / name, **fields)


def test_complete_group_no_incomplete_no_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    for seed in compute_pooled_f1.SEEDS:
        _write_cell(tmp_path, "t6", 100, 5, seed)
    pooled, incomplete, duplicates = compute_pooled_f1.committed_cascade_pooled()
    assert incomplete == {}
    assert duplicates == {}
    key = ("t6", 100, 5, "cosine")
    assert key in pooled
    assert pooled[key]["pooled"] == pytest.approx(0.5)


def test_missing_seed_flagged_incomplete(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    seeds = compute_pooled_f1.SEEDS[:-1]  # drop one of the 10 expected seeds
    for seed in seeds:
        _write_cell(tmp_path, "t6", 100, 5, seed)
    pooled, incomplete, duplicates = compute_pooled_f1.committed_cascade_pooled()
    assert duplicates == {}
    group = ("t6", 100, 5)
    assert group in incomplete
    assert sorted(incomplete[group]) == sorted(seeds)
    assert set(compute_pooled_f1.SEEDS) - set(seeds) == {compute_pooled_f1.SEEDS[-1]}


def test_extra_unexpected_seed_flagged_incomplete(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    for seed in compute_pooled_f1.SEEDS:
        _write_cell(tmp_path, "t6", 100, 5, seed)
    extra_seed = 99999999
    _write_cell(tmp_path, "t6", 100, 5, extra_seed)
    pooled, incomplete, duplicates = compute_pooled_f1.committed_cascade_pooled()
    assert duplicates == {}
    group = ("t6", 100, 5)
    assert group in incomplete
    assert extra_seed in incomplete[group]


def test_zero_padded_duplicate_seed_file_flagged(tmp_path, monkeypatch):
    """The exact scenario from PR #33's fourth review round: a zero-padded
    filename parses to an already-seen seed integer. The seed *set* still
    looks complete (10 distinct seed values across 11 files), so this must
    be caught by the duplicate check specifically, not the completeness
    check."""
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    for seed in compute_pooled_f1.SEEDS:
        _write_cell(tmp_path, "t6", 100, 5, seed)
    dup_seed = compute_pooled_f1.SEEDS[0]
    dup_name = f"cascade_t6_100_5_0{dup_seed}.npz"  # zero-padded -> same int value
    _write_cell(tmp_path, "t6", 100, 5, dup_seed, filename=dup_name)

    pooled, incomplete, duplicates = compute_pooled_f1.committed_cascade_pooled()
    group = ("t6", 100, 5)
    assert group not in incomplete, (
        "the 10-seed *set* is unchanged by a same-seed duplicate file -- confirming "
        "the completeness check alone cannot catch this case"
    )
    assert group in duplicates
    assert duplicates[group].keys() == {dup_seed}
    assert sorted(duplicates[group][dup_seed]) == sorted(
        [f"cascade_t6_100_5_{dup_seed}.npz", dup_name]
    )


def test_real_committed_cascade_evidence_shape_if_hydrated():
    """If real committed cascade evidence is present (LFS payload hydrated),
    it must be exactly 18 groups x 10 seeds = 180 files with zero duplicates
    and zero incomplete groups -- the invariant PR #33's hardening protects.
    Skips cleanly on LFS pointer stubs, matching tests/test_cell_schema.py."""
    files = sorted(compute_pooled_f1.CASCADE_DIR.glob("cascade_*.npz"))
    if not files:
        pytest.skip(f"No cascade cells found at {compute_pooled_f1.CASCADE_DIR}")
    with open(files[0], "rb") as fh:
        if fh.read(64).startswith(b"version https://git-lfs.github.com/spec/v1"):
            pytest.skip(
                "cascade cells are LFS pointer stubs in this environment "
                "(no `git lfs pull` performed)."
            )
    expected_groups = len(compute_pooled_f1.SCALES) * len(compute_pooled_f1.RS) * len(compute_pooled_f1.KS)
    assert expected_groups == 18
    assert len(files) == expected_groups * len(compute_pooled_f1.SEEDS) == 180
    pooled, incomplete, duplicates = compute_pooled_f1.committed_cascade_pooled()
    assert incomplete == {}, f"incomplete cascade seed groups: {incomplete}"
    assert duplicates == {}, f"duplicate cascade seed files: {duplicates}"
    assert len(pooled) == expected_groups * len(_METRICS)
