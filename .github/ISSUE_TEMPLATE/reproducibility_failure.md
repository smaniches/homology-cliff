---
name: Reproducibility failure
about: A paper claim does not reproduce on your system
title: "[REPRO] "
labels: reproducibility
---

## Which paper and which claim?
<!-- e.g. Paper 1, cliff gap 0.745 at t30 R=1000 k=25 cosine -->

## What did you run?

```
```

## Expected output (with citation)
<!-- Quote the exact value and the paper section/figure/table where it appears -->

## Actual output

## Cell identifier
<!-- Which data/cells/*/cell_*.npz did you compare against? Paste its SHA256 entry from MANIFEST.sha256.json -->

## Divergence
<!-- Is the divergence greater than bootstrap-CI-level noise? By how much? -->

## Environment

- OS:
- Python:
- numpy:
- FAISS:
- git rev-parse HEAD:
- `git lfs ls-files | head -5` output:

## Hypothesis

<!-- Your best guess at what might cause the divergence. LFS pull issue? numpy version drift? seed handling? -->

This is the most valuable category of report. Thank you for filing.
