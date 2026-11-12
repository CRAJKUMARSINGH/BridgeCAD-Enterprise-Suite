"""bridgecad_draw.asset_sheet2_deck_abutment — PMGSY minor bridge, sheet 02 of 03.

Reproduces page 2 of
``sample-gad-drawings/ilide.info-01-gad-at-ch-2-300-7x9-0-pr_*.pdf``:

  * SECTION A-A — transverse deck section: 8 400 overall, 7 500 carriageway,
    450 kerbs, 2.0 % camber, 75 mm wearing coat over the RCC slab, abutment cap
    and dirt wall.
  * SOIL PROFILE — 0.00 / -0.50 / -1.00 / -1.50 strata legend.
  * P.C.C. ABUTMENT SECTION — approach slab 300, levelling course 150, 20 mm
    expansion joint, footing steps B1 / 700 / B2, 1 200 deep footing, 100 mm
    weep holes, 1:3 batter.
  * P.C.C. RETURN WALL SECTION — 1 in 3 front batter, 1 in 10 rear, base B3.
  * TOE WALL SECTION.
  * GENERAL NOTES — the thirteen notes printed on the source sheet.
"""

from __future__ import annotations

from pathlib import Path

from ._sheetkit import TXT_XS, Sheet
from .asset_specs import PMGSY_SLAB, SlabBridgeSpec


# ---------------------------------------------------------------------------


def _deck_section(sh: Sheet, spec: SlabBridgeSpec,
                  rect: tuple[float, float, float, float]) -> None:
    hw = spec.deck_width_m / 2.0
    kerb = spec.kerb_mm / 1000.0
    cw = spec.carriageway_m / 2.0
    slab = spec.deck_slab_mm / 1000.0
    wc = spec.wearing_mm / 1000.0
    panel = sh.panel(rect, (-hw - 1.2, hw + 1.2), (-0.75, slab + wc + 1.45),
                     fit="uniform", pad=1.0)

    top_mid = slab + wc
    pts_top = [(-hw, slab), (-cw, slab + wc), (0.0, top_mid), (cw, slab + wc), (hw, slab)]
    body = [(-hw, 0.0)] + pts_top + [(hw, 0.0)]
    panel.poly(body, layer="SUPER-DECK", close=True)
    panel.hatch(body, pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING")
    # wearing coat over the carriageway only
    panel.poly([(-cw, slab), (-cw, slab + wc), (0.0, top_mid), (cw, slab + wc), (cw, slab)],
               layer="SUPER-WEARING", close=True)
    # kerbs
    for s in (-1, 1):
        x0 = cw if s > 0 else -hw
        panel.rect(x0, slab, kerb, wc + 0.30, layer="SUPER-KERB")
    # railing posts + rail
    for s in (-1, 1):
        xp = s * (cw + kerb / 2.0)
        panel.rect(xp - 0.06, slab + wc + 0.30, 0.12, 0.85, layer="SUPER-PARAPET")
        panel.line(xp - 0.09, slab + wc + 1.15, xp + 0.09, slab + wc + 1.15,
                   layer="SUPER-PARAPET", lw=30)
    # abutment cap + dirt wall under the slab ends
    for s in (-1, 1):
        x0 = cw if s > 0 else -hw
        panel.rect(x0, -0.30, kerb + 0.05, 0.30, layer="SUB-ABUT")
        panel.rect(x0 + (0.05 if s < 0 else -0.05), -0.45, kerb, 0.15, layer="SUB-DIRT-WALL")

    # ---- dimensions --------------------------------------------------
    yb = panel.Y(-0.75) + 4.0
    sh.dim_h(panel.X(-hw), panel.X(hw), yb, f"{spec.deck_width_m * 1e3:.0f} OVERALL WIDTH",
             off=-5.5, th=1.9)
    sh.dim_h(panel.X(-cw), panel.X(cw), yb + 11.0,
             f"{spec.carriageway_m * 1e3:.0f} CARRIAGEWAY", off=-5.5, th=1.9)
    for s in (-1, 1):
        x0 = cw if s > 0 else -hw
        sh.dim_h(panel.X(x0), panel.X(x0 + kerb), yb + 11.0, f"{spec.kerb_mm:.0f}",
                 off=-3.0, th=1.7)
    sh.dim_v(panel.Y(0.0), panel.Y(slab), panel.X(hw) + 7.0,
             f"{spec.deck_slab_mm:.0f}", off=4.0, th=1.8)
    sh.dim_v(panel.Y(slab), panel.Y(slab + wc), panel.X(hw) + 15.0,
             f"{spec.wearing_mm:.0f}", off=4.0, th=1.6)

    # ---- callouts ----------------------------------------------------
    panel.leader(0.0, top_mid, 0.0, 6.0, "CAMBER 2.0 % (CROWN)")
    panel.leader(-cw * 0.55, slab + wc, 0.0, 8.0, "75 mm WEARING COAT")
    panel.leader(cw * 0.45, slab * 0.55, 0.0, -8.0,
                 f"R.C.C. SOLID SLAB {spec.deck_slab_mm:.0f} THK")
    panel.leader(-hw + 0.06, -0.36, -14.0, -8.0, "ABUTMENT CAP", align="RIGHT")
    panel.leader(hw - 0.06, slab + wc + 0.90, 14.0, 6.0, "R.C.C. RAILING", align="LEFT")

    panel.caption_below("Section A-A",
                        f"TRANSVERSE SECTION OF DECK \u2014 {spec.deck_width_m:.1f} m WIDE  |  "
                        f"CAMBER 2.0 %  \u2014  NOT TO SCALE")


# ---------------------------------------------------------------------------


def _soil_profile(sh: Sheet, spec: SlabBridgeSpec,
                  rect: tuple[float, float, float, float]) -> None:
    panel = sh.panel(rect, (0.0, 3.4), (-1.95, 0.45), fit="xy", pad=1.0)
    layers = [
        (0.0, -0.50, "SOFT SOIL", "ANSI37", 5.0),
        (-0.50, -1.00, "SOFT ROCK", "ANSI32", 3.0),
        (-1.00, -1.50, "HARD ROCK", "ANSI33", 3.0),
    ]
    for y0, y1, name, pat, sc in layers:
        panel.rect(0.65, y1, 1.85, y0 - y1, layer="FOUND-SOIL")
        panel.hatch([(0.65, y1), (2.50, y1), (2.50, y0), (0.65, y0)],
                    pattern=pat, scale=sc, layer="FOUND-SOIL")
        panel.text(name, 1.58, (y0 + y1) / 2.0 - 0.07, 1.8, "TEXT-SPEC", align="CENTER")
        panel.text(f"{abs(y0 - y1):.2f} m", 2.62, (y0 + y1) / 2.0 - 0.07, 1.6, "TEXT-SPEC")
    panel.line(0.65, 0.05, 0.65, -1.62, layer="DIM-LEVEL")
    for yv, lab in ((0.0, "0.00  AVG. G.L."), (-0.50, "-0.50"),
                    (-1.00, "-1.00"), (-1.50, "-1.50")):
        panel.line(0.40, yv, 0.90, yv, layer="DIM-LEVEL")
        panel.text(lab, 0.35, yv - 0.06, 1.6, "TEXT-LEVEL", align="RIGHT")
    panel.caption_below("Soil Profile", "STRATA ON WHICH THE FOUNDATION SITS")


# ---------------------------------------------------------------------------


def _abutment_section(sh: Sheet, spec: SlabBridgeSpec,
                      rect: tuple[float, float, float, float]) -> None:
    b1, b2 = spec.b1, spec.b2
    fd = spec.footing_depth_mm / 1000.0
    panel = sh.panel(rect, (-3.4, b1 + 0.7), (-fd - 0.75, 0.95), fit="uniform", pad=1.0)

    pts = [(0.0, 0.30), (0.45, 0.30), (0.75, -0.45), (1.05, -0.90), (b1, -fd), (0.0, -fd)]
    panel.poly(pts, layer="SUB-ABUT", close=True)
    panel.hatch(pts, pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING")
    # levelling course + footing projection
    panel.rect(0.0, -fd, b1, 0.15, layer="FOUND-OPEN")
    panel.rect(-0.15, -fd - 0.10, b1 + 0.15, 0.10, layer="FOUND-OPEN")
    # approach slab on the deck side
    panel.rect(-3.0, 0.30, 3.0, spec.approach_slab_mm / 1000.0, layer="SUPER-DECK", color=9)
    # expansion joint
    panel.line(0.0, 0.24, 0.0, 0.66, layer="SUB-EXPJOINT", color=1, lw=35)
    panel.text(f"{spec.expansion_gap_mm if hasattr(spec, 'expansion_gap_mm') else 20} EJ",
               0.10, 0.70, 1.6, "TEXT-SPEC")
    # weep hole
    panel.sample(-0.13, -0.25, 0.05, layer="SUB-PIER")
    panel.leader(-0.13, -0.25, -18.0, -1.0, f"{spec.weep_hole_mm:.0f} WEEP HOLE",
                 align="RIGHT")

    sh.dim_h(panel.X(0.0), panel.X(b1), panel.Y(-fd - 0.35), f"B1 = {b1:.2f} m",
             off=-4.5, th=1.8)
    sh.dim_h(panel.X(0.0), panel.X(b2), panel.Y(0.42) + 10.0, f"B2 = {b2:.2f} m",
             off=4.0, th=1.7)
    sh.dim_v(panel.Y(-fd), panel.Y(0.0), panel.X(b1) + 5.0, f"{spec.footing_depth_mm:.0f}",
             off=4.0, th=1.8)
    sh.dim_v(panel.Y(0.30), panel.Y(0.30 + spec.approach_slab_mm / 1000.0),
             panel.X(-3.2), "300", off=-4.0, th=1.6)
    panel.text("BATTER 1:3", 0.55, -0.72, 1.6, "TEXT-SPEC", rot=71.6)
    panel.text("150 PCC M15", 0.10, -fd + 0.03, 1.5, "TEXT-SPEC")
    panel.text("SURFACE REINF. 8 TOR @ 200 C/C BOTH WAYS (5 kg/Sq.M)",
               0.20, -fd - 0.42, 1.5, "TEXT-SPEC")
    panel.caption_below("P.C.C. Abutment Section", "M-15 LEVELLING COURSE UNDER FOOTING")


# ---------------------------------------------------------------------------


def _return_wall_section(sh: Sheet, spec: SlabBridgeSpec,
                         rect: tuple[float, float, float, float]) -> None:
    fd = spec.footing_depth_mm / 1000.0
    b3 = spec.b3
    h = 1.10
    panel = sh.panel(rect, (-0.35, b3 + 0.35), (-fd - 0.55, h + 0.35), fit="uniform", pad=1.0)
    pts = [
        (0.0, h), (0.30, h),
        (0.30 + h / 3.0, 0.0), (b3, 0.0),
        (b3, -fd), (0.0, -fd),
    ]
    panel.poly(pts, layer="SUB-ABUT", close=True)
    panel.hatch(pts, pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING")
    panel.rect(0.0, -fd, b3, 0.15, layer="FOUND-OPEN")
    for wy in (-0.28, -0.62):
        xw = 0.30 + (h / 3.0) * (1.0 - abs(wy) / h)
        panel.sample(xw - 0.05, wy, 0.05, layer="SUB-PIER")
    sh.dim_h(panel.X(0.0), panel.X(b3), panel.Y(-fd - 0.30), f"B3 = {b3:.2f} m",
             off=-4.0, th=1.8)
    sh.dim_v(panel.Y(0.0), panel.Y(h), panel.X(-0.20), f"{h * 1000:.0f}", off=-4.0, th=1.6)
    panel.text("1:3", 0.62, 0.55, 1.7, "TEXT-SPEC", rot=71.6)
    panel.text("1:10", 0.06, 0.55, 1.5, "TEXT-SPEC", rot=84.3)
    panel.caption_below("P.C.C. Return Wall Section", "WEEP HOLES @ 1000 C/C")


# ---------------------------------------------------------------------------


def _toe_wall_section(sh: Sheet, spec: SlabBridgeSpec,
                      rect: tuple[float, float, float, float]) -> None:
    panel = sh.panel(rect, (-0.30, 1.85), (-0.95, 0.95), fit="uniform", pad=1.0)
    pts = [(0.0, 0.45), (0.30, 0.45), (0.55, -0.30), (1.60, -0.30), (1.60, -0.60), (0.0, -0.60)]
    panel.poly(pts, layer="SUB-ABUT", close=True)
    panel.hatch(pts, pattern="ANSI31", scale=4.0, layer="STRUC-HATCHING")
    panel.band(-0.25, 0.45, 1.75, 0.90, pattern="ANSI37", scale=5.0, layer="FOUND-SOIL")
    panel.line(-0.25, 0.45, 1.75, 0.45, layer="CIVIL-GROUND")
    sh.dim_h(panel.X(0.0), panel.X(1.60), panel.Y(-0.60) - 3.0, "1600", off=-3.5, th=1.6)
    sh.dim_v(panel.Y(-0.60), panel.Y(0.45), panel.X(1.85), "1050", off=3.0, th=1.6)
    panel.caption_below("Toe Wall Section", "AT APPROACH EMBANKMENT TOE")


# ---------------------------------------------------------------------------


def generate(spec: SlabBridgeSpec = PMGSY_SLAB,
             output_path: str | Path = "Sheet2_DeckSection.dxf") -> Path:
    sh = Sheet("A3", "PMGSY GAD Sheet 02")
    sh.banner("DECK SECTION, SUB-STRUCTURE DETAILS & GENERAL NOTES  \u2014  "
              f"{spec.spans} SPANS OF {spec.span_m:.1f} m", 279.0)

    # top band: section A-A (left) + schedule + geometry checks (right)
    _deck_section(sh, spec, (12.0, 198.0, 196.0, 268.0))
    sh.text("SCHEDULE OF BRIDGE DATA", 204.0, 264.0, 2.3, "TEXT-HEADER")
    sh.table(204.0, 260.0, (40.0, 44.0), [["PARAMETER", "VALUE"]] + spec.schedule_rows(),
             row_h=3.6, th=1.75)

    # middle band: four details, each with its caption in the gap below
    _soil_profile(sh, spec, (12.0, 128.0, 92.0, 186.0))
    _abutment_section(sh, spec, (98.0, 128.0, 196.0, 186.0))
    _return_wall_section(sh, spec, (202.0, 128.0, 288.0, 186.0))
    _toe_wall_section(sh, spec, (294.0, 128.0, 374.0, 186.0))

    # notes in two columns so the block clears both title block and captions
    all_notes = list(spec.notes)
    split = (len(all_notes) + 1) // 2
    sh.notes(12.0, 112.0, 196.0, all_notes[:split], heading="GENERAL NOTES :-",
             th=TXT_XS, gap=3.2)
    sh.notes(216.0, 112.0, 196.0, all_notes[split:], heading="", th=TXT_XS, gap=3.2,
             start=split + 1)

    # geometry checks, top right
    sh.text("GEOMETRY CHECKS", 296.0, 264.0, 2.3, "TEXT-HEADER")
    checks = [
        ["CHECK", "RESULT"],
        ["FRL \u2212 BL", f"{spec.height_m:.3f} m (source 5.015)"],
        ["FRL \u2212 (75+600)", f"{spec.soffit:.3f} m soffit"],
        ["B1 + 2x700 + B2", f"{spec.b1 + 1.4 + spec.b2:.2f} m"],
        ["DECK \u2212 CW \u2212 2 KERB", f"{spec.deck_width_m - spec.carriageway_m - 2 * spec.kerb_mm / 1000:.3f} m"],
        ["SPAN x N", f"{spec.span_m:.1f} x {spec.spans} = {spec.length_m:.1f} m"],
    ]
    sh.table(296.0, 260.0, (34.0, 42.0), checks, row_h=4.0, th=1.6)

    sh.title_block(
        client=spec.ident.client, consultant=spec.ident.consultant, road=spec.ident.road,
        title="GENERAL ARRANGEMENT DRAWING \u2014 DECK SECTION & SUB-STRUCTURE DETAILS",
        drawing_no=f"{spec.ident.drawing_prefix} / 02", sheet_no="02",
        total_sheets=f"{spec.ident.total_sheets:02d}", scale="NTS",
        date=spec.ident.date, drawn=spec.ident.drawn, designed=spec.ident.designed,
        approved=spec.ident.approved, revision=spec.ident.revision,
    )
    sh.footer("BridgeCAD Enterprise Suite \u2014 asset pack \u2014 sheet 02/03")
    return sh.save(output_path)


__all__ = ["generate"]
