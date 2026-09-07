#!/usr/bin/env python3
"""Compute CVSS 4.0 scores for supplied vectors.

Print score, severity, and normalized vector as tab-separated fields.
Exit nonzero if any vector fails.
"""

import sys

from cvss import CVSS4


def main(argv):
    if not argv:
        sys.exit("usage: cvss_score.py <vector> [vector ...]")

    bad = 0
    for vector in argv:
        try:
            scored = CVSS4(vector)
        except Exception as e:
            print(f"FAIL {vector} -> {e}")
            bad = 1
            continue
        print(f"{scored.base_score}\t{scored.severity}\t{scored.clean_vector()}")
    return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
