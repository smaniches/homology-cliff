# ESM-2 t33 650M frozen representation pilot

**State:** completed exploratory real-model extraction pilot. **Not a biological benchmark result or leaderboard row.**

## Question, dataset and method

Does frozen Homology Cliff input support ESM-2 t33 embedding extraction using the residue-only mean pooling method matched to archived ESM-2 t30 representations in PR #78?

Six preselected row indices (4670, 14847, 24533, 10775, 5190, 23445) span lengths 5, 78, 184, 516, 703 and 995. Selection did not use protein labels or benchmark scores.

Model: facebook/esm2_t33_650M_UR50D at immutable revision 08e4846e537177426273712802403f7ba8261b6c.
Frozen dataset SHA-256: c99d8329c02b806b9d208465946c68826d17245cd9e012ca9a7b94faea0a60fc.
Runtime: FP32/EVAL/CPU. Exclude CLS/EOS/PAD during residue mean pooling, then L2 normalize. Compare with special-token-including pooling as a diagnostic. Test two sequences alone versus padded batch.

## Executed evidence

- Real-model [Actions run #41405031973](https://github.com/smaniches/homology-cliff/actions/runs/41405031973): SUCCESS; frozen source hash verified; eight unit tests passed; pretrained 650M forward passes completed.
- [Original zipped artifact #13123640761](https://github.com/smaniches/homology-cliff/actions/runs/41405031973/artifacts/13123640761) holds pilot_result.json and pilot_embedding.npy. The temporary artifact expires by platform retention policy.
- Original JSON SHA-256: 2c0a2bf8794b666fcfb77539a2b91e06d782f6b626f0ee252e43215687b7fa17. Numerical values preserved in [results/41405031973.json](results/41405031973.json).
- Embedding matrix: 6 x 1280, float32, all finite; unit norms from 0.99999994 to 1.00000000. NPY SHA-256: 2074ee00b89619abe5cafaa0877207c87e717636e185700a6c5e30791ed6b5d0.
- Alone-versus-padded-batch L2 differences on the first two rows: 3.684654e-7 and 0.0, under the declared 0.001 tolerance.
- Residue-only versus special-token-including cosine ranged from 0.9885191653 at five residues to 0.9999995695 at 995 residues (mean 0.9980666120). This reflects a difference in numerical representation, not established biological benefit.
- The first pilot recorded transient pull-request test merge SHA 299801f43a14754d77fea52038de7cc3b7b1039b. The code is now pinned to the exact model revision used there.

## Boundaries and next experiment

This does not measure protein function, cliff gaps, F1, statistical significance, training effects, or generalization. The original binary pilot embedding is preserved in the linked Actions artifact; the source and reproducibility hashes are preserved in this repository.

The next stage is full 24,885-protein embedding extraction on an appropriately authorized GPU, with exact model revision and row-order checks, isolated outputs, crash-safe checkpoints and SHA-256 manifest. Then use the existing frozen panel/seed/metric protocol and seed-variance gate. Do not edit preregistration or promote leaderboard claims until the actual downstream benchmark is validated.
