# Reproducibility: Methods and Pre-Registrations

## Scripts to run
- `all of code/harnesses/`

## Evidence on disk
all 9,360 cells

## Supplementary note
SHA256 manifest at MANIFEST.sha256.json root.

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
