#!/usr/bin/env python3
"""Verify every harness and analysis script imports cleanly.

Exists to catch defects of the v1.4.3-and-earlier kind: hardcoded
absolute Windows paths, missing repo-relative resolution, top-level
imports of GPU-only or runtime-only dependencies. If this script
exits 0 in CI, a fresh clone can at minimum execute `import` on
every script without crashing -- a prerequisite for the README's
"rerun any single harness" claim.

Behavior:
  - Imports each harness via sys.path manipulation and asserts the
    REPO_ROOT and primary path constants resolve to existing on-disk
    locations.
  - AST-parses every analysis script (parse-only, no execution) so
    that scripts which load data at top level do not need their data
    files present in CI.
  - Imports run_calibration to verify its faiss-deferred design.
  - Greps the entire code/ tree for the v1.4.3-and-earlier Windows
    path string and fails if any reappears.

Exit code:
  0  on full success
  1  on any import failure, parse error, missing file, or path-style
     regression in code/

Designed to run on a fresh clone WITHOUT git lfs pull. Only depends
on numpy and scipy.
"""
from __future__ import annotations

import ast
import importlib
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESSES_DIR = REPO_ROOT / "code" / "harnesses"
ANALYSES_DIR = REPO_ROOT / "code" / "analyses"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def step_master_harness() -> bool:
    print("\n[1/4] master harness imports cleanly")
    sys.path.insert(0, str(HARNESSES_DIR))
    try:
        import run_cliff  # type: ignore
    except Exception as e:
        fail(f"run_cliff import: {e!r}")
        return False
    if run_cliff.REPO_ROOT.name != "homology-cliff":
        fail(f"run_cliff.REPO_ROOT = {run_cliff.REPO_ROOT}")
        return False
    if not run_cliff.PRE_DIR.exists():
        fail(f"PRE_DIR does not exist: {run_cliff.PRE_DIR}")
        return False
    prereg = run_cliff.PRE_DIR / "PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md"
    if not prereg.is_file():
        fail(f"locked pre-reg missing: {prereg}")
        return False
    # PROTEINS_JSON may be an LFS stub; .exists() is enough here.
    if not run_cliff.PROTEINS_JSON.exists():
        fail(f"PROTEINS_JSON candidate does not resolve: "
             f"{run_cliff.PROTEINS_JSON}")
        return False
    print(f"  REPO_ROOT     = {run_cliff.REPO_ROOT}")
    print(f"  PRE_DIR       = {run_cliff.PRE_DIR}")
    print(f"  PROTEINS_JSON = {run_cliff.PROTEINS_JSON}")
    print("  OK")
    return True


def step_dependent_harnesses() -> bool:
    print("\n[2/4] dependent harnesses import cleanly")
    failed = False
    expected = [
        ("run_cliff_fullnull", "FULLNULL_DIR", "fullnull"),
        ("run_cascade", "CASCADE_DIR", "cascade"),
        ("run_fisher", "FISHER_DIR", "fisher"),
    ]
    for name, attr_name, expected_dir_name in expected:
        try:
            mod = importlib.import_module(name)
        except Exception as e:
            fail(f"{name} import: {e!r}")
            failed = True
            continue
        if not hasattr(mod, attr_name):
            fail(f"{name} does not expose {attr_name}")
            failed = True
            continue
        d = getattr(mod, attr_name)
        if not hasattr(d, "name") or d.name != expected_dir_name:
            fail(f"{name}.{attr_name} resolves to wrong dir: {d}")
            failed = True
            continue
        print(f"  {name}.{attr_name} -> {d}: OK")
    return not failed


def step_analysis_scripts() -> bool:
    print("\n[3/4] analysis scripts AST-parse + run_calibration imports")
    failed = False
    for path in sorted(ANALYSES_DIR.glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as e:
            fail(f"{path.name} parse error: {e!r}")
            failed = True
            continue
        print(f"  {path.name}: parses OK")
    sys.path.insert(0, str(ANALYSES_DIR))
    try:
        import run_calibration  # type: ignore # noqa: F401
        print("  run_calibration: imports OK (faiss is deferred to main())")
    except Exception as e:
        fail(f"run_calibration top-level import: {e!r}")
        failed = True
    return not failed


def step_forbid_windows_paths() -> bool:
    print("\n[4/4] no hardcoded Windows paths in code/")
    failed = False
    for py_file in (REPO_ROOT / "code").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        # Match any reference to the v1.4.3-and-earlier root.
        if re.search(r"C:[\\/]TOPOLOGICA_BIOSECURITY", text):
            fail(f"{py_file.relative_to(REPO_ROOT)} contains C:\\TOPOLOGICA_BIOSECURITY")
            failed = True
    if not failed:
        print("  no hardcoded Windows paths -- OK")
    return not failed


def main() -> int:
    steps = [
        step_master_harness,
        step_dependent_harnesses,
        step_analysis_scripts,
        step_forbid_windows_paths,
    ]
    results = [step() for step in steps]
    if all(results):
        print("\nAll smoke checks passed.")
        return 0
    print("\nOne or more smoke checks failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
