#!/usr/bin/env python3
"""Audit BOQ line provenance.

Rules, from MASTER-PLAN §Q3-C and GUIDE §11:
  1. every line has a status
  2. `estimated` lines carry a multiplier and a source note
  3. `calculated` lines carry a formula and source fields
  4. `not_calculated` lines carry a reason and no amount
  5. estimated fraction is below the ceiling for this stage

    python scripts/check_boq_provenance.py [--ceiling 0.45]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
for _pkg in ("bridgecad-core", "bridgecad-bill", "bridgecad-io"):
    _p = ROOT / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GOLDEN = ROOT / "tests" / "draw" / "golden"
CEILING_BY_STAGE = {"baseline": 0.70, "q3": 0.45, "release": 0.20}


def _audit_one(fid: str) -> tuple[list[str], dict[str, int]]:
    from bridgecad_bill.processor import build_boq
    from tests.e2e.run_e2e import _build_from_fixture

    data = json.loads(
        next(p for p in GOLDEN.glob("*.json")
             if json.loads(p.read_text())["_meta"]["fixture_id"] == fid).read_text()
    )
    project = _build_from_fixture(data)
    lines = build_boq(project)

    errors: list[str] = []
    counts = {"calculated": 0, "estimated": 0, "not_calculated": 0}

    for ln in lines:
        status = getattr(ln.status, "value", str(ln.status))
        counts[status] = counts.get(status, 0) + 1
        ref = f"{fid}:{ln.item_no}"

        if status == "estimated":
            if not ln.multiplier or not ln.multiplier_source:
                errors.append(f"{ref}: estimated without multiplier or source")
        elif status == "calculated":
            if not ln.formula or not ln.source_fields:
                errors.append(f"{ref}: calculated without formula or source fields")
        elif status == "not_calculated":
            if not ln.reason:
                errors.append(f"{ref}: not_calculated without a reason")
            if ln.amount is not None:
                errors.append(f"{ref}: not_calculated but carries an amount")
        else:
            errors.append(f"{ref}: unknown status {status!r}")

    return errors, counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ceiling", type=float, default=None,
                    help=f"max estimated fraction; default per stage {CEILING_BY_STAGE}")
    ap.add_argument("--stage", choices=CEILING_BY_STAGE, default="q3")
    args = ap.parse_args()
    ceiling = args.ceiling if args.ceiling is not None else CEILING_BY_STAGE[args.stage]

    fids = sorted(
        json.loads(p.read_text())["_meta"]["fixture_id"] for p in GOLDEN.glob("*.json")
    )
    if not fids:
        print("  no golden fixtures")
        return 1

    all_errors: list[str] = []
    total = {"calculated": 0, "estimated": 0, "not_calculated": 0}

    for fid in fids:
        try:
            errors, counts = _audit_one(fid)
        except Exception as exc:
            all_errors.append(f"{fid}: audit crashed: {exc}")
            continue
        all_errors.extend(errors)
        for k, v in counts.items():
            total[k] = total.get(k, 0) + v

    grand = sum(total.values()) or 1
    est_frac = total["estimated"] / grand

    for e in all_errors[:40]:
        print(f"  [FAIL] {e}")

    print()
    print(f"  calculated     {total['calculated']:4d}  ({100*total['calculated']/grand:5.1f}%)")
    print(f"  estimated      {total['estimated']:4d}  ({100*est_frac:5.1f}%)  ceiling {ceiling:.0%}")
    print(f"  not_calculated {total['not_calculated']:4d}")

    failed = bool(all_errors) or est_frac > ceiling
    print(f"\n  provenance: {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
