import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(r"e:\Rajkumar\BridgeCAD-Enterprise-Suite")
for pkg in ["bridgecad-catalogue", "bridgecad-core", "bridgecad-draw", "bridgecad-qa"]:
    p = REPO / "packages" / pkg
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

spec = importlib.util.spec_from_file_location(
    "gen9", REPO / "artifacts" / "gad-acceptance" / "_gen_nine_span.py")
gen9 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen9)

from bridgecad_catalogue import registry
from bridgecad_catalogue import resolve as R

card = registry.by_id("BR-I-2022-002")
ov = {**gen9.BASE, **gen9.VARIANTS[1][1]}
p = R.resolve(card, ov)
p["id"] = card["id"]
gen = gen9._load_generator()
project = gen._build_project(p)

from bridgecad_draw import sheet8_side_elevations as s8
import bridgecad_draw.dxf_engine as de

_orig_ef = s8._draw_abutment_endface


def _spy(*a, **k):
    print("sc", a[3], "th", a[4], "overall_w", a[5])
    print("par_h_m", a[20], "abt_h_m", a[22], "wing_h", a[26], "app_t", a[28])
    print("pile_cut_rl", a[35], "pile_tip_rl", a[36], "tod_rl", a[37],
          "sof_rl", a[38])
    print("road_approach", a[39], "abt_base_rl", a[40], "hfl_rl", a[41],
          "scour_rl", a[42], "found_type", a[43])
    vy = a[2]
    print("vy(102.5)", vy(102.5), "vy(101.925)", vy(101.925),
          "vy(95.925)", vy(95.925), "vy(87.0)", vy(87.0))
    return _orig_ef(*a, **k)


s8._draw_abutment_endface = _spy

doc, msp = de.new_sheet("diag")
s8._draw(msp, project)

ext = defaultdict(lambda: [1e9, -1e9, 1e9, -1e9])
for e in msp:
    t = e.dxftype()
    if t not in ("LINE", "RECTANGLE", "LWPOLYLINE", "CIRCLE", "ARC", "SOLID", "HATCH"):
        continue
    try:
        if t == "LINE":
            xs = [e.dxf.start[0], e.dxf.end[0]]
            ys = [e.dxf.start[1], e.dxf.end[1]]
        elif t == "CIRCLE" or t == "ARC":
            xs = [e.dxf.center[0] - e.dxf.radius, e.dxf.center[0] + e.dxf.radius]
            ys = [e.dxf.center[1] - e.dxf.radius, e.dxf.center[1] + e.dxf.radius]
        else:
            pts = list(e.vertices()) if hasattr(e, "vertices") else []
            if t == "HATCH":
                pts = [p for path in e.paths for p in getattr(path, "vertices", [])]
            if not pts:
                continue
            xs = [pt[0] for pt in pts]
            ys = [pt[1] for pt in pts]
    except Exception:
        continue
    if max(xs) > 400:  # View 1 only
        continue
    b = ext[str(e.dxf.layer)]
    b[0] = min(b[0], min(xs)); b[1] = max(b[1], max(xs))
    b[2] = min(b[2], min(ys)); b[3] = max(b[3], max(ys))

print("layer                          x0      x1      y0      y1")
for k, v in sorted(ext.items()):
    print(f"{k:28s} {v[0]:7.2f} {v[1]:7.2f} {v[2]:7.2f} {v[3]:7.2f}")

print()
print("abutment_stack:", )
from bridgecad_core.abutment_stack import resolve_abutment_stack
st = resolve_abutment_stack(project)
print("  bear", st.bear_rl, "cap_top", st.cap_top, "cap_bot", st.cap_bot)
