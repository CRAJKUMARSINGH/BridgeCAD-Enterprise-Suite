#!/usr/bin/env python3
"""State what the corpus actually covers, and name what it does not.

A corpus with four bridges sounds like coverage. It is coverage of exactly the
regions those four bridges sit in, and nothing else. This writes the regions and
flags the thin ones, so "we have four reference bridges" becomes a checkable
statement instead of a reassuring one.

Sweep parameters are also reported: the extrapolation test runs outside the
corpus and is labelled as extrapolation, not validation.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "references" / "cases"
OUT = REPO / "references" / "coverage.json"

PARAMS = ("nspan", "span_m", "carriageway_m", "abtl_m", "splay_deg")
MIN_DISTINCT = 3


def main() -> int:
    cases = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CASES.glob("*.json"))]
    coverage: dict[str, dict] = {}
    for p in PARAMS:
        vals = sorted({str(c["parameters"][p]) for c in cases if p in c["parameters"]})
        coverage[p] = {
            "distinct": len(vals),
            "values": vals,
            "thin": len(vals) < MIN_DISTINCT,
            "bridges": sorted(c["id"] for c in cases if p in c["parameters"]),
        }

    thin = [p for p, v in coverage.items() if v["thin"]]
    payload = {
        "cases": len(cases),
        "coverage": coverage,
        "thin": thin,
        "known_gaps": [
            "no skew bridge",
            "no curved or integral abutment",
            "no splay below 30 or above 60 deg",
            "no carriageway above 11 m",
            "no nspan above 4",
            "no bridge where ABTL < carriageway (negative face run)",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for p, v in coverage.items():
        flag = "  THIN" if v["thin"] else ""
        print(f"  {p:<16} {v['distinct']} distinct{flag}")
    print(f"\n  {len(thin)} thin parameter(s): {', '.join(thin) if thin else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
