"""bridgecad_draw.asset_sheet3_pier — PMGSY minor bridge, sheet 03 of 03.

Reproduces page 3 of
``sample-gad-drawings/ilide.info-01-gad-at-ch-2-300-7x9-0-pr_*.pdf``:

  * PIER ELEVATION — 8 400 deck over a symmetrical mass-concrete pier, stepped
    footing envelopes 9 300 / 9 900 / 10 500 / 11 100.
  * PIER PLAN — the same four envelopes from above, rounded shaft ends and the
    upstream cutwater nose.
  * P.C.C. PIER SECTION — shaft 900 wide, cap, RCC solid slab seat, 20 mm
    expansion gap each side, footing steps 300, founding level.
  * RETAINING WALL SECTION — crest 450, base B = H/3 + 300 heel, 1:3 batter,
    150 levelling course, 100 weep hole.

Every height in this module is an ABSOLUTE reduced level (metres), never a
height above the bed: mixing the two is what makes a pier elevation draw the
deck inside the foundation.
"""

from __future__ import annotations

from pathlib import Path

from ._sheetkit import TXT_XS, Sheet
from .asset_specs import PMGSY_SLAB, SlabBridgeSpec


def _pier_elevation(sh: Sheet, spec: SlabBridgeSpec,
                    rect: tuple[float, float, float, float]) -> None:
    hw = spec.deck_width_m / 2.0
    kerb = spec.kerb_mm / 1000.0
    cw = spec.carriageway_m / 2.0
    steps = list(spec.pier_steps_m)
    fl, frl = spec.found_level, spec.frl
    soffit = spec.soffit

    panel = sh.panel(rect, (-steps[-1] / 2.0 - 0.6, steps[-1] / 2.0 + 0.6),
                     (fl - 0.8, frl + 0.9), fit="uniform", pad=1.0)

    # ---- deck + wearing coat (absolute RLs) --------------------------
    panel.rect(-hw, soffit, spec.deck_width_m, spec.deck_thickness_m, layer="SUPER-DECK")
    panel.hatch([(-hw, soffit), (hw, soffit), (hw, soffit + spec.deck_thickness_m),
                 (-hw, soffit + spec.deck_thickness_m)],
                pattern="ANSI31", scale=6.0, layer="STRUC-HATCHING")
    panel.line(-hw, frl, hw, frl, layer="SUPER-WEARING", lw=30)
    for s in (-1, 1):
        x0 = cw if s > 0 else -hw
        panel.rect(x0, soffit + spec.deck_thickness_m, kerb, 0.30, layer="SUPER-KERB")

    # ---- pier cap + shaft --------------------------------------------
    cap_bot = soffit - 0.09
    panel.rect(-hw, cap_bot, spec.deck_width_m, 0.09, layer="SUB-PIER")
    half = spec.pier_stem_m / 2.0
    shaft_top = cap_bot - 0.35
    panel.rect(-half, shaft_top, spec.pier_stem_m, 0.35, layer="SUB-PIER")
    taper = 0.30
    y_bed = spec.bed_level + 0.30
    shaft = [(-half, shaft_top), (half, shaft_top),
             (half + taper, y_bed), (-half - taper, y_bed)]
    panel.poly(shaft, layer="SUB-PIER", close=True)
    panel.hatch(shaft, pattern="ANSI31", scale=5.0, layer="STRUC-HATCHING")

    # ---- stepped footing ---------------------------------------------
    w = spec.pier_stem_m + 2 * taper
    yy = y_bed
    for _ in range(2):
        w += spec.pier_step_m
        panel.rect(-w / 2.0, yy - 0.30, w, 0.30, layer="SUB-PIER")
        yy -= 0.30
    panel.rect(-steps[-1] / 2.0, fl, steps[-1], yy - fl, layer="FOUND-OPEN")
    panel.hatch([(-steps[-1] / 2.0, fl), (steps[-1] / 2.0, fl),
                 (steps[-1] / 2.0, yy), (-steps[-1] / 2.0, yy)],
                pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING")
    panel.line(-steps[-1] / 2.0 - 0.4, fl, steps[-1] / 2.0 + 0.4, fl,
               layer="CIVIL-GROUND", linetype="DASHED")
    # soil either side of the pier up to bed level
    for s in (-1, 1):
        x0 = steps[-1] / 2.0 if s > 0 else -steps[-1] / 2.0 - 1.0
        panel.band(x0, fl - 0.8, x0 + 1.0, spec.bed_level, pattern="ANSI37", scale=6.0,
                   layer="FOUND-SOIL")

    # ---- dimensions --------------------------------------------------
    ybot = fl - 0.55
    sh.dim_h(panel.X(-hw), panel.X(hw), panel.Y(frl + 0.55),
             f"{spec.deck_width_m * 1e3:.0f} OVERALL", off=4.0, th=1.9)
    sh.dim_h(panel.X(-cw), panel.X(cw), panel.Y(frl + 0.20),
             f"{spec.carriageway_m * 1e3:.0f} C/WAY", off=4.0, th=1.7)
    for i, wv in enumerate(steps):
        sh.dim_h(panel.X(-wv / 2.0), panel.X(wv / 2.0), panel.Y(ybot) - 2.0 - i * 6.5,
                 f"{wv * 1000:.0f}", off=-4.0, th=1.8)
    sh.dim_v(panel.Y(spec.bed_level), panel.Y(y_bed), panel.X(steps[-1] / 2.0) + 7.0,
             "300", off=4.0, th=1.6)
    sh.dim_v(panel.Y(fl), panel.Y(yy), panel.X(steps[-1] / 2.0) + 15.0, "900 TOT.",
             off=4.0, th=1.6)

    panel.text(f"FOUND. LVL RL {fl:.3f}", 0.0, fl - 0.22, 1.8, "TEXT-LEVEL", align="CENTER")
    panel.text(f"BED LVL RL {spec.bed_level:.3f}", 0.0, spec.bed_level + 0.08, 1.7,
               "TEXT-LEVEL", align="CENTER")
    panel.leader(0.0, shaft_top - 0.15, 16.0, -2.0, f"PIER SHAFT {spec.pier_stem_m * 1000:.0f} WIDE")
    panel.leader(0.0, cap_bot - 0.03, 16.0, 2.0, "PIER CAP \u2014 RCC M20")
    panel.caption_below("Pier Elevation", f"TYPICAL FOR PIERS P1 TO P{spec.spans - 1}")


def _pier_plan(sh: Sheet, spec: SlabBridgeSpec,
               rect: tuple[float, float, float, float]) -> None:
    steps = list(spec.pier_steps_m)
    plan_len = 2.10
    panel = sh.panel(rect, (-steps[-1] / 2.0 - 0.5, steps[-1] / 2.0 + 0.5),
                     (-plan_len / 2.0 - 0.35, plan_len / 2.0 + 0.35), fit="uniform", pad=1.0)
    for i, w in enumerate(steps):
        panel.rect(-w / 2.0, -plan_len / 2.0, w, plan_len,
                   layer="SUB-PIER" if i else "FOUND-CAP")
    half = spec.pier_stem_m / 2.0
    panel.rect(-half, -plan_len / 2.0, spec.pier_stem_m, plan_len, layer="SUB-PIER")
    panel.circle(-half, 0.0, plan_len / 2.0, layer="SUB-PIER")
    panel.circle(half, 0.0, plan_len / 2.0, layer="SUB-PIER")
    panel.poly([(-half, -plan_len / 2.0), (-half - 0.55, 0.0), (-half, plan_len / 2.0)],
               layer="SUB-PIER")
    panel.line(-steps[-1] / 2.0 - 0.4, 0.0, steps[-1] / 2.0 + 0.4, 0.0,
               layer="STRUC-CENTRE", linetype="CENTER")
    panel.line(0.0, -plan_len / 2.0 - 0.3, 0.0, plan_len / 2.0 + 0.3,
               layer="STRUC-CENTRE", linetype="CENTER")
    for i, w in enumerate(steps):
        sh.dim_h(panel.X(-w / 2.0), panel.X(w / 2.0), panel.Y(-plan_len / 2.0) - 4.0 - i * 5.5,
                 f"{w * 1000:.0f}", off=-3.5, th=1.7)
    sh.dim_v(panel.Y(-plan_len / 2.0), panel.Y(plan_len / 2.0), panel.X(steps[-1] / 2.0) + 6.0,
             f"{plan_len * 1000:.0f}", off=4.0, th=1.6)
    panel.leader(-half - 0.27, 0.55, -14.0, 8.0, "CUTWATER NOSE (U/S)", align="RIGHT")
    panel.caption_below("Pier Plan", "CONCENTRIC STEPPED FOOTING ENVELOPES")


def _pier_section(sh: Sheet, spec: SlabBridgeSpec,
                  rect: tuple[float, float, float, float]) -> None:
    steps = list(spec.pier_steps_m)
    fl, frl, soffit = spec.found_level, spec.frl, spec.soffit
    panel = sh.panel(rect, (-steps[-1] / 2.0 - 0.5, steps[-1] / 2.0 + 0.5),
                     (fl - 0.8, frl + 0.8), fit="uniform", pad=1.0)

    # slab seat both sides of the 20 mm gap
    for s in (-1, 1):
        x0 = 0.0 if s > 0 else -(steps[-1] / 2.0)
        panel.rect(x0, soffit, steps[-1] / 2.0, spec.deck_thickness_m, layer="SUPER-DECK")
    panel.line(0.0, soffit - 0.35, 0.0, frl + 0.35, layer="SUB-EXPJOINT", color=1, lw=40)
    panel.text("20 mm EXP. GAP AT C/L", 0.12, frl + 0.42, 1.7, "TEXT-SPEC")

    half = spec.pier_stem_m / 2.0
    cap_bot = soffit - 0.09
    panel.rect(-half - 0.35, cap_bot, spec.pier_stem_m + 0.70, 0.09, layer="SUB-PIER")
    shaft_top = cap_bot - 0.35
    panel.rect(-half, shaft_top, spec.pier_stem_m, 0.35, layer="SUB-PIER")
    y_bed = spec.bed_level + 0.30
    shaft = [(-half, shaft_top), (half, shaft_top), (half, y_bed), (-half, y_bed)]
    panel.poly(shaft, layer="SUB-PIER", close=True)
    panel.hatch(shaft, pattern="ANSI31", scale=5.0, layer="STRUC-HATCHING")

    w = spec.pier_stem_m
    yy = y_bed
    for _ in range(2):
        w += 2 * spec.pier_step_m
        panel.rect(-w / 2.0, yy - 0.30, w, 0.30, layer="SUB-PIER")
        yy -= 0.30
    panel.rect(-steps[-1] / 2.0, fl, steps[-1], yy - fl, layer="FOUND-OPEN")
    panel.hatch([(-steps[-1] / 2.0, fl), (steps[-1] / 2.0, fl),
                 (steps[-1] / 2.0, yy), (-steps[-1] / 2.0, yy)],
                pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING")
    for s in (-1, 1):
        x0 = steps[-1] / 2.0 if s > 0 else -steps[-1] / 2.0 - 0.9
        panel.band(x0, fl - 0.8, x0 + 0.9, spec.bed_level, pattern="ANSI37", scale=6.0,
                   layer="FOUND-SOIL")

    sh.dim_h(panel.X(-half), panel.X(half), panel.Y(shaft_top) + 6.0,
             f"{spec.pier_stem_m * 1000:.0f}", off=4.0, th=1.7)
    sh.dim_v(panel.Y(fl), panel.Y(yy), panel.X(steps[-1] / 2.0) + 6.0, "600", off=4.0, th=1.6)
    panel.text(f"FOUND. LVL RL {fl:.3f}", 0.0, fl - 0.22, 1.8, "TEXT-LEVEL", align="CENTER")
    panel.text("RCC SOLID SLAB SEAT", 0.0, soffit + 0.06, 1.6, "TEXT-SPEC", align="CENTER")
    panel.caption_below("P.C.C. Pier Section", f"SHAFT {spec.pier_stem_m * 1000:.0f} WIDE, "
                                              "STEPS 300")


def _retaining_wall(sh: Sheet, spec: SlabBridgeSpec,
                    rect: tuple[float, float, float, float]) -> None:
    h = 3.0
    heel = 0.30
    base = h / 3.0 + heel  # B = H/3 + 300 heel
    fd = 1.20
    crest = 0.45
    panel = sh.panel(rect, (-0.6, base + 0.5), (-fd - 0.7, h + 0.7), fit="uniform", pad=1.0)
    pts = [(0.0, h), (crest, h), (crest + h / 3.0, 0.0), (base, 0.0),
           (base, -fd), (0.0, -fd)]
    panel.poly(pts, layer="SUB-ABUT", close=True)
    panel.hatch(pts, pattern="ANSI31", scale=5.0, layer="STRUC-HATCHING")
    panel.rect(0.0, -fd, base, 0.15, layer="FOUND-OPEN")
    panel.sample(crest * 0.5, -0.35, 0.06, layer="SUB-PIER")
    # backfill against the rear face
    panel.band(-0.55, 0.0, 0.0, h - 0.15, pattern="ANSI37", scale=5.0, layer="FOUND-SOIL")
    panel.line(-0.55, h - 0.15, 0.0, h - 0.15, layer="CIVIL-GROUND")
    sh.dim_h(panel.X(0.0), panel.X(base), panel.Y(-fd) - 4.0, f"B = H/3 + 300 = {base:.2f} m",
             off=-4.0, th=1.7)
    sh.dim_h(panel.X(0.0), panel.X(crest), panel.Y(h) + 5.0, "450", off=4.0, th=1.6)
    panel.text("BATTER 1:3", 0.75, 1.55, 1.7, "TEXT-SPEC", rot=71.6)
    panel.caption_below("Retaining Wall Section", "GRAVITY TYPE \u2014 PCC M20")


# ---------------------------------------------------------------------------


def generate(spec: SlabBridgeSpec = PMGSY_SLAB,
             output_path: str | Path = "Sheet3_PierDetails.dxf") -> Path:
    sh = Sheet("A3", "PMGSY GAD Sheet 03")
    sh.banner("PIER & RETAINING WALL DETAILS  \u2014  "
              f"{spec.spans} x {spec.span_m:.1f} m R.C.C. SOLID SLAB", 279.0)

    _pier_elevation(sh, spec, (12.0, 200.0, 170.0, 270.0))
    _pier_plan(sh, spec, (180.0, 208.0, 410.0, 268.0))
    _pier_section(sh, spec, (12.0, 110.0, 170.0, 184.0))
    _retaining_wall(sh, spec, (180.0, 110.0, 286.0, 184.0))

    # ---- footing envelope summary ------------------------------------
    sh.text("FOOTING ENVELOPE SUMMARY", 296.0, 190.0, 2.2, "TEXT-HEADER")
    rows = [["STEP", "WIDTH (m)"]] + [
        [f"STEP {i + 1}", f"{w:.3f}"] for i, w in enumerate(spec.pier_steps_m)
    ] + [["SHAFT", f"{spec.pier_stem_m:.3f}"],
         ["OFFSET / SIDE", f"{spec.pier_step_m:.3f}"]]
    sh.table(296.0, 186.0, (34.0, 40.0), rows, row_h=4.1, th=1.8)

    # ---- verification + notes ----------------------------------------
    sh.notes(296.0, 148.0, 112.0, [
        "PIER IS MASS CONCRETE PCC M20, CAP RCC M20.",
        "PIERS P1 TO P6 ARE IDENTICAL.",
        "ENVELOPES ARE CONCENTRIC ABOUT BOTH AXES.",
        "CUTWATER NOSE ON THE U/S FACE OF THE SHAFT.",
        f"FOUNDING LEVEL RL {spec.found_level:.3f} m.",
    ], heading="PIER NOTES :-", th=TXT_XS, gap=3.4)
    sh.text("SOURCE : ilide.info-01-gad-at-ch-2-300-7x9-0-pr.pdf, page 3",
            296.0, 120.0, 1.5, "TEXT-SPEC")

    # ---- envelope arithmetic, clear of the title block ----------------
    sh.text("ENVELOPE ARITHMETIC (REPRODUCED FROM SOURCE)", 12.0, 100.0, 2.1, "TEXT-HEADER")
    sh.text(f"{spec.pier_steps_m[0]:.1f} \u2192 {spec.pier_steps_m[1]:.1f} \u2192 "
            f"{spec.pier_steps_m[2]:.1f} \u2192 {spec.pier_steps_m[3]:.1f} m :  "
            f"EACH STEP ADDS {2 * spec.pier_step_m:.1f} m "
            f"({spec.pier_step_m * 1000:.0f} mm EACH SIDE)", 12.0, 94.0, 1.7, "TEXT-SPEC")
    sh.text(f"STEPPED HEIGHT (3 x 300) = 900 mm, FOOTING SLAB 450 mm, "
            f"TOTAL BELOW BED {spec.bed_level - spec.found_level:.2f} m",
            12.0, 89.0, 1.7, "TEXT-SPEC")

    sh.title_block(
        client=spec.ident.client, consultant=spec.ident.consultant, road=spec.ident.road,
        title="GENERAL ARRANGEMENT DRAWING \u2014 PIER & RETAINING WALL DETAILS",
        drawing_no=f"{spec.ident.drawing_prefix} / 03", sheet_no="03",
        total_sheets=f"{spec.ident.total_sheets:02d}", scale="NTS",
        date=spec.ident.date, drawn=spec.ident.drawn, designed=spec.ident.designed,
        approved=spec.ident.approved, revision=spec.ident.revision,
    )
    sh.footer("BridgeCAD Enterprise Suite \u2014 asset pack \u2014 sheet 03/03")
    return sh.save(output_path)


__all__ = ["generate"]
