#!/usr/bin/env python3
"""Generate the 8-sheet package for each golden case into a target directory.

Shared by measure.sh and any CI job that needs real DXFs. No pytest involved.

    python scripts/_gen_golden_packages.py --out build/metrics/pkg
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).parents[1]
for _pkg in (
    "bridgecad-core", "bridgecad-io", "bridgecad-draw",
    "bridgecad-bill", "bridgecad-qa", "bridgecad-export",
):
    _p = ROOT / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GOLDEN = ROOT / "tests" / "draw" / "golden"


def _fixture(fid: str) -> Path:
    for p in sorted(GOLDEN.glob("*.json")):
        if json.loads(p.read_text(encoding="utf-8")).get("_meta", {}).get("fixture_id") == fid:
            return p
    raise FileNotFoundError(f"no golden fixture {fid!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cases", nargs="*", default=None)
    args = ap.parse_args()

    from bridgecad_draw.booklet import generate_package
    from tests.e2e.run_e2e import _build_from_fixture

    ids = args.cases
    if not ids:
        ids = [
            json.loads(p.read_text(encoding="utf-8"))["_meta"]["fixture_id"]
            for p in sorted(GOLDEN.glob("*.json"))
        ]
    if not ids:
        print("  no golden fixtures — run scripts/freeze_golden.py --write")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    rc = 0
    for fid in ids:
        try:
            data = json.loads(_fixture(fid).read_text(encoding="utf-8"))
            project = _build_from_fixture(data)
            dest = args.out / fid
            sheets = generate_package(project, dest, prefix=fid)
            print(f"  [ok] {fid}: {len(sheets)}/8 sheets")
        except Exception as exc:
            print(f"  [FAIL] {fid}: {exc}")
            traceback.print_exc()
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
