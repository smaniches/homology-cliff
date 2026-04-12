"""Schema + basic-stats sanity tests on committed .npz cells."""
import numpy as np, glob, os
from pathlib import Path
DATA = Path(__file__).parent.parent / "data" / "cells"

def _sample(pattern, n=10):
    files = sorted(glob.glob(str(DATA/pattern)))
    return files[:n]

def test_main_cells_schema():
    for f in _sample("main/cell_*.npz"):
        d = np.load(f, allow_pickle=True)
        assert set(d.files) == {"cell","shuffle","close","moderate","distant"}, f"bad schema {f}"
        for s in ("close","moderate","distant"):
            r = d[s].item()
            assert "n" in r and "f1" in r and "f1_ci_lo" in r and "f1_ci_hi" in r

def test_fullnull_gap_near_zero():
    """Sanity: any 20 fullnull cells should give gap near 0."""
    gaps = []
    for f in _sample("fullnull/fullnull_*.npz", n=20):
        d = np.load(f, allow_pickle=True)
        gaps.append(d["close"].item()["f1"] - d["distant"].item()["f1"])
    assert abs(np.mean(gaps)) < 0.15, f"fullnull gaps drifted from zero: {np.mean(gaps)}"

def test_main_gap_substantial():
    """Sanity: any 20 main cells should give gap materially > 0."""
    gaps = []
    for f in _sample("main/cell_*_cosine_*.npz", n=20):
        d = np.load(f, allow_pickle=True)
        gaps.append(d["close"].item()["f1"] - d["distant"].item()["f1"])
    assert np.mean(gaps) > 0.2, f"main cliff gap should be >0.2: {np.mean(gaps)}"

def test_cell_counts():
    assert len(glob.glob(str(DATA/"main/*.npz"))) == 3000
    assert len(glob.glob(str(DATA/"negctrl/*.npz"))) == 3000
    assert len(glob.glob(str(DATA/"fullnull/*.npz"))) == 3000
    assert len(glob.glob(str(DATA/"cascade/*.npz"))) == 180
    assert len(glob.glob(str(DATA/"fisher/*.npz"))) == 180
