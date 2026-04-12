# Reproducibility Protocol

To reproduce all 9,360 per-cell outputs + the five papers in this compendium:

## 1. Prerequisites
- Python 3.11+, Windows/Linux/macOS with 36+ GB RAM, no GPU required for main experiments
- `pip install numpy scikit-learn faiss-cpu torch biopython`
- MiKTeX or TeXLive for compiling LaTeX papers

## 2. Data + embeddings (not committed, too large)
- Place `experiment2_proteins_25k_filtered.json` (24,885 proteins, 7,133 positive) at `_data/data_25k/`
- Compute ESM-2 t6/t12/t30 embeddings (or obtain from author) and place at `_embeddings/embeddings_25k_{t6,t12,t30}/test_embeddings_25k_{scale}.npy`
- L2-normalize all embeddings (verification: `np.linalg.norm(emb, axis=1).mean() ≈ 1.0`)

## 3. Execute (in order)
```bash
cd code/harnesses
python run_cliff.py --scale t6 t12 t30 --resume      # 3000-cell main factorial (~6h)
python run_cliff.py --gate-only                       # seed-variance gate
python run_cliff_fullnull.py --scale t6 t12 t30       # 3000-cell full-null (~5h)
python run_cascade.py --scale t6 t12 t30              # 180 cascade cells
python run_fisher.py --scale t6 t12 t30               # 180 fisher cells
```

## 4. Analyses
```bash
cd ../analyses
python v3_aggregate.py > results.txt
python run_calibration.py
python run_mapper.py
python run_mapper_augmentation.py
python run_adversarial_phase1.py
```

## 5. Compile papers
```bash
cd ../../papers
for p in 01_*/ 02_*/ 03_*/ 04_*/ 05_*/; do
  cd $p && pdflatex paper.tex && pdflatex paper.tex && cd ..
done
```

## 6. Pre-registration SHA256 verification
The harnesses abort if pre-reg file hashes have drifted. Expected:
- main: `139f60129d4e73dfb13444c360cc80c5b48c217d9bc87b1bf4b48b06515bcc06`
- full-null addendum: `f3864d097a0c611d790e6fb15a42e7efb36b2d1b103be4ec1c4f28f99d1004dc`

## 7. Optional: PLM benchmark extension (requires GPU)
Open `code/colab_notebook/plm_benchmark.ipynb` in Google Colab (T4 free / A100 Pro), upload the proteins JSON, Run All, download `.npy` files to `_embeddings/`. Then rerun the main factorial with new scale names.
