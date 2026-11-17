"""Measure the cross-view agreement values for the nine-span package.

Reads the generated evidence DXFs (read-only) and prints every number the
cross-view test will assert, plus the canonical resolver record.
"""
from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _pkg in ["bridgecad-core", "bridgecad-draw", "bridgecad-catalogue"]:
    _p = REPO / "packages" / _pkg
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ezdxf  # noqa: E402

OUT = REPO / "artifacts" / "gad-acceptance" / "nine_span_slab" / "e969b72979196f78e2d04129c2462268d6caf099"
P = "e969b72979196f78e2d04129c2462268d6caf099"


def msp(name):
    return ezdxf.readfile(str(OUT / f"{P}_{name}.dxf")).modelspace()


def rects(space, layer):
    out = []
    for e in space:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == layer:
            pts = e.get_points("xy")
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def hlines(space, layer):
    out = []
    for e in space:
        if e.dxftype() == "LINE" and e.dxf.layer == layer:
            s, en = e.dxf.start, e.dxf.end
            if abs(s.y - en.y) < 1e-9:
                out.append((min(s.x, en.x), s.y, max(s.x, en.x)))
    return out


def load_gen():
    spec = importlib.util.spec_from_file_location("_gen", REPO / "scripts" / "generate_all_pwd_gads.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    from bridgecad_catalogue import registry
    from bridgecad_catalogue.resolve import resolve
    from bridgecad_core.geometry.long_section import typical_pier_support_level

    gen = load_gen()
    card = registry.by_id("BR-I-2022-002")
    params = resolve(card, {"span_count": "9", "span_length_m": "10"})
    params["id"] = card["id"]
    project = gen._build_project(params)

    # ── Sheet 1 plan ───────────────────────────────────────────────────────
    s1 = msp("Sheet1_Plan")
    outline = rects(s1, "STRUC-OUTLINE")
    print("S1 STRUC-OUTLINE:", outline)
    ox0 = outline[0][0]
    ox1 = outline[0][2]
    sc_plan = (ox1 - ox0) / 90.0
    print(f"S1 plan mm/m = {sc_plan:.6f}  (denom {1000.0/sc_plan:.3f})")

    def plan_ch(x):
        return (x - ox0) / sc_plan

    pier_c = sorted(round((r[0] + r[2]) / 2.0, 6) for r in rects(s1, "SUB-PIER"))
    abut_c = sorted(round((r[0] + r[2]) / 2.0, 6) for r in rects(s1, "SUB-ABUT"))
    print("S1 SUB-PIER count:", len(pier_c), "chainages:", [round(plan_ch(x), 4) for x in pier_c])
    print("S1 SUB-ABUT count:", len(abut_c), "chainages:", [round(plan_ch(x), 4) for x in abut_c])

    # ── Sheet 2 long section ───────────────────────────────────────────────
    s2 = msp("Sheet2_LongSection")
    deck = hlines(s2, "SUPER-DECK")
    print("S2 SUPER-DECK horizontal lines (x0,y,x1):", deck)
    sfx0 = min(d[0] for d in deck)
    sfx1 = max(d[2] for d in deck)
    sc_h = (sfx1 - sfx0) / 90.0
    print(f"S2 H mm/m = {sc_h:.6f} (H denom {1000.0/sc_h:.3f})")
    ys = sorted(d[1] for d in deck)
    y_soffit, y_slabtop = ys[0], ys[1]
    hfl_line = hlines(s2, "CIVIL-HFL")
    y_hfl = hfl_line[0][1]
    sc_v = (y_soffit - y_hfl) / (101.925 - 100.0)
    print(f"S2 V mm/m = {sc_v:.6f} (V denom {1000.0/sc_v:.3f})  y_hfl={y_hfl} y_soffit={y_soffit}")

    def sec_rl(y):
        return 100.0 + (y - y_hfl) / sc_v

    def sec_ch(x):
        return (x - sfx0) / sc_h

    # group SUB-PIER rects by x-centre
    from collections import defaultdict

    groups = defaultdict(list)
    for r in rects(s2, "SUB-PIER"):
        groups[round((r[0] + r[2]) / 2.0, 6)].append(r)
    print("S2 SUB-PIER unique x-centres:", len(groups))
    for cx in sorted(groups):
        rs = sorted(groups[cx], key=lambda r: r[1])
        ch = sec_ch(cx)
        print(f"  x={cx} ch={ch:.4f}")
        for r in rs:
            print(f"     y0={r[1]:.4f} y1={r[3]:.4f}  RL0={sec_rl(r[1]):.4f} RL1={sec_rl(r[3]):.4f}"
                  f"  x0={r[0]:.4f} x1={r[2]:.4f}")
    print("S2 SUB-ABUT rects:")
    for r in sorted(rects(s2, "SUB-ABUT"), key=lambda r: r[0]):
        print(f"  x0={r[0]:.4f} x1={r[2]:.4f} y0={r[1]:.4f} y1={r[3]:.4f}"
              f"  ch_c={(sec_ch((r[0]+r[2])/2)):.4f} RL0={sec_rl(r[1]):.4f} RL1={sec_rl(r[3]):.4f}")

    # ── canonical record ───────────────────────────────────────────────────
    rec = typical_pier_support_level(project)
    import json
    print("RECORD:", json.dumps(rec.to_json(), indent=2))
    print("shaft_base_rec =", rec.shaft_base_rl_m, " footing_top_rec =", rec.footing_top_rl_m)
    print("pier_height_typical_m =", project.substructure.pier_height_typical_m)
    print("HFL - pier_height =", Decimal("100.0") - Decimal(str(project.substructure.pier_height_typical_m)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
