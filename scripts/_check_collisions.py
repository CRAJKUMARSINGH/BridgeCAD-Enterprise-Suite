"""Detail the remaining HIGH collisions — confirm false positive vs genuine."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'packages/bridgecad-draw'))
from bridgecad_draw.layout_audit import BBox
import ezdxf

REPO = pathlib.Path(__file__).parents[1]
pkg_dir = sorted((REPO / 'artifacts/gad-acceptance/nine_span_slab_resolved').iterdir())
pkg_dir = [d for d in pkg_dir if d.is_dir()][0]

for dxf_path in sorted(pkg_dir.glob('*.dxf')):
    sheet = dxf_path.stem.split('_', 1)[-1] if '_' in dxf_path.stem else dxf_path.stem
    if 'Sheet8' not in sheet:
        continue
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    boxes = []
    for e in msp.query('TEXT MTEXT'):
        box = BBox.from_entity(e, sheet=sheet)
        if box.width > 0 and box.height > 0:
            boxes.append((e.dxf.layer, box))

    print(f'\n=== {sheet} ===')
    for i, (la, a) in enumerate(boxes):
        for lb, b in boxes[i+1:]:
            if not a.overlaps(b):
                continue
            # y separation between centres
            cy_a = (a.y0 + a.y1) / 2
            cy_b = (b.y0 + b.y1) / 2
            y_sep = abs(cy_a - cy_b)
            cx_a = (a.x0 + a.x1) / 2
            cx_b = (b.x0 + b.x1) / 2
            x_sep = abs(cx_a - cx_b)
            genuine = y_sep < max(a.height, b.height) * 2 and x_sep < max(a.width, b.width)
            print(f"  {'GENUINE' if genuine else 'FP-WIDE-BOX':12s}  "
                  f"y_sep={y_sep:.1f}mm  x_sep={x_sep:.1f}mm  "
                  f"'{a.text[:35]}' x '{b.text[:35]}'")
