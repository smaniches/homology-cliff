# ESM-2 t30 archived-embedding compatibility: executed result

**Evidence status:** completed exploratory reference assay; methodological compatibility evidence, **not** a new biological benchmark result.

- GitHub Actions execution: https://github.com/smaniches/homology-cliff/actions/runs/41371173247
- Source PR (runtime repair): https://github.com/smaniches/homology-cliff/pull/78
- Source run's artifact: `esm2-t30-parity-evidence` (artifact ID 13108439577)
- Results preserved in this branch: [results/41371173247.json](results/41371173247.json)
- Original artifact JSON SHA-256 before copying values into the repository: `1fabad078d879e5998bf52fb65b158727b7c3c46734fec2e28beda22b14650a5`
- Source runner merge revision: `ddf6cdf285891d9dc506fb3e9d3868ec734f06d2`
- Original dataset SHA-256: `c99d8329c02b806b9d208465946c68826d17245cd9e012ca9a7b94faea0a60fc`
- Archived t30 embedding SHA-256: `15d6e3656b46729a2483b7fbc603e49a61f25206e3854676bc2e528164608fd6`
- Model: `facebook/esm2_t30_150M_UR50D`, immutable revision `a695f6045e2e32885fa60af20c13cb35398ce30c`
- Runtime: Python 3.11.17; PyTorch 2.5.1+cpu; Transformers 4.46.3; NumPy 2.1.3.

## Test

The workflow downloaded the existing Git LFS objects and verified both SHA-256 values, then performed **actual pretrained-model inference**, using 18 deterministic, length-stratified protein sequences from the immutable 24,885-row dataset. No fitting, training, benchmark evaluation, label modification, or external data collection occurred.

The output of each candidate pooling/truncation path was compared to the archived embedding direction with cosine similarity. These are **directional** comparisons: they do not establish raw coordinate or byte-for-byte equality.

| Convention | Mean cosine vs. archive | Minimum cosine |
|---|---:|---:|
| Residue-only mean, 1022-residue slice | 0.9999999999999125 | 0.9999999999995755 |
| Attention-mask mean including special tokens, 1022-residue slice | 0.9990954441943837 | 0.9846869462219839 |
| Residue-only mean, 1022-token window | 0.9999999999999125 | 0.9999999999995755 |
| Attention-mask mean including special tokens, 1022-token window | 0.9990954441943837 | 0.9846869462219839 |

Residue-only pooling was closer to the archived embedding **for all 18 tested proteins**. The largest attention-pooling discrepancy occurred for a 5-residue input (cosine approximately 0.984687), consistent with a larger relative effect from including special tokens in very short sequences.

The tested length-stratification algorithm includes the **global maximum-length sequence**. Its observed length was 995 residues. Therefore both truncation paths produced identical results on this dataset: the different 1022-token/residue cutoffs were not discriminated by this experiment and do not alter inputs when sequences are this short.

## Consequence for the proposed t33 extension

The existing [t33 prototype](../../code/kaggle_notebooks/cell4_esm2_t33.py) and [PLM notebook](../../code/colab_notebook/plm_benchmark.ipynb) compute a mean over the attention mask, including special tokens. This is **not the convention identified by the t30 archive parity assay**. Future cross-scale comparisons should align pooling conventions explicitly and validate the actual t33 embedding method before calculating a cliff-gap score. This document does not change existing archived results or approve a t33 benchmark claim.

## Boundaries

- Small stratified reference assay (18/24,885); not an exhaustive numerical parity proof.
- Mean cosine nearly one strongly supports matching embedding **directions**, not raw array identity.
- Results do not establish biological utility, causal claims, external validity, or cross-model superiority.
- A passing CI job establishes this computation executed; it does not independently validate the published benchmark's biological conclusions.
- Keep changes to extraction protocol separately versioned; never rewrite preregistration documents or previously released embeddings in place.

**Promotion:** Runtime repair passed; methodological compatibility evidence passed on the prespecified 18 samples. Full downstream benchmark validation remains **not performed**.
