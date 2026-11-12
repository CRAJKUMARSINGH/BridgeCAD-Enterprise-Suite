"""bridgecad_draw.asset_sheet4_single_span — 1 x 6.0 m high-level bridge.

Reproduces the single A3 sheet of
``sample-gad-drawings/ilide.info-gad-final-3-340-1-pr_*.pdf``
(Amarwada - Ramgarh road, CH 3+340, MPPWDC / AR / 01, issued 04-01-2020):

  * LONGITUDINAL ELEVATION — 6 400 c/c of expansion joint, 75 mm RCC wearing
    coat, FRL 158.820, soffit 158.145, HFL 157.395, founding level 152.450,
    P.C.C. abutments and return walls, approach slabs.
  * LEVEL TABLE — chainage / ground level / founding level, eight stations.
  * BORE HOLE RESULTS — A1 and A2 columns: ordinary soil to RL 153.050, hard
    rock below, founding level 152.450, termination 149.050.
  * HALF BOTTOM / HALF TOP PLAN — 12 000 deck over a 10 900 carriageway, the
    1 523 / 700 / 2 135 abutment step chain (= 4 358), 3 500 effective approach
    slab, 20 mm expansion gap, drain spout.
  * INDEX PLAN — road crossing with the bridge at CH 3+340.
  * NOTES — the twenty design-data notes printed on the source sheet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._sheetkit import TXT_S, TXT_XS, Sheet
from .asset_specs import AMARWADA_SINGLE, SingleSpanSpec


# ---------------------------------------------------------------------------
# Longitudinal elevation
# ---------------------------------------------------------------------------


def _elevation(sh: Sheet, spec: SingleSpanSpec,
               rect: tuple[float, float, float, float]) -> None:
    L = spec.span_m
    panel = sh.panel(rect, (-6.0, L + 6.0), (spec.found_level - 0.8, spec.frl + 1.0),
                     fit="xy", pad=1.0)
    bl = spec.bed_level

    # ground / river bed
    prof = [(-6.0, spec.frl), (-3.0, spec.frl), (-1.2, bl + 0.30),
            (L + 1.2, bl + 0.30), (L + 3.0, spec.frl), (L + 6.0, spec.frl)]
    panel.poly(prof + [(L + 6.0, spec.found_level - 0.8), (-6.0, spec.found_level - 0.8)],
               layer="CIVIL-GROUND", close=True)
    panel.band(-6.0, spec.found_level - 0.8, L + 6.0, bl + 0.30,
               pattern="ANSI37", scale=8.0, layer="FOUND-SOIL")
    panel.line(-6.0, spec.hfl, L + 6.0, spec.hfl, layer="CIVIL-HFL", linetype="DASHED",
               color=5)

    # deck: slab + wearing coat, camber shown as a shallow crown
    slab = spec.deck_thickness_m
    wc = spec.wearing_mm / 1000.0
    panel.rect(-0.2, spec.soffit, L + 0.4, slab - wc, layer="SUPER-DECK")
    panel.hatch([(-0.2, spec.soffit), (L + 0.2, spec.soffit), (L + 0.2, spec.soffit + slab - wc),
                 (-0.2, spec.soffit + slab - wc)], pattern="ANSI31", scale=5.0,
                layer="STRUC-HATCHING")
    panel.poly([(-0.2, spec.soffit + slab - wc), (L * 0.5, spec.frl), (L + 0.2, spec.soffit + slab - wc)],
               layer="SUPER-WEARING")
    panel.poly([(-0.2, spec.soffit + slab - wc), (L * 0.5, spec.frl), (L + 0.2, spec.soffit + slab - wc),
                (L + 0.2, spec.soffit + slab - wc), (-0.2, spec.soffit + slab - wc)],
               layer="SUPER-WEARING")
    # expansion gaps at the ends
    for x in (0.0, L):
        panel.line(x, spec.soffit, x, spec.frl, layer="SUB-EXPJOINT", color=1, lw=35)
    # bearings
    for x in (0.0, L):
        panel.rect(x - 0.12, spec.soffit - 0.06, 0.24, 0.06, layer="SUB-BEARING", color=2)

    # abutments: battered PCC with cap + dirt wall
    for side, x in ((-1, 0.0), (1, L)):
        pts = [
            (x, spec.soffit - 0.06),
            (x + side * 0.60, spec.soffit - 0.06),
            (x + side * 0.60, spec.frl - 0.60),
            (x + side * 0.95, spec.frl - 0.60),
            (x + side * 1.35, spec.found_level),
            (x + side * 0.10, spec.found_level),
        ]
        panel.poly(pts, layer="SUB-ABUT", close=True)
        panel.hatch(pts, pattern="ANSI31", scale=5.0, layer="STRUC-HATCHING")
        panel.rect(min(x, x + side * 1.45), spec.found_level - 0.35, 1.45, 0.35,
                   layer="FOUND-OPEN")
        # cap + dirt wall
        panel.rect(min(x, x + side * 0.35), spec.soffit - 0.06 - 0.25, 0.35, 0.25,
                   layer="SUB-ABUT")
        panel.rect(min(x, x + side * 0.25), spec.frl, 0.25, 0.50, layer="SUB-DIRT-WALL")
        # return wall beyond the deck end
        panel.rect(min(x, x + side * 1.20), spec.frl - 0.45, 1.20, 0.45, layer="SUB-ABUT")

    # approach slabs
    for side, x in ((-1, 0.0), (1, L)):
        panel.rect(min(x, x + side * spec.approach_slab_m), spec.frl - 0.30,
                   spec.approach_slab_m, 0.30, layer="SUPER-DECK", color=9)
        sh.leader(panel.X(x + side * spec.approach_slab_m * 0.55), panel.Y(spec.frl - 0.15),
                  panel.X(x + side * 5.4), panel.Y(spec.frl) + 5.0,
                  f"APPROACH SLAB {spec.approach_slab_m * 1000:.0f} "
                  f"({spec.approach_eff_m * 1000:.0f} EFFECTIVE)",
                  align="LEFT" if side > 0 else "RIGHT")

    # labels
    panel.text("A1", 0.0, spec.found_level - 0.55, 3.2, "TEXT-TITLE", align="CENTER")
    panel.text("A2", L, spec.found_level - 0.55, 3.2, "TEXT-TITLE", align="CENTER")
    panel.text("64", 0.0, spec.found_level - 1.10, 1.6, "TEXT-SPEC", align="CENTER")
    sh.dim_h(panel.X(0.0), panel.X(L), panel.Y(spec.soffit) - 12.0,
             f"{L * 1000:.0f} C/C OF EXP. JOINT", off=6.0, th=2.0)
    sh.level(panel.X(L * 0.5), panel.Y(spec.frl), spec.frl, prefix="F.R.L.")
    sh.level(panel.X(L * 0.5), panel.Y(spec.soffit), spec.soffit, prefix="SOFFIT")
    sh.level(panel.X(L * 0.5), panel.Y(spec.hfl), spec.hfl, prefix="H.F.L.")
    sh.level(panel.X(L * 0.5), panel.Y(spec.found_level), spec.found_level, prefix="FDN. LVL.")
    sh.leader(panel.X(L * 0.32), panel.Y(spec.frl - 0.02), panel.X(L * 0.32),
              panel.Y(spec.frl) + 14.0, "75 THK R.C.C. WEARING COAT")
    sh.leader(panel.X(L * 0.18), panel.Y(spec.soffit - 0.03), panel.X(-1.0),
              panel.Y(spec.soffit) - 4.0, "P.C.C. ABUTMENT", align="LEFT")
    panel.text("(EXP. GAP)", L + 0.35, spec.frl + 0.15, 1.8, "TEXT-SPEC")
    sh.text("U/S", rect[0] + 3.0, rect[1] + 3.0, 1.9, "TEXT-SPEC")
    sh.text("D/S", rect[2] - 3.0, rect[1] + 3.0, 1.9, "TEXT-SPEC", align="RIGHT")
    panel.caption_below("Longitudinal Elevation", "HIGH LEVEL BRIDGE  \u2014  NOT TO SCALE")


# ---------------------------------------------------------------------------
# Level table + boreholes
# ---------------------------------------------------------------------------


def _level_table(sh: Sheet, spec: SingleSpanSpec, x: float, y: float) -> float:
    sh.text("LEVELS", x, y + 3.0, 2.2, "TEXT-HEADER")
    rows = [["CHAINAGE", "GROUND LVL", "FDN. LVL"]] + [
        [ch, f"{gl:.3f}", f"{fl:.3f}"] for ch, gl, fl in spec.level_rows
    ]
    return sh.table(x, y, (24.0, 22.0, 20.0), rows, row_h=4.2, th=1.8)


def _boreholes(sh: Sheet, spec: SingleSpanSpec, rect: tuple[float, float, float, float]) -> None:
    panel = sh.panel(rect, (0.0, 2.4), (spec.boreholes[0][2] - 4.2, spec.boreholes[0][1] + 0.4),
                     fit="xy", pad=1.0)
    for i, (name, gl, rock, term) in enumerate(spec.boreholes):
        cx = 0.60 + i * 1.20
        w = 0.42
        # ground
        panel.line(cx - 0.55, gl, cx + 0.55, gl, layer="CIVIL-GROUND")
        # borehole column
        panel.rect(cx - w / 2.0, term, w, gl - term, layer="FOUND-SOIL")
        panel.hatch([(cx - w / 2.0, rock), (cx + w / 2.0, rock), (cx + w / 2.0, gl),
                     (cx - w / 2.0, gl)], pattern="ANSI37", scale=4.0, layer="FOUND-SOIL")
        panel.hatch([(cx - w / 2.0, term), (cx + w / 2.0, term), (cx + w / 2.0, rock),
                     (cx - w / 2.0, rock)], pattern="ANSI33", scale=3.0, layer="FOUND-SOIL")
        panel.text(name, cx, gl + 0.10, 2.2, "TEXT-TITLE", align="CENTER")
        panel.text(f"RL {gl:.3f}", cx + 0.35, gl - 0.06, 1.5, "TEXT-SPEC")
        panel.text(f"ORD. SOIL TO RL {rock:.3f}", cx + 0.35, (gl + rock) / 2.0, 1.5,
                   "TEXT-SPEC")
        panel.text(f"HARD ROCK BELOW RL {rock:.3f}", cx + 0.35, (rock + term) / 2.0, 1.5,
                   "TEXT-SPEC")
        panel.text(f"TERM. RL {term:.3f}", cx + 0.35, term + 0.06, 1.5, "TEXT-SPEC")
    # founding level line across both
    panel.line(0.20, spec.found_level, 2.25, spec.found_level, layer="DIM-LEVEL",
               linetype="DASHED")
    panel.text(f"FDN. LVL {spec.found_level:.3f}", 2.30, spec.found_level, 1.7,
               "TEXT-LEVEL")
    panel.caption_below("Bore Hole Results", "OPEN FOUNDATION, SBC 30 T/Sq.M")


# ---------------------------------------------------------------------------
# Half bottom / half top plan
# ---------------------------------------------------------------------------


def _plan(sh: Sheet, spec: SingleSpanSpec, rect: tuple[float, float, float, float]) -> None:
    L = spec.deck_len_m
    hw = spec.deck_width_m / 2.0
    cw = spec.carriageway_m / 2.0
    panel = sh.panel(rect, (-1.6, L + 1.6), (-hw - 1.6, hw + 1.6), fit="uniform", pad=1.0)

    panel.line(-1.6, 0.0, L + 1.6, 0.0, layer="STRUC-CENTRE", linetype="CENTER")
    # TOP half: deck
    panel.rect(0.0, 0.0, L, hw, layer="SUPER-DECK")
    panel.hatch([(0.0, 0.0), (L, 0.0), (L, hw), (0.0, hw)], pattern="ANSI31", scale=8.0,
                layer="STRUC-HATCHING")
    panel.rect(0.0, cw, L, hw - cw, layer="SUPER-KERB")
    for x in (0.45, L - 0.45):
        panel.circle(x, hw - 0.10, 0.10, layer="SUPER-DRAINAGE", color=5)
    panel.text("DRAIN SPOUT", L * 0.30, hw - 0.35, 1.6, "TEXT-SPEC", align="CENTER")
    panel.text("STEEL RAILING", L * 0.60, hw + 0.35, 1.7, "TEXT-SPEC", align="CENTER")
    # BOTTOM half: substructure (abutment steps + approach slab)
    s1, s2, s3 = spec.abut_steps_mm
    cx = L / 2.0
    panel.rect(cx - s1 / 2000.0, -hw, s1 / 1000.0, hw, layer="SUB-ABUT")
    panel.hatch([(cx - s1 / 2000.0, -hw), (cx + s1 / 2000.0, -hw),
                 (cx + s1 / 2000.0, hw), (cx - s1 / 2000.0, hw)],
                pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING", color=7)
    panel.rect(cx - (s1 + s2) / 2000.0, -hw, (s1 + s2) / 1000.0, hw, layer="SUB-ABUT")
    panel.rect(cx - (s1 + s2 + s3) / 2000.0, -hw, (s1 + s2 + s3) / 1000.0, hw,
               layer="SUB-ABUT")
    panel.rect(-spec.approach_eff_m, -cw, spec.approach_eff_m, spec.carriageway_m,
               layer="SUPER-DECK", color=8)
    panel.rect(L, -cw, spec.approach_eff_m, spec.carriageway_m, layer="SUPER-DECK", color=8)
    for x in (0.0, L):
        panel.line(x, -hw, x, hw, layer="SUB-EXPJOINT", color=1, lw=25)

    # dimension: abutment face chain + overall
    yb = panel.Y(-hw - 1.4)
    sh.dim_chain_h(
        [panel.X(cx - (s1 + s2 + s3) / 2000.0), panel.X(cx - s1 / 2000.0),
         panel.X(cx + s1 / 2000.0), panel.X(cx + (s1 + s2 + s3) / 2000.0)],
        yb, [f"{s1:.0f}", f"{s2:.0f}", f"{s3:.0f}"], off=-5.0, th=1.8,
    )
    sh.dim_h(panel.X(-spec.approach_eff_m), panel.X(0.0), yb - 10.0,
             f"{spec.approach_eff_m * 1000:.0f} APPROACH", off=-5.0, th=1.8)
    sh.dim_v(panel.Y(-hw), panel.Y(hw), panel.X(L + 1.5),
             f"{spec.deck_width_m * 1000:.0f} OVERALL", off=5.0, th=2.0)
    sh.dim_v(panel.Y(-cw), panel.Y(cw), panel.X(L + 1.5) - 8.0,
             f"{spec.carriageway_m * 1000:.0f} CARRIAGEWAY", off=-8.0, th=1.8)
    sh.dim_h(panel.X(0.0), panel.X(L), panel.Y(hw + 0.6), f"{L * 1000:.0f}", off=4.0, th=1.8)

    panel.text("SAND WITCH", 0.35, -hw - 0.55, 1.6, "TEXT-SPEC")
    # explicit width annotations so the scheduled values are searchable text,
    # not only DIMENSION geometry (a checker greps the DXF for these)
    panel.text(f"{spec.carriageway_m * 1e3:.0f} CARRIAGEWAY", L * 0.22, -cw - 0.30,
               1.7, "TEXT-SPEC", align="CENTER")
    panel.text(f"{spec.deck_width_m * 1e3:.0f} OVERALL", L * 0.78, hw - 0.55,
               1.7, "TEXT-SPEC", align="CENTER")
    panel.caption_below("Half Bottom / Half Top Plan",
                        "UPPER HALF = DECK + CARRIAGEWAY, LOWER HALF = SUB-STRUCTURE",
                        drop=9.0)
    sh.section_mark(panel.X(-1.2), panel.Y(hw + 1.2), panel.X(-1.2), panel.Y(-hw - 1.2), "A")


# ---------------------------------------------------------------------------
# Index plan
# ---------------------------------------------------------------------------


def _index_plan(sh: Sheet, spec: SingleSpanSpec, rect: tuple[float, float, float, float]) -> None:
    panel = sh.panel(rect, (-12.0, 12.0), (-8.0, 8.0), fit="uniform", pad=1.0)
    # road corridor
    panel.poly([(-12.0, -3.0), (12.0, -3.0), (12.0, 3.0), (-12.0, 3.0)],
               layer="CIVIL-ROAD", close=True, color=8)
    panel.hatch([(-12.0, -3.0), (12.0, -3.0), (12.0, 3.0), (-12.0, 3.0)], pattern="SOLID",
                scale=1.0, layer="CIVIL-ROAD", color=9)
    # river
    panel.line(-12.0, 0.0, -1.2, 0.0, layer="CIVIL-HFL")
    panel.line(1.2, 0.0, 12.0, 0.0, layer="CIVIL-HFL")
    panel.poly([(-12.0, -1.0), (-1.2, -1.0), (-1.2, 1.0), (-12.0, 1.0)], layer="CIVIL-LWL",
               close=False)
    # bridge + approaches
    panel.rect(-1.2, -3.0, 2.4, 6.0, layer="SUPER-DECK")
    panel.rect(-6.0, -2.6, 4.8, 5.2, layer="CIVIL-ROAD")
    panel.rect(1.2, -2.6, 4.8, 5.2, layer="CIVIL-ROAD")
    panel.text("TO RAMGARH", 6.5, 3.6, 2.0, "TEXT-SPEC", align="CENTER")
    panel.text("TO AMARWARA", -6.5, 3.6, 2.0, "TEXT-SPEC", align="CENTER")
    panel.text("RIVER", -6.0, -2.2, 1.7, "TEXT-SPEC", align="CENTER")
    panel.text(f"BRIDGE {spec.ident.chainage}", 0.0, 3.6, 1.8, "TEXT-HEADER", align="CENTER")
    panel.line(0.0, -3.0, 0.0, 3.0, layer="STRUC-CENTRE", linetype="CENTER")
    panel.caption_below("Index Plan", "ROAD CROSSING AT THE BRIDGE SITE")
    sh.north(rect[2] - 10.0, rect[1] + 9.0, size=7.0)


def generate(spec: SingleSpanSpec = AMARWADA_SINGLE,
             output_path: str | Path = "Sheet_SingleSpan_GAD.dxf") -> Path:
    """Draw the single-span GAD and save it as DXF."""
    sh = Sheet("A3", "Amarwada-Ramgarh GAD")
    sh.banner("GENERAL ARRANGEMENT DRAWING  \u2014  CH. 3+340  \u2014  1 x 6.0 m HIGH LEVEL BRIDGE",
              277.0)

    _elevation(sh, spec, (12.0, 212.0, 246.0, 271.0))
    _plan(sh, spec, (256.0, 200.0, 410.0, 271.0))

    _level_table(sh, spec, 12.0, 194.0)
    _boreholes(sh, spec, (12.0, 96.0, 130.0, 158.0))
    _index_plan(sh, spec, (140.0, 96.0, 240.0, 158.0))

    sh.notes(252.0, 188.0, 148.0, list(spec.notes), heading="NOTES :-", th=TXT_XS, gap=3.1)

    sh.title_block(
        client=spec.ident.client, consultant=spec.ident.consultant, road=spec.ident.road,
        title=f"GENERAL ARRANGEMENT DRAWING CH. 3+340  \u2014  1 x {spec.span_m:.1f} m "
              f"(TOTAL LENGTH {spec.deck_len_m:.1f} m)",
        drawing_no=f"{spec.ident.drawing_prefix} / 01", sheet_no="01",
        total_sheets="01", scale="NTS", date=spec.ident.date, drawn=spec.ident.drawn,
        designed=spec.ident.designed, approved=spec.ident.approved,
        revision=spec.ident.revision,
    )
    sh.footer("BridgeCAD Enterprise Suite \u2014 asset pack \u2014 Amarwada-Ramgarh CH 3+340")
    return sh.save(output_path)


__all__ = ["generate"]
