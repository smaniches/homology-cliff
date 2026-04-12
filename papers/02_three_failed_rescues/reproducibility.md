# Reproducibility: Three Failed Rescue Attempts

## Scripts to run
- `code/harnesses/run_cascade.py`
- `code/harnesses/run_fisher.py`
- `code/analyses/run_mapper_augmentation.py`

## Evidence on disk
data/cells/cascade/ (180) + data/cells/fisher/ (180) + data/results_summaries/mapper_augmentation_results.json

## Supplementary note
All 180 cascade cells + 180 Fisher cells committed.

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
