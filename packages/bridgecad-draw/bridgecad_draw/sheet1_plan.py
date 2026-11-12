"""
bridgecad_draw.sheet1_plan — Bridge GAD Sheet 1: Plan View.

Draws (on a single DXF modelspace):
  1. Deck outline (skew-aware, hatched carriageway zone)
  2. Pier cap footprints (one per internal pier)
  3. Abutment footprints (A1 and A2)
  4. Bearing pad symbols (⊕ crosses)
  5. Bridge centreline (CENTER linetype)
  6. Chainage markers along centreline
  7. Span dimension strings
  8. Overall width dimension
  9. North arrow + scale bar
 10. Title block via titleblocks module
 11. Sheet border
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .dxf_engine import new_sheet, save
from .fit import LADDER, MIN_TEXT_MM
from .primitives import (
    chainage_tag,
    circle,
    dim_linear_h,
    dim_linear_v,
    hatch_rect,
    line,
    north_arrow,
    polyline,
    rectangle,
    scale_bar,
    section_arrow,
    text,
)
from .titleblocks import draw_border, draw_title_block

# ---------------------------------------------------------------------------
# Drawing constants (mm in model space)
# ---------------------------------------------------------------------------
_SHEET_W = 841.0  # A1 landscape width  mm
_SHEET_H = 594.0  # A1 landscape height mm
_MARGIN = 10.0  # sheet margin mm
_TB_H = 65.0  # reserve height for title block at bottom (IRC SP:55)
_REV_W = 50.0  # revision strip width mm

# ── Annotation gutters ────────────────────────────────────────────────────
# Every annotation offset below is an ABSOLUTE millimetre gap from the deck
# outline. They used to be written as multiples of the fit-scale (mm per
# metre); at 1:15-ish that threw the north arrow, scale bar, section arrows
# and the Total-L dimension hundreds of millimetres off the A1 frame, where
# they were clipped on plot. Fixed gaps cannot do that.
_ANN_TOP = 46.0  # view label + Total-L dimension + north arrow
_ANN_BOT = 40.0  # span dimension + chainage tags + scale bar
_LAB_W = 22.0  # left gutter for support labels
_RIGHT_W = 22.0  # right gutter for overall-width / kerb staffs

_PLAN_X0 = _MARGIN + _LAB_W
_PLAN_Y0 = _MARGIN + _TB_H + _ANN_BOT
_PLAN_W = _SHEET_W - 2.0 * _MARGIN - _LAB_W - _RIGHT_W
_PLAN_H = _SHEET_H - _MARGIN - _ANN_TOP - _PLAN_Y0

_SCALE_FIT_SHRINK = 0.93  # leaves a little air inside the plan box

# Fixed annotation gaps (mm) measured from the deck edges / centreline.
_OFF_DIM_TOP = 7.0  # "Total L" dimension, above the deck
_OFF_SUB = 18.0  # "(Not to Scale …)" subtitle (lower line)
_OFF_LABEL = 27.0  # "PLAN VIEW" title (upper line)
_OFF_DIM_BOT = 6.0  # span dimensions, below the deck
_OFF_CHAIN = 15.0  # chainage ticks
_OFF_SBAR = 31.0  # scale bar baseline
_OFF_SIDE = 11.0  # side staffs (CW, overall width)
_OFF_KERB = 20.0  # kerb staffs (further out than CW, no overlap)
_OFF_ABUT = 11.0  # abutment-width staff
_OFF_SECTION = 10.0  # section-arrow cut-line overrun
_NARROW_SIZE = 8.0  # north-arrow symbol size (mm)
_SECTION_SIZE = 6.0  # section-arrow symbol size (mm)
_TEXT_MAX = 5.0  # adaptive text cap (mm) — keeps short bridges legible


def generate(
    project: Any,
    output_path: str | Path,
    scale_denom: int | None = None,
) -> Path:
    """Generate Sheet 1 (Plan View) as a DXF file.

    Parameters
    ----------
    project : BridgeProject
        Validated Pydantic model.
    output_path : str | Path
        Where to save the DXF file.
    scale_denom : int | None
        Denominator of drawing scale (100 = 1:100).  ``None`` (default) lets
        the sheet pick the largest rung of the shared scale ladder that fits
        the plan — the denominator printed in the title block is then the one
        the geometry was actually drawn at.

    Returns
    -------
    Path
        Saved DXF file path.
    """
    doc, msp = new_sheet("S1 Plan View")
    _draw_plan(msp, project, scale_denom)
    return save(doc, output_path)


def _draw_plan(msp: Any, project: Any, scale_denom: int | None = None) -> None:
    """Core plan-view drawing logic — operates on msp directly."""
    from bridgecad_core.geometry import compute_plan_geometry

    gi = project.geometry_input
    sub = project.substructure
    pm = project.project_master

    # ── Geometry calculation ─────────────────────────────────────────────
    geom = compute_plan_geometry(project)

    # ── Presence by type (SS3 §A6) ───────────────────────────────────────
    # Sheet 1 drew pier caps and bearing symbols unconditionally. A box cell
    # (004) or a box culvert is monolithic: there is no separate pier cap and
    # no bearing, so both must be gated on the *model*, not the sheet.
    from bridgecad_core import types as T

    _no_pier_ss = (
        T.SuperstructureType.BOX_CULVERT,
        getattr(T.SuperstructureType, "BOX_CELL_MULTI", T.SuperstructureType.BOX_CULVERT),
    )
    has_piers = project.superstructure.type not in _no_pier_ss
    # A bearingless structure carries no bearing symbol. The model encodes
    # "no bearing" as an unset ``bearing_type`` (``BearingType | None``) — there
    # is no ``NONE`` member — so a ``None`` here means no symbols.
    _brg_type = getattr(project.bearings_joints, "bearing_type", None)
    bearings = geom.bearing_positions if _brg_type is not None else []

    total_len = float(gi.total_length_m)  # m
    overall_w = float(gi.overall_width_m)  # m
    cw = float(gi.carriageway_width_m)  # m
    span_lens = [float(s) for s in gi.span_lengths_m]
    pier_cap_w = float(sub.pier_cap_width_m or 2.0)  # m
    pier_cap_l = float(sub.pier_cap_length_m or overall_w * 1.1)  # m
    abt_w = float(sub.abutment_width_m or 1.2)  # m
    abt_l = float(sub.abutment_length_m or overall_w * 1.1)  # m
    kerb_l = float(gi.kerb_width_left_m or 0.25)  # m
    kerb_r = float(gi.kerb_width_right_m or 0.25)  # m
    skew_deg = float(gi.skew_angle_deg or 0.0)

    # ── Scale: model-space mm per metre ──────────────────────────────────
    # Fit the bridge (total_len × overall_w) into the plan area. The horizontal
    # budget must span the END FOOTPRINTS too: the A1 abutment is dimensioned
    # from `hpos(0) - abt_w·scale` to `hpos(0)`, so fitting only [0, total_len]
    # let the A1 width dimension plot off the left edge on a short, wide-footprint
    # bridge (a 24 m arch ran 16 mm past x = 0).
    x_lo = -abt_w
    x_hi = total_len + abt_w
    x_span = max(x_hi - x_lo, 0.1)

    # The plan is drawn at a *standard* scale — a rung of the shared ladder —
    # and the title block prints that rung. It used to fit itself to the box
    # with an invented denominator (`min(scale_h, scale_v) * 0.93`) and then
    # claim "1:100": a 24 m arch came out at about 1:15 under a "1:100" title.
    if scale_denom is not None:
        denom = scale_denom
    else:
        denom = next(
            (
                d
                for d in LADDER
                if x_span * (1000.0 / d) <= _PLAN_W * _SCALE_FIT_SHRINK
                and overall_w * (1000.0 / d) <= _PLAN_H * _SCALE_FIT_SHRINK
            ),
            None,
        )
    if denom is None:
        # Longer than the coarsest rung can carry in one view. A broken strip
        # layout is the real answer; until that exists the plan is fit to the
        # box and the *fitted* denominator is printed, so the caption still
        # agrees with the geometry.
        scale = min(_PLAN_W / x_span, _PLAN_H / max(overall_w, 0.1)) * _SCALE_FIT_SHRINK
        denom = max(1, round(1000.0 / scale))
    else:
        scale = 1000.0 / denom

    # Coordinate mapper: x=chainage, y=transverse (offset from CL)
    cx_offset = _PLAN_X0 + (_PLAN_W - x_span * scale) / 2.0 - x_lo * scale
    cy_offset = _PLAN_Y0 + (_PLAN_H - overall_w * scale) / 2.0

    def hpos(ch: float) -> float:  # chainage → mm X on sheet
        return cx_offset + ch * scale

    def vpos(y_m: float) -> float:  # transverse offset → mm Y on sheet
        return cy_offset + (y_m + overall_w / 2.0) * scale

    half_w = overall_w / 2.0
    half_cw = cw / 2.0

    # ── Sheet border & title block ────────────────────────────────────────
    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-001") or "GAD-001",
        drawing_title="GENERAL ARRANGEMENT — PLAN VIEW",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        date_str=str(getattr(pm, "date_issued", "") or ""),
        designed_by=getattr(pm, "designed_by", "") or "",
        checked_by=getattr(pm, "checked_by", "") or "",
        approved_by=getattr(pm, "approved_by", "") or "",
        client=getattr(getattr(pm, "client", None), "name", "") or "",
        consultant=getattr(getattr(pm, "consultant", None), "name", "") or "",
        scale_str=f"1:{denom}",
        sheet_no="1",
        total_sheets="9",
    )

    text_h = min(_TEXT_MAX, max(MIN_TEXT_MM, scale * 0.5))  # adaptive text height mm (capped)

    # ── Centreline ───────────────────────────────────────────────────────
    cl_y = vpos(0.0)
    line(msp, (hpos(0), cl_y), (hpos(total_len), cl_y), layer="STRUC-CENTRE")

    # ── Deck outline ──────────────────────────────────────────────────────
    # The plan is drawn SHEARED: chainage runs along x and any point at
    # transverse offset `off` is shifted by `-off * scale * sin(theta)`.
    # `sin_t` / `cos_t` are shared by the skew tick and the bearing symbols so
    # everything uses this one mapping.
    skew_rad = math.radians(skew_deg)
    cos_t = math.cos(skew_rad)
    sin_t = math.sin(skew_rad)
    deck_pts = [
        (hpos(0) + half_w * scale * sin_t, vpos(-half_w)),
        (hpos(0) - half_w * scale * sin_t, vpos(half_w)),
        (hpos(total_len) - half_w * scale * sin_t, vpos(half_w)),
        (hpos(total_len) + half_w * scale * sin_t, vpos(-half_w)),
    ]
    # Fall back to simple rect when skew ≈ 0
    if abs(skew_deg) < 0.5:
        deck_pts = [
            (hpos(0), vpos(-half_w)),
            (hpos(0), vpos(half_w)),
            (hpos(total_len), vpos(half_w)),
            (hpos(total_len), vpos(-half_w)),
        ]
    polyline(msp, deck_pts, layer="STRUC-OUTLINE", close=True, lw=50)
    # Audit-required SUPER-DECK layer tag (IRC standard domain layer for deck plan outline)
    polyline(msp, deck_pts, layer="SUPER-DECK", close=True, lw=30)

    # Carriageway zone hatch (light)
    if abs(skew_deg) < 0.5:
        hatch_rect(
            msp,
            hpos(0),
            vpos(-half_cw),
            total_len * scale,
            cw * scale,
            pattern="ANSI31",
            scale=scale * 0.08,
            layer="STRUC-HATCHING",
            color=8,
        )

    # ── Abutments ─────────────────────────────────────────────────────────
    for ch, label in [(0.0, "A1"), (total_len, "A2")]:
        ax = hpos(ch) - abt_w * scale / 2.0
        ay = vpos(-abt_l / 2.0)
        aw = abt_w * scale
        ah = abt_l * scale
        rectangle(msp, ax, ay, aw, ah, layer="SUB-ABUT", lw=40)
        hatch_rect(
            msp, ax, ay, aw, ah, pattern="ANSI31", scale=scale * 0.05, layer="SUB-ABUT", color=3
        )
        # Dirt wall footprint on the outboard (fill) face of the abutment
        dirt_t_plan = float(getattr(sub, "dirt_wall_thickness_mm", None) or 300) / 1000.0
        dw_plan_x = ax - dirt_t_plan * scale if label == "A1" else ax + aw
        rectangle(msp, dw_plan_x, ay, dirt_t_plan * scale, ah, layer="SUB-DIRT-WALL", lw=35)
        text(
            msp,
            "DW",
            dw_plan_x + dirt_t_plan * scale / 2.0,
            ay - text_h * 1.4,
            height=text_h * 0.8,
            layer="TEXT-SPEC",
            halign="CENTER",
        )
        text(msp, label, ax - text_h * 4, vpos(0), height=text_h * 1.2, layer="TEXT-GENERAL")

    # ── Piers ─────────────────────────────────────────────────────────────
    # Presence gate (SS3 §A6): a box cell / box culvert has no separate pier
    # cap, so there is nothing to draw here for those families.
    cumul = 0.0
    for i, slen in enumerate(span_lens[:-1]):
        cumul += slen
        if not has_piers:
            continue
        px = hpos(cumul) - pier_cap_w * scale / 2.0
        py = vpos(-pier_cap_l / 2.0)
        pw = pier_cap_w * scale
        ph = pier_cap_l * scale
        rectangle(msp, px, py, pw, ph, layer="SUB-PIER", lw=40)
        hatch_rect(
            msp, px, py, pw, ph, pattern="ANSI31", scale=scale * 0.05, layer="SUB-PIER", color=2
        )
        # FR-3: Pier labels on NORTHERN deck edge (north = y = vpos(+half_w), label
        # plus tidy offset).  Old code placed them on south vpos(-half_w) below.
        text(
            msp,
            f"P{i+1}",
            hpos(cumul) - text_h * 1.5,
            vpos(half_w) + text_h * 1.2,  # NORTH edge + spacing
            height=text_h,
            layer="TEXT-GENERAL",
        )

    # ── Skew annotation (guide #4): angle at CL of each support ────────────
    if abs(skew_deg) >= 0.5:
        skew_dir = getattr(gi, "skew_direction", None)
        dir_name = getattr(skew_dir, "name", str(skew_dir or ""))
        skew_note = f"SKEW = {skew_deg:.1f}° {dir_name}".strip()
        # Support line angle tick at A1 chainage.  `support_line` returns its
        # points in the ROTATED model frame, so mapping them straight through
        # the sheared hpos/vpos inverted the tick slope (it ran diagonally
        # across the deck).  Rebuild the A1 support line in the local
        # (chainage, offset) frame and map it with the same shear as the deck.
        from bridgecad_core.skew import support_line

        sl = support_line(project, 0.0)
        _c0 = float(sl.chainage_m)
        line(
            msp,
            (hpos(_c0) - half_w * scale * sin_t, vpos(half_w)),
            (hpos(_c0) + half_w * scale * sin_t, vpos(-half_w)),
            layer="MISC-SETOUT",
            color=1,
        )
        text(
            msp,
            skew_note,
            hpos(0.0),
            vpos(-half_w) - text_h * 3.5,
            height=text_h * 1.1,
            layer="TEXT-HEADER",
            color=1,
        )

    # ── Bearing symbols (cross marks) ─────────────────────────────────────
    # `compute_plan_geometry` rotates the whole bridge clockwise about the A1
    # centre, so an A2 bearing arrives as (x', y') with y' ≈ -total_len·sinθ
    # (-8.6 m on a 30° skew).  The plan here is drawn SHEARED, so the rotated
    # point must be un-rotated back to the local (chainage, offset) frame and
    # then sheared like the deck outline — otherwise the A2 bearings land well
    # clear of the deck and run off the sheet.
    for bx, by in bearings:
        lx = bx * cos_t - by * sin_t  # chainage (local)
        ly = bx * sin_t + by * cos_t  # transverse offset (local)
        sx = hpos(lx) - ly * scale * sin_t
        sy = vpos(ly)
        r = scale * 0.3
        line(msp, (sx - r, sy), (sx + r, sy), layer="SUB-BEARING")
        line(msp, (sx, sy - r), (sx, sy + r), layer="SUB-BEARING")
        circle(msp, sx, sy, r, layer="SUB-BEARING")

    # ── Span dimensions ───────────────────────────────────────────────────
    dim_y = vpos(-half_w) - _OFF_DIM_BOT
    cumul = 0.0
    for slen in span_lens:
        x1 = hpos(cumul)
        x2 = hpos(cumul + slen)
        dim_linear_h(
            msp,
            x1,
            vpos(-half_w),
            x2,
            vpos(-half_w),
            dim_y=dim_y,
            label=f"{slen:.3f} m",
            text_height=text_h * 0.9,
        )
        cumul += slen

    # Overall width dimension (right side)
    dim_x = hpos(total_len) + _OFF_SIDE
    dim_linear_v(
        msp,
        hpos(total_len),
        vpos(-half_w),
        hpos(total_len),
        vpos(half_w),
        dim_x=dim_x,
        label=f"OW={overall_w:.3f} m",
        text_height=text_h * 0.9,
    )

    # Overall length dimension (above deck)
    dim_linear_h(
        msp,
        hpos(0),
        vpos(half_w),
        hpos(total_len),
        vpos(half_w),
        dim_y=vpos(half_w) + _OFF_DIM_TOP,
        label=f"Total L = {total_len:.3f} m",
        text_height=text_h,
    )

    # ── Principal plan dimensions (IRC SP:55 §4) ──────────────────────────
    # Carriageway width — transverse, measured across the deck at mid-span.
    dim_linear_v(
        msp,
        hpos(total_len * 0.5),
        vpos(-half_cw),
        hpos(total_len * 0.5),
        vpos(half_cw),
        dim_x=hpos(total_len * 0.5) - _OFF_SIDE,
        label=f"CW={cw:.3f} m",
        text_height=text_h * 0.9,
    )
    # Abutment widths — longitudinal extent of each end footprint.
    for ch, tag in ((0.0, "A1"), (total_len, "A2")):
        dim_linear_h(
            msp,
            hpos(ch) - abt_w * scale,
            vpos(0.0),
            hpos(ch),
            vpos(0.0),
            dim_y=vpos(0.0) - _OFF_ABUT,
            label=f"{tag} W={abt_w:.3f} m",
            text_height=text_h * 0.8,
        )
    # Kerb widths (left / right) — transverse staff at mid-span.
    for side, kw, tag in ((-1, kerb_l, "L"), (+1, kerb_r, "R")):
        dim_linear_v(
            msp,
            hpos(total_len * 0.5),
            vpos(side * half_cw),
            hpos(total_len * 0.5),
            vpos(side * (half_cw + kw)),
            dim_x=hpos(total_len * 0.5) + side * _OFF_KERB,
            label=f"KERB{tag}={kw:.2f} m",
            text_height=text_h * 0.75,
        )

    # ── Chainage markers ──────────────────────────────────────────────────
    ch_start = float(gi.chainage_start_km or 0) * 1000.0  # → m absolute
    cumul = 0.0
    for i, slen in enumerate(span_lens):
        chainage_tag(
            msp,
            hpos(cumul),
            vpos(-half_w) - _OFF_CHAIN,
            (ch_start + cumul) / 1000.0,
            text_height=text_h * 0.85,
        )
        cumul += slen
    chainage_tag(
        msp,
        hpos(total_len),
        vpos(-half_w) - _OFF_CHAIN,
        (ch_start + total_len) / 1000.0,
        text_height=text_h * 0.85,
    )

    # ── North arrow ───────────────────────────────────────────────────────
    # Anchored in the top-left gutter at a fixed symbol size: it used to be
    # ``vpos(half_w) + scale*5.0`` with ``size=scale*1.5``, which for a short
    # bridge (large fit-scale) pushed it hundreds of mm above the A1 frame.
    na_x = _PLAN_X0 + 12.0
    na_y = vpos(half_w) + _OFF_LABEL
    north_arrow(msp, na_x, na_y, size=_NARROW_SIZE)

    # ── Scale bar ─────────────────────────────────────────────────────────
    # Labelled with the same denominator as the title block, so the two cannot
    # disagree. (The bar's tick *lengths* are the primitive's own nominal ones
    # — 1 unit per metre — which is a separate primitive-level defect.)
    sb_x = hpos(total_len * 0.5) - 40.0
    sb_y = vpos(-half_w) - _OFF_SBAR
    scale_bar(
        msp,
        sb_x,
        sb_y,
        denom,
        segments=4,
        seg_len_m=min(25.0, max(1.0, round(total_len / 5))),
        text_height=text_h * 0.85,
    )

    # ── View label ────────────────────────────────────────────────────────
    text(
        msp,
        "PLAN VIEW",
        hpos(total_len / 2),
        vpos(half_w) + _OFF_LABEL,
        height=text_h * 1.4,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    text(
        msp,
        f"SCALE 1:{denom} — ALL DIMENSIONS IN METRES",
        hpos(total_len / 2),
        vpos(half_w) + _OFF_SUB,
        height=text_h * 0.9 * 0.9,
        layer="TEXT-SPEC",
        halign="CENTER",
        color=8,
    )  # FR-8: demoted 10% smaller + grey colour (8)

    # ── Section-cut markers for Sheet 8 views (FR-5) ─────────────────────
    # A-A cut line: just upstream of A1 abutment (Sheet 8 View 1 = abutment A2
    # end-face; we keep A-A on A1-side for conventional section labelling).
    aa_x = hpos(0.0)
    aa_y1 = vpos(-half_w) - _OFF_SECTION
    aa_y2 = vpos(+half_w) + _OFF_SECTION
    section_arrow(
        msp, aa_x, aa_y2, aa_y1, label="A-A", size=_SECTION_SIZE, text_height=text_h * 0.95
    )

    # B-B cut line: at first internal pier chainage (or 1 m past A1 if no pier,
    # i.e. span_count == 1) — matches Sheet 8 View 2 pier transverse / fallback.
    # A box cell / culvert has no pier to cut through, so B-B is not shown and
    # the sheet says why (SS3 §A6) instead of drawing a section that does not
    # exist.
    if has_piers:
        bb_ch: float = pier_ch[0] if (pier_ch := geom.pier_centrelines) else 1.0
        if isinstance(bb_ch, tuple):
            bb_ch = float(bb_ch[0])
        bb_x = hpos(bb_ch)
        bb_y1 = vpos(-half_w) - _OFF_SECTION
        bb_y2 = vpos(+half_w) + _OFF_SECTION
        section_arrow(
            msp, bb_x, bb_y2, bb_y1, label="B-B", size=_SECTION_SIZE, text_height=text_h * 0.95
        )
    else:
        text(
            msp,
            "SECTION B-B NOT APPLICABLE (NO PIER)",
            hpos(total_len / 2),
            vpos(-half_w) - _OFF_SECTION - text_h * 1.5,
            height=text_h * 0.9,
            layer="TEXT-SPEC",
            halign="CENTER",
            color=8,
        )


__all__ = ["generate"]
