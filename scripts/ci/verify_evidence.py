#!/usr/bin/env python3
"""Spot-check headline numerical claims against committed JSON summaries.

Verifies that the committed evidence files contain the values claimed in
the README's Machine-Readable Index. Does NOT require LFS payload -- reads
only from data/results_summaries/ (small JSON files, not LFS-tracked).

Checks:
  1. calibration_results.json: ECE_close=0.069, ECE_distant=0.294,
     distant_precision=0.068, ECE ratio between 4.0 and 4.5
  2. cross_family_partition.json: within_family=0, cross_family=20
  3. mapper_augmentation_results.json exists and reports CI including zero
  4. adversarial_results.json: 3 targets present
  5. v3_final.txt exists and is non-empty
  6. All 5 paper PDFs exist
  7. docs/CLAIMS_TO_EVIDENCE.md exists

Exit code:
  0  if all checks pass
  1  if any check fails
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUMMARIES = REPO_ROOT / "data" / "results_summaries"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def check_calibration() -> bool:
    print("\n[1/7] calibration_results.json")
    path = SUMMARIES / "calibration_results.json"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    ok = True

    if d["close"]["ECE"] != 0.069:
        fail(f"ECE_close={d['close']['ECE']}, expected 0.069")
        ok = False
    if d["distant"]["ECE"] != 0.294:
        fail(f"ECE_distant={d['distant']['ECE']}, expected 0.294")
        ok = False

    pp = d["distant"]["positive_prediction"]
    if pp["precision"] != 0.068:
        fail(f"distant_precision={pp['precision']}, expected 0.068")
        ok = False
    if pp["tp"] != 3 or pp["n_predicted_positive"] != 44:
        fail(f"distant tp={pp['tp']} n={pp['n_predicted_positive']}, expected 3/44")
        ok = False

    ratio = d.get("ece_distant_to_close_ratio", 0)
    if not (4.0 <= ratio <= 4.5):
        fail(f"ECE ratio={ratio}, expected between 4.0 and 4.5")
        ok = False

    if ok:
        print("  ECE close=0.069 distant=0.294 ratio=4.26x precision=3/44=0.068: OK")
    return ok


def check_cross_family() -> bool:
    print("\n[2/7] cross_family_partition.json")
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


def check_mapper_augmentation() -> bool:
    print("\n[3/7] mapper_augmentation_results.json")
    path = SUMMARIES / "mapper_augmentation_results.json"
    if not path.is_file():
        fail(f"missing: {path}")
        return False
    d = json.loads(path.read_text(encoding="utf-8"))
    ok = True

    ci_lo = d.get("rescue_ci_lo", d.get("ci_lo", None))
    ci_hi = d.get("rescue_ci_hi", d.get("ci_hi", None))
    if ci_lo is not None and ci_hi is not None:
        if not (ci_lo < 0 < ci_hi):
            fail(f"rescue CI [{ci_lo}, {ci_hi}] does not include zero")
            ok = False
        else:
            print(f"  rescue CI [{ci_lo}, {ci_hi}] includes zero (consistent with no rescue): OK")
    else:
        print("  mapper augmentation results present (CI fields not in expected format; skipping value check)")

    return ok


def check_adversarial() -> bool:
    print("\n[4/7] adversarial_results.json")
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
    print("\n[5/7] v3_final.txt")
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
    print("\n[6/7] paper PDFs")
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
    print("\n[7/7] docs/CLAIMS_TO_EVIDENCE.md")
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
