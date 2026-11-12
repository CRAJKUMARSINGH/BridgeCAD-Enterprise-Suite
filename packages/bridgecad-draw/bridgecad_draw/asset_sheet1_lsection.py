"""bridgecad_draw.asset_sheet1_lsection — PMGSY minor bridge, sheet 01 of 03.

Reproduces page 1 of
``sample-gad-drawings/ilide.info-01-gad-at-ch-2-300-7x9-0-pr_*.pdf``:

  * L-SECTIONAL ELEVATION — seven 9.000 m spans, 20 mm expansion joints,
    75 mm wearing coat over the RCC solid slab, approach slabs, return walls,
    weep holes, PCC abutments and the battered PCC piers with stepped footings.
  * PLAN VIEW — deck outline, 7 500 carriageway between 450 kerbs, pier cap
    footprints, abutments, railing, drainage spouts, 2:1 bank slopes, span
    chain and overall-width dimensions.
  * SCHEDULE OF BRIDGE DATA — chainage / FRL / BL / height / width / B1..B4,
    plus the arithmetic checks that tie the schedule to the geometry.

A3 landscape, everything driven by :class:`asset_specs.SlabBridgeSpec`.
"""

from __future__ import annotations

from pathlib import Path

from ._sheetkit import TXT_XS, Sheet
from .asset_specs import PMGSY_SLAB, SlabBridgeSpec


def _ground_profile(spec: SlabBridgeSpec) -> list[tuple[float, float]]:
    """Bed level under the bridge, embankment rising on a 2:1 slope to FRL."""
    bl = spec.bed_level
    run = 6.0
    L = spec.length_m
    return [
        (-run - 3.0, spec.frl + 0.15),
        (-run, spec.frl),
        (-run * 0.55, (spec.frl + bl) / 2.0),
        (-2.5, bl + 0.35),
        (L + 2.5, bl + 0.35),
        (L + run * 0.55, (spec.frl + bl) / 2.0),
        (L + run, spec.frl),
        (L + run + 3.0, spec.frl + 0.15),
    ]


# ---------------------------------------------------------------------------


def _elevation(sh: Sheet, spec: SlabBridgeSpec) -> None:
    L = spec.length_m
    soffit = spec.soffit
    wc_top = spec.frl
    wc_bot = spec.frl - spec.wearing_mm / 1000.0
    slab_bot = soffit
    panel = sh.panel((12.0, 200.0, 412.0, 274.0), (-9.0, L + 9.0),
                     (spec.found_level - 0.9, spec.frl + 1.5), fit="xy", pad=1.0)

    # ---- ground ------------------------------------------------------
    prof = _ground_profile(spec)
    panel.poly(prof, layer="CIVIL-GROUND", close=True)
    panel.band(-9.0, spec.found_level - 0.9, L + 9.0, spec.bed_level + 0.35,
               pattern="ANSI37", scale=9.0, layer="FOUND-SOIL")
    panel.line(-9.0, spec.bed_level, L + 9.0, spec.bed_level, layer="CIVIL-HFL",
               linetype="DASHED")

    # ---- deck --------------------------------------------------------
    panel.rect(0.0, slab_bot, L, wc_bot - slab_bot, layer="SUPER-DECK")
    panel.hatch([(0.0, slab_bot), (L, slab_bot), (L, wc_bot), (0.0, wc_bot)],
                pattern="ANSI31", scale=6.0, layer="STRUC-HATCHING")
    panel.rect(0.0, wc_bot, L, wc_top - wc_bot, layer="SUPER-WEARING", color=8)
    # kerbs / railing along the deck edge
    panel.line(0.0, wc_top + 0.55, L, wc_top + 0.55, layer="SUPER-PARAPET", lw=25)
    for i in range(0, spec.spans * 4):
        xk = i * spec.span_m / 4.0
        panel.line(xk, wc_top, xk, wc_top + 0.55, layer="SUPER-PARAPET", lw=13)

    # ---- expansion joints + bearings ---------------------------------
    for i in range(spec.spans + 1):
        x = i * spec.span_m
        panel.line(x, slab_bot, x, wc_top, layer="SUB-EXPJOINT", color=1, lw=35)
        panel.rect(x - 0.16, slab_bot - 0.07, 0.32, 0.07, layer="SUB-BEARING", color=2)

    # ---- piers -------------------------------------------------------
    for x in spec.pier_chainages():
        half = spec.pier_stem_m / 2.0
        cap_top = slab_bot - 0.07
        panel.rect(x - half - 0.10, cap_top - 0.10, spec.pier_stem_m + 0.20, 0.10,
                   layer="SUB-PIER")
        panel.rect(x - half, cap_top - 0.45, spec.pier_stem_m, 0.35, layer="SUB-PIER")
        y_top = cap_top - 0.45
        y_bot = spec.bed_level + 0.30
        taper = 0.30
        shaft = [(x - half, y_top), (x + half, y_top),
                 (x + half + taper, y_bot), (x - half - taper, y_bot)]
        panel.poly(shaft, layer="SUB-PIER", close=True)
        panel.hatch(shaft, pattern="ANSI31", scale=6.0, layer="STRUC-HATCHING")
        w = spec.pier_stem_m + 2 * taper
        yy = y_bot
        for _ in range(2):
            w += spec.pier_step_m
            panel.rect(x - w / 2.0, yy - 0.30, w, 0.30, layer="SUB-PIER")
            yy -= 0.30
        panel.rect(x - w / 2.0 - 0.15, yy - 0.45, w + 0.30, 0.45, layer="FOUND-OPEN")
        panel.hatch([(x - w / 2.0 - 0.15, yy - 0.45), (x + w / 2.0 + 0.15, yy - 0.45),
                     (x + w / 2.0 + 0.15, yy), (x - w / 2.0 - 0.15, yy)],
                    pattern="ANSI31", scale=5.0, layer="STRUC-HATCHING")

    # ---- abutments ---------------------------------------------------
    for side, x in ((-1, 0.0), (1, L)):
        pts = [
            (x, slab_bot - 0.07),
            (x + side * 0.45, slab_bot - 0.07),
            (x + side * 0.45, wc_top - 0.65),
            (x + side * 1.05, wc_top - 0.65),
            (x + side * 1.35, spec.found_level),
            (x + side * 0.15, spec.found_level),
        ]
        panel.poly(pts, layer="SUB-ABUT", close=True)
        panel.hatch(pts, pattern="ANSI31", scale=6.0, layer="STRUC-HATCHING")
        panel.rect(min(x, x + side * spec.b1) - 0.10, spec.found_level - 0.55,
                   spec.b1 + 0.20, 0.55, layer="FOUND-OPEN")
        panel.rect(min(x, x + side * 0.30), wc_top, 0.30, 0.55, layer="SUB-DIRT-WALL")
        panel.rect(min(x, x + side * 1.10), wc_top - 0.30, 1.10, 0.30, layer="SUB-ABUT")
        for wy in (wc_top - 1.10, wc_top - 2.10):
            panel.sample(x + side * 0.72, wy, 0.11, layer="SUB-PIER")

    # ---- approach slabs ---------------------------------------------
    for side, x in ((-1, 0.0), (1, L)):
        panel.rect(min(x, x + side * 2.6), wc_top - spec.approach_slab_mm / 1000.0, 2.6,
                   spec.approach_slab_mm / 1000.0, layer="SUPER-DECK", color=9)

    # ---- supports ----------------------------------------------------
    panel.text("A1", 0.0, spec.found_level - 0.75, 3.2, "TEXT-TITLE", align="CENTER")
    panel.text("A2", L, spec.found_level - 0.75, 3.2, "TEXT-TITLE", align="CENTER")
    for i, x in enumerate(spec.pier_chainages(), start=1):
        panel.text(f"P{i}", x, spec.found_level - 0.75, 3.0, "TEXT-HEADER", align="CENTER")

    # ---- span chain --------------------------------------------------
    dy = spec.bed_level - 1.15
    xs = [0.0] + spec.pier_chainages() + [L]
    for i in range(len(xs) - 1):
        lab = (f"{spec.span_m * 1000:.0f} C/C" if i == 0
               else (f"{spec.span_m * 1000:.0f}" if i < spec.spans - 1 else
                     f"{spec.span_m * 1000:.0f} TYP."))
        sh.dim_h(panel.X(xs[i]), panel.X(xs[i + 1]), panel.Y(dy), lab, off=-6.0, th=1.9)
    sh.dim_h(panel.X(0.0), panel.X(L), panel.Y(dy) - 9.0,
             f"OVERALL {L:.0f} m  ({spec.spans} SPANS @ {spec.span_m:.1f} m)", off=-6.0,
             th=2.0)

    # ---- levels ------------------------------------------------------
    for val, tag in ((wc_top, "F.R.L."), (slab_bot, "SOFFIT"),
                     (spec.bed_level, "BED LVL"), (spec.found_level, "FOUND. LVL")):
        sh.level(panel.X(L * 0.5), panel.Y(val), val, prefix=tag, dx=-3.0)

    # ---- leaders (all relative to the feature) ------------------------
    panel.leader(L * 0.62, wc_top, 0.0, 7.0, "75 mm THK R.C.C. WEARING COAT")
    panel.leader(L * 0.30, slab_bot + 0.30, 0.0, -9.0,
                 f"R.C.C. SOLID SLAB {spec.deck_slab_mm:.0f} THK")
    panel.leader(0.0, wc_top + 0.28, -22.0, 4.0, "DIRT WALL", align="RIGHT")
    panel.leader(-1.3, wc_top - 0.16, -26.0, -6.0, "APPROACH SLAB 300 THK", align="RIGHT")
    panel.leader(spec.pier_chainages()[1], spec.bed_level - 0.05, 0.0, -6.0,
                 "BED LEVEL \u2014 SAND / SILT")
    panel.caption_below("L-Sectional Elevation",
                        f"{spec.spans} x {spec.span_m:.1f} m R.C.C. SOLID SLAB  \u2014  "
                        f"NOT TO SCALE")


# ---------------------------------------------------------------------------


def _plan(sh: Sheet, spec: SlabBridgeSpec) -> None:
    L = spec.length_m
    hw = spec.deck_width_m / 2.0
    cw = spec.carriageway_m / 2.0
    kerb = spec.kerb_mm / 1000.0
    panel = sh.panel((12.0, 106.0, 412.0, 188.0), (-6.0, L + 6.0),
                     (-hw - 3.0, hw + 3.0), fit="uniform", pad=1.5)

    # ---- deck + kerbs + railing --------------------------------------
    panel.rect(0.0, -hw, L, spec.deck_width_m, layer="SUPER-DECK")
    panel.hatch([(0.0, -hw), (L, -hw), (L, hw), (0.0, hw)],
                pattern="ANSI31", scale=9.0, layer="STRUC-HATCHING")
    panel.rect(0.0, -cw, L, spec.carriageway_m, layer="SUPER-DECK", color=7)
    panel.rect(0.0, cw, L, kerb, layer="SUPER-KERB")
    panel.rect(0.0, -hw, L, kerb, layer="SUPER-KERB")
    for s in (-1, 1):
        panel.line(0.0, s * hw, L, s * hw, layer="SUPER-PARAPET", lw=35)
    # bank edges beyond the deck ends
    for x0, x1 in ((-6.0, 0.0), (L, L + 6.0)):
        panel.line(x0, -hw, x1, -hw, layer="CIVIL-GROUND")
        panel.line(x0, hw, x1, hw, layer="CIVIL-GROUND")

    # ---- centreline -----------------------------------------------
    panel.line(-6.0, 0.0, L + 6.0, 0.0, layer="STRUC-CENTRE", linetype="CENTER")

    # ---- piers, abutments, joints -----------------------------------
    for x in spec.pier_chainages():
        panel.rect(x - 0.45, -hw, 0.90, spec.deck_width_m, layer="SUB-PIER", color=6)
        panel.hatch([(x - 0.45, -hw), (x + 0.45, -hw), (x + 0.45, hw), (x - 0.45, hw)],
                    pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING", color=6)
    for x in (0.0, L):
        x0 = x if x else -0.55
        panel.rect(x0, -hw - 0.35, 0.55, spec.deck_width_m + 0.70, layer="SUB-ABUT")
    for i in range(spec.spans + 1):
        panel.line(i * spec.span_m, -hw, i * spec.span_m, hw, layer="SUB-EXPJOINT",
                   color=1, lw=25)
    for i in range(spec.spans):
        for s in (-1, 1):
            panel.sample(4.5 + i * spec.span_m, s * (cw + 0.18), 0.14,
                         layer="SUPER-DRAINAGE")

    # ---- bank slopes -------------------------------------------------
    for x, sgn in ((0.0, -1), (L, 1)):
        panel.line(x, hw, x + sgn * 2.0, hw + 2.4, layer="CIVIL-GROUND", linetype="DASHED")
        panel.line(x, -hw, x + sgn * 2.0, -hw - 2.4, layer="CIVIL-GROUND", linetype="DASHED")
        panel.text("SLOPE 2:1", x + sgn * 1.4, hw + 2.7, 1.9, "TEXT-SPEC", align="CENTER")

    # ---- dimensions --------------------------------------------------
    yb = panel.Y(-hw) - 7.0
    xs = [0.0] + spec.pier_chainages() + [L]
    for i in range(len(xs) - 1):
        sh.dim_h(panel.X(xs[i]), panel.X(xs[i + 1]), yb,
                 f"{spec.span_m * 1000:.0f} C/C EXP. JOINT" if i in (0, spec.spans - 1)
                 else None, off=-5.5, th=1.8)
    sh.dim_v(panel.Y(-hw), panel.Y(hw), panel.X(L) + 9.0,
             f"{spec.deck_width_m * 1e3:.0f} OVERALL", off=5.0, th=2.0)
    sh.dim_v(panel.Y(-cw), panel.Y(cw), panel.X(-2.5),
             f"{spec.carriageway_m * 1e3:.0f} CARRIAGEWAY", off=-6.0, th=1.8)

    # ---- labels ------------------------------------------------------
    panel.text("STEEL RAILING", L * 0.18, hw + 0.45, 1.8, "TEXT-SPEC", align="CENTER")
    panel.text(f"{spec.kerb_mm:.0f} KERB", L * 0.55, cw + kerb / 2.0 - 0.12, 1.6,
               "TEXT-SPEC", align="CENTER")
    panel.text("DRAINAGE SPOUT", L * 0.36, -cw - 1.05, 1.6, "TEXT-SPEC", align="CENTER")
    panel.text("A1", 0.0, -hw - 1.35, 2.8, "TEXT-TITLE", align="CENTER")
    panel.text("A2", L, -hw - 1.35, 2.8, "TEXT-TITLE", align="CENTER")
    for i, x in enumerate(spec.pier_chainages(), start=1):
        panel.text(f"P{i}", x, -hw - 1.35, 2.5, "TEXT-HEADER", align="CENTER")

    panel.caption_below("Plan View",
                        f"DECK {spec.deck_width_m * 1e3:.0f} OVERALL  |  CARRIAGEWAY "
                        f"{spec.carriageway_m * 1e3:.0f}  |  450 KERB  \u2014  NOT TO SCALE")
    sh.north(panel.X(L + 4.0), panel.y1 - 14.0, size=8.0)


# ---------------------------------------------------------------------------


def _schedule(sh: Sheet, spec: SlabBridgeSpec) -> None:
    x, y = 12.0, 92.0
    sh.text("SCHEDULE OF BRIDGE DATA", x, y + 2.0, 2.4, "TEXT-HEADER")
    rows = [["PARAMETER", "VALUE"]] + spec.schedule_rows()
    bot = sh.table(x, y - 1.0, (48.0, 50.0), rows, row_h=4.0, th=1.85)
    sh.text(f"HEIGHT CHECK :  FRL {spec.frl:.3f} \u2212 BL {spec.bed_level:.3f} = "
            f"{spec.height_m:.3f} m  (source schedule 5.015 m)", x, bot - 5.0, 1.8,
            "TEXT-SPEC")
    sh.text(f"SOFFIT (DERIVED) :  FRL \u2212 (75 WC + {spec.deck_slab_mm:.0f} SLAB) = "
            f"{spec.soffit:.3f} m", x, bot - 9.5, 1.8, "TEXT-SPEC")

    # legend, to the right of the schedule and clear of the title block
    lx = 118.0
    sh.text("LEGEND", lx, y + 2.0, 2.4, "TEXT-HEADER")
    items = [
        ("ANSI31", "PLAIN / REINFORCED CEMENT CONCRETE", "STRUC-HATCHING"),
        ("ANSI37", "FOUNDATION SOIL / BACKFILL", "FOUND-SOIL"),
        ("DASHED", "BED LEVEL / GROUND LINE", "CIVIL-GROUND"),
        ("CENTER", "BRIDGE CENTRE LINE", "STRUC-CENTRE"),
        ("SOLID", "WEARING COAT / APPROACH SLAB", "SUPER-WEARING"),
    ]
    ly = y - 3.0
    for pat, name, layer in items:
        sh.hatch_box(lx, ly - 3.0, 9.0, 4.0, pattern=pat if pat != "SOLID" else "SOLID",
                     scale=3.0, layer=layer)
        sh.rect(lx, ly - 3.0, 9.0, 4.0, layer="BORDER-INNER", lw=9)
        sh.text(name, lx + 12.0, ly - 1.8, 1.8, "TEXT-GENERAL")
        ly -= 7.6
    sh.text("DRAWING SET REPRODUCES SAMPLE-GAD-DRAWINGS/", lx, ly - 2.0, 1.6, "TEXT-SPEC")
    sh.text("ilide.info-01-gad-at-ch-2-300-7x9-0-pr.pdf  (page 1)", lx, ly - 5.4, 1.6,
            "TEXT-SPEC")


def generate(spec: SlabBridgeSpec = PMGSY_SLAB,
             output_path: str | Path = "Sheet1_LSection_Plan.dxf") -> Path:
    sh = Sheet("A3", "PMGSY GAD Sheet 01")
    sh.banner(f"GENERAL ARRANGEMENT DRAWING OF MINOR BRIDGE \u2014 SPAN {spec.spans} x "
              f"{spec.span_m:.1f} m", 279.0)
    _elevation(sh, spec)
    _plan(sh, spec)
    _schedule(sh, spec)
    sh.title_block(
        client=spec.ident.client, consultant=spec.ident.consultant, road=spec.ident.road,
        title=f"GENERAL ARRANGEMENT DRAWING OF MINOR BRIDGE OF SPAN "
              f"{spec.spans} x {spec.span_m:.1f} MTR.",
        drawing_no=f"{spec.ident.drawing_prefix} / 01", sheet_no="01",
        total_sheets=f"{spec.ident.total_sheets:02d}", scale="NTS",
        date=spec.ident.date, drawn=spec.ident.drawn, designed=spec.ident.designed,
        approved=spec.ident.approved, revision=spec.ident.revision,
    )
    sh.footer("BridgeCAD Enterprise Suite \u2014 asset pack \u2014 sheet 01/03 \u2014 "
              "dimensions verbatim from source GAD")
    return sh.save(output_path)


__all__ = ["generate"]
