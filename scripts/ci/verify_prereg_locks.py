#!/usr/bin/env python3
"""Verify pre-registration SHA256 locks claimed in paper abstracts.

The compendium's central credibility claim is that hypotheses were locked
via SHA256 before any experiment ran. Each paper cites a 16-character
prefix of the lock; the harness `code/harnesses/run_cliff.py` verifies
the full hash at runtime and aborts if the file has been edited. This
script duplicates the verification at CI time so the public Actions tab
displays the integrity status independently of any harness run.

Exit code:
  0  if every claimed pre-registration hash matches the file on disk
  1  if any does not (means the file has been edited since lock --
     a destructive event that voids the registration)
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


# Claimed pre-registration locks, taken verbatim from the paper sources.
# If any of these need to change, the paper that cites the prefix must
# also change in the SAME commit.
EXPECTED = {
    "data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md":
        "139f60129d4e73dfb13444c360cc80c5b48c217d9bc87b1bf4b48b06515bcc06",
    "data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md":
        "f3864d097a0c611d790e6fb15a42e7efb36b2d1b103be4ec1c4f28f99d1004dc",
}


def main() -> int:
    fail = False
    for rel_path, expected in EXPECTED.items():
        path = REPO_ROOT / rel_path
        if not path.is_file():
            print(f"MISSING  {rel_path}")
            fail = True
            continue
        with open(path, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        if actual == expected:
            print(f"OK       {rel_path}")
            print(f"           sha256 = {actual}")
        else:
            print(f"MISMATCH {rel_path}")
            print(f"           expected = {expected}")
            print(f"           actual   = {actual}")
            fail = True

    if fail:
        print("\nFAILED: pre-registration locks do not match. Any byte-level edit "
              "to a SHA256-locked pre-reg voids the registration.")
        return 1

    print("\nAll pre-registration hashes verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
