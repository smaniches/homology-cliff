# Reproducibility: Cross-Family and Mapper Topology

## Scripts to run
- `code/analyses/run_mapper.py`
- `code/analyses/fetch_pfam_v3.py`

## Evidence on disk
data/results_summaries/mapper_graph.json + data/annotations/proteins_25k_pfam.json

## Supplementary note
149 Mapper nodes, Pfam annotations for most of 24,885 accessions.

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
