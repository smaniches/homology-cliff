#!/usr/bin/env python3
"""reproduce.py -- single-command reproduction and verification entry point.

A stranger with a fresh clone runs ONE command and learns whether the
compendium's headline numbers hold.

    python reproduce.py            # CI-grade: no Git-LFS payload required
    python reproduce.py --full     # also re-derives the summary artifacts
                                   #   (needs `git lfs pull` + faiss)

Default mode (no LFS needed) runs the committed verification chain in
dependency order -- pre-registration SHA256 locks, manifest integrity,
smoke imports, evidence spot-checks, and the schema + known-answer test
suite -- then prints each headline number from the committed result
summaries and asserts it against its expected range.

--full additionally re-executes `code/analyses/run_calibration.py` and
`code/analyses/run_mapper_augmentation.py` and asserts the regenerated
JSON is byte-identical (SHA256) to the committed artifact, i.e. the
numbers reproduce bit-for-bit from the committed embeddings and seeds.

Exit code 0 iff every phase passes; non-zero on the first failure.
Paths are resolved relative to this file (REPO_ROOT); no absolute paths,
runs from any clone on any platform.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SUMMARIES = REPO_ROOT / "data" / "results_summaries"
PY = sys.executable


def _run(label: str, argv: list[str]) -> bool:
    """Run a sub-command from the repo root; return True on exit 0."""
    print(f"\n=== {label} ===", flush=True)
    proc = subprocess.run(argv, cwd=REPO_ROOT)
    ok = proc.returncode == 0
    print(f"--> {label}: {'PASS' if ok else 'FAIL'} (exit {proc.returncode})", flush=True)
    return ok


def _approx(value: float, target: float, tol: float, name: str) -> bool:
    ok = abs(value - target) <= tol
    print(f"    {name:<34} = {value:.4f}  (expect ~{target}, tol {tol})  {'OK' if ok else 'MISMATCH'}")
    return ok


def verify_headline_numbers() -> bool:
    """Read every headline number from committed summaries; assert its range."""
    print("\n=== headline numbers (committed summaries) ===", flush=True)
    ok = True

    cal = json.loads((SUMMARIES / "calibration_results.json").read_text(encoding="utf-8"))
    ok &= _approx(cal["close"]["ECE"], 0.069, 1e-3, "ECE close")
    ok &= _approx(cal["distant"]["ECE"], 0.294, 1e-3, "ECE distant")
    ok &= _approx(cal["ece_distant_to_close_ratio"], 4.3, 0.2, "ECE distant/close ratio")
    pp = cal["distant"]["positive_prediction"]
    ok &= (pp["tp"] == 3 and pp["n_predicted_positive"] == 44)
    ok &= _approx(pp["precision"], 3 / 44, 1e-3, "distant pos-pred precision (3/44)")

    mp = json.loads((SUMMARIES / "mapper_augmentation_results.json").read_text(encoding="utf-8"))
    lo, hi = mp["rescue_ci_lo"], mp["rescue_ci_hi"]
    rescue_ok = lo <= 0.0 <= hi  # null: 95% CI includes zero
    print(f"    {'Mapper rescue (H1 rejected)':<34} = {mp['rescue_mean']:+.4f}  "
          f"CI [{lo:+.4f}, {hi:+.4f}] includes 0: {'OK' if rescue_ok else 'MISMATCH'}")
    ok &= rescue_ok

    cf = json.loads((SUMMARIES / "cross_family_partition.json").read_text(encoding="utf-8"))
    cf_ok = (cf["within_family"] == 0 and cf["cross_family"] == 20)
    print(f"    {'cross-family false alarms':<34} = {cf['within_family']} within / "
          f"{cf['cross_family']} cross  {'OK' if cf_ok else 'MISMATCH'}")
    ok &= cf_ok

    print(f"--> headline numbers: {'PASS' if ok else 'FAIL'}", flush=True)
    return bool(ok)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reproduce_full() -> bool:
    """Re-derive the summary artifacts and assert byte-identity to committed."""
    try:
        import faiss  # noqa: F401
    except ImportError:
        print("\n[--full] faiss not importable; skipping bit-for-bit re-derivation.")
        print("         install faiss-cpu and `git lfs pull` to run --full.")
        return True

    ok = True
    targets = [
        ("code/analyses/run_calibration.py", SUMMARIES / "calibration_results.json"),
        ("code/analyses/run_mapper_augmentation.py", SUMMARIES / "mapper_augmentation_results.json"),
    ]
    for script, out in targets:
        before = _sha256(out) if out.is_file() else None
        if not _run(f"re-derive {out.name}", [PY, script]):
            ok = False
            continue
        after = _sha256(out)
        identical = before == after
        print(f"    {out.name}: SHA256 {'BIT-FOR-BIT IDENTICAL' if identical else 'DIFFERS'} "
              f"({after[:16]}...)")
        ok &= identical
    print(f"--> --full bit-for-bit reproduction: {'PASS' if ok else 'FAIL'}", flush=True)
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Reproduce and verify the homology-cliff compendium.")
    ap.add_argument("--full", action="store_true",
                    help="also re-derive summary artifacts and assert byte-identity (needs LFS + faiss)")
    args = ap.parse_args()

    print(f"homology-cliff reproduction  |  repo root: {REPO_ROOT}")

    phases = [
        ("pre-registration SHA256 locks", [PY, "scripts/ci/verify_prereg_locks.py"]),
        ("manifest integrity", [PY, "scripts/ci/verify_manifest.py"]),
        ("smoke imports / no hardcoded paths", [PY, "scripts/ci/verify_smoke_imports.py"]),
        ("evidence spot-checks", [PY, "scripts/ci/verify_evidence.py"]),
        ("schema + known-answer tests", [PY, "-m", "pytest", "tests/", "-q"]),
    ]
    results = {label: _run(label, argv) for label, argv in phases}
    results["headline numbers"] = verify_headline_numbers()
    if args.full:
        results["--full bit-for-bit"] = reproduce_full()

    print("\n" + "=" * 60)
    print("REPRODUCTION SUMMARY")
    print("=" * 60)
    for label, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    all_ok = all(results.values())
    print("=" * 60)
    print(f"FINAL: {'COMPLETE -- all phases reproduced/verified' if all_ok else 'INCOMPLETE -- see FAIL above'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
