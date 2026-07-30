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
`code/analyses/run_mapper_augmentation.py`:
  - `calibration_results.json` must be byte-identical (SHA256) to the
    committed artifact -- the numbers reproduce bit-for-bit.
  - `mapper_augmentation_results.json` is compared field-aware instead
    (see `mapper_results_match()`): exact schema, R/k/scale, arm names,
    seed values/ordering, and n_dist; dist_f1 and the rescue mean/CI to
    1e-12 (float round-trip noise only); close_f1 alone to 1e-4. FAISS/BLAS
    threshold behavior can produce bounded cross-platform drift in
    close_f1 (observed: 6.156e-05, Windows/Python 3.13 vs the Linux-
    committed value) even though dist_f1, the rescue statistics actually
    computed from it, and the H1 conclusion are unaffected. Universal
    bit-for-bit identity is NOT claimed for this artifact. Either way,
    the regenerated file is restored to its committed bytes afterward --
    `--full` never leaves the working tree modified.

Exit code 0 iff every phase passes; non-zero on the first failure.
Paths are resolved relative to this file (REPO_ROOT); no absolute paths,
runs from any clone on any platform.
"""
from __future__ import annotations

import argparse
import contextlib
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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@contextlib.contextmanager
def _preserved(path: Path):
    """Snapshot `path`'s bytes on entry; restore them on exit no matter what
    happens inside the with-block (a re-derivation subprocess crash, a raised
    exception during comparison, or simply a comparison mismatch). `--full`
    re-derives artifacts to CHECK them against the committed evidence, not to
    replace them -- the working tree must be unchanged (`git status` clean)
    after every run, whether that run passes or fails. Yields the original
    bytes (None if `path` did not exist beforehand).

    If `path` did NOT exist on entry but the with-block created it (a subprocess
    that writes a fresh artifact when its committed copy is absent), it is
    removed on exit so the working tree is still unchanged -- the "never leaves
    the working tree modified" contract holds even from a partial checkout,
    not only from one where both committed artifacts already exist.
    """
    original = path.read_bytes() if path.is_file() else None
    try:
        yield original
    finally:
        if original is not None:
            path.write_bytes(original)
        elif path.exists():
            path.unlink()


def _calibration_matches(original: bytes | None, regenerated: bytes) -> tuple[bool, str]:
    """calibration_results.json: strict SHA256 byte-identity (unchanged)."""
    if original is None:
        return False, "    calibration_results.json: no committed artifact to compare against"
    ident = _sha256(original) == _sha256(regenerated)
    return ident, (f"    calibration_results.json: SHA256 "
                   f"{'BIT-FOR-BIT IDENTICAL' if ident else 'DIFFERS'} "
                   f"({_sha256(regenerated)[:16]}...)")


_MAPPER_ARMS = ("uniform", "biased")
_MAPPER_RESULT_KEYS = {"seed", "dist_f1", "close_f1", "n_dist"}
_MAPPER_EXACT_TOL = 1e-12   # float round-trip noise only: dist_f1, rescue_mean, rescue_ci_lo/hi
_MAPPER_CLOSE_F1_TOL = 1e-4  # FAISS/BLAS cross-platform threshold drift in close_f1 only


def mapper_results_match(committed: dict, generated: dict) -> tuple[bool, str]:
    """Field-aware comparison for mapper_augmentation_results.json.

    Cross-platform bit-for-bit identity is NOT guaranteed for this artifact:
    FAISS/BLAS threshold behavior in the k-NN + bootstrap pipeline can produce
    bounded floating-point drift in `close_f1` between platforms (observed:
    6.156e-05 on a Windows/Python 3.13 re-derivation vs the Linux-committed
    value at results.uniform[2].close_f1), even though the seeds, panel
    construction, and every other value are identical. `dist_f1` -- what the
    Mapper H1 rescue hypothesis and rescue_mean/CI are actually computed from
    -- and every structural/exact field are still required to match exactly
    (up to 1e-12, i.e. float round-trip noise only).

    Checks, in order: exact top-level key set; exact arm name set (must be
    {"uniform", "biased"}); exact R/k/scale; exact rescue_mean/rescue_ci_lo/
    rescue_ci_hi (1e-12); per arm, exact result-list length, then per entry
    (compared positionally, so seed *ordering* is enforced, not just the
    value set): exact result-entry key set, exact seed, exact n_dist, exact
    dist_f1 (1e-12), and close_f1 within 1e-4. Any non-finite value anywhere
    a float comparison is expected is rejected outright.

    Returns (ok, message). `message` always reports the single worst float
    drift found (JSON path, committed value, generated value, tolerance
    applied) regardless of pass/fail, plus every specific violation on
    failure.
    """
    violations: list[str] = []
    worst: tuple[float, str, float, float, float] | None = None  # (drift, path, committed, generated, tol)

    def check_exact(path: str, c_val, g_val) -> None:
        if c_val != g_val:
            violations.append(f"{path}: committed={c_val!r} generated={g_val!r} (exact match required)")

    def check_float(path: str, c_val: float, g_val: float, tol: float) -> None:
        nonlocal worst
        if not (isinstance(c_val, (int, float)) and isinstance(g_val, (int, float))
                and math.isfinite(c_val) and math.isfinite(g_val)):
            violations.append(f"{path}: non-finite or non-numeric value "
                              f"(committed={c_val!r}, generated={g_val!r})")
            return
        drift = abs(c_val - g_val)
        if worst is None or drift > worst[0]:
            worst = (drift, path, c_val, g_val, tol)
        if drift > tol:
            violations.append(f"{path}: committed={c_val!r} generated={g_val!r} "
                              f"drift={drift:.3e} exceeds tolerance {tol:.0e}")

    if set(committed) != set(generated):
        violations.append(f"top-level keys: committed={sorted(committed)} generated={sorted(generated)}")
    c_arms = set(committed.get("results", {})) if isinstance(committed.get("results"), dict) else set()
    g_arms = set(generated.get("results", {})) if isinstance(generated.get("results"), dict) else set()
    if c_arms != set(_MAPPER_ARMS) or g_arms != set(_MAPPER_ARMS):
        violations.append(f"results arm names: committed={sorted(c_arms)} generated={sorted(g_arms)} "
                          f"expected={sorted(_MAPPER_ARMS)}")

    if not violations:  # only compare per-field once the top-level shape is sane
        check_exact("R", committed["R"], generated["R"])
        check_exact("k", committed["k"], generated["k"])
        check_exact("scale", committed["scale"], generated["scale"])
        check_float("rescue_mean", committed["rescue_mean"], generated["rescue_mean"], _MAPPER_EXACT_TOL)
        check_float("rescue_ci_lo", committed["rescue_ci_lo"], generated["rescue_ci_lo"], _MAPPER_EXACT_TOL)
        check_float("rescue_ci_hi", committed["rescue_ci_hi"], generated["rescue_ci_hi"], _MAPPER_EXACT_TOL)

        for arm in _MAPPER_ARMS:
            c_list, g_list = committed["results"][arm], generated["results"][arm]
            if len(c_list) != len(g_list):
                violations.append(f"results.{arm}: length committed={len(c_list)} generated={len(g_list)}")
                continue
            for i, (c_entry, g_entry) in enumerate(zip(c_list, g_list)):
                if set(c_entry) != _MAPPER_RESULT_KEYS or set(g_entry) != _MAPPER_RESULT_KEYS:
                    violations.append(f"results.{arm}[{i}]: keys committed={sorted(c_entry)} "
                                      f"generated={sorted(g_entry)} expected={sorted(_MAPPER_RESULT_KEYS)}")
                    continue
                check_exact(f"results.{arm}[{i}].seed", c_entry["seed"], g_entry["seed"])
                check_exact(f"results.{arm}[{i}].n_dist", c_entry["n_dist"], g_entry["n_dist"])
                check_float(f"results.{arm}[{i}].dist_f1", c_entry["dist_f1"], g_entry["dist_f1"],
                           _MAPPER_EXACT_TOL)
                check_float(f"results.{arm}[{i}].close_f1", c_entry["close_f1"], g_entry["close_f1"],
                           _MAPPER_CLOSE_F1_TOL)

    ok = not violations
    lines = []
    if worst is not None:
        drift, path, c_val, g_val, tol = worst
        lines.append(f"    mapper_augmentation_results.json: worst drift @ {path}: "
                    f"committed={c_val!r} generated={g_val!r} drift={drift:.3e} tol={tol:.0e}")
    if violations:
        lines.append(f"    mapper_augmentation_results.json: MISMATCH ({len(violations)} violation(s)):")
        lines.extend(f"      {v}" for v in violations)
    else:
        lines.append("    mapper_augmentation_results.json: within field-aware tolerance "
                     "(schema/R/k/scale/seeds/n_dist/dist_f1/rescue exact; close_f1 <= 1e-4)")
    return ok, "\n".join(lines)


def _mapper_matches(original: bytes | None, regenerated: bytes) -> tuple[bool, str]:
    if original is None:
        return False, "    mapper_augmentation_results.json: no committed artifact to compare against"
    try:
        committed = json.loads(original)
        generated = json.loads(regenerated)
    except json.JSONDecodeError as e:
        return False, f"    mapper_augmentation_results.json: JSON decode error: {e}"
    return mapper_results_match(committed, generated)


def _reproduce_and_restore(script: str, out: Path, compare) -> bool:
    """Run `script` to regenerate `out`, compare it against the committed bytes
    via `compare(original, regenerated) -> (ok, message)`, then always restore
    `out` to its original committed bytes (see `_preserved`)."""
    with _preserved(out) as original:
        if not _run(f"re-derive {out.name}", [PY, script]):
            return False
        if not out.is_file():
            print(f"    {out.name}: script did not produce the expected output file")
            return False
        ok, message = compare(original, out.read_bytes())
        print(message)
        return ok


def reproduce_full() -> bool:
    """Re-derive the summary artifacts and check them against committed evidence.

    Called only when --full is explicitly requested. A missing dependency (faiss,
    and transitively torch inside knn_learned) or an unhydrated Git-LFS payload is a
    FAILURE here, not a silent skip: --full promises to actually re-derive from the
    committed evidence, so if it cannot run, that is an INCOMPLETE reproduction and
    must produce a non-zero exit code -- never a printed "COMPLETE -- all phases
    reproduced/verified" after quietly skipping the very thing --full was asked to do.
    (torch and LFS-pointer-stub failures need no special case here: knn_learned's
    lazy `import torch` and run_cliff.load_embeddings()'s is_lfs_stub() check both
    raise inside the re-derivation subprocesses below, so `_run()` already reports
    those as FAIL via a non-zero subprocess exit code.)

    calibration_results.json must be byte-identical (strict SHA256).
    mapper_augmentation_results.json is checked field-aware instead
    (mapper_results_match) -- see that function's docstring for why universal
    bit-for-bit identity is not claimed for it. Either artifact's regenerated
    bytes are restored to the committed originals afterward regardless of
    outcome -- or removed, if the artifact was absent to begin with and the
    re-derivation created it (_preserved / _reproduce_and_restore): --full
    never leaves the working tree modified.
    """
    try:
        import faiss  # noqa: F401
    except ImportError:
        print("\n[--full] FAIL: faiss is not importable, so the requested full "
              "re-derivation cannot run.")
        print("         install faiss-cpu (see the GPU floors in pyproject.toml) and run "
              "`git lfs pull`, or omit --full to run the CI-grade (non-LFS) checks only.")
        return False

    ok = True
    ok &= _reproduce_and_restore("code/analyses/run_calibration.py",
                                 SUMMARIES / "calibration_results.json", _calibration_matches)
    ok &= _reproduce_and_restore("code/analyses/run_mapper_augmentation.py",
                                 SUMMARIES / "mapper_augmentation_results.json", _mapper_matches)
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
                    help="also re-derive summary artifacts and check them against committed evidence "
                         "(calibration: byte-identical; mapper: field-aware tolerance) -- needs LFS + faiss")
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
        results["--full artifact agreement"] = reproduce_full()

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
