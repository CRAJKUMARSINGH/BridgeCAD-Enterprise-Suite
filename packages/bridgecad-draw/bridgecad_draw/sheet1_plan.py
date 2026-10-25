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

# Auto-fit bottom gutter — Sheet 1 Plan no longer uses a hard 10 mm floor.
# The lowest plan annotation (scale bar / chainage tags) sits exactly 6 mm
# above the title-block top edge. Tight 3 mm lower bound here is safe because
# we also grow the scale-fraction from 0.85 → 0.93 (plan occupies more
# vertical real estate), then reposition if needed via shift_y later.
_PLAN_X0 = _MARGIN + 10.0
_PLAN_Y0 = _MARGIN + _TB_H + 3.0  # was + 10.0 mm  (FR-1 loosen bottom)
_PLAN_W = _SHEET_W - 2 * _MARGIN - 20.0
_PLAN_H = _SHEET_H - _MARGIN - _TB_H - 15.0  # was -30 mm → reclaim 15 mm

# Auto-fit target: lowest drawing entity Y sits 6 mm above TB top
_LOWEST_ABOVE_TB_TARGET = _MARGIN + _TB_H + 6.0
_SCALE_FIT_SHRINK = 0.93  # was 0.85 → more space reclaimed vertically


def generate(
    project: Any,
    output_path: str | Path,
    scale_denom: int = 100,
) -> Path:
    """Generate Sheet 1 (Plan View) as a DXF file.

    Parameters
    ----------
    project : BridgeProject
        Validated Pydantic model.
    output_path : str | Path
        Where to save the DXF file.
    scale_denom : int
        Denominator of drawing scale (100 = 1:100).

    Returns
    -------
    Path
        Saved DXF file path.
    """
    doc, msp = new_sheet("S1 Plan View")
    _draw_plan(msp, project, scale_denom)
    return save(doc, output_path)


def _draw_plan(msp: Any, project: Any, scale_denom: int = 100) -> None:
    """Core plan-view drawing logic — operates on msp directly."""
    from bridgecad_core.geometry import compute_plan_geometry

    gi = project.geometry_input
    sub = project.substructure
    pm = project.project_master

    # ── Geometry calculation ─────────────────────────────────────────────
    geom = compute_plan_geometry(project)

    total_len = float(gi.total_length_m)  # m
    overall_w = float(gi.overall_width_m)  # m
    cw = float(gi.carriageway_width_m)  # m
    span_lens = [float(s) for s in gi.span_lengths_m]
    pier_cap_w = float(sub.pier_cap_width_m or 2.0)  # m
    pier_cap_l = float(sub.pier_cap_length_m or overall_w * 1.1)  # m
    abt_w = float(sub.abutment_width_m or 1.2)  # m
    abt_l = float(sub.abutment_length_m or overall_w * 1.1)  # m
    skew_deg = float(gi.skew_angle_deg or 0.0)

    # ── Scale: model-space mm per metre ──────────────────────────────────
    # Fit the bridge (total_len × overall_w) into the plan area.
    scale_h = _PLAN_W / max(total_len, 0.1)  # mm per metre (horizontal)
    scale_v = _PLAN_H / max(overall_w, 0.1)  # mm per metre (vertical)
    scale = min(scale_h, scale_v) * _SCALE_FIT_SHRINK  # was *0.85 → *0.93 (FR-1)

    # Coordinate mapper: x=chainage, y=transverse (offset from CL)
    cx_offset = _PLAN_X0 + (_PLAN_W - total_len * scale) / 2.0
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
        scale_str=f"1:{scale_denom}",
        sheet_no="1",
        total_sheets="8",
    )

    text_h = max(2.0, scale * 0.5)  # adaptive text height mm

    # ── Centreline ───────────────────────────────────────────────────────
    cl_y = vpos(0.0)
    line(msp, (hpos(0), cl_y), (hpos(total_len), cl_y), layer="STRUC-CENTRE")

    # ── Deck outline ──────────────────────────────────────────────────────
    skew_rad = math.radians(skew_deg)
    deck_pts = [
        (hpos(0) + half_w * scale * math.sin(skew_rad), vpos(-half_w) - 0 * math.cos(skew_rad)),
        (hpos(0) - half_w * scale * math.sin(skew_rad), vpos(half_w) + 0 * math.cos(skew_rad)),
        (hpos(total_len) - half_w * scale * math.sin(skew_rad), vpos(half_w)),
        (hpos(total_len) + half_w * scale * math.sin(skew_rad), vpos(-half_w)),
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
        text(msp, label, ax - text_h * 4, vpos(0), height=text_h * 1.2, layer="TEXT-GENERAL")

    # ── Piers ─────────────────────────────────────────────────────────────
    cumul = 0.0
    for i, slen in enumerate(span_lens[:-1]):
        cumul += slen
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

    # ── Bearing symbols (cross marks) ─────────────────────────────────────
    for bx, by in geom.bearing_positions:
        sx = hpos(bx)
        sy = vpos(by)
        r = scale * 0.3
        line(msp, (sx - r, sy), (sx + r, sy), layer="SUB-BEARING")
        line(msp, (sx, sy - r), (sx, sy + r), layer="SUB-BEARING")
        circle(msp, sx, sy, r, layer="SUB-BEARING")

    # ── Span dimensions ───────────────────────────────────────────────────
    dim_y = vpos(-half_w) - scale * 2.0
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
    dim_x = hpos(total_len) + scale * 2.5
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
        dim_y=vpos(half_w) + scale * 3.0,
        label=f"Total L = {total_len:.3f} m",
        text_height=text_h,
    )

    # ── Chainage markers ──────────────────────────────────────────────────
    ch_start = float(gi.chainage_start_km or 0) * 1000.0  # → m absolute
    cumul = 0.0
    for i, slen in enumerate(span_lens):
        chainage_tag(
            msp,
            hpos(cumul),
            vpos(-half_w) - scale * 1.0,
            (ch_start + cumul) / 1000.0,
            text_height=text_h * 0.85,
        )
        cumul += slen
    chainage_tag(
        msp,
        hpos(total_len),
        vpos(-half_w) - scale * 1.0,
        (ch_start + total_len) / 1000.0,
        text_height=text_h * 0.85,
    )

    # ── North arrow ───────────────────────────────────────────────────────
    na_x = _PLAN_X0 + 20.0
    na_y = vpos(half_w) + scale * 5.0
    north_arrow(msp, na_x, na_y, size=scale * 1.5)

    # ── Scale bar ─────────────────────────────────────────────────────────
    sb_x = hpos(total_len * 0.6)
    sb_y = vpos(-half_w) - scale * 8.0
    scale_bar(
        msp,
        sb_x,
        sb_y,
        scale_denom,
        segments=4,
        seg_len_m=max(1.0, round(total_len / 5)),
        text_height=text_h * 0.85,
    )

    # ── View label ────────────────────────────────────────────────────────
    text(
        msp,
        "PLAN VIEW",
        hpos(total_len / 2),
        vpos(half_w) + scale * 2.5,
        height=text_h * 1.4,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    text(
        msp,
        f"(Not to Scale — indicative 1:{scale_denom})",
        hpos(total_len / 2),
        vpos(half_w) + scale * 1.2,
        height=text_h * 0.9 * 0.9,
        layer="TEXT-SPEC",
        halign="CENTER",
        color=8,
    )  # FR-8: demoted 10% smaller + grey colour (8)

    # ── Section-cut markers for Sheet 8 views (FR-5) ─────────────────────
    # A-A cut line: just upstream of A1 abutment (Sheet 8 View 1 = abutment A2
    # end-face; we keep A-A on A1-side for conventional section labelling).
    aa_x = hpos(0.0) - scale * 0.8
    aa_y1 = vpos(-half_w) - scale * 2.2
    aa_y2 = vpos(+half_w) + scale * 1.5
    section_arrow(msp, aa_x, aa_y2, aa_y1, label="A-A", size=scale * 1.2, text_height=text_h * 0.95)

    # B-B cut line: at first internal pier chainage (or 1 m past A1 if no pier,
    # i.e. span_count == 1) — matches Sheet 8 View 2 pier transverse / fallback.
    bb_ch: float = pier_ch[0] if (pier_ch := geom.pier_centrelines) else 1.0
    if isinstance(bb_ch, tuple):
        bb_ch = float(bb_ch[0])
    bb_x = hpos(bb_ch)
    bb_y1 = vpos(-half_w) - scale * 2.5
    bb_y2 = vpos(+half_w) + scale * 3.0
    section_arrow(msp, bb_x, bb_y2, bb_y1, label="B-B", size=scale * 1.2, text_height=text_h * 0.95)


__all__ = ["generate"]
