#!/usr/bin/env python3
"""Verify the SHA-256 byte identities of three archived registrations.

These hashes detect edits to the registered files; they do not establish
when a protocol was written or executed. Public history does not establish
registration-before-execution for the original experiments. See
docs/ERRATUM_2026-10-15.md for chronology and archive scope.

The runtime harness checks only the main factorial registration; this script
checks all three declared file hashes in CI.

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


# Registered file hashes: byte-identity checks, not evidence of lock time.
# The lock is canonically defined over the LF-normalized bytes of each file
# (the form committed to git). We strip CR before hashing so the check is
# byte-stable across platforms: on a Windows clone with core.autocrlf=true the
# working tree carries CRLF line endings, which would otherwise produce a
# spurious MISMATCH even though no content was edited. Normalizing CR here
# matches what `.gitattributes` (`data/prereg/*.md text eol=lf`) guarantees for
# fresh clones, and keeps the EXPECTED hashes below unchanged.
# If any of these need to change, the paper that cites the prefix must
# also change in the SAME commit.
EXPECTED = {
    "data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_v1.md":
        "139f60129d4e73dfb13444c360cc80c5b48c217d9bc87b1bf4b48b06515bcc06",
    "data/prereg/PRE_REGISTRATION_HOMOLOGY_CLIFF_ADDENDUM_FULLNULL.md":
        "f3864d097a0c611d790e6fb15a42e7efb36b2d1b103be4ec1c4f28f99d1004dc",
    # Confirmatory 10-seed extension: the public commit sequence is consistent
    # with registration preceding its later run, not an external timestamp.
    # No runtime harness verifies this registration (CI-only file hash).
    # Its companion digest is at PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md.sha256.
    "data/prereg/PRE_REGISTRATION_CROSS_FAMILY_10SEED_v1.md":
        "204953efeb098f7004b5e82586d5db6f721439b0abe9d214256817679a7a6804",
}


def main() -> int:
    fail = False
    for rel_path, expected in EXPECTED.items():
        path = REPO_ROOT / rel_path
        if not path.is_file():
            print(f"MISSING  {rel_path}")
            fail = True
            continue
        # Hash the LF-normalized content (strip CR) so a CRLF working tree
        # does not void an otherwise-intact registration. See EXPECTED above.
        content = path.read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(content).hexdigest()
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
