# Reproducibility: Homology Cliff and Its Rescue

## Scripts to run
- `code/harnesses/run_cliff.py`

## Evidence on disk
data/cells/main/ (3000) + data/cells/fullnull/ (3000)

## Supplementary note
Full 300-group fullnull table: data/results_summaries/v3_final.txt lines 1-400.

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
