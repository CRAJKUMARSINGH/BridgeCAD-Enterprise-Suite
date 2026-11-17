"""Temporary diagnostic: dump Sheet2 text boxes near the two reported collisions."""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "packages" / "bridgecad-draw"))

import ezdxf  # noqa: E402

from bridgecad_draw.layout_audit import BBox  # noqa: E402

pkg = [d for d in sorted((REPO / "artifacts/gad-acceptance/nine_span_slab_resolved").iterdir()) if d.is_dir()][0]
sheet2 = [p for p in pkg.glob("*Sheet2*.dxf")][0]
print("sheet2:", sheet2.name)

doc = ezdxf.readfile(str(sheet2))
msp = doc.modelspace()

rows = []
for e in msp.query("TEXT MTEXT"):
    box = BBox.from_entity(e, sheet="S2")
    rows.append((box.y0, box.x0, box.x1, box.y1, e.dxf.layer, str(box.text), e.dxftype()))

print("\n--- region A: y in [85,108], x in [640,700] ---")
for y0, x0, x1, y1, lyr, txt, k in sorted(rows):
    if 85 <= y0 <= 108 and 640 <= x0 <= 700:
        print(f"  y {y0:7.2f}-{y1:7.2f}  x {x0:7.2f}-{x1:7.2f}  {lyr:16s} {k:5s} {txt!r}")

print("\n--- region C: x0 > 660 (right part of the drawing), all y ---")
for y0, x0, x1, y1, lyr, txt, k in sorted(rows):
    if x0 > 660:
        print(f"  y {y0:7.2f}-{y1:7.2f}  x {x0:7.2f}-{x1:7.2f}  {lyr:16s} {k:5s} {txt!r}")
