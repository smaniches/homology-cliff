"""Schema and basic-stats sanity tests on committed .npz cells.

Designed to run in two contexts:

1. **Workstation (LFS pulled).** All 4 tests execute against real numpy
   archives. test_cell_counts checks filename inventory; the other three
   check the per-cell schema {cell, shuffle, close, moderate, distant}
   and the close-distant gap distributions on main vs fullnull cells.

2. **CI (LFS not pulled, files are pointer stubs).** The 3 data-dependent
   tests gracefully skip via pytest.skip() with a clear message; only
   test_cell_counts runs (it inspects filenames only). This produces a
   GREEN CI badge that honestly reports `1 passed, 3 skipped` without
   burning LFS bandwidth on every CI run.
"""
import glob
import os
from pathlib import Path

import numpy as np
import pytest

DATA = Path(__file__).parent.parent / "data" / "cells"

LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def _is_lfs_pointer(path: str) -> bool:
    """Return True if the file looks like a Git LFS pointer stub."""
    try:
        with open(path, "rb") as fh:
            return fh.read(64).startswith(LFS_POINTER_PREFIX)
    except OSError:
        return False


def _sample(pattern, n=10):
    files = sorted(glob.glob(str(DATA / pattern)))
    return files[:n]


def _skip_if_lfs_stubs(files, kind):
    """If any sampled file is an LFS pointer stub, skip the test cleanly."""
    if not files:
        pytest.skip(f"No {kind} cells found at {DATA}/{kind}/")
    if any(_is_lfs_pointer(f) for f in files):
        pytest.skip(
            f"{kind} cells are LFS pointer stubs in this environment "
            f"(no `git lfs pull` performed). Skipping data-dependent test; "
            f"run `git lfs pull` locally to execute the full suite."
        )


def test_main_cells_schema():
    """Every main-factorial cell must have the locked npz schema."""
    files = _sample("main/cell_*.npz")
    _skip_if_lfs_stubs(files, "main")
    for f in files:
        d = np.load(f, allow_pickle=True)
        assert set(d.files) == {"cell", "shuffle", "close", "moderate", "distant"}, (
            f"bad schema {f}: got {sorted(d.files)}")
        for stratum in ("close", "moderate", "distant"):
            r = d[stratum].item()
            for required in ("n", "f1", "f1_ci_lo", "f1_ci_hi"):
                assert required in r, (
                    f"missing key {required!r} in {f}:{stratum}")


def test_fullnull_gap_near_zero():
    """Sanity: any 20 fullnull cells should give close-distant gap near zero.

    The full-pool permutation null permutes labels across all 24,885
    proteins, then evaluates retrieval. Stratification is geometric and
    label-free, so the close-distant F1 gap should be indistinguishable
    from zero. A non-zero mean gap would indicate a stratification
    artifact in the original cliff finding.
    """
    files = _sample("fullnull/fullnull_*.npz", n=20)
    _skip_if_lfs_stubs(files, "fullnull")
    gaps = []
    for f in files:
        d = np.load(f, allow_pickle=True)
        gaps.append(d["close"].item()["f1"] - d["distant"].item()["f1"])
    assert abs(np.mean(gaps)) < 0.15, (
        f"fullnull gaps drifted from zero: mean={np.mean(gaps):.4f}")


def test_main_gap_substantial():
    """Sanity: any 20 main-factorial cells should give gap materially > 0.

    Paper 1 reports a +0.745 gap at t30 R=1000 k=25 cosine. Sampled across
    a mix of cells, the mean should comfortably exceed 0.2 even at small
    scales and panels.
    """
    files = _sample("main/cell_*_cosine_*.npz", n=20)
    _skip_if_lfs_stubs(files, "main")
    gaps = []
    for f in files:
        d = np.load(f, allow_pickle=True)
        gaps.append(d["close"].item()["f1"] - d["distant"].item()["f1"])
    assert np.mean(gaps) > 0.2, (
        f"main cliff gap should be > 0.2 on cosine cells: got {np.mean(gaps):.4f}")


def test_cell_counts():
    """Filename inventory: all 9,360 expected cells are committed.

    Inspects directory contents only (no LFS payload required), so this
    test runs in every environment including bare CI.
    """
    counts = {
        "main": len(glob.glob(str(DATA / "main/*.npz"))),
        "negctrl": len(glob.glob(str(DATA / "negctrl/*.npz"))),
        "fullnull": len(glob.glob(str(DATA / "fullnull/*.npz"))),
        "cascade": len(glob.glob(str(DATA / "cascade/*.npz"))),
        "fisher": len(glob.glob(str(DATA / "fisher/*.npz"))),
    }
    expected = {"main": 3000, "negctrl": 3000, "fullnull": 3000,
                "cascade": 180, "fisher": 180}
    assert counts == expected, (
        f"Cell count mismatch.\nExpected: {expected}\nActual:   {counts}")
