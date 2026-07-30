"""Regression tests for compute_pooled_f1's cascade seed-file integrity checks.

PR #33's review rounds added five checks that main() runs before trusting the
committed cascade evidence, in the order main() applies them:

  0. exact inventory -- the on-disk cascade_*.npz filename set (raw string
     comparison, no regex parsing) must exactly equal the canonical 180-name
     grid (3 scales x 3 panel sizes x 2 neighbor counts x 10 seeds), checked
     BEFORE any cell is loaded. This is the first-line defense: a malformed or
     noncanonical name that still matches the `cascade_*.npz` glob (a stray
     suffix, a zero-padded duplicate, a typo) would otherwise fail the per-file
     regex parser silently (`pat.match()` with no `$`/fullmatch anchor just
     `continue`s past it) and vanish from every other check with zero record.
  1. completeness -- every *expected* (scale, R, k) group (from the SCALES x
     RS x KS grid, including a group with zero files on disk) must have
     exactly the 10 expected SEEDS, not a subset (a missing file would
     otherwise silently average over fewer seeds and still "match").
  2. no duplicates -- no seed within a group may be backed by more than one
     file (e.g. a zero-padded filename parsing to an already-seen seed
     integer), which the seed-*set* check alone cannot see because the
     duplicate seed value collapses into the set while its data still
     accumulates into the mean.
  3. no unexpected groups -- a fully-populated, non-duplicate group whose
     (scale, R, k) key falls outside the expected grid entirely would pass
     both checks above (its seed set and file count are fine) while never
     being validated by the per-group cross-check loop, which only ever
     visits the expected grid. (Also caught by check 0 above; retained as
     defense in depth against a bug there.)
  4. embedded-identity match -- a cell's (scale, R, k, seed) recorded inside
     the .npz itself (run_cascade.py writes these) must agree with the
     identity parsed from its filename, catching e.g. a file overwritten
     with another seed's payload -- a case check 0 cannot catch, since it
     only ever compares filenames, never file content.

These tests pin that detection logic directly so a future edit cannot
regress it silently. Style matches tests/test_numerics_known_answer.py:
synthetic fixtures via tmp_path + monkeypatch, numpy-only (compute_pooled_f1
imports run_cliff/run_fisher, which defer faiss/torch to call sites, so
importing it needs no heavy dependency, no faiss/torch, and no LFS data).
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


def _write_cell(cascade_dir, scale, R, k, seed, *, filename=None, value=0.5, embedded=None):
    """Write a synthetic cascade_{scale}_{R}_{k}_{seed}.npz with all 16 scalar F1
    fields committed_cascade_pooled() reads (4 metrics x close/mod/dist/pooled),
    plus the embedded scale/R/k/seed identity fields run_cascade.py also writes.

    `embedded` overrides the identity fields (default: matching (scale, R, k,
    seed)) to simulate a cell whose content disagrees with its filename."""
    es, eR, ek, eseed = embedded if embedded is not None else (scale, R, k, seed)
    fields = {"scale": es, "R": eR, "k": ek, "seed": eseed}
    for met in _METRICS:
        for suffix in compute_pooled_f1._STRATUM_TO_CELL_SUFFIX.values():
            fields[f"{met}_{suffix}"] = np.float64(value)
    name = filename or f"cascade_{scale}_{R}_{k}_{seed}.npz"
    np.savez(cascade_dir / name, **fields)


def _write_full_canonical_grid(cascade_dir, *, skip_groups=(), extra_groups=()):
    """Write the full canonical 180-file grid, minus any (scale, R, k) group in
    `skip_groups` (entirely omitted), plus a full 10-seed set for every
    (scale, R, k) in `extra_groups` (outside the real SCALES x RS x KS grid)."""
    skip = set(skip_groups)
    for scale in compute_pooled_f1.SCALES:
        for R in compute_pooled_f1.RS:
            for k in compute_pooled_f1.KS:
                if (scale, R, k) in skip:
                    continue
                for seed in compute_pooled_f1.SEEDS:
                    _write_cell(cascade_dir, scale, R, k, seed)
    for scale, R, k in extra_groups:
        for seed in compute_pooled_f1.SEEDS:
            _write_cell(cascade_dir, scale, R, k, seed)


def _group_filenames(scale, R, k):
    return {f"cascade_{scale}_{R}_{k}_{seed}.npz" for seed in compute_pooled_f1.SEEDS}


# ---------------------------------------------------------------------------
# check 0: cascade_inventory_mismatch() / expected_cascade_filenames()
# ---------------------------------------------------------------------------

def test_expected_cascade_filenames_is_the_canonical_180_set():
    names = compute_pooled_f1.expected_cascade_filenames()
    assert len(names) == 180
    assert all(name.startswith("cascade_") and name.endswith(".npz") for name in names)


def test_inventory_exact_canonical_set_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    _write_full_canonical_grid(tmp_path)
    assert len(list(tmp_path.glob("cascade_*.npz"))) == 180
    missing, unexpected = compute_pooled_f1.cascade_inventory_mismatch()
    assert missing == []
    assert unexpected == []


def test_inventory_wholly_missing_group_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    missing_group = ("t6", 100, 5)
    _write_full_canonical_grid(tmp_path, skip_groups=[missing_group])
    missing, unexpected = compute_pooled_f1.cascade_inventory_mismatch()
    assert set(missing) == _group_filenames(*missing_group)
    assert unexpected == []


def test_inventory_wholly_extra_group_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    extra_group = ("t99", 100, 5)
    assert extra_group[0] not in compute_pooled_f1.SCALES
    _write_full_canonical_grid(tmp_path, extra_groups=[extra_group])
    missing, unexpected = compute_pooled_f1.cascade_inventory_mismatch()
    assert missing == []
    assert set(unexpected) == _group_filenames(*extra_group)


def test_inventory_malformed_filename_reported_not_silently_skipped(tmp_path, monkeypatch):
    """A file matching the `cascade_*.npz` glob but not a canonical name (a stray
    suffix here) must surface as `unexpected`, not silently vanish. The per-file
    regex parser in committed_cascade_pooled() would `continue` past this name
    with zero record anywhere -- this exact-inventory check is what catches it."""
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    _write_full_canonical_grid(tmp_path)
    malformed_name = "cascade_t6_100_5_20260410_extra.npz"
    _write_cell(tmp_path, "t6", 100, 5, compute_pooled_f1.SEEDS[0], filename=malformed_name)
    missing, unexpected = compute_pooled_f1.cascade_inventory_mismatch()
    assert missing == []
    assert unexpected == [malformed_name]


# ---------------------------------------------------------------------------
# checks 1-4: committed_cascade_pooled()
# ---------------------------------------------------------------------------

def test_complete_grid_no_incomplete_no_duplicates_no_unexpected_no_mismatched(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    _write_full_canonical_grid(tmp_path)
    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert incomplete == {}
    assert duplicates == {}
    assert unexpected == []
    assert mismatched == {}
    key = ("t6", 100, 5, "cosine")
    assert key in pooled
    assert pooled[key]["pooled"] == pytest.approx(0.5)
    assert len(pooled) == 18 * len(_METRICS)


def test_missing_seed_flagged_incomplete(tmp_path, monkeypatch):
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    seeds = compute_pooled_f1.SEEDS[:-1]  # drop one of the 10 expected seeds
    for seed in seeds:
        _write_cell(tmp_path, "t6", 100, 5, seed)
    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert duplicates == {}
    assert unexpected == []
    assert mismatched == {}
    group = ("t6", 100, 5)
    assert group in incomplete
    assert sorted(incomplete[group]) == sorted(seeds)
    assert set(compute_pooled_f1.SEEDS) - set(seeds) == {compute_pooled_f1.SEEDS[-1]}


def test_wholly_missing_group_flagged_incomplete_with_zero_files(tmp_path, monkeypatch):
    """A group with *zero* files on disk must still be reported (found=[]), not silently
    skipped -- a check that only iterates observed groups would never see it at all."""
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    group = ("t6", 100, 5)
    _write_full_canonical_grid(tmp_path, skip_groups=[group])
    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert duplicates == {}
    assert unexpected == []
    assert mismatched == {}
    assert group in incomplete
    assert incomplete[group] == []
    for metric in _METRICS:
        assert (*group, metric) not in pooled


def test_extra_unexpected_seed_value_flagged_incomplete(tmp_path, monkeypatch):
    """An 11th distinct seed value within an otherwise-expected group is a set mismatch,
    not a duplicate (the extra seed is a value SEEDS never contains, not a repeat)."""
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    for seed in compute_pooled_f1.SEEDS:
        _write_cell(tmp_path, "t6", 100, 5, seed)
    extra_seed = 99999999
    _write_cell(tmp_path, "t6", 100, 5, extra_seed)
    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert duplicates == {}
    assert unexpected == []
    assert mismatched == {}
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

    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert unexpected == []
    assert mismatched == {}
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


def test_group_outside_expected_grid_flagged_unexpected(tmp_path, monkeypatch):
    """A fully-populated, non-duplicate group at a (scale, R, k) outside the SCALES x
    RS x KS grid must still be rejected: its seed set is complete and duplicate-free,
    so it would silently pass both the incomplete and duplicate checks, and the
    per-group cross-check loop never visits an unexpected key to catch it there."""
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    extra_group = ("t99", 100, 5)
    assert extra_group[0] not in compute_pooled_f1.SCALES
    _write_full_canonical_grid(tmp_path, extra_groups=[extra_group])
    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert mismatched == {}
    assert duplicates == {}
    assert incomplete == {}, (
        "incomplete only iterates the expected grid, so a fully-populated group at an "
        "unexpected key must not appear there"
    )
    assert unexpected == [extra_group]


def test_embedded_identity_mismatch_flagged_and_excluded(tmp_path, monkeypatch):
    """A cell whose filename says one (scale, R, k, seed) but whose embedded fields say
    another (e.g. a file overwritten with a different seed's payload) must be flagged
    and excluded from both the pooled means and the completeness bookkeeping -- its
    filename-implied slot in the group must count as still unfilled."""
    monkeypatch.setattr(compute_pooled_f1, "CASCADE_DIR", tmp_path)
    good_seeds = compute_pooled_f1.SEEDS[:-1]
    for seed in good_seeds:
        _write_cell(tmp_path, "t6", 100, 5, seed)
    bad_seed = compute_pooled_f1.SEEDS[-1]
    bad_name = f"cascade_t6_100_5_{bad_seed}.npz"
    # Filename implies (t6, 100, 5, bad_seed); the payload actually belongs to a
    # different seed entirely (as if the file were overwritten by a copy error).
    swapped_seed = good_seeds[0]
    _write_cell(tmp_path, "t6", 100, 5, bad_seed, filename=bad_name,
                embedded=("t6", 100, 5, swapped_seed))

    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert mismatched.keys() == {bad_name}
    parsed, embedded = mismatched[bad_name]
    assert parsed == ("t6", 100, 5, bad_seed)
    assert embedded == ("t6", 100, 5, swapped_seed)

    assert duplicates == {}
    assert unexpected == []
    group = ("t6", 100, 5)
    assert group in incomplete, "the mismatched file's slot must not count as filled"
    assert bad_seed not in incomplete[group]
    assert set(incomplete[group]) == set(good_seeds)


def test_real_committed_cascade_evidence_shape_if_hydrated():
    """If real committed cascade evidence is present (LFS payload hydrated), the
    filename inventory must exactly equal the canonical 180-name grid, and
    committed_cascade_pooled() must report zero duplicates, zero incomplete
    groups, zero unexpected groups, and zero embedded-identity mismatches --
    the invariant PR #33's hardening protects. Skips cleanly on LFS pointer
    stubs, matching tests/test_cell_schema.py."""
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

    missing, unexpected_files = compute_pooled_f1.cascade_inventory_mismatch()
    assert missing == [], f"missing cascade cell files: {missing}"
    assert unexpected_files == [], f"unexpected cascade cell files: {unexpected_files}"

    pooled, incomplete, duplicates, unexpected, mismatched = compute_pooled_f1.committed_cascade_pooled()
    assert incomplete == {}, f"incomplete cascade seed groups: {incomplete}"
    assert duplicates == {}, f"duplicate cascade seed files: {duplicates}"
    assert unexpected == [], f"unexpected cascade seed groups: {unexpected}"
    assert mismatched == {}, f"cascade cells with mismatched embedded identity: {mismatched}"
    assert len(pooled) == expected_groups * len(_METRICS)
