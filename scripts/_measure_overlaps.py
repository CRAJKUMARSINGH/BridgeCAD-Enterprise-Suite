"""Investigate annotation overlaps in the resolved nine-span package.

Outputs a collision report: sheet, entities, bounding boxes, severity.
Distinguishes hatch/table intersections (expected) from genuine label collisions.
"""
import sys, json, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'packages/bridgecad-draw'))
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'packages/bridgecad-qa'))

from bridgecad_draw.layout_audit import BBox

import ezdxf

REPO = pathlib.Path(__file__).parents[1]
pkg_dir = sorted((REPO / 'artifacts/gad-acceptance/nine_span_slab_resolved').iterdir())
pkg_dir = [d for d in pkg_dir if d.is_dir()][0]

# Hatch / table layers whose text-box intersection with a label is expected
# (a hatched fill zone overlaps dimension labels by design; a table header
# overlaps its own cell text).
EXPECTED_OVERLAP_LAYERS = frozenset({
    'HTCH-GENERAL', 'HTCH-CONCRETE', 'HTCH-REBAR', 'HTCH-EARTH',
    'TABL-GRID', 'TABL-BOX', 'TABL-HEADER',
})

collisions = []
for dxf_path in sorted(pkg_dir.glob('*.dxf')):
    sheet = dxf_path.stem.split('_', 1)[-1] if '_' in dxf_path.stem else dxf_path.stem
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    boxes = []
    for e in msp.query('TEXT MTEXT'):
        box = BBox.from_entity(e, sheet=sheet)
        if box.width > 0 and box.height > 0:
            boxes.append((e.dxf.layer, box, e.dxftype()))
    for i, (lyr_a, a, ka) in enumerate(boxes):
        for lyr_b, b, kb in boxes[i+1:]:
            if not a.overlaps(b):
                continue
            # Is this an expected table/hatch intersection?
            expected = bool(EXPECTED_OVERLAP_LAYERS & {lyr_a, lyr_b})
            # Classify severity: two non-identical labels on the same sheet
            # and same view area that fully overlap are HIGH; partial overlap
            # (corner clip) is MEDIUM; expected table/hatch is LOW
            area_a = a.width * a.height
            area_b = b.width * b.height
            ox = max(0, min(a.x1, b.x1) - max(a.x0, b.x0))
            oy = max(0, min(a.y1, b.y1) - max(a.y0, b.y0))
            overlap_area = ox * oy
            overlap_pct = overlap_area / min(area_a, area_b) if min(area_a, area_b) > 0 else 0
            if expected:
                sev = 'LOW'
            elif overlap_pct > 0.5:
                sev = 'HIGH'
            elif overlap_pct > 0.1:
                sev = 'MEDIUM'
            else:
                sev = 'LOW'
            collisions.append({
                'sheet': sheet,
                'entity_a': {'layer': lyr_a, 'type': ka,
                             'text': a.text[:40], 'bbox': [round(a.x0,2), round(a.y0,2), round(a.x1,2), round(a.y1,2)]},
                'entity_b': {'layer': lyr_b, 'type': kb,
                             'text': b.text[:40], 'bbox': [round(b.x0,2), round(b.y0,2), round(b.x1,2), round(b.y1,2)]},
                'overlap_pct': round(overlap_pct * 100, 1),
                'severity': sev,
                'expected': expected,
            })

print(f'Total collisions: {len(collisions)}')
by_sev = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
for c in collisions:
    by_sev[c['severity']].append(c)

for sev in ('HIGH', 'MEDIUM', 'LOW'):
    items = by_sev[sev]
    print(f'\n--- {sev} ({len(items)}) ---')
    for c in items:
        print(f"  {c['sheet']:25s}  {c['entity_a']['layer']:20s} '{c['entity_a']['text']}'"
              f"  x  {c['entity_b']['layer']:20s} '{c['entity_b']['text']}'  ({c['overlap_pct']}% overlap)")

out = REPO / 'artifacts/gad-acceptance/collision-report.json'
out.write_text(json.dumps({'total': len(collisions), 'collisions': collisions}, indent=2), encoding='utf-8')
print(f'\nwrote {out}')
