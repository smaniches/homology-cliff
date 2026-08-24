# Reproducibility: Cross-Family Predominance and Mapper Topology

## Confirmatory evidence

The original single-seed partition remains at `data/results_summaries/cross_family_partition.json`.
The preregistered panel-composition confirmation is committed at `data/results_summaries/cross_family_partition_10seed.json`.
Its SHA256 is `332b939622ac2a174124f5378d74d2df074d66561654c7b84e55002608677b7d`.
The locked protocol is `data/prereg/PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md` (SHA256 `204953efeb098f7004b5e82586d5db6f721439b0abe9d214256817679a7a6804`).

A no-LFS verification of the committed result:

```bash
python -c "import json; d=json.load(open('data/results_summaries/cross_family_partition_10seed.json')); s=d['cross_family_fraction_across_seeds']; print(f'mean={s["mean"]:.6f} median={s["median"]:.3f} min={s["min"]:.3f} max={s["max"]:.3f}'); print(d['decision'])"
python scripts/ci/verify_evidence.py
python scripts/ci/verify_prereg_locks.py
```

Expected seed-level summary: mean 0.994113, median 1.000, minimum 0.962, maximum 1.000, with all four decision booleans true.

## Re-executing the confirmatory computation

Re-execution requires the three frozen Git-LFS inputs and FAISS CPU:

```bash
git lfs pull --include="data/embeddings/embeddings_t30.npy,data/sequences/proteins_25k_sequences.json,data/annotations/proteins_25k_pfam.json"
pip install "numpy==2.4.6" "faiss-cpu==1.15.0"
python scripts/ci/verify_prereg_locks.py
python scripts/ci/verify_manifest.py
python code/analyses/run_cross_family_partition_10seed.py
```

The runner verifies the locked inputs, requires seed 20260410 to reproduce the committed original detail exactly, then evaluates all ten fixed seeds. The panel seed is the robustness unit; recurring accession appearances must not be pooled into an independent-trials binomial interval.

## Mapper context

- `code/analyses/run_mapper.py`
- `data/results_summaries/mapper_graph.json`
- 149 Mapper nodes; Pfam annotations cover 21,615 of 24,885 accessions.

Mapper is exploratory context and is not part of the preregistered ten-seed decision rule.

## Environment

Python 3.11+, NumPy, FAISS CPU for the cross-family runner; SciPy/scikit-learn for Mapper-related analyses. See `pyproject.toml` and the recorded GitHub Actions run environment.
