"""Probe per-sheet region rectangles + declared scales for the layout test.

For each generated evidence sheet, print:
  * the title-block rectangle (union of TITLEBLK-BOX LWPOLYLINE bboxes)
  * the drawing-view rectangle (union of structural/civil/super/sub/found layers)
  * whether those two rectangles overlap
  * every declared "1:<denom>" scale found in TEXT/MTEXT
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import ezdxf

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "artifacts" / "gad-acceptance" / "nine_span_slab" / "e969b72979196f78e2d04129c2462268d6caf099"
P = "e969b72979196f78e2d04129c2462268d6caf099"

SHEETS = [
    "Sheet1_Plan", "Sheet2_LongSection", "Sheet3_CrossSection", "Sheet4_Foundation",
    "Sheet5_PierAbutment", "Sheet6_BearingsJoints", "Sheet7_BOQ",
    "Sheet8_SideElevations", "Sheet9_Reinforcement",
]

VIEW_PREFIXES = ("STRUC", "SUPER", "SUB-", "CIVIL", "FOUND", "ABUT", "DIM")


def bbox(space, pred):
    xs0 = ys0 = float("inf")
    xs1 = ys1 = float("-inf")
    n = 0
    for e in space:
        if not pred(e):
            continue
        try:
            pts = e.get_points("xy")
        except Exception:
            continue
        if not pts:
            continue
        n += 1
        for (x, y) in pts:
            xs0, ys0, xs1, ys1 = min(xs0, x), min(ys0, y), max(xs1, x), max(ys1, y)
    if n == 0:
        return None
    return (xs0, ys0, xs1, ys1, n)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def main():
    for name in SHEETS:
        path = OUT / f"{P}_{name}.dxf"
        if not path.exists():
            print(f"== {name}: MISSING ==")
            continue
        msp = ezdxf.readfile(str(path)).modelspace()
        tb = bbox(msp, lambda e: e.dxf.layer == "TITLEBLK-BOX")
        view = bbox(msp, lambda e: str(e.dxf.layer).startswith(VIEW_PREFIXES))
        print(f"== {name} ==")
        print(f"   TB   : {tb}")
        print(f"   VIEW : {view}")
        print(f"   OVERLAP: {overlaps(tb, view) if (tb and view) else 'n/a'}")
        denoms = set()
        for e in msp.query("TEXT MTEXT"):
            content = getattr(e.dxf, "text", None) or getattr(e, "text", "") or ""
            for m in re.finditer(r"1\s*:\s*(\d+)", str(content)):
                denoms.add(int(m.group(1)))
        print(f"   DENOMS: {sorted(denoms)}")
        print()


if __name__ == "__main__":
    sys.exit(main())
