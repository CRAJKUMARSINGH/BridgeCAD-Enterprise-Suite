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
from .fit import MIN_TEXT_MM, Fit, choose_fit
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
_RIGHT_LABEL_W = 60.0  # right gutter for HFL / LWL / scour / pile-tip labels
_TH_MAX = 6.0  # text-height cap (mm): the fit-scale can be ~65 mm/m on a
#                short bridge, so an uncapped `sc_h * 0.4` drowned the sheet.


def _chainage_pitch(total_m: float) -> float:
    """Uniform chainage interval for the *labelled* grid — the LISP `xincr`.

    Keeps roughly 6–12 labels across the bridge so the axis grid stays legible
    without the numbers colliding. The chainage is drawn two-tier around this
    pitch: unlabelled ticks at half the pitch and a labelled tick on it.
    """
    for pitch in (1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 50.0, 100.0):
        if total_m / pitch <= 12:
            return pitch
    return 200.0


def _annot_mode(span_mm: float, pier_pitch_mm: float) -> str:
    """How much annotation the pier line can carry on paper — SS3 §A2.

    The section used to print its full annotation set regardless of how small
    it had been drawn, so on a 270 m nine-span the eight `ΔREF=` strings and the
    per-pier labels all landed on the same few millimetres. Gate each tier on
    the paper space actually available:

    ``full``         span length + in-line T.O.C. tags + the ΔREF table
    ``index``        span index tags only; per-pier labels rotated off the line
    ``index-narrow`` span index tags at 90°; no per-pier tag at all
    """
    if span_mm >= 30 and pier_pitch_mm >= 20:
        return "full"
    if span_mm >= 18 and pier_pitch_mm >= 12:
        return "index"
    return "index-narrow"


def generate(
    project: Any,
    output_path: str | Path,
    scale_denom: int | None = None,
    v_exag: float = 1.0,
) -> Path:
    """Generate Sheet 2 (Longitudinal Section) as a DXF file.

    Parameters
    ----------
    project : BridgeProject
    output_path : str | Path
    scale_denom : int | None
        Horizontal scale denominator. ``None`` (default) lets the sheet pick
        the largest standard rung that fits the elevation — a fitted scale far
        from any preferred number is what made the printed caption a lie.
        An explicit denominator is honoured as given: the geometry is then
        drawn at *that* scale, so the caption derived from it stays true.
    v_exag : float
        Vertical exaggeration applied to the section (SS3 §A3). ``1.0``
        (default) is a true section whose vertical scale is the height fit; a
        value > 1 stretches the vertical proportionally and the printed V
        scale/V.E. follow the geometry drawn.

    Returns
    -------
    Path
    """
    doc, msp = new_sheet("S2 Long Section")
    _draw_long_section(msp, project, scale_denom, v_exag)
    return save(doc, output_path)


def _draw_long_section(
    msp: Any,
    project: Any,
    scale_denom: int | None = None,
    v_exag: float = 1.0,
) -> None:
    from bridgecad_core import types as T
    from bridgecad_core.geometry import compute_long_section_geometry

    gi = project.geometry_input
    sub = project.substructure
    fd = project.foundation_details
    ss = project.superstructure
    pm = project.project_master

    # ── Presence by type (SS3 §A4) ────────────────────────────────────────
    # A raft or open foundation carries no piles; a box culvert or a box cell
    # carries no *separate* intermediate piers (the monolithic cell walls do
    # the work, not a shaft+cap). Both gates are driven by the *model*, never
    # by the sheet, so a 004 raft box cannot inherit a pile group it does not
    # have.
    _no_pier_ss = (
        T.SuperstructureType.BOX_CULVERT,
        getattr(T.SuperstructureType, "BOX_CELL_MULTI", T.SuperstructureType.BOX_CULVERT),
    )
    has_piles = fd.type == T.FoundationType.PILE
    has_piers = ss.type not in _no_pier_ss

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

    # The vertical fit must cover everything the sheet actually draws, not just
    # the hydraulic RLs: the pier shafts run down to ``HFL − pier_height_typical``
    # and the abutment shafts to ``soffit − abutment_height``.  On the PWD booklet
    # fixtures (which print no absolute RLs, so HFL/scour/pile-tip all resolve to
    # the same datum) those bases sit several metres below the old
    # ``min(pile_tip, scour)`` datum and the shafts — and their ``P1..Pn`` labels —
    # plotted 220–294 mm below the sheet frame.
    pier_base_rl = hfl_rl - float(sub.pier_height_typical_m or 8.0)
    abt_base_rl = soffit_rl - float(sub.abutment_height_m or 3.2)
    rl_low = min(pile_tip_rl, scour_rl, pier_base_rl, abt_base_rl)
    datum_rl = rl_low - 2.0  # baseline datum
    rl_range = max(top_rl + 2.0, hfl_rl + 3.0) - datum_rl

    # The wearing coat and both approach slabs run a full approach-slab length
    # past each deck end, so the horizontal fit must span them or they plot off
    # the sheet.
    from bridgecad_core.abutment_stack import resolve_abutment_stack

    stack = resolve_abutment_stack(project)
    app_l = float(sub.approach_slab_length_m or 3.5)

    # ── Drawing area ───────────────────────────────────────────────────────
    draw_x0 = _MARGIN + _LEVEL_AXIS_W + 5.0
    draw_y0 = _MARGIN + _TB_H + _CHAINAGE_H + 3.0  # FR-2: was +10.0, now 3 mm gutter
    draw_w = _SHEET_W - draw_x0 - _MARGIN - _RIGHT_LABEL_W
    draw_h = _SHEET_H - draw_y0 - _MARGIN - 13.0  # FR-2: reclaim ~7 mm previously wasted

    # Scale factors (mm per metre). The horizontal scale is a rung of the
    # shared ladder, never `draw_w / ch_span`: an invented denominator is what
    # let this sheet's title block claim "1:100" for a view drawn at about
    # 1:382 (PWD 010 — 9 × 30 m). The vertical scale is the fit that fills the
    # drawing height; the exaggeration is *reported* from the two, never
    # asserted.
    ch_min = -app_l  # left-most drawn chainage (approach slab tail)
    ch_max = total_len + app_l  # right-most drawn chainage
    ch_span = max(ch_max - ch_min, 0.1)
    fit = choose_fit(ch_span, draw_w, len(span_lens) + 2)
    if scale_denom is not None:
        fit = Fit(scale_denom, 1000.0 / scale_denom, False, 1)
    sc_h = fit.mm_per_m  # horizontal — a ladder rung, so the caption is true
    # Vertical scale: the height fit, exaggerated by `v_exag` (SS3 §A3). Every
    # vertical *size* must then be drawn through `sy()` (a `vy` RL delta), never
    # as `metres * sc_v * v_exag` — the old form's `v_exag` cancelled the one
    # already folded into `sc_v`, so the section drew flat under an exaggerated
    # caption. `v_exag=1.0` is an un-exaggerated fitted section.
    sc_v = (draw_h / max(rl_range, 0.1)) * v_exag
    v_eff = sc_v / sc_h  # the *real* vertical exaggeration, for the caption

    CoordMapper(
        datum_rl=datum_rl,
        origin_ch=0.0,
        h_scale=sc_h / 1000.0,  # CoordMapper expects h_scale in m→unit
        v_scale=sc_v / 1000.0,
        x_offset=draw_x0,
        y_offset=draw_y0,
    )

    def hx(ch):
        return draw_x0 + (ch - ch_min) * sc_h

    def vy(rl):
        return draw_y0 + (rl - datum_rl) * sc_v

    def sy(m: float) -> float:
        """A vertical size in metres → paper mm at the section's vertical scale.

        Every thickness must go through here (or through `vy` as an RL delta):
        `m * sc_v * v_exag` was the form whose `v_exag` cancelled the one in
        `sc_v`, drawing an un-exaggerated section under an exaggerated caption.
        """
        return m * sc_v

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
        scale_str=f"{fit.scale_str} H   1:{round(1000.0 / sc_v)} V  (V.E.={v_eff:.2f}x)",
        sheet_no="2",
        total_sheets="9",
    )

    th = min(_TH_MAX, max(MIN_TEXT_MM, sc_h * 0.4))  # adaptive text height mm (capped)

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
    # xincr pitch — two-tier grid (SS3 §A2): unlabelled ticks at half the
    # pitch, a labelled tick on it. At 270 m the old single tier printed 21
    # numbers into a 20 mm band; halving the tick spacing and labelling only the
    # majors keeps the grid readable without the numbers colliding.
    ch_pitch = _chainage_pitch(total_len)
    ch_minor = ch_pitch / 2.0
    _step = round(ch_pitch / ch_minor)  # majors every `_step` minor ticks
    tick = 0
    while tick * ch_minor <= total_len + 1e-6:
        ch_mark = tick * ch_minor
        xt = hx(ch_mark)
        major = tick % _step == 0
        line(
            msp,
            (xt, draw_y0),
            (xt, draw_y0 - th * (1.0 if major else 0.55)),
            layer="CIVIL-CHAINAGE",
        )
        if major:
            text(
                msp,
                f"{ch_mark:.0f}",
                xt,
                draw_y0 - th * 2.6,
                height=th * 0.7,
                layer="TEXT-LEVEL",
                halign="CENTER",
            )
        tick += 1

    def _near_grid_label(ch: float) -> bool:
        """True when a span tag at *ch* would sit on a labelled grid tick."""
        nearest = round(ch / ch_pitch) * ch_pitch
        return abs(ch - nearest) < ch_pitch * 0.25

    # Chainage markers every span — suppressed when they would collide with a
    # labelled grid tick (SS3 §A2). The terminal tag is never suppressed.
    cumul = 0.0
    for slen in span_lens:
        if not _near_grid_label(cumul):
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
    # The graduations must stop where the modelled extent stops, or the top tick
    # plots above the frame (a culvert with a low HFL left `rl_range` at
    # `top_rl + 2` while this loop ran to `top_rl + 2.5` → +2 mm over the top).
    rl_top = min(top_rl + 2.5, datum_rl + rl_range)
    rl_val = math.floor(rl_bot)
    while rl_val <= rl_top:
        yy = vy(rl_val)
        tick_len = th * 2 if rl_val % 5 == 0 else th * 1.0
        line(msp, (draw_x0 - tick_len, yy), (draw_x0, yy), layer="DIM-LEVEL")
        if rl_val % 2 == 0:
            text(
                msp,
                f"{rl_val:.0f}",
                _MARGIN + 12.0,
                yy - th * 0.5,
                height=th * 0.8,
                layer="TEXT-LEVEL",
            )
        rl_val += rl_step

    # Axis title along the level axis (LISP `layout()` label "BED LEVEL").
    # Anchored at the bottom of the axis: rotated 90° it grows upward, so a
    # bottom anchor keeps it inside the frame (a top anchor ran 35 mm past it).
    text(
        msp,
        "BED LEVEL",
        _MARGIN + 2.0,
        draw_y0 + 2.0,
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
    pier_cap_h = sy(float(sub.pier_cap_depth_m or 0.8))
    pier_ped_h = sy(float(sub.pier_pedestal_height_m or 0.2))

    # FR-4: pull authoritative T.O.C. RLs from LongSectionGeometry (tie to
    # plan-northern-edge reference via same top-of-deck / soffit datum chain)
    toc_rls = ls.pier_top_of_cap_rl_m
    plan_ref_rl = ls.plan_northern_edge_reference_rl

    # Annotation density governor (SS3 §A2): a span's paper length decides how
    # much the pier line can carry. On a 270 m nine-span at 1:400 a span is
    # 75 mm — "full"; swept to 1:250 it is 120 mm — still "full"; a many-span
    # type at a coarse rung drops to index tags only.
    _mean_span_m = (total_len / len(span_lens)) if span_lens else 0.0
    _span_mm = _mean_span_m * sc_h
    annot = _annot_mode(_span_mm, _span_mm)

    def _span_tag(i: int, slen: float) -> tuple[str, int]:
        """Span label and its rotation for the current annotation tier."""
        if annot == "full":
            return _span_label(i, slen), 0
        return f"S{i+1}", (90 if annot == "index-narrow" else 0)

    # Consolidated pier table (SS3 §A2) — one row per pier, right gutter. Built
    # here, drawn after the loop so it sits above everything the loop plotted.
    _pier_rows: list[str] = []

    cumul = 0.0
    for i, slen in enumerate(span_lens[:-1]):
        cumul += slen

        # Span label at mid-span — drawn whether or not a support exists there.
        _stext, _srot = _span_tag(i, slen)
        text(
            msp,
            _stext,
            hx(cumul - slen / 2.0),
            sof_y_mm + (top_y_mm - sof_y_mm) / 2,
            height=th * 1.1,
            layer="TEXT-GENERAL",
            halign="CENTER",
            rotation=_srot,
        )

        # Presence gate: a box culvert has no intermediate pier/cap/pedestal.
        if not has_piers:
            continue

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

        # FR-4: T.O.C. P{i} level tag + dashed guide to the level axis so the
        # reader can verify alignment with the plan's northern-edge RL. Only
        # drawn at "full" density (SS3 §A2) — at the coarser tiers these tags
        # are what collided into a single unreadable stack. The ΔREF value is
        # never drawn in-line any more; it goes into the table below.
        _toc = toc_rls[i] if i < len(toc_rls) else (ls.soffit_rl - pier_ped_h - pier_cap_h)
        if annot == "full":
            level_tag(
                msp,
                px + pier_w_mm + sc_h * 0.5,
                py_toc,
                _toc,
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

            # Fine dashed STRUC-SECTION guide from the T.O.C. rightwards to the
            # level axis — visual proof of the offset from the top-of-deck datum.
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

        _pier_rows.append(f"P{i+1}  {float(_toc):.3f}  {(float(_toc) - float(plan_ref_rl)):+.2f}")

        text(
            msp,
            f"P{i+1}",
            hx(cumul) - pier_w_mm * 0.5,
            py_bot - th * 2,
            height=th,
            layer="TEXT-GENERAL",
            rotation=(90 if annot == "index-narrow" else 0),
        )

    # ── Consolidated ΔREF table (SS3 §A2) ─────────────────────────────────
    # Eight strings clamped to the same x at the same y was the old output;
    # one sorted row per pier in the right gutter replaces it.
    if annot == "full" and _pier_rows:
        _tab_x = hx(total_len) + sc_h * 0.3 + th * 9.0
        _tab_top = vy(top_rl) - th * 2.0
        text(
            msp,
            "PIER   T.O.C.RL   ΔREF",
            _tab_x,
            _tab_top,
            height=th * 0.8,
            layer="TEXT-HEADER",
        )
        for _r, _row in enumerate(_pier_rows, 1):
            text(
                msp,
                _row,
                _tab_x,
                _tab_top - _r * th * 1.6,
                height=th * 0.75,
                layer="TEXT-SPEC",
                color=8,
            )

    # Last span label
    mid_x = hx(total_len - span_lens[-1] / 2.0)
    _lstext, _lsrot = _span_tag(len(span_lens) - 1, span_lens[-1])
    text(
        msp,
        _lstext,
        mid_x,
        sof_y_mm + (top_y_mm - sof_y_mm) / 2,
        height=th * 1.1,
        layer="TEXT-GENERAL",
        halign="CENTER",
        rotation=_lsrot,
    )

    # ── Abutments ─────────────────────────────────────────────────────────
    abt_w_mm = float(sub.abutment_width_m or 1.2) * sc_h
    abt_h_mm = sy(float(sub.abutment_height_m or 3.2))
    cap_d2 = float(sub.abutment_cap_depth_mm or 600) / 1000.0
    cap_proj2 = float(sub.abutment_cap_projection_front_mm or 300) / 1000.0
    cap_proj2_r = float(sub.abutment_cap_projection_rear_mm or 300) / 1000.0
    dw_t2 = float(sub.dirt_wall_thickness_mm or 300) / 1000.0
    ped_h2 = float(sub.abutment_pedestal_height_m or 0.15)
    brg_t2 = 0.10
    app_t2 = float(sub.approach_slab_thickness_mm or 200) / 1000.0

    def sy2(m: float) -> float:
        return sy(m)

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
    # Presence gate (SS3 §A4): only a PILE foundation has piles. A raft or an
    # open footing previously inherited a pile group under every support.
    if has_piles:
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
    # The offsets above the deck are scale-proportional (`sy`), so a compact
    # structure (small RL range → large mm-per-metre) pushes the label stack
    # through the top border. Shift the whole stack down by the overflow.
    _lbl_top = vy(top_rl) + sy(2.5)
    _lbl_shift = max(0.0, (_lbl_top + th * 1.5) - (_SHEET_H - _MARGIN))
    text(
        msp,
        "LONGITUDINAL SECTION",
        draw_x0 + draw_w / 2,
        _lbl_top - _lbl_shift,
        height=th * 1.5,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    # The printed scales are the ones the geometry was drawn at: H is the ladder
    # rung, V is the height fit, and the exaggeration is their ratio. The old
    # caption typed a constant ("1:100 V, V.E.=2×") beside a fitted view.
    text(
        msp,
        f"H Scale {fit.scale_str}   V Scale 1:{round(1000.0 / sc_v)}  (V.E.={v_eff:.2f}x)",
        draw_x0 + draw_w / 2,
        vy(top_rl) + sy(1.0) - _lbl_shift,
        height=th * 0.9,
        layer="TEXT-SPEC",
        halign="CENTER",
    )
    text(
        msp,
        "ALL DIMENSIONS IN METRES UNLESS NOTED",
        draw_x0 + draw_w / 2,
        vy(top_rl) + sy(0.15) - _lbl_shift,
        height=th * 0.9 * 0.9,
        layer="TEXT-SPEC",
        halign="CENTER",
        color=8,
    )  # FR-8: demoted 10% smaller + grey colour (8)

    # ── Principal dimensions (vertical level/thickness staffs) ───────────
    # The drawing area has no gutter below the chainage axis and the deck-top
    # band already carries the view title, so the section's principal
    # dimensions run as vertical staffs stacked just inside the right edge,
    # each measured against the datum baseline.
    deck_t = float(getattr(project.superstructure, "deck_thickness_mm", 0) or 0) / 1000.0
    base_y = vy(datum_rl)
    # The abutment staff only carries a PILE leg when the foundation has piles
    # (SS3 §A4 — a raft/open footing must not claim a pile-tip dimension).
    abt_levels = [
        (f"ABUT={float(stack.cap_top) - float(stack.app_bot):.3f}m", float(stack.app_bot)),
    ]
    if has_piles:
        abt_levels.append(
            (f"PILE={pile_tip_rl - float(fd.pile_cutoff_level_m or scour_rl):.3f}m", pile_tip_rl)
        )
    staffs = (
        (draw_x0 + draw_w * 0.97, (
            ("T.O.DECK", top_rl),
            ("HFL", hfl_rl),
            ("LWL", lwl_rl),
        )),
        (draw_x0 + draw_w * 0.93, (
            (f"WC={wc_t * 1000:.0f}mm", top_rl - wc_t),
            (f"DECK={deck_t * 1000:.0f}mm", top_rl - wc_t - deck_t),
        )),
        (draw_x0 + draw_w * 0.89, (
            (f"SCOUR={hfl_rl - scour_rl:.3f}m", scour_rl),
        )),
        (draw_x0 + draw_w * 0.85, tuple(abt_levels)),
    )
    for staff_x, levels in staffs:
        for lv_label, lv_rl in levels:
            dim_linear_v(
                msp,
                staff_x,
                base_y,
                staff_x,
                vy(lv_rl),
                dim_x=staff_x,
                label=lv_label,
                text_height=th * 0.85,
            )


__all__ = ["generate"]
