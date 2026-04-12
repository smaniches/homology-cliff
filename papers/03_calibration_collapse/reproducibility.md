# Reproducibility: Calibration Collapse

## Scripts to run
- `code/analyses/run_calibration.py`

## Evidence on disk
data/cells/main/cell_t30_1000_25_cosine_*.npz (10 seeds)

## Supplementary note
ECE per bin, reliability diagram data at seed 20260410.

## Expected hashes
See root `MANIFEST.sha256.json` for SHA256 of every .npz output file produced by this paper's harnesses.

## Exact commands
```bash
cd <repo_root>
pytest tests/ -v
python code/harnesses/run_cliff.py --scale t30 --resume  # example
```

## Environment
Python 3.11+, numpy, scipy, scikit-learn, faiss-cpu, torch. See `pyproject.toml`.
