"""
bridgecad_draw.sheet2_long_section — Bridge GAD Sheet 2: Longitudinal Section.

Draws:
  1. Ground profile polyline (green, from geometry module)
  2. HFL, LWL, Scour level horizontal datum lines
  3. Deck top and soffit lines
  4. Pier shafts (elevation)
  5. Abutment front faces
  6. Pile tips (vertical lines below pile cap)
  7. Level tags for HFL, LWL, Scour, Soffit, Top-of-deck, Pile tip
  8. Span labels and dimension strings
  9. Pier / abutment labels
 10. Section hatching (deck slab, piers, foundations)
 11. Chainage axis at bottom
 12. Title block + border (Sheet 2 of 7)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .dxf_engine import CoordMapper, new_sheet, save
from .primitives import (
    chainage_tag,
    circle,
    dim_linear_v,
    hatch_poly,
    hatch_rect,
    level_tag,
    line,
    polyline,
    rectangle,
    text,
)
from .titleblocks import draw_border, draw_title_block

# ---------------------------------------------------------------------------
# Layout constants (A1 landscape, mm)
# ---------------------------------------------------------------------------
_SHEET_W = 841.0
_SHEET_H = 594.0
_MARGIN = 10.0
_TB_H = 65.0  # title block height at bottom
_LEVEL_AXIS_W = 30.0  # width of level axis on left
_CHAINAGE_H = 20.0  # height of chainage axis at bottom of drawing


def _chainage_pitch(total_m: float) -> float:
    """Uniform chainage interval for the axis ticks — the LISP `xincr`.

    Keeps roughly 6–12 ticks across the bridge so the axis grid stays legible
    at 1:100 without the labels colliding.
    """
    for pitch in (1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 50.0, 100.0):
        if total_m / pitch <= 12:
            return pitch
    return 200.0


def generate(
    project: Any,
    output_path: str | Path,
    scale_denom: int = 100,
    v_exag: float = 2.0,
) -> Path:
    """Generate Sheet 2 (Longitudinal Section) as a DXF file.

    Parameters
    ----------
    project : BridgeProject
    output_path : str | Path
    scale_denom : int
        Horizontal scale denominator (e.g. 100 for 1:100).
    v_exag : float
        Vertical exaggeration multiplier (default 2.0 for readability).

    Returns
    -------
    Path
    """
    doc, msp = new_sheet("S2 Long Section")
    _draw_long_section(msp, project, scale_denom, v_exag)
    return save(doc, output_path)


def _draw_long_section(msp: Any, project: Any, scale_denom: int = 100, v_exag: float = 2.0) -> None:
    from bridgecad_core.geometry import compute_long_section_geometry

    gi = project.geometry_input
    sub = project.substructure
    fd = project.foundation_details
    pm = project.project_master

    # ── Geometry ──────────────────────────────────────────────────────────
    ls = compute_long_section_geometry(project)

    total_len = float(gi.total_length_m)
    span_lens = [float(s) for s in gi.span_lengths_m]
    # Skew: effective span = clear span × cos(skew) per IRC reduction; the
    # geometric span stays primary and the effective value is annotated.
    _skew_deg = float(gi.skew_angle_deg or 0.0)
    import math as _math

    _skew_cos = _math.cos(_math.radians(_skew_deg)) if _skew_deg else 1.0

    def _span_label(i: int, slen: float) -> str:
        if _skew_deg < 0.5:
            return f"{slen:.1f} m"
        return f"{slen:.1f} m (eff {slen * _skew_cos:.1f})"

    hfl_rl = ls.hfl_rl
    lwl_rl = ls.lwl_rl
    scour_rl = ls.scour_level_rl
    soffit_rl = ls.soffit_rl
    top_rl = ls.top_of_deck_rl
    pile_tip_rl = ls.pile_tip_rl

    datum_rl = min(pile_tip_rl, scour_rl) - 2.0  # baseline datum
    rl_range = max(top_rl + 2.0, hfl_rl + 3.0) - datum_rl

    # ── Drawing area ───────────────────────────────────────────────────────
    draw_x0 = _MARGIN + _LEVEL_AXIS_W + 5.0
    draw_y0 = _MARGIN + _TB_H + _CHAINAGE_H + 3.0  # FR-2: was +10.0, now 3 mm gutter
    draw_w = _SHEET_W - draw_x0 - _MARGIN - 10.0
    draw_h = _SHEET_H - draw_y0 - _MARGIN - 13.0  # FR-2: reclaim ~7 mm previously wasted

    # Scale factors (mm per metre)
    sc_h = draw_w / max(total_len, 0.1)  # horizontal
    sc_v = draw_h / max(rl_range, 0.1) / v_exag  # vertical (exaggerated)

    CoordMapper(
        datum_rl=datum_rl,
        origin_ch=0.0,
        h_scale=sc_h / 1000.0,  # CoordMapper expects h_scale in m→unit
        v_scale=sc_v / 1000.0 * v_exag,
        x_offset=draw_x0,
        y_offset=draw_y0,
    )

    def hx(ch):
        return draw_x0 + ch * sc_h

    def vy(rl):
        return draw_y0 + (rl - datum_rl) * sc_v * v_exag

    # ── Border & title block ───────────────────────────────────────────────
    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-002") or "GAD-002",
        drawing_title="GENERAL ARRANGEMENT — LONGITUDINAL SECTION",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        date_str=str(getattr(pm, "date_issued", "") or ""),
        designed_by=getattr(pm, "designed_by", "") or "",
        checked_by=getattr(pm, "checked_by", "") or "",
        approved_by=getattr(pm, "approved_by", "") or "",
        client=getattr(getattr(pm, "client", None), "name", "") or "",
        consultant=getattr(getattr(pm, "consultant", None), "name", "") or "",
        scale_str=f"1:{scale_denom} H  1:{int(scale_denom/v_exag)} V",
        sheet_no="2",
        total_sheets="8",
    )

    th = max(2.5, sc_h * 0.4)  # adaptive text height mm

    # ── Datum / chainage axis (LISP `layout()`: axis → ticks → axis title) ─
    line(msp, (draw_x0, draw_y0), (hx(total_len), draw_y0), layer="CIVIL-CHAINAGE")
    # Axis title, drawn once at the right-hand end of the chainage axis.
    text(
        msp,
        "CHAINAGE",
        hx(total_len) + th * 2.0,
        draw_y0 - th * 0.4,
        height=th * 0.9,
        layer="TEXT-LEVEL",
    )
    # xincr pitch — uniform ticks + chainage text at a constant interval.
    ch_pitch = _chainage_pitch(total_len)
    ch_mark = 0.0
    while ch_mark <= total_len + 1e-6:
        xt = hx(ch_mark)
        line(msp, (xt, draw_y0), (xt, draw_y0 - th * 1.0), layer="CIVIL-CHAINAGE")
        text(
            msp,
            f"{ch_mark:.0f}",
            xt,
            draw_y0 - th * 2.6,
            height=th * 0.7,
            layer="TEXT-LEVEL",
            halign="CENTER",
        )
        ch_mark += ch_pitch
    # Chainage markers every span
    cumul = 0.0
    for slen in span_lens:
        chainage_tag(
            msp,
            hx(cumul),
            draw_y0 - 2.0,
            (float(gi.chainage_start_km or 0) * 1000 + cumul) / 1000.0,
            text_height=th * 0.8,
        )
        cumul += slen
    chainage_tag(
        msp,
        hx(total_len),
        draw_y0 - 2.0,
        (float(gi.chainage_start_km or 0) * 1000 + total_len) / 1000.0,
        text_height=th * 0.8,
    )

    # ── Level axis (left side) ─────────────────────────────────────────────
    line(msp, (draw_x0, draw_y0), (draw_x0, vy(top_rl + 2.0)), layer="DIM-LEVEL")

    # Level scale graduations every 1m RL
    rl_step = 1.0
    rl_bot = max(pile_tip_rl - 1.0, datum_rl)
    rl_top = top_rl + 2.5
    rl_val = math.floor(rl_bot)
    while rl_val <= rl_top:
        yy = vy(rl_val)
        tick_len = th * 3 if rl_val % 5 == 0 else th * 1.5
        line(msp, (draw_x0 - tick_len, yy), (draw_x0, yy), layer="DIM-LEVEL")
        if rl_val % 2 == 0:
            text(
                msp,
                f"{rl_val:.0f}",
                draw_x0 - th * 8,
                yy - th * 0.5,
                height=th * 0.8,
                layer="TEXT-LEVEL",
            )
        rl_val += rl_step

    # Axis title along the level axis (LISP `layout()` label "BED LEVEL").
    text(
        msp,
        "BED LEVEL",
        draw_x0 - th * 8.0,
        vy(rl_top) + th * 1.0,
        height=th * 0.9,
        layer="TEXT-LEVEL",
        rotation=90,
    )

    # ── Ground profile (LISP `cs()` — polyline through the survey points) ──
    gnd_pts = [(hx(ch), vy(rl)) for ch, rl in ls.ground_profile_pts]
    if len(gnd_pts) >= 2:
        polyline(msp, gnd_pts, layer="CIVIL-GROUND", color=3)
        text(
            msp,
            "EXISTING GROUND LEVEL",
            gnd_pts[-1][0] + sc_h * 0.5,
            gnd_pts[-1][1],
            height=th * 0.85,
            layer="CIVIL-GROUND",
            color=3,
        )
    # LISP `cs()` per-point treatment: small tick at the point, drop line from
    # the point down to the datum axis, and the RL printed at every point.
    for ch_pt, rl_pt in ls.ground_profile_pts:
        gx, gy = hx(ch_pt), vy(rl_pt)
        line(msp, (gx, gy), (gx, draw_y0), layer="CIVIL-GROUND", color=8, linetype="DASHED2")
        line(msp, (gx - th * 0.5, gy), (gx + th * 0.5, gy), layer="CIVIL-GROUND", color=3)
        text(
            msp,
            f"{rl_pt:.3f}",
            gx,
            gy - th * 0.9,
            height=th * 0.55,
            layer="TEXT-LEVEL",
            halign="CENTER",
            color=8,
        )

    # ── HFL line ──────────────────────────────────────────────────────────
    hfl_y_mm = vy(hfl_rl)
    line(msp, (draw_x0, hfl_y_mm), (hx(total_len), hfl_y_mm), layer="CIVIL-HFL", color=5)
    level_tag(msp, draw_x0 - 2.0, hfl_y_mm, hfl_rl, text_height=th * 0.85, layer="CIVIL-HFL")
    text(
        msp,
        "HFL",
        hx(total_len) + sc_h * 0.3,
        hfl_y_mm,
        height=th * 0.85,
        layer="CIVIL-HFL",
        color=5,
    )

    # ── LWL line ──────────────────────────────────────────────────────────
    lwl_y_mm = vy(lwl_rl)
    line(msp, (draw_x0, lwl_y_mm), (hx(total_len), lwl_y_mm), layer="CIVIL-LWL", color=4)
    level_tag(msp, draw_x0 - 2.0, lwl_y_mm, lwl_rl, text_height=th * 0.85, layer="CIVIL-LWL")
    text(
        msp,
        "LWL",
        hx(total_len) + sc_h * 0.3,
        lwl_y_mm,
        height=th * 0.85,
        layer="CIVIL-LWL",
        color=4,
    )

    # ── Scour level ───────────────────────────────────────────────────────
    scour_y_mm = vy(scour_rl)
    line(msp, (draw_x0, scour_y_mm), (hx(total_len), scour_y_mm), layer="CIVIL-SCOUR", color=1)
    level_tag(msp, draw_x0 - 2.0, scour_y_mm, scour_rl, text_height=th * 0.85, layer="CIVIL-SCOUR")
    text(
        msp,
        "DESIGN SCOUR LEVEL",
        hx(total_len) + sc_h * 0.3,
        scour_y_mm,
        height=th * 0.85,
        layer="CIVIL-SCOUR",
        color=1,
    )

    # ── Deck profile: slab + continuous wearing coat (guide #1 step 3) ────
    from bridgecad_core.abutment_stack import resolve_abutment_stack

    stack = resolve_abutment_stack(project)
    app_l = float(sub.approach_slab_length_m or 3.5)
    wc_t = float(project.superstructure.wearing_coat_thickness_mm or 65) / 1000.0

    sof_y_mm = vy(soffit_rl)
    top_y_mm = vy(top_rl)
    slab_top_y = vy(top_rl - wc_t)  # top of deck slab = road level less the coat

    # Deck slab outline — the slab, and only the slab, breaks at each joint.
    line(msp, (hx(0), slab_top_y), (hx(total_len), slab_top_y), layer="SUPER-DECK")
    line(msp, (hx(0), sof_y_mm), (hx(total_len), sof_y_mm), layer="SUPER-DECK")
    hatch_rect(
        msp,
        hx(0),
        sof_y_mm,
        total_len * sc_h,
        slab_top_y - sof_y_mm,
        pattern="ANSI31",
        scale=sc_h * 0.04,
        layer="STRUC-HATCHING",
        color=8,
    )
    for jx in (0.0, total_len):  # break the slab at each joint — never the coat
        line(msp, (hx(jx), sof_y_mm), (hx(jx), slab_top_y), layer="SUPER-DECK", lw=25)

    level_tag(msp, draw_x0 - 2.0, sof_y_mm, soffit_rl, text_height=th * 0.85)
    level_tag(msp, draw_x0 - 2.0, top_y_mm, top_rl, text_height=th * 0.85)

    # ── Continuous wearing coat over both approach slabs ──────────────────
    # The coat runs end to end over both approach slabs; only its ends taper
    # (1:20). Nothing else may break it — the slab joints do not.
    x_left = -app_l
    x_right = total_len + app_l
    taper_len = wc_t * 20.0
    coat_pts = [
        (hx(x_left), vy(top_rl)),
        (hx(x_right), vy(top_rl)),
        (hx(x_right - taper_len), slab_top_y),
        (hx(x_left + taper_len), slab_top_y),
    ]
    polyline(msp, coat_pts, layer="SUPER-WEARING", close=True, lw=25)
    hatch_poly(msp, coat_pts, pattern="SOLID", scale=1.0, layer="SUPER-WEARING", color=8)
    text(
        msp,
        "CONTINUOUS WEARING COAT OVER APPROACH SLABS",
        hx(x_left),
        vy(top_rl) + th * 1.4,
        height=th * 0.8,
        layer="TEXT-SPEC",
        color=8,
    )

    # ── Approach slabs (resolved stack) ───────────────────────────────────
    app_bot_y = vy(float(stack.app_bot))
    for ax in (x_left, total_len):
        rectangle(
            msp,
            hx(ax),
            app_bot_y,
            app_l * sc_h,
            slab_top_y - app_bot_y,
            layer="CIVIL-ROAD",
            lw=25,
        )
        hatch_rect(
            msp,
            hx(ax),
            app_bot_y,
            app_l * sc_h,
            slab_top_y - app_bot_y,
            pattern="ANSI31",
            scale=sc_h * 0.04,
            layer="STRUC-HATCHING",
            color=8,
        )
        text(
            msp,
            "APPROACH SLAB",
            hx(ax + app_l / 2.0),
            app_bot_y - th * 1.5,
            height=th * 0.8,
            layer="TEXT-SPEC",
            halign="CENTER",
        )

    # ── Dirt wall at each abutment (resolved stack) ───────────────────────
    # Thin wall (DWTH) flush with the deck end, cap top up to approach-slab
    # soffit — never a full-width abutment extension.
    dw_t = float(sub.dirt_wall_thickness_mm or 300) / 1000.0
    cap_top_y = vy(float(stack.cap_top))
    for ax, side in ((0.0, -1.0), (total_len, 1.0)):
        dw_x = hx(ax) - dw_t * sc_h if side < 0 else hx(ax)
        rectangle(
            msp,
            dw_x,
            cap_top_y,
            dw_t * sc_h,
            app_bot_y - cap_top_y,
            layer="ABUT-PROF",
            lw=35,
        )
        text(
            msp,
            "DWTH",
            dw_x + dw_t * sc_h / 2.0,
            cap_top_y + (app_bot_y - cap_top_y) / 2.0,
            height=th * 0.7,
            layer="TEXT-SPEC",
            halign="CENTER",
            color=4,
        )

    # ── Pier shafts ───────────────────────────────────────────────────────
    pier_w_mm = float(sub.pier_shaft_width_m or 1.5) * sc_h
    pier_cap_h = float(sub.pier_cap_depth_m or 0.8) * sc_v * v_exag
    pier_ped_h = float(sub.pier_pedestal_height_m or 0.2) * sc_v * v_exag

    # FR-4: pull authoritative T.O.C. RLs from LongSectionGeometry (tie to
    # plan-northern-edge reference via same top-of-deck / soffit datum chain)
    toc_rls = ls.pier_top_of_cap_rl_m
    plan_ref_rl = ls.plan_northern_edge_reference_rl

    cumul = 0.0
    for i, slen in enumerate(span_lens[:-1]):
        cumul += slen
        px = hx(cumul) - pier_w_mm / 2.0

        # FR-4: pier TOP of pier-cap is authoritative vy(toc_rls[i]) — not the
        # old `soffit − pedestal − cap` manual in-place calc.  Pier cap sits
        # *below* this datum; pedestal above carries the soffit.
        py_toc = vy(toc_rls[i]) if i < len(toc_rls) else (sof_y_mm - pier_ped_h - pier_cap_h)
        py_cap_bot = py_toc - pier_cap_h  # cap bottom
        py_shaft_top = py_cap_bot  # pier shaft top = cap bottom
        py_bot = vy(hfl_rl - float(sub.pier_height_typical_m or 8.0))

        # Pier shaft (rectangle sits from shaft_top DOWN to base RL)
        rectangle(msp, px, py_bot, pier_w_mm, py_shaft_top - py_bot, layer="SUB-PIER", lw=40)
        hatch_rect(
            msp,
            px,
            py_bot,
            pier_w_mm,
            py_shaft_top - py_bot,
            pattern="ANSI31",
            scale=sc_h * 0.04,
            layer="STRUC-HATCHING",
            color=8,
        )

        # Pier cap — anchored to T.O.C. surface (py_cap_top = top-of-cap)
        cap_w = float(sub.pier_cap_width_m or 2.0) * sc_h
        rectangle(
            msp, hx(cumul) - cap_w / 2, py_cap_bot, cap_w, pier_cap_h, layer="SUB-PIER", lw=40
        )
        hatch_rect(
            msp,
            hx(cumul) - cap_w / 2,
            py_cap_bot,
            cap_w,
            pier_cap_h,
            pattern="ANSI31",
            scale=sc_h * 0.04,
            layer="STRUC-HATCHING",
        )

        # FR-4: T.O.C. P{i} level tag + dashed horizontal guide to level-axis
        # so reader can verify alignment with plan's northern-edge reference RL.
        level_tag(
            msp,
            px + pier_w_mm + sc_h * 0.5,
            py_toc,
            toc_rls[i] if i < len(toc_rls) else (ls.soffit_rl - pier_ped_h - pier_cap_h),
            text_height=th * 0.85,
        )
        text(
            msp,
            f"T.O.C. P{i+1}",
            px + pier_w_mm + sc_h * 0.5 + th * 10,
            py_toc,
            height=th * 0.9,
            layer="TEXT-HEADER",
        )

        # FR-4: fine dashed STRUC-SECTION guide line from T.O.C. rightwards to
        # level axis — proves visually that T.O.C. sits at correct offset from
        # the plan_northern_edge_reference_rl (top-of-deck datum).
        guide_x1 = px + pier_w_mm * 1.5 + sc_h
        guide_x2 = draw_x0 - th * 2.5
        line(
            msp,
            (guide_x1, py_toc),
            (guide_x2, py_toc),
            layer="STRUC-SECTION",
            color=8,
            linetype="DASHED",
        )
        # mini-tag at level-axis end showing the reference delta
        ref_delta = (
            toc_rls[i] if i < len(toc_rls) else (ls.soffit_rl - pier_ped_h - pier_cap_h)
        ) - plan_ref_rl
        text(
            msp,
            f"ΔREF={ref_delta:+.2f}m",
            guide_x2 - th * 12,
            py_toc - th * 1.1,
            height=th * 0.65,
            layer="TEXT-SPEC",
            color=8,
        )

        text(
            msp,
            f"P{i+1}",
            hx(cumul) - pier_w_mm * 0.5,
            py_bot - th * 2,
            height=th,
            layer="TEXT-GENERAL",
        )

        # Span label at mid-span
        mid_x = hx(cumul - slen / 2.0)
        text(
            msp,
            _span_label(i, slen),
            mid_x,
            sof_y_mm + (top_y_mm - sof_y_mm) / 2,
            height=th * 1.1,
            layer="TEXT-GENERAL",
            halign="CENTER",
        )

    # Last span label
    mid_x = hx(total_len - span_lens[-1] / 2.0)
    text(
        msp,
        _span_label(len(span_lens) - 1, span_lens[-1]),
        mid_x,
        sof_y_mm + (top_y_mm - sof_y_mm) / 2,
        height=th * 1.1,
        layer="TEXT-GENERAL",
        halign="CENTER",
    )

    # ── Abutments ─────────────────────────────────────────────────────────
    abt_w_mm = float(sub.abutment_width_m or 1.2) * sc_h
    abt_h_mm = float(sub.abutment_height_m or 3.2) * sc_v * v_exag
    cap_d2 = float(sub.abutment_cap_depth_mm or 600) / 1000.0
    cap_proj2 = float(sub.abutment_cap_projection_front_mm or 300) / 1000.0
    cap_proj2_r = float(sub.abutment_cap_projection_rear_mm or 300) / 1000.0
    dw_t2 = float(sub.dirt_wall_thickness_mm or 300) / 1000.0
    ped_h2 = float(sub.abutment_pedestal_height_m or 0.15)
    brg_t2 = 0.10
    app_t2 = float(sub.approach_slab_thickness_mm or 200) / 1000.0

    def sy2(m: float) -> float:
        return m * sc_v * v_exag

    for ch, label, sgn in [(0.0, "A1", -1.0), (total_len, "A2", +1.0)]:
        ax = hx(ch) - abt_w_mm if sgn < 0 else hx(ch)
        shaft_bot = sof_y_mm - abt_h_mm
        # Cap levels
        cap_bot_y2 = sof_y_mm - sy2(brg_t2 + ped_h2)
        cap_top_y2 = cap_bot_y2 - sy2(cap_d2)

        # Shaft stops at the cap soffit
        rectangle(msp, ax, shaft_bot, abt_w_mm, cap_bot_y2 - shaft_bot, layer="SUB-ABUT", lw=40)
        hatch_rect(
            msp,
            ax,
            shaft_bot,
            abt_w_mm,
            cap_bot_y2 - shaft_bot,
            pattern="ANSI31",
            scale=sc_h * 0.04,
            layer="STRUC-HATCHING",
        )

        # Cap — asymmetric: front (bearing shelf) on the river side, larger
        # rear (dirt-wall seat) on the approach side. sgn=+1 → approach to +x.
        cap_front_off = sy2(cap_proj2)
        cap_rear_off = sy2(cap_proj2_r)
        cap_x0_2 = ax - (cap_front_off if sgn > 0 else cap_rear_off)
        cap_x1_2 = ax + abt_w_mm + (cap_rear_off if sgn > 0 else cap_front_off)
        cap_w2 = cap_x1_2 - cap_x0_2
        rectangle(msp, cap_x0_2, cap_top_y2, cap_w2, sy2(cap_d2), layer="SUB-ABUT", lw=40)
        hatch_rect(
            msp,
            cap_x0_2,
            cap_top_y2,
            cap_w2,
            sy2(cap_d2),
            pattern="ANSI31",
            scale=sc_h * 0.04,
            layer="STRUC-HATCHING",
        )

        # Pedestal + bearing
        ped_w_mm2 = abt_w_mm * 0.55
        ped_x_2 = ax + (abt_w_mm - ped_w_mm2) / 2.0
        rectangle(
            msp,
            ped_x_2,
            sof_y_mm - sy2(brg_t2 + ped_h2),
            ped_w_mm2,
            sy2(ped_h2),
            layer="SUB-ABUT",
            lw=30,
        )
        rectangle(
            msp, ped_x_2, sof_y_mm - sy2(brg_t2), ped_w_mm2, sy2(brg_t2), layer="SUB-BEARING", lw=30
        )

        # Dirt wall on the rear (approach) face, up to approach-slab soffit
        dirt_x_2 = cap_x0_2 if sgn < 0 else cap_x0_2 + cap_w2 - sy2(dw_t2)
        dw_top_y2 = vy(top_rl - wc_t) - sy2(app_t2)
        if dw_top_y2 > cap_top_y2:
            rectangle(
                msp,
                dirt_x_2,
                cap_top_y2,
                sy2(dw_t2),
                dw_top_y2 - cap_top_y2,
                layer="SUB-DIRT-WALL",
                lw=40,
            )
            hatch_rect(
                msp,
                dirt_x_2,
                cap_top_y2,
                sy2(dw_t2),
                dw_top_y2 - cap_top_y2,
                pattern="ANSI31",
                scale=sc_h * 0.04,
                layer="STRUC-HATCHING",
            )
            text(
                msp,
                "DIRT WALL",
                dirt_x_2 + sy2(dw_t2) + th * 0.6 if sgn > 0 else dirt_x_2 - th * 4,
                cap_top_y2 + (dw_top_y2 - cap_top_y2) * 0.5,
                height=th * 0.75,
                layer="TEXT-SPEC",
            )

        text(
            msp,
            label,
            ax - th * 2 if sgn < 0 else ax + abt_w_mm + th * 0.5,
            shaft_bot + abt_h_mm / 2,
            height=th,
            layer="TEXT-GENERAL",
        )

    # ── Piles / foundations ───────────────────────────────────────────────
    pile_dia_mm = float(fd.pile_diameter_mm or 1200) / 1000.0 * sc_h
    pile_tip_y = vy(pile_tip_rl)
    pile_cut_y = vy(float(fd.pile_cutoff_level_m or scour_rl) - 1.0)

    piles_per_pier = int(fd.piles_per_pier or 4)
    cols = max(1, round(piles_per_pier**0.5))

    # Show pile group elevation under each support
    for ch, is_abut in [(0.0, True), (total_len, True)] + [
        (sum(span_lens[: i + 1]), False) for i in range(len(span_lens) - 1)
    ]:
        for c in range(cols):
            offset = (c - (cols - 1) / 2.0) * float(fd.pile_spacing_m or 2.4) * sc_h
            px = hx(ch) + offset - pile_dia_mm / 2.0
            line(
                msp,
                (hx(ch) + offset, pile_cut_y),
                (hx(ch) + offset, pile_tip_y),
                layer="FOUND-PILE",
                lw=35,
            )
            circle(msp, hx(ch) + offset, pile_cut_y, pile_dia_mm / 2.0, layer="FOUND-PILE")

    level_tag(msp, draw_x0 - 2.0, pile_tip_y, pile_tip_rl, text_height=th * 0.85)
    text(
        msp,
        "PILE TIP LEVEL",
        hx(total_len) + sc_h * 0.3,
        pile_tip_y,
        height=th * 0.85,
        layer="TEXT-GENERAL",
    )

    # ── Freeboard annotation ──────────────────────────────────────────────
    fb_mid_x = hx(total_len * 0.7)
    dim_linear_v(
        msp,
        fb_mid_x,
        hfl_y_mm,
        fb_mid_x,
        sof_y_mm,
        dim_x=fb_mid_x + sc_h * 2.0,
        label=f"FB={ls.freeboard_m:.3f}m",
        text_height=th * 0.9,
    )

    # ── View label ────────────────────────────────────────────────────────
    text(
        msp,
        "LONGITUDINAL SECTION",
        draw_x0 + draw_w / 2,
        vy(top_rl) + sc_v * v_exag * 2.5,
        height=th * 1.5,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    text(
        msp,
        f"H Scale 1:{scale_denom}   V Scale 1:{int(scale_denom/v_exag)} (V.E.={v_exag}×)",
        draw_x0 + draw_w / 2,
        vy(top_rl) + sc_v * v_exag * 1.0,
        height=th * 0.9,
        layer="TEXT-SPEC",
        halign="CENTER",
    )
    text(
        msp,
        "(Not to Scale — indicative)",
        draw_x0 + draw_w / 2,
        vy(top_rl) + sc_v * v_exag * 0.15,
        height=th * 0.9 * 0.9,
        layer="TEXT-SPEC",
        halign="CENTER",
        color=8,
    )  # FR-8: demoted 10% smaller + grey colour (8)


__all__ = ["generate"]
