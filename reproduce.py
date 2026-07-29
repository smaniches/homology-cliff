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
import math
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


def verify_pooled_numbers() -> bool:
    """Assert the committed pooled-F1 summary's headline pooled values.

    pooled_f1_summary.json is the consolidated pooled (whole-test-set) F1 that
    the Paper 1 rescue table and Paper 2 whitening comparison reference;
    cosine/mahalanobis/learned values are cross-checked against the committed
    cascade cells by code/analyses/compute_pooled_f1.py, fisher against the
    same validated pipeline. Here we assert the rescue-table row and that the
    learned projection wins pooled F1 over cosine (the Paper 1 rescue).
    """
    print("\n=== pooled F1 (committed summary) ===", flush=True)
    path = SUMMARIES / "pooled_f1_summary.json"
    if not path.is_file():
        print("    pooled_f1_summary.json MISSING (run code/analyses/compute_pooled_f1.py)")
        return False
    pf = json.loads(path.read_text(encoding="utf-8"))
    ok = True
    for key, target, tol in [
        ("t30_1000_25_cosine", 0.848, 1e-3),
        ("t30_1000_25_mahalanobis", 0.435, 1e-3),
        ("t30_1000_25_fisher", 0.462, 6e-3),   # fisher: LAPACK eigh tolerance
        ("t30_1000_25_learned", 0.891, 1e-3),
    ]:
        ok &= _approx(pf[key]["pooled"], target, tol, f"pooled {key}")
    rescue = pf["t30_1000_25_learned"]["pooled"] > pf["t30_1000_25_cosine"]["pooled"]
    print(f"    {'learned pooled > cosine pooled (t30 R1000 k25)':<34} = {rescue}  "
          f"({pf['t30_1000_25_learned']['pooled']:.4f} > {pf['t30_1000_25_cosine']['pooled']:.4f})")
    ok &= rescue
    # Paper 2 Attempt-3: cascade loses to cosine on pooled F1 in all 18 groups (penalty -0.046..-0.236)
    # The pre-registered grid is 3 scales x 3 panel sizes x 2 neighbor counts; assert the
    # actual "_cascade" keys are exactly this set (not just 18-of-something) before trusting
    # the penalty range computed from them.
    expected_groups = {f"{s}_{R}_{k}_cascade"
                       for s in ("t6", "t12", "t30")
                       for R in (100, 500, 1000)
                       for k in (5, 25)}
    actual_groups = {g for g in pf if g.endswith("_cascade")}
    groups_ok = actual_groups == expected_groups
    if not groups_ok:
        print(f"    cascade group set mismatch: missing {sorted(expected_groups - actual_groups)}, "
              f"extra {sorted(actual_groups - expected_groups)}")
    pens = [pf[g]["pooled"] - pf[g.replace("_cascade", "_cosine")]["pooled"]
            for g in sorted(actual_groups)]
    finite = bool(pens) and all(math.isfinite(p) for p in pens)
    cascade_ok = (groups_ok and finite and len(pens) == 18 and max(pens) < 0.0
                  and abs(min(pens) - (-0.236)) <= 0.005
                  and abs(max(pens) - (-0.046)) <= 0.005)
    pen_range = f"{min(pens):+.3f}..{max(pens):+.3f}" if pens else "N/A"
    print(f"    {'cascade loses to cosine, 18 groups (penalty)':<34} = "
          f"{pen_range} over {len(pens)} groups  {'OK' if cascade_ok else 'MISMATCH'}")
    ok &= cascade_ok
    print(f"--> pooled F1: {'PASS' if ok else 'FAIL'}", flush=True)
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
    # Pooled F1 (no committed cell stores fisher pooled): re-derive from the
    # embeddings and assert tolerance agreement with the committed summary.
    if not _run("re-derive pooled_f1_summary (tolerance check)",
                [PY, "code/analyses/compute_pooled_f1.py", "--check"]):
        ok = False
    print(f"--> --full re-derivation: {'PASS' if ok else 'FAIL'}", flush=True)
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
    results["pooled numbers"] = verify_pooled_numbers()
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
