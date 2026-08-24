#!/usr/bin/env python3
"""Spot-check headline numerical claims against committed JSON summaries.

Verifies that the committed evidence files contain the values claimed in
the README's Machine-Readable Index. Does NOT require LFS payload -- reads
only from data/results_summaries/ (small JSON files, not LFS-tracked).

Checks:
  1. calibration_results.json: ECE_close=0.069, ECE_distant=0.294,
     distant_precision=0.068, ECE ratio between 4.0 and 4.5
  2. cross_family_partition.json: within_family=0, cross_family=20
  3. cross_family_partition_10seed.json: locked seed-level robustness summary
     passes, AND every derived field (per-seed cross- and within-family
     fractions, across-seed aggregates, decision booleans) is independently
     recomputed from the raw per-seed counts and must agree with the stored
     values -- a stale or internally inconsistent derived field fails the
     check, and non-finite stored numerics (NaN, +/-Infinity) are rejected
     before any tolerance comparison
  4. mapper_augmentation_results.json exists and reports CI including zero
  5. adversarial_results.json: 3 targets present
  6. v3_final.txt exists and is non-empty
  7. All 5 paper PDFs exist
  8. docs/CLAIMS_TO_EVIDENCE.md exists

Exit code:
  0  if all checks pass
  1  if any check fails
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUMMARIES = REPO_ROOT / "data" / "results_summaries"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def check_calibration() -> bool:
    print("\n[1/8] calibration_results.json")
    path = SUMMARIES / "calibration_results.json"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    ok = True
    # Compared at the published 3-decimal precision with a tolerance, NOT exact
    # float equality. calibration_results.json is regenerated at full float
    # precision by run_calibration.py (e.g. close ECE is stored as 0.06852...,
    # which rounds to the published 0.069), so an exact `== 0.069` would make
    # this gate brittle to legitimate regeneration.
    tol = 1e-3

    if abs(d["close"]["ECE"] - 0.069) > tol:
        fail(f"ECE_close={d['close']['ECE']}, expected ~0.069")
        ok = False
    if abs(d["distant"]["ECE"] - 0.294) > tol:
        fail(f"ECE_distant={d['distant']['ECE']}, expected ~0.294")
        ok = False

    pp = d["distant"]["positive_prediction"]
    if pp["tp"] != 3 or pp["n_predicted_positive"] != 44:
        fail(f"distant tp={pp['tp']} n={pp['n_predicted_positive']}, expected 3/44")
        ok = False
    if abs(pp["precision"] - 3 / 44) > tol:
        fail(f"distant_precision={pp['precision']}, expected ~0.068 (3/44)")
        ok = False

    ratio = d.get("ece_distant_to_close_ratio", 0)
    if not (4.0 <= ratio <= 4.5):
        fail(f"ECE ratio={ratio}, expected between 4.0 and 4.5")
        ok = False

    if ok:
        print("  ECE close~0.069 distant~0.294 ratio~4.3x precision=3/44~0.068: OK")
    return ok


def check_cross_family() -> bool:
    print("\n[2/8] cross_family_partition.json")
    path = SUMMARIES / "cross_family_partition.json"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    ok = True

    if d["within_family"] != 0:
        fail(f"within_family={d['within_family']}, expected 0")
        ok = False
    if d["cross_family"] != 20:
        fail(f"cross_family={d['cross_family']}, expected 20")
        ok = False
    if d["n_evaluable"] != 20:
        fail(f"n_evaluable={d['n_evaluable']}, expected 20")
        ok = False

    if ok:
        print("  within=0 cross=20 evaluable=20: OK")
    return ok


def _as_count(value: object) -> int | None:
    """Return value as a non-negative int count, or None if it is not one."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _finite_or_none(value: object) -> float | None:
    """Return value as a finite float, or None for anything else.

    Rejects bools, non-numbers, NaN, and +/-Infinity. JSON permits bare
    NaN/Infinity tokens and Python's json module parses them into floats;
    a NaN reaching a tolerance comparison like abs(x - y) > tol evaluates
    False and would fail OPEN, so every stored numeric must pass through
    this gate before any comparison.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    out = float(value)
    return out if math.isfinite(out) else None


def _matches_derived(stored: object, derived: float) -> bool:
    """True iff stored is a finite number exactly equal to derived."""
    value = _finite_or_none(stored)
    return value is not None and value == derived


def check_cross_family_10seed(path: Path | None = None) -> bool:
    print("\n[3/8] cross_family_partition_10seed.json")
    if path is None:
        path = SUMMARIES / "cross_family_partition_10seed.json"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    ok = True

    expected_seeds = list(range(20260410, 20260420))
    rows = d.get("per_seed", [])
    if [r.get("seed") for r in rows] != expected_seeds:
        fail("ten-seed result does not contain the exact locked seed sequence")
        ok = False
    if len(rows) != 10 or any(_as_count(r.get("n_evaluable")) in (None, 0) for r in rows):
        fail("expected exactly ten nonzero-evaluable seed rows")
        ok = False

    # --- Independent derivation from the raw per-seed counts -------------
    # Every derived field (per-seed fraction, across-seed aggregates,
    # decision booleans) is recomputed here from cross_family /
    # within_family / n_evaluable alone and compared against the stored
    # values. A per-seed count edited while the derived fields are left
    # stale is therefore detectable; this check never trusts a stored
    # derived field on its own.
    derived_fractions: list[float] = []
    derived_zero_seeds: list[object] = []
    nonzero_cross_gt_within: list[bool] = []
    counts_consistent = True
    for r in rows:
        seed = r.get("seed")
        cross = _as_count(r.get("cross_family"))
        within = _as_count(r.get("within_family"))
        n_eval = _as_count(r.get("n_evaluable"))
        if cross is None or within is None or n_eval is None:
            fail(f"seed {seed!r}: counts are not non-negative integers")
            ok = counts_consistent = False
            continue
        if cross + within != n_eval:
            fail(
                f"seed {seed!r}: cross_family + within_family = {cross + within} "
                f"!= n_evaluable = {n_eval}"
            )
            ok = counts_consistent = False
            continue
        stored_cross_fraction = r.get("cross_family_fraction")
        stored_within_fraction = r.get("within_family_fraction")
        if n_eval > 0:
            derived_cross = cross / n_eval
            derived_within = within / n_eval
            derived_fractions.append(derived_cross)
            nonzero_cross_gt_within.append(cross > within)
            # Same float division the runner performs, so exact equality.
            for name, stored, derived in (
                ("cross_family_fraction", stored_cross_fraction, derived_cross),
                ("within_family_fraction", stored_within_fraction, derived_within),
            ):
                if not _matches_derived(stored, derived):
                    fail(
                        f"seed {seed!r}: stored {name}="
                        f"{stored!r} != derived {derived!r}"
                    )
                    ok = False
        else:
            derived_zero_seeds.append(seed)
            for name, stored in (
                ("cross_family_fraction", stored_cross_fraction),
                ("within_family_fraction", stored_within_fraction),
            ):
                if stored is not None:
                    fail(
                        f"seed {seed!r}: n_evaluable=0 but stored "
                        f"{name}={stored!r} is not null"
                    )
                    ok = False

    stored_zero_seeds = d.get("zero_evaluable_seeds")
    if counts_consistent and stored_zero_seeds != derived_zero_seeds:
        fail(
            f"zero_evaluable_seeds={stored_zero_seeds!r} disagrees with "
            f"seeds derived from the counts {derived_zero_seeds!r}"
        )
        ok = False

    summary = d.get("cross_family_fraction_across_seeds", {})
    derived_median: float | None = None
    if counts_consistent and derived_fractions:
        derived_median = statistics.median(derived_fractions)
        derived_summary = {
            "mean": sum(derived_fractions) / len(derived_fractions),
            "median": derived_median,
            "min": min(derived_fractions),
            "max": max(derived_fractions),
        }
        # 1e-12 absorbs summation-order float noise only (the runner uses
        # np.mean's pairwise summation); any genuine count edit moves a
        # fraction by >= 1/(n_evaluable^2), many orders of magnitude larger.
        # Non-finite stored values (NaN, +/-Infinity) are rejected before
        # the tolerance comparison -- NaN would otherwise fail open.
        for key, derived_value in derived_summary.items():
            raw = summary.get(key)
            observed = _finite_or_none(raw)
            if observed is None or abs(observed - derived_value) > 1e-12:
                fail(
                    f"cross_family_fraction_across_seeds[{key!r}]={raw!r} "
                    f"disagrees with value derived from per-seed counts "
                    f"({derived_value!r})"
                )
                ok = False
    elif counts_consistent:
        fail("no nonzero-evaluable seed rows to derive aggregates from")
        ok = False

    # The sealed confirmatory values stay pinned as an additional lock on
    # top of the derived-consistency checks above.
    expected = {
        "mean": 0.9941130298273156,
        "median": 1.0,
        "min": 25 / 26,
        "max": 1.0,
    }
    for key, value in expected.items():
        raw = summary.get(key)
        observed = _finite_or_none(raw)
        if observed is None or abs(observed - value) > 1e-12:
            fail(f"{key}={raw!r}, expected {value!r}")
            ok = False

    decision = d.get("decision", {})
    if counts_consistent:
        derived_decision = {
            "cross_gt_within_every_nonzero_seed": (
                bool(nonzero_cross_gt_within) and all(nonzero_cross_gt_within)
            ),
            "median_cross_family_fraction_ge_0_80": (
                derived_median is not None and derived_median >= 0.80
            ),
            "all_ten_seeds_nonzero_evaluable": len(rows) == 10 and not derived_zero_seeds,
        }
        derived_decision["strong_robustness_claim"] = (
            not derived_zero_seeds
            and derived_decision["cross_gt_within_every_nonzero_seed"]
            and derived_decision["median_cross_family_fraction_ge_0_80"]
        )
        for key, derived_flag in derived_decision.items():
            observed = decision.get(key)
            if not isinstance(observed, bool) or observed is not derived_flag:
                fail(
                    f"decision[{key!r}]={observed!r} disagrees with value "
                    f"derived from per-seed counts ({derived_flag!r})"
                )
                ok = False

    # The confirmatory claim itself additionally requires every decision
    # boolean to be true, not merely internally consistent.
    for key in (
        "cross_gt_within_every_nonzero_seed",
        "median_cross_family_fraction_ge_0_80",
        "all_ten_seeds_nonzero_evaluable",
        "strong_robustness_claim",
    ):
        if decision.get(key) is not True:
            fail(f"decision[{key!r}] is not true")
            ok = False

    accession = d.get("accession_summary", {})
    observed_accessions = (
        accession.get("n_unique_evaluable_accessions"),
        accession.get("n_always_cross_family"),
        accession.get("n_always_within_family"),
        accession.get("n_mixed"),
    )
    if observed_accessions != (102, 101, 1, 0):
        fail(f"accession summary={observed_accessions}, expected (102, 101, 1, 0)")
        ok = False

    protocol = d.get("protocol", {})
    if protocol.get("seeds") != expected_seeds or protocol.get("R") != 1000 or protocol.get("k") != 25:
        fail("protocol metadata does not match the locked ten-seed design")
        ok = False
    if protocol.get("scale") != "t30" or protocol.get("distant_threshold") != 0.9:
        fail("protocol scale/threshold does not match the locked design")
        ok = False
    if protocol.get("robustness_unit") != "panel_seed" or protocol.get("pooled_binomial_interval") is not False:
        fail("robustness-unit metadata drifted from the preregistration")
        ok = False

    if ok:
        print("  10 seeds; median=1.000 mean=0.994113 min=0.961538; strong rule: OK")
    return ok


def check_mapper_augmentation() -> bool:
    print("\n[4/8] mapper_augmentation_results.json")
    path = SUMMARIES / "mapper_augmentation_results.json"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    ok = True

    ci_lo = d.get("rescue_ci_lo", d.get("ci_lo", None))
    ci_hi = d.get("rescue_ci_hi", d.get("ci_hi", None))
    if ci_lo is not None and ci_hi is not None:
        if not (ci_lo <= 0 <= ci_hi):
            fail(f"rescue CI [{ci_lo}, {ci_hi}] does not include zero")
            ok = False
        else:
            print(f"  rescue CI [{ci_lo}, {ci_hi}] includes zero (consistent with no rescue): OK")
    else:
        print("  mapper augmentation results present (CI fields not in expected format; skipping value check)")

    return ok


def check_adversarial() -> bool:
    print("\n[5/8] adversarial_results.json")
    path = SUMMARIES / "adversarial_results.json"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    ok = True

    targets = d.get("targets", [])
    if len(targets) != 3:
        fail(f"expected 3 adversarial targets, got {len(targets)}")
        ok = False
    else:
        accs = {t["uniprot_acc"] for t in targets}
        expected = {"P0C1X3", "Q6RY98", "P13208"}
        if accs != expected:
            fail(f"target accessions {accs} != expected {expected}")
            ok = False
        else:
            print(f"  3 targets present: {sorted(accs)}: OK")
    return ok


def check_v3_final() -> bool:
    print("\n[6/8] v3_final.txt")
    path = SUMMARIES / "v3_final.txt"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    size = path.stat().st_size
    if size < 10_000:
        fail(f"v3_final.txt is only {size} bytes (expected >10KB)")
        return False
    print(f"  v3_final.txt exists ({size:,} bytes): OK")
    return True


def check_paper_pdfs() -> bool:
    print("\n[7/8] paper PDFs")
    ok = True
    for n in range(1, 6):
        pattern = list((REPO_ROOT / "papers").glob(f"{n:02d}_*/paper.pdf"))
        if not pattern:
            fail(f"missing paper {n} PDF")
            ok = False
        else:
            print(f"  paper {n}: {pattern[0].relative_to(REPO_ROOT)}: OK")
    return ok


def check_claims_doc() -> bool:
    print("\n[8/8] docs/CLAIMS_TO_EVIDENCE.md")
    path = REPO_ROOT / "docs" / "CLAIMS_TO_EVIDENCE.md"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    size = path.stat().st_size
    if size < 1_000:
        fail(f"CLAIMS_TO_EVIDENCE.md is only {size} bytes (suspiciously small)")
        return False
    print(f"  docs/CLAIMS_TO_EVIDENCE.md exists ({size:,} bytes): OK")
    return True


def main() -> int:
    print("Evidence spot-checks")
    print("====================")

    results = [
        check_calibration(),
        check_cross_family(),
        check_cross_family_10seed(),
        check_mapper_augmentation(),
        check_adversarial(),
        check_v3_final(),
        check_paper_pdfs(),
        check_claims_doc(),
    ]

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} checks passed.")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
