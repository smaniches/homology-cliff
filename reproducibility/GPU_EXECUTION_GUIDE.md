# GPU Execution Guide — PLM Benchmark + Adversarial Phase 2

Neither of these can run on your local i7 (no GPU). Both are set up for one-click cloud execution. **This guide is for you to actually execute them.**

## Option 1: Colab Pro A100 (RECOMMENDED — faster + cleaner)

### Setup (one time)
1. Go to colab.research.google.com and subscribe to Colab Pro ($10/mo) if not already
2. Runtime → Change runtime type → A100 GPU

### PLM Benchmark — run this first
1. Open `code/colab_notebook/plm_benchmark.ipynb` from this repo on GitHub (or upload the ipynb to Colab directly via File → Upload notebook)
2. Upload `data/sequences/proteins_25k_sequences.json` to the notebook's `/content/` (left sidebar → Files → upload → file is 8.2 MB)
3. **Runtime → Run all**
4. Wait approximately 90 minutes (ProtT5 + ESM-2 t33 + SaProt sequentially; A100 is ~3x faster than T4)
5. Three `.npy` files appear in `/content/`:
   - `embeddings_prot_t5.npy` (~100 MB, 1024d)
   - `embeddings_t33.npy` (~127 MB, 1280d)
   - `embeddings_saprot.npy` (~127 MB, 1280d)
6. Download all three to your local `C:\TOPOLOGICA_BIOSECURITY\homology_cliff_repo\data\embeddings\`
7. Back on your local machine: run the factorial for the new scales:
   ```powershell
   cd C:\TOPOLOGICA_BIOSECURITY\homology_cliff_repo
   python code/harnesses/run_cliff.py --scale prot_t5 --resume
   python code/harnesses/run_cliff.py --scale t33 --resume
   python code/harnesses/run_cliff.py --scale saprot --resume
   ```
   Each is ~2 hours CPU. This produces 1,500 additional per-cell .npz outputs per scale.

### Adversarial Phase 2 — run this after PLM Benchmark succeeds
1. New Colab notebook, A100 (or even T4 works — only 90 sequences to embed)
2. Paste the three cells from `code/kaggle_notebooks/adv_cell*.py` sequentially
3. **Runtime → Run all**
4. Wait approximately 5 minutes
5. Download `/content/adversarial_edits.json` (approximately 200 KB) to `C:\TOPOLOGICA_BIOSECURITY\homology_cliff_repo\data\results_summaries\`
6. On your local machine, analyze:
   ```powershell
   python code/analyses/run_adversarial_phase2_local.py data\results_summaries\adversarial_edits.json
   ```
   Outputs: minimum BLOSUM-favorable edits to flip each of the 3 distant-TP targets (P0C1X3, Q6RY98, P13208) from predicted-negative to predicted-positive.

## Option 2: Kaggle T4 (FREE, but slower)

### Setup (one time)
1. kaggle.com → create account if needed → Settings → enable phone verification (required for free GPU)

### PLM Benchmark via Kaggle
1. New Notebook → Settings → Accelerator: GPU T4 x1 → Internet: On
2. Upload `data/sequences/proteins_25k_sequences.json` as a Kaggle dataset (New Dataset → upload → title: "protein-test-set")
3. Add the dataset to the notebook (right sidebar → Add Data → your dataset)
4. Paste the four cells from `code/kaggle_notebooks/cell1_setup.py`, `cell2_prot_t5.py`, `cell3_saprot.py`, `cell4_esm2_t33.py`
5. **Save Version → Save & Run All**
6. Wait approximately 3 hours (T4 is slower; session has 12h limit so plan accordingly)
7. Once the notebook completes, the `.npy` outputs appear in `/kaggle/working/` — right sidebar → Output → download each file
8. Copy to local `_embeddings/` and proceed with the local re-run of the factorial

## If anything fails
- ProtT5 OOM on T4: reduce `BATCH` to 2 in cell 2
- SaProt requires `trust_remote_code=True` (already set)
- ESM-3 requires HuggingFace gated access (requires approved HF token in environment); skip if not approved
- UniProt FASTA fetch in adversarial cell 1 may rate-limit: add `time.sleep(1)` between requests

## Verification checklist (after either path)
- [ ] Three new .npy files in `data/embeddings/` each ~100-130 MB
- [ ] SHA256 manifest updated: `python code/analyses/update_manifest.py`
- [ ] Factorial re-run produces new cells in `data/cells/main/cell_{prot_t5,t33,saprot}_*.npz`
- [ ] v3_aggregate.py regenerates `v3_final.txt` with 5 scales not 3
- [ ] Paper 1 Figure 1 (cliff_surface) re-rendered with 5 scale curves
- [ ] Git commit: `feat(v1.3): PLM benchmark complete across 5 scales`
