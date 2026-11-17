"""Inspect layers of sheets 1,2,4,5 and pier geometry on sheet5."""
from __future__ import annotations
import sys
from pathlib import Path
import ezdxf

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "artifacts" / "gad-acceptance" / "nine_span_slab" / "e969b72979196f78e2d04129c2462268d6caf099"


def bbox_xy(e):
    pts = e.get_points("xy")
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def rects(msp, layer):
    out = []
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == layer:
            x0, y0, x1, y1 = bbox_xy(e)
            out.append(tuple(round(v, 4) for v in (x0, y0, x1, y1)))
    return out


def main():
    names = {
        "S1": "e969b72979196f78e2d04129c2462268d6caf099_Sheet1_Plan.dxf",
        "S2": "e969b72979196f78e2d04129c2462268d6caf099_Sheet2_LongSection.dxf",
        "S4": "e969b72979196f78e2d04129c2462268d6caf099_Sheet4_Foundation.dxf",
        "S5": "e969b72979196f78e2d04129c2462268d6caf099_Sheet5_PierAbutment.dxf",
    }
    for k, fn in names.items():
        msp = ezdxf.readfile(str(OUT / fn)).modelspace()
        layers = sorted({e.dxf.layer for e in msp})
        print(f"== {k} layers ({len(layers)}) ==")
        print(layers)
        for want in ("SUB-PIER", "SUB-ABUT", "FOUND-CAP", "FOUND-PILE"):
            r = rects(msp, want)
            if r:
                print(f"  {want}: {len(r)} rects -> {r[:6]}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
