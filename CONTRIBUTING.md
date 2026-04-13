# Contributing

Thank you for your interest in the Homology Cliff compendium. This is a single-author research artifact maintained by Santiago Maniches, Independent Researcher, under TOPOLOGICA LLC (solo research lab). Contributions from the community are welcome and encouraged, especially reproducibility reports, dataset extensions, and independent replication attempts.

## Ways to contribute

1. **Replicate an experiment.** Clone the repo, `git lfs pull`, pick a single cell from the 9,360 committed results, rerun its harness, and confirm the output `.npz` hash matches `MANIFEST.sha256.json`. File an issue with your result.
2. **Extend the PLM benchmark.** Run the Colab notebook or Kaggle scaffold on a PLM not currently in the factorial (ProtT5, SaProt, ESM-3 are scaffolded; others welcome). Submit a PR with your embeddings, updated MANIFEST, and the new factorial outputs.
3. **Report a bug.** Use the "bug_report" issue template. Required fields: cell identifier, pre-registration SHA256 you're running against, exact command, observed output, expected output.
4. **Report a data issue.** Use the "data_issue" template for questions about the 24,885-protein test set, Pfam coverage, labels, or sequence retrieval.
5. **Report a reproducibility failure.** Use the "reproducibility_failure" template. This is the most valuable category of report. Required fields: what you ran, what you expected (citing the paper/section), what you got.
6. **Extend the cross-family analysis** to more seeds (currently only seed 20260410 analyzed).
7. **Suggest a new pre-registered rescue hypothesis.** We document 4 rejections and 1 acceptance; a rigorous proposal for a 6th rescue is welcome. Pre-registration must be SHA256-locked before execution.

## Workflow

```bash
git clone https://github.com/smaniches/homology-cliff.git
cd homology-cliff
git lfs install && git lfs pull
pytest tests/ -v                              # confirm you can reproduce schema and invariants
# Make your change on a feature branch
git checkout -b feature/<what-you-are-doing>
# Commit with explicit provenance
git commit -m "feat: <description> (reproduces paper N section M)"
```

## Pull request checklist

- [ ] All `pytest tests/` still pass
- [ ] If you add data files: update `MANIFEST.sha256.json` via `python code/analyses/update_manifest.py`
- [ ] If you add experimental results: include the pre-registration file (.md) with its SHA256 locked before the PR
- [ ] If you modify a paper: recompile the .pdf and commit both .tex and .pdf
- [ ] Update `CHANGELOG.md` under an `[Unreleased]` heading

## Code style

Python: PEP 8, type hints where reasonable, numpy/scipy/sklearn stylistic conventions. No non-stdlib dependencies added without discussion.

## Licensing

By contributing, you agree that your contributions will be licensed under CC-BY-4.0 (for papers and prose) and MIT (for code), matching the repository's dual-license.

## Contact

Santiago Maniches · santiago at topologica dot ai · [topologica.ai](https://topologica.ai) · Independent Researcher, TOPOLOGICA LLC.

For sensitive issues see `SECURITY.md`. For scope disagreements or methodological disputes, open a GitHub Discussion rather than an Issue.
