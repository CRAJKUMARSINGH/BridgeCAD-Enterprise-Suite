"""
bridgecad_draw.sheet8_side_elevations — Sheet 8: Side & End Elevations.

Production-quality GAD sheet on A1 landscape — two views side-by-side:

  **View 1 (Left half):  Abutment End-Face A2** (viewer looking back from A2 towards A1)
    - Full transverse cross-face of the abutment:
      deck slab, wearing coat, kerbs, parapet/railing, footpaths,
      bearing pads, abutment shaft (concrete hatch), return walls L/R,
      wing-wall splay indicators (dashed), approach-slab hatch,
      foundation pile group / open footing below.
    - RL tags at every structural level + width dimensions.

  **View 2 (Right half): Pier Transverse Face (cut B-B)**
    - If span_count >= 2 (internal piers exist):
        Deck, girder webs/flanges outline, bearings, pier cap (hatch),
        pier shaft (hatch), pile cap (hatch), full pile-group
        transverse elevation with column/pile count labels, all RL tags.
    - If span_count == 1 (no internal piers):
        *Fallback:* "TYPICAL ABUTMENT TRANSVERSE SECTION" — same
        abutment end-face geometry as View 1 but labelled generically
        (so the sheet still carries meaningful content on single-span
        projects like the simple_12m smoke fixture).

Layers, text heights, and dimension style follow IRC SP:55-2019 Annex F / Annex D
patterns used on sheets 1–7.  Drawing title matches IRC example naming.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .dxf_engine import new_sheet, save
from .primitives import (
    circle,
    dim_linear_h,
    hatch_poly,
    hatch_rect,
    level_tag,
    line,
    polyline,
    rectangle,
    scale_bar,
    text,
)
from .titleblocks import draw_border, draw_title_block

# ── Sheet constants (A1 landscape, mm model-space) ──────────────────────────
_SHEET_W = 841.0
_SHEET_H = 594.0
_MARGIN  = 10.0
_TB_H    = 65.0        # IRC SP:55 title block reserved height at bottom

# Two-view split: vertical divide at sheet horizontal midpoint, with a gutter.
_VIEW_GUTTER_W = 18.0  # mm gap between left/right views
_VIEW1_X0 = _MARGIN + 6.0
_VIEW2_X0 = _MARGIN + (_SHEET_W - 2 * _MARGIN) * 0.50 + _VIEW_GUTTER_W / 2.0
_VIEW_W   = (_SHEET_W - 2 * _MARGIN - _VIEW_GUTTER_W) * 0.50
_VIEW_Y0  = _MARGIN + _TB_H + 12.0
_VIEW_H   = _SHEET_H - _VIEW_Y0 - _MARGIN - 22.0

def generate(project: Any, output_path: str | Path,
             scale_denom: int = 50) -> Path:
    """Generate Sheet 8 (Side & End Elevations) as a DXF file."""
    doc, msp = new_sheet("S8 Side Elevations")
    _draw(msp, project, scale_denom)
    return save(doc, output_path)


def _draw(msp: Any, project: Any, scale_denom: int = 50) -> None:
    from bridgecad_core.geometry import compute_long_section_geometry

    gi  = project.geometry_input
    ss  = project.superstructure
    sub = project.substructure
    fd  = project.foundation_details
    hd  = project.hydraulic_data
    pm  = project.project_master

    span_count = int(getattr(gi, "span_count", len(getattr(gi, "span_lengths_m", [1.0]))))
    has_internal_pier = span_count > 1

    ls = compute_long_section_geometry(project)

    # ── Derived geometry (metres) ──────────────────────────────────────────
    cw        = float(gi.carriageway_width_m)
    kerb_l    = float(gi.kerb_width_left_m  or 0.25)
    kerb_r    = float(gi.kerb_width_right_m or 0.25)
    fp_l      = float(gi.footpath_left_m    or 0.0)
    fp_r      = float(gi.footpath_right_m   or 0.0)
    cb_l      = float(gi.crash_barrier_width_left_m  or 0.0)
    cb_r      = float(gi.crash_barrier_width_right_m or 0.0)
    overall_w = cw + kerb_l + kerb_r + fp_l + fp_r + cb_l + cb_r
    half_ow   = overall_w / 2.0
    half_cw   = cw / 2.0

    deck_t_m  = float(ss.deck_thickness_mm  or 200) / 1000.0
    wc_t_m    = float(ss.wearing_coat_thickness_mm or 65) / 1000.0
    gd_m      = float(ss.girder_depth_mm    or 900) / 1000.0
    gs_m      = float(ss.girder_spacing_m   or 2.5)
    n_girders = int(ss.girders_per_deck_count or 4)
    par_h_m   = float(ss.parapet_height_mm  or 1000) / 1000.0

    # Substructure
    abt_w_m   = float(sub.abutment_width_m  or 1.0)
    abt_h_m   = float(sub.abutment_height_m or 2.8)
    abt_len_m = float(sub.abutment_length_m or overall_w * 1.1)
    ret_w_m   = float(sub.return_wall_length_m or 3.5)
    wing_splay_m = float(sub.wing_wall_splay_length_m or 2.5)
    wing_h_m  = float(sub.wing_wall_height_m or 2.0)
    app_l_m   = float(sub.approach_slab_length_m   or 3.5)
    app_t_m   = float(sub.approach_slab_thickness_mm or 200) / 1000.0
    ped_h_m   = float(sub.abutment_pedestal_height_m or 0.15)

    # Pier values (only used for has-internal-pier View 2 path)
    pier_cap_w_m  = float(sub.pier_cap_width_m  or 1.8)
    pier_cap_d_m  = float(sub.pier_cap_depth_m  or 0.65)
    pier_shaft_w_m= float(sub.pier_shaft_width_m or 1.2)
    pier_shaft_l_m= float(sub.pier_shaft_length_m or abt_len_m * 0.98)
    pier_ped_h_m  = float(sub.pier_pedestal_height_m or 0.15)

    # Foundation
    pile_dia_m  = float(fd.pile_diameter_mm or 1000) / 1000.0
    pile_len_m  = float(fd.pile_length_m  or 12.0)
    pile_sp_m   = float(fd.pile_spacing_m or 2.0)
    piles_n     = int(fd.piles_per_pier or 4)
    pile_cap_t_m= float(fd.pile_cap_thickness_mm or 1200) / 1000.0
    pile_cut_rl = float(fd.pile_cutoff_level_m or 110.5)
    pile_tip_rl = pile_cut_rl - pile_len_m
    found_type  = str(getattr(getattr(fd, "type", None), "name", getattr(fd, "type", "PILE"))).upper()

    # Levels
    tod_rl  = float(pm.road_level_rl_m or ls.top_of_deck_rl)   # Top-of-deck RL
    sof_rl  = float(hd.actual_soffit_level_m or ls.soffit_rl)  # Soffit RL
    road_rl_approach = tod_rl - 0.01 * float(gi.gradient_pct or 0) * app_l_m
    abt_base_rl = sof_rl - ped_h_m - abt_h_m   # bottom of abutment shaft
    # If pile foundation, abutment sits on pile cap top (= pile_cut + pile_cap_t)
    if "PILE" in found_type:
        cap_top_rl = pile_cut_rl + pile_cap_t_m
        abt_base_rl = min(abt_base_rl, cap_top_rl)
    hfl_rl  = float(hd.hfl_m or 0)
    scour_rl= float(hd.scour_level_m or 0)

    # ── BORDER + TITLE BLOCK ───────────────────────────────────────────────
    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title = getattr(pm, "project_title", "") or "",
        bridge_name   = getattr(pm, "bridge_name",  "") or "",
        drawing_no    = getattr(pm, "drawing_no", "GAD-008") or "GAD-008",
        drawing_title = "GENERAL ARRANGEMENT — SIDE & END ELEVATIONS",
        revision      = getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        date_str      = str(getattr(pm, "date_issued", "") or ""),
        designed_by   = getattr(pm, "designed_by",  "") or "",
        checked_by    = getattr(pm, "checked_by",   "") or "",
        approved_by   = getattr(pm, "approved_by",  "") or "",
        client        = getattr(getattr(pm, "client",      None), "name", "") or "",
        consultant    = getattr(getattr(pm, "consultant",  None), "name", "") or "",
        scale_str     = f"1:{scale_denom}",
        sheet_no      = "8",
        total_sheets  = "8",
    )

    # ── Adaptive scale per view (fit overall_w × total_height into box) ──
    # We try to pick a single scale mm/m that fits the larger of the two views.
    abut_vheight_m = (tod_rl + par_h_m + 0.5) - min(pile_tip_rl, scour_rl - 0.5)
    pier_vheight_m = (tod_rl + par_h_m + 0.5) - min(pile_tip_rl, scour_rl - 0.5)
    # Horizontal fit: abutment end-face needs overall_w + 2×ret_w_m + approach
    abut_hwidth_m  = overall_w + 2 * ret_w_m + max(app_l_m, wing_splay_m) * 0.75
    pier_hwidth_m  = overall_w + 2.0

    sc = min(
        _VIEW_W / max(abut_hwidth_m, pier_hwidth_m, 0.1),
        _VIEW_H / max(abut_vheight_m, pier_vheight_m, 0.1),
    ) * 0.88

    th = max(2.0, sc * 0.22)   # text height mm

    # ═══════════════════════════════════════════════════════════════════════
    #  VIEW 1 — Abutment End-Face A2 (left half of page)
    # ═══════════════════════════════════════════════════════════════════════
    v1_cx = _VIEW1_X0 + _VIEW_W / 2.0
    def v1hx(x_m): return v1_cx + x_m * sc                 # transverse x
    def v1vy(rl):  return _VIEW_Y0 + (rl - (tod_rl + par_h_m + 0.8)) * (-sc)   # RL → y

    _draw_abutment_endface(
        msp, v1hx, v1vy, sc, th,
        overall_w, cw, half_ow, half_cw,
        kerb_l, kerb_r, fp_l, fp_r, cb_l, cb_r,
        deck_t_m, wc_t_m, gd_m, gs_m, n_girders, par_h_m,
        abt_w_m, abt_h_m, abt_len_m, ret_w_m,
        wing_splay_m, wing_h_m,
        app_l_m, app_t_m, ped_h_m,
        pile_dia_m, pile_len_m, pile_sp_m, piles_n, pile_cap_t_m,
        pile_cut_rl, pile_tip_rl,
        tod_rl, sof_rl, road_rl_approach, abt_base_rl, hfl_rl, scour_rl,
        found_type,
        view_label="VIEW 1 — SECTION A-A  |  ABUTMENT A2 END-FACE (LOOKING A1)",
    )

    # ═══════════════════════════════════════════════════════════════════════
    #  VIEW 2 — Pier transverse / Fallback typical abutment (right half)
    # ═══════════════════════════════════════════════════════════════════════
    v2_cx = _VIEW2_X0 + _VIEW_W / 2.0
    def v2hx(x_m): return v2_cx + x_m * sc
    def v2vy(rl):  return _VIEW_Y0 + (rl - (tod_rl + par_h_m + 0.8)) * (-sc)

    if has_internal_pier:
        _draw_pier_transverse(
            msp, v2hx, v2vy, sc, th,
            overall_w, cw, half_ow, half_cw,
            kerb_l, kerb_r, fp_l, fp_r, cb_l, cb_r,
            deck_t_m, wc_t_m, gd_m, gs_m, n_girders, par_h_m,
            pier_cap_w_m, pier_cap_d_m, pier_shaft_w_m, pier_shaft_l_m,
            pier_ped_h_m,
            pile_dia_m, pile_len_m, pile_sp_m, piles_n, pile_cap_t_m,
            pile_cut_rl, pile_tip_rl,
            tod_rl, sof_rl, hfl_rl, scour_rl,
            found_type,
            view_label="VIEW 2 — SECTION B-B  |  PIER P1 TRANSVERSE FACE",
        )
    else:
        # ── Fallback: Typical Abutment Transverse Section ─────────────────
        _draw_abutment_endface(
            msp, v2hx, v2vy, sc, th,
            overall_w, cw, half_ow, half_cw,
            kerb_l, kerb_r, fp_l, fp_r, cb_l, cb_r,
            deck_t_m, wc_t_m, gd_m, gs_m, n_girders, par_h_m,
            abt_w_m, abt_h_m, abt_len_m, ret_w_m,
            wing_splay_m, wing_h_m,
            app_l_m, app_t_m, ped_h_m,
            pile_dia_m, pile_len_m, pile_sp_m, piles_n, pile_cap_t_m,
            pile_cut_rl, pile_tip_rl,
            tod_rl, sof_rl, road_rl_approach, abt_base_rl, hfl_rl, scour_rl,
            found_type,
            view_label="VIEW 2 — TYPICAL ABUTMENT TRANSVERSE SECTION",
        )

    # ── Scale bar below View 2 ─────────────────────────────────────────────
    scale_bar(msp, _VIEW2_X0 + 6.0, _VIEW_Y0 + _VIEW_H + th * 1.5,
              scale_denom,
              segments=4, seg_len_m=max(1.0, round(overall_w / 5)),
              text_height=th * 0.85)

    # ── NTS disclaimer (FR-8: demoted, grey 8, 10% smaller) ──────────────
    text(msp, "(Not to Scale — indicative)",
         (_VIEW1_X0 + _VIEW_W / 2.0 + _VIEW2_X0 + _VIEW_W / 2.0) / 2.0,
         _VIEW_Y0 + _VIEW_H + th * 6.0,
         height=th * 0.9, layer="TEXT-SPEC", halign="CENTER", color=8)


# ── Sub-routines: two view drawers ──────────────────────────────────────────
def _draw_abutment_endface(
    msp, vhx, vvy, sc, th,
    overall_w, cw, half_ow, half_cw,
    kerb_l, kerb_r, fp_l, fp_r, cb_l, cb_r,
    deck_t_m, wc_t_m, gd_m, gs_m, n_girders, par_h_m,
    abt_w_m, abt_h_m, abt_len_m, ret_w_m,
    wing_splay_m, wing_h_m,
    app_l_m, app_t_m, ped_h_m,
    pile_dia_m, pile_len_m, pile_sp_m, piles_n, pile_cap_t_m,
    pile_cut_rl, pile_tip_rl,
    tod_rl, sof_rl, road_rl_approach, abt_base_rl, hfl_rl, scour_rl,
    found_type,
    view_label,
):
    """Draw a single abutment end-face view at the given coordinate origin."""

    # ── Header label (view title) ──────────────────────────────────────────
    hdr_y = vvy(tod_rl + par_h_m + 0.55)
    text(msp, view_label, vhx(0.0), hdr_y,
         height=th * 1.45, layer="TEXT-HEADER", halign="CENTER")

    # ── Parapets ───────────────────────────────────────────────────────────
    max(cb_l, 0.25)
    for side, sign, par_w_actual in [("L", -1, max(cb_l, 0.25)),
                                       ("R", +1, max(cb_r, 0.25))]:
        xp = vhx(sign * (half_cw + kerb_l + fp_l if sign == -1 else
                          half_cw + kerb_r + fp_r))
        if sign == -1:
            xp = vhx(-half_ow + par_w_actual) - par_w_actual * sc
        else:
            xp = vhx(half_ow)
        y_base = vvy(tod_rl)
        y_top  = vvy(tod_rl - par_h_m)
        rectangle(msp, xp, y_top, par_w_actual * sc, (y_base - y_top),
                  layer="SUPER-PARAPET", lw=40)
        hatch_rect(msp, xp, y_top, par_w_actual * sc, (y_base - y_top),
                   pattern="ANSI31", scale=sc * 0.012, layer="STRUC-HATCHING")

    # ── Footpaths (if present) ─────────────────────────────────────────────
    for sign, fp_w, cb_w, kerb_w, idx in [
        (-1, fp_l, cb_l, kerb_l, 0),
        (+1, fp_r, cb_r, kerb_r, 1),
    ]:
        if fp_w <= 0:
            continue
        fp_x_start = sign * (half_cw + kerb_w)
        fp_x_end   = fp_x_start + sign * fp_w
        x1 = vhx(min(fp_x_start, fp_x_end))
        x2 = vhx(max(fp_x_start, fp_x_end))
        y_fp_top = vvy(tod_rl - wc_t_m - deck_t_m * 0.15)
        y_fp_bot = vvy(tod_rl - wc_t_m)
        rectangle(msp, x1, y_fp_top, x2 - x1, y_fp_bot - y_fp_top,
                  layer="SUPER-FOOTPATH", lw=25)

    # ── Kerbs ──────────────────────────────────────────────────────────────
    kerb_h_sc = 0.22 * sc
    # Left kerb
    xs_outer_L = -(half_cw + kerb_l)
    xs_inner_L = -half_cw
    kerb_pts_L = [
        (vhx(xs_inner_L), vvy(tod_rl)),
        (vhx(xs_outer_L), vvy(tod_rl)),
        (vhx(xs_outer_L), vvy(tod_rl) + kerb_h_sc),
        (vhx(-(half_cw + kerb_l * 0.7)), vvy(tod_rl) + kerb_h_sc + kerb_h_sc * 0.4),
        (vhx(xs_inner_L), vvy(tod_rl) + kerb_h_sc * 0.6),
    ]
    polyline(msp, kerb_pts_L, layer="SUPER-KERB", close=True, lw=35)
    hatch_poly(msp, kerb_pts_L, pattern="ANSI31",
               scale=sc * 0.014, layer="STRUC-HATCHING")
    # Right kerb
    xs_outer_R = (half_cw + kerb_r)
    xs_inner_R = half_cw
    kerb_pts_R = [
        (vhx(xs_inner_R), vvy(tod_rl)),
        (vhx(xs_outer_R), vvy(tod_rl)),
        (vhx(xs_outer_R), vvy(tod_rl) + kerb_h_sc),
        (vhx(half_cw + kerb_r * 0.7), vvy(tod_rl) + kerb_h_sc + kerb_h_sc * 0.4),
        (vhx(xs_inner_R), vvy(tod_rl) + kerb_h_sc * 0.6),
    ]
    polyline(msp, kerb_pts_R, layer="SUPER-KERB", close=True, lw=35)
    hatch_poly(msp, kerb_pts_R, pattern="ANSI31",
               scale=sc * 0.014, layer="STRUC-HATCHING")

    # ── Wearing coat ───────────────────────────────────────────────────────
    wc_y_top = vvy(tod_rl)
    wc_y_bot = vvy(tod_rl - wc_t_m)
    x1_cw = vhx(-half_cw)
    x2_cw = vhx( half_cw)
    hatch_rect(msp, x1_cw, wc_y_bot, x2_cw - x1_cw, wc_y_top - wc_y_bot,
               pattern="AR-SAND", scale=sc * 0.004,
               layer="SUPER-WEARING", color=8)
    rectangle(msp, x1_cw, wc_y_bot, x2_cw - x1_cw, wc_y_top - wc_y_bot,
              layer="SUPER-WEARING")

    # ── Deck slab ──────────────────────────────────────────────────────────
    deck_y_top = wc_y_bot
    deck_y_bot = vvy(tod_rl - wc_t_m - deck_t_m)
    x1_ow = vhx(-half_ow)
    x2_ow = vhx( half_ow)
    rectangle(msp, x1_ow, deck_y_bot, x2_ow - x1_ow, deck_y_top - deck_y_bot,
              layer="SUPER-DECK", lw=50)
    hatch_rect(msp, x1_ow, deck_y_bot, x2_ow - x1_ow, deck_y_top - deck_y_bot,
               pattern="ANSI31", scale=sc * 0.02, layer="STRUC-HATCHING")

    # ── Girders (elevation — dashed hidden-line beneath deck) ──────────────
    if gd_m > 0:
        gir_bot_y = vvy(sof_rl)
        g_cents = [(i - (n_girders - 1) / 2.0) * gs_m for i in range(n_girders)]
        # Just show webs as dashed lines on STRUC-HIDDEN
        for gx in g_cents:
            line(msp, (vhx(gx), deck_y_bot), (vhx(gx), gir_bot_y),
                 layer="STRUC-HIDDEN", linetype="HIDDEN", color=8)
        # Girder soffit line (hidden)
        line(msp, (vhx(g_cents[0] - gs_m / 2), gir_bot_y),
                  (vhx(g_cents[-1] + gs_m / 2), gir_bot_y),
             layer="STRUC-HIDDEN", linetype="HIDDEN", color=8)

    # ── Bearing pads (below deck / abutment seat) ──────────────────────────
    bearing_w_m = 0.40
    bearing_t_m = ped_h_m * 0.4
    brg_y_top = vvy(sof_rl + ped_h_m * 0.0)   # bearing sits on abutment cap seat
    brg_y_bot = vvy(sof_rl - bearing_t_m)
    for off_sign in (-1, +1):
        bx = vhx(off_sign * (abt_len_m * 0.40)) - bearing_w_m * sc / 2.0
        rectangle(msp, bx, brg_y_bot, bearing_w_m * sc, brg_y_top - brg_y_bot,
                  layer="SUB-BEARING", lw=30)

    # ── Abutment shaft (thick transverse wall) ─────────────────────────────
    abt_shaft_y_top = vvy(sof_rl - ped_h_m)
    abt_shaft_y_bot = vvy(abt_base_rl)
    shaft_half_w_m = min(overall_w * 0.46, abt_len_m * 0.5)
    sa_x1 = vhx(-shaft_half_w_m)
    sa_x2 = vhx( shaft_half_w_m)
    rectangle(msp, sa_x1, abt_shaft_y_bot, sa_x2 - sa_x1,
              abt_shaft_y_top - abt_shaft_y_bot,
              layer="SUB-ABUT", lw=50)
    hatch_rect(msp, sa_x1, abt_shaft_y_bot, sa_x2 - sa_x1,
               abt_shaft_y_top - abt_shaft_y_bot,
               pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")

    # Pedestal strip between bearing seat level and shaft top
    line(msp, (vhx(-shaft_half_w_m * 0.8), vvy(sof_rl)),
              (vhx( shaft_half_w_m * 0.8), vvy(sof_rl)),
         layer="SUB-ABUT", lw=40)

    # ── Return walls L / R ─────────────────────────────────────────────────
    for sign in (-1, +1):
        rw_x_start = vhx(sign * shaft_half_w_m)
        rw_x_end   = vhx(sign * (shaft_half_w_m + ret_w_m))
        x1r = min(rw_x_start, rw_x_end)
        x2r = max(rw_x_start, rw_x_end)
        rw_top_y = vvy(sof_rl - ped_h_m - abt_h_m * 0.05)
        rectangle(msp, x1r, abt_shaft_y_bot * 0.92 + 0.08 * rw_top_y,
                  x2r - x1r, rw_top_y - abt_shaft_y_bot * 0.92 - 0.08 * rw_top_y,
                  layer="SUB-ABUT", lw=40)
        hatch_rect(msp, x1r, abt_shaft_y_bot * 0.92 + 0.08 * rw_top_y,
                   x2r - x1r, rw_top_y - abt_shaft_y_bot * 0.92 - 0.08 * rw_top_y,
                   pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")
        text(msp, f"RETURN WALL {ret_w_m:.1f}m",
             (x1r + x2r) / 2.0, abt_shaft_y_bot * 0.92 + 0.08 * rw_top_y - th * 1.5,
             height=th * 0.75, layer="TEXT-GENERAL", halign="CENTER", color=3)

    # ── Wing wall splay (dashed lines, view indicator) ────────────────────
    for sign in (-1, +1):
        start = (vhx(sign * shaft_half_w_m), vvy(sof_rl - ped_h_m))
        end   = (vhx(sign * (shaft_half_w_m + wing_splay_m)),
                 vvy(abt_base_rl + (sof_rl - ped_h_m - abt_base_rl) * (1.0 - wing_h_m / abt_h_m)))
        line(msp, start, end, layer="SUB-ABUT", color=3, linetype="DASHED")
        text(msp, f"WW SPLAY {wing_splay_m:.1f}m",
             end[0] + sign * th, end[1] - th * 0.5,
             height=th * 0.7, layer="TEXT-SPEC", color=3,
             halign="LEFT" if sign == +1 else "RIGHT")

    # ── Approach slab (partial hatch — road side) ──────────────────────────
    if app_l_m > 0 and app_t_m > 0:
        as_x_left  = vhx(-half_ow - app_l_m * 0.55)
        as_x_right = vhx(-half_ow)
        as_y_top   = vvy(road_rl_approach)
        as_y_bot   = vvy(road_rl_approach - app_t_m)
        rectangle(msp, as_x_left, as_y_bot,
                  as_x_right - as_x_left, as_y_top - as_y_bot,
                  layer="CIVIL-ROAD", lw=25)
        hatch_rect(msp, as_x_left, as_y_bot,
                   as_x_right - as_x_left, as_y_top - as_y_bot,
                   pattern="ANSI31", scale=sc * 0.025, layer="STRUC-HATCHING",
                   color=7)
        level_tag(msp, as_x_left - th * 2, as_y_top, road_rl_approach,
                  text_height=th * 0.85)
        text(msp, f"APPROACH SLAB  {app_l_m:.1f}×{app_t_m*1000:.0f}mm",
             (as_x_left + as_x_right) / 2.0, as_y_bot - th * 1.5,
             height=th * 0.75, layer="TEXT-GENERAL", halign="CENTER")

    # ── Pile cap + piles (if PILE foundation) ─────────────────────────────
    if "PILE" in found_type:
        cap_top_y = vvy(pile_cut_rl + pile_cap_t_m)
        cap_bot_y = vvy(pile_cut_rl)
        cap_x1    = vhx(-shaft_half_w_m - 0.20)
        cap_x2    = vhx( shaft_half_w_m + 0.20)
        rectangle(msp, cap_x1, cap_bot_y, cap_x2 - cap_x1, cap_top_y - cap_bot_y,
                  layer="FOUND-CAP", lw=40)
        hatch_rect(msp, cap_x1, cap_bot_y, cap_x2 - cap_x1, cap_top_y - cap_bot_y,
                   pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")

        piles_cols = max(2, min(piles_n, 6))
        spacing_m = pile_sp_m
        pile_r = pile_dia_m / 2.0
        for idx in range(piles_cols):
            offset_m = (idx - (piles_cols - 1) / 2.0) * spacing_m
            pcx = vhx(offset_m)
            # Pile top circle (cutoff)
            circle(msp, pcx, cap_bot_y, pile_r * sc, layer="FOUND-PILE", color=4)
            # Pile shaft vertical line
            line(msp, (pcx, cap_bot_y), (pcx, vvy(pile_tip_rl)),
                 layer="FOUND-PILE", lw=35, color=4)
            # Pile tip tick
            line(msp, (pcx - pile_r * sc, vvy(pile_tip_rl)),
                      (pcx + pile_r * sc, vvy(pile_tip_rl)),
                 layer="FOUND-PILE", lw=35, color=4)

        pile_label = (f"{pile_dia_m*1000:.0f} Ø BORED PILE  "
                      f"/ {piles_cols} NOS  c/c {spacing_m:.2f}m")
        text(msp, pile_label, vhx(0.0),
             vvy(pile_tip_rl) - th * 2.0,
             height=th * 0.85, layer="TEXT-GENERAL", halign="CENTER")

    # ── RL level tags (left side of view 1) ────────────────────────────────
    tag_x_left = vhx(-half_ow - ret_w_m - app_l_m * 0.4 - th * 5.5)
    levels = [
        ("TOP OF DECK / FORMATION",     tod_rl),
        ("SOFFIT OF DECK",              sof_rl),
        ("BEARING SEAT",                sof_rl - ped_h_m * 0.6),
        ("TOP OF ABUTMENT / PILE CAP",  abt_base_rl if "PILE" not in found_type else (pile_cut_rl + pile_cap_t_m)),
        ("ABUTMENT BASE / FOOTING",     abt_base_rl),
    ]
    if "PILE" in found_type:
        levels += [
            ("PILE CUT-OFF RL",            pile_cut_rl),
            ("PILE TIP RL",                pile_tip_rl),
        ]
    drawn = set()
    for label, rl in levels:
        if round(rl, 2) in drawn:
            continue
        drawn.add(round(rl, 2))
        yy = vvy(rl)
        if not (_VIEW_Y0 + 2 < yy < _VIEW_Y0 + _VIEW_H - 2):
            continue
        # tick to abutment
        line(msp, (tag_x_left, yy), (vhx(-shaft_half_w_m - 0.1), yy),
             layer="DIM-LEVEL", color=5)
        level_tag(msp, tag_x_left, yy, rl, text_height=th * 0.85)
        text(msp, label, tag_x_left + th * 8, yy - th * 0.5,
             height=th * 0.75, layer="TEXT-LEVEL")

    # ── Width dimension strings ───────────────────────────────────────────
    dim_y_par = vvy(tod_rl - wc_t_m - deck_t_m - gd_m * 0.05) - th * 2.0
    # Parapet-to-parapet (overall width)
    dim_linear_h(msp, vhx(-half_ow), dim_y_par + th,
                 vhx( half_ow), dim_y_par + th,
                 dim_y=dim_y_par,
                 label=f"P-P = {overall_w:.3f} m",
                 text_height=th * 0.9)
    # Carriageway
    dim_y_cw = dim_y_par - th * 3.5
    dim_linear_h(msp, vhx(-half_cw), dim_y_cw + th * 0.5,
                 vhx( half_cw), dim_y_cw + th * 0.5,
                 dim_y=dim_y_cw,
                 label=f"CW = {cw:.3f} m",
                 text_height=th * 0.9)
    # Bearing centres
    bc_sep = abt_len_m * 0.80
    dim_y_bc = vvy(sof_rl - ped_h_m - bearing_t_m) + th * 2.5
    dim_linear_h(msp,
                 vhx(-bc_sep / 2), dim_y_bc,
                 vhx( bc_sep / 2), dim_y_bc,
                 dim_y=dim_y_bc + th * 0.5,
                 label=f"BRG c/c {bc_sep:.2f} m",
                 text_height=th * 0.8)

    # ── HFL line (if within viewport) ──────────────────────────────────────
    if _VIEW_Y0 < vvy(hfl_rl) < _VIEW_Y0 + _VIEW_H:
        y_hfl = vvy(hfl_rl)
        line(msp, (vhx(-half_ow - ret_w_m * 1.2), y_hfl),
                  (vhx( half_ow + ret_w_m * 1.2), y_hfl),
             layer="CIVIL-HFL", color=5, linetype="DASHED")
        text(msp, f"HFL RL {hfl_rl:.3f}",
             vhx(-half_ow - ret_w_m), y_hfl - th * 0.7,
             height=th * 0.75, layer="CIVIL-HFL", color=5)

    # ── Scour line ─────────────────────────────────────────────────────────
    if _VIEW_Y0 < vvy(scour_rl) < _VIEW_Y0 + _VIEW_H:
        y_sc = vvy(scour_rl)
        line(msp, (vhx(-half_ow - ret_w_m * 1.2), y_sc),
                  (vhx( half_ow + ret_w_m * 1.2), y_sc),
             layer="CIVIL-SCOUR", color=1, linetype="DASHED2")
        text(msp, f"SCOUR RL {scour_rl:.3f}",
             vhx( half_ow + ret_w_m), y_sc - th * 0.7,
             height=th * 0.75, layer="CIVIL-SCOUR", color=1)


def _draw_pier_transverse(
    msp, vhx, vvy, sc, th,
    overall_w, cw, half_ow, half_cw,
    kerb_l, kerb_r, fp_l, fp_r, cb_l, cb_r,
    deck_t_m, wc_t_m, gd_m, gs_m, n_girders, par_h_m,
    pier_cap_w_m, pier_cap_d_m, pier_shaft_w_m, pier_shaft_l_m,
    pier_ped_h_m,
    pile_dia_m, pile_len_m, pile_sp_m, piles_n, pile_cap_t_m,
    pile_cut_rl, pile_tip_rl,
    tod_rl, sof_rl, hfl_rl, scour_rl,
    found_type,
    view_label,
):
    """Pier transverse cut (Section B-B): deck + girder + bearings + cap + shaft + piles."""

    # ── Header label ───────────────────────────────────────────────────────
    hdr_y = vvy(tod_rl + par_h_m + 0.55)
    text(msp, view_label, vhx(0.0), hdr_y,
         height=th * 1.45, layer="TEXT-HEADER", halign="CENTER")

    # ── Parapets ───────────────────────────────────────────────────────────
    for side_sign, par_w in [(-1, max(cb_l, 0.25)), (+1, max(cb_r, 0.25))]:
        xp = vhx(-half_ow) if side_sign == -1 else vhx(half_ow - par_w * sc)
        if side_sign == +1:
            xp = vhx(half_ow) - par_w * sc
        y_base = vvy(tod_rl)
        y_top  = vvy(tod_rl - par_h_m)
        rectangle(msp, xp, y_top, par_w * sc, (y_base - y_top),
                  layer="SUPER-PARAPET", lw=40)
        hatch_rect(msp, xp, y_top, par_w * sc, (y_base - y_top),
                   pattern="ANSI31", scale=sc * 0.012, layer="STRUC-HATCHING")

    # ── Kerbs ──────────────────────────────────────────────────────────────
    kerb_h_sc = 0.22 * sc
    for side_sign, kw in [(-1, kerb_l), (+1, kerb_r)]:
        xs_outer = -(half_cw + kw) if side_sign == -1 else (half_cw + kw)
        xs_inner = -half_cw if side_sign == -1 else half_cw
        kerb_pts = [
            (vhx(xs_inner), vvy(tod_rl)),
            (vhx(xs_outer), vvy(tod_rl)),
            (vhx(xs_outer), vvy(tod_rl) + kerb_h_sc),
            (vhx(xs_outer - side_sign * kw * 0.3), vvy(tod_rl) + kerb_h_sc + kerb_h_sc * 0.4),
            (vhx(xs_inner), vvy(tod_rl) + kerb_h_sc * 0.6),
        ]
        polyline(msp, kerb_pts, layer="SUPER-KERB", close=True, lw=35)
        hatch_poly(msp, kerb_pts, pattern="ANSI31",
                   scale=sc * 0.014, layer="STRUC-HATCHING")

    # ── Wearing coat + Deck slab ─────────────────────────────────────────
    wc_y_top = vvy(tod_rl)
    wc_y_bot = vvy(tod_rl - wc_t_m)
    hatch_rect(msp, vhx(-half_cw), wc_y_bot,
               vhx(half_cw) - vhx(-half_cw), wc_y_top - wc_y_bot,
               pattern="AR-SAND", scale=sc * 0.004,
               layer="SUPER-WEARING", color=8)
    deck_y_top = wc_y_bot
    deck_y_bot = vvy(tod_rl - wc_t_m - deck_t_m)
    x1_ow = vhx(-half_ow)
    x2_ow = vhx( half_ow)
    rectangle(msp, x1_ow, deck_y_bot, x2_ow - x1_ow, deck_y_top - deck_y_bot,
              layer="SUPER-DECK", lw=50)
    hatch_rect(msp, x1_ow, deck_y_bot, x2_ow - x1_ow, deck_y_top - deck_y_bot,
               pattern="ANSI31", scale=sc * 0.02, layer="STRUC-HATCHING")

    # ── Girders (transverse — I/box outline) ──────────────────────────────
    gir_top = deck_y_bot
    gir_bot = vvy(sof_rl)
    if gd_m > 0 and n_girders >= 2:
        g_cents = [(i - (n_girders - 1) / 2.0) * gs_m for i in range(n_girders)]
        for gx in g_cents:
            # Simple I girder: top flange, web, bottom flange rectangles
            tf_half = 0.28 * gs_m
            web_th   = max(0.20, 0.08 * gd_m)
            tf_h     = 0.12 * gd_m
            bf_h     = 0.12 * gd_m
            pts = [
                (vhx(gx - tf_half), gir_top),
                (vhx(gx + tf_half), gir_top),
                (vhx(gx + tf_half), gir_top - tf_h * sc),
                (vhx(gx + web_th / 2), gir_top - tf_h * sc),
                (vhx(gx + web_th / 2), gir_bot + bf_h * sc),
                (vhx(gx + tf_half * 0.7), gir_bot + bf_h * sc),
                (vhx(gx + tf_half * 0.7), gir_bot),
                (vhx(gx - tf_half * 0.7), gir_bot),
                (vhx(gx - tf_half * 0.7), gir_bot + bf_h * sc),
                (vhx(gx - web_th / 2), gir_bot + bf_h * sc),
                (vhx(gx - web_th / 2), gir_top - tf_h * sc),
                (vhx(gx - tf_half), gir_top - tf_h * sc),
            ]
            polyline(msp, pts, layer="SUPER-GIRDER", close=True, lw=40)
            hatch_poly(msp, pts, pattern="ANSI31",
                       scale=sc * 0.016, layer="STRUC-HATCHING")

    # ── Bearing pads ──────────────────────────────────────────────────────
    brg_w_m = 0.40
    brg_t_m = pier_ped_h_m * 0.55
    brg_y_bot = vvy(sof_rl - brg_t_m)
    for sign in (-1, +1):
        off = pier_shaft_l_m * 0.40
        bx = vhx(sign * off) - brg_w_m * sc / 2.0
        rectangle(msp, bx, brg_y_bot, brg_w_m * sc,
                  vvy(sof_rl) - brg_y_bot,
                  layer="SUB-BEARING", lw=30)

    # ── Pedestal ──────────────────────────────────────────────────────────
    ped_y_top = vvy(sof_rl)
    ped_y_bot = vvy(sof_rl - pier_ped_h_m)
    ped_half = pier_shaft_l_m * 0.42
    rectangle(msp, vhx(-ped_half), ped_y_bot,
              vhx(ped_half) - vhx(-ped_half), ped_y_top - ped_y_bot,
              layer="SUB-PIER", lw=30)

    # ── Pier cap ──────────────────────────────────────────────────────────
    cap_y_top = ped_y_bot
    cap_y_bot = vvy(sof_rl - pier_ped_h_m - pier_cap_d_m)
    pier_cap_w_m / 2.0
    cap_half_l = pier_shaft_l_m / 2.0
    rectangle(msp, vhx(-cap_half_l), cap_y_bot,
              vhx(cap_half_l) - vhx(-cap_half_l), cap_y_top - cap_y_bot,
              layer="SUB-PIER", lw=50)
    hatch_rect(msp, vhx(-cap_half_l), cap_y_bot,
               vhx(cap_half_l) - vhx(-cap_half_l), cap_y_top - cap_y_bot,
               pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")
    level_tag(msp, vhx(-cap_half_l) - th * 3, cap_y_top,
              sof_rl - pier_ped_h_m, text_height=th * 0.85)
    text(msp, "T.O.C. (TOP OF PIER CAP)",
         vhx(-cap_half_l) - th * 3 + th * 9, cap_y_top - th * 0.4,
         height=th * 0.8, layer="TEXT-HEADER")

    # ── Pier shaft ────────────────────────────────────────────────────────
    shaft_y_top = cap_y_bot
    shaft_y_bot = vvy(pile_cut_rl + pile_cap_t_m) if "PILE" in found_type else (
                  cap_y_bot - 6.0 * sc)
    sh_half_w_l = pier_shaft_l_m / 2.0
    rectangle(msp, vhx(-sh_half_w_l), shaft_y_bot,
              vhx(sh_half_w_l) - vhx(-sh_half_w_l), shaft_y_top - shaft_y_bot,
              layer="SUB-PIER", lw=50)
    hatch_rect(msp, vhx(-sh_half_w_l), shaft_y_bot,
               vhx(sh_half_w_l) - vhx(-sh_half_w_l), shaft_y_top - shaft_y_bot,
               pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING", color=8)

    # ── Pile cap + piles ──────────────────────────────────────────────────
    if "PILE" in found_type:
        pcap_top = shaft_y_bot
        pcap_bot = vvy(pile_cut_rl)
        pcap_half_l = pier_shaft_l_m / 2.0 + 0.15
        rectangle(msp, vhx(-pcap_half_l), pcap_bot,
                  vhx(pcap_half_l) - vhx(-pcap_half_l), pcap_top - pcap_bot,
                  layer="FOUND-CAP", lw=40)
        hatch_rect(msp, vhx(-pcap_half_l), pcap_bot,
                   vhx(pcap_half_l) - vhx(-pcap_half_l), pcap_top - pcap_bot,
                   pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")

        piles_cols = max(2, min(piles_n, 6))
        pile_r = pile_dia_m / 2.0
        for idx in range(piles_cols):
            off = (idx - (piles_cols - 1) / 2.0) * pile_sp_m
            pcx = vhx(off)
            circle(msp, pcx, pcap_bot, pile_r * sc, layer="FOUND-PILE", color=4)
            line(msp, (pcx, pcap_bot), (pcx, vvy(pile_tip_rl)),
                 layer="FOUND-PILE", lw=35, color=4)
            line(msp, (pcx - pile_r * sc, vvy(pile_tip_rl)),
                      (pcx + pile_r * sc, vvy(pile_tip_rl)),
                 layer="FOUND-PILE", lw=35, color=4)

        label = (f"{pile_dia_m*1000:.0f} Ø BORED PILE / "
                 f"{piles_cols} NOS  c/c {pile_sp_m:.2f}m")
        text(msp, label, vhx(0.0), vvy(pile_tip_rl) - th * 2.0,
             height=th * 0.85, layer="TEXT-GENERAL", halign="CENTER")

    # ── RL level tags (right side of pier view) ────────────────────────────
    tag_x = vhx(sh_half_w_l) + th * 12.0
    levels = [
        ("T.O.D. / FORMATION RL",    tod_rl),
        ("SOFFIT RL",                sof_rl),
        ("TOP OF PIER CAP RL",       sof_rl - pier_ped_h_m),
        ("BASE OF PIER SHAFT",       shaft_y_bot if shaft_y_bot else pile_cut_rl),
    ]
    if "PILE" in found_type:
        levels += [
            ("PILE CUT-OFF RL",        pile_cut_rl),
            ("PILE TIP RL",            pile_tip_rl),
        ]
    drawn = set()
    for label, rl in levels:
        if round(rl, 2) in drawn:
            continue
        drawn.add(round(rl, 2))
        yy = vvy(rl) if rl > 50 else rl   # if not RL (rare) use as mm
        if not (_VIEW_Y0 + 2 < yy < _VIEW_Y0 + _VIEW_H - 2):
            continue
        # try to find the right x-tick point on structure
        tick_end = vhx(sh_half_w_l + 0.2)
        line(msp, (tag_x, yy), (tick_end, yy),
             layer="DIM-LEVEL", color=5)
        level_tag(msp, tag_x, yy, rl, text_height=th * 0.85)
        text(msp, label, tag_x + th * 8, yy - th * 0.5,
             height=th * 0.75, layer="TEXT-LEVEL")

    # ── Width dims (carriageway + overall) ────────────────────────────────
    dim_base_y = gir_bot - th * 1.5
    dim_linear_h(msp, vhx(-half_cw), dim_base_y,
                 vhx( half_cw), dim_base_y,
                 dim_y=dim_base_y + th * 1.5,
                 label=f"CW = {cw:.3f} m", text_height=th * 0.9)
    dim_y2 = dim_base_y - th * 3.5
    dim_linear_h(msp, vhx(-half_ow), dim_y2,
                 vhx( half_ow), dim_y2,
                 dim_y=dim_y2 + th * 1.5,
                 label=f"OW = {overall_w:.3f} m", text_height=th * 0.9)

    # ── HFL line ──────────────────────────────────────────────────────────
    if _VIEW_Y0 < vvy(hfl_rl) < _VIEW_Y0 + _VIEW_H:
        y_hfl = vvy(hfl_rl)
        line(msp, (vhx(-half_ow - 1.5), y_hfl), (vhx(half_ow + 1.5), y_hfl),
             layer="CIVIL-HFL", color=5, linetype="DASHED")
        text(msp, f"HFL RL {hfl_rl:.3f}", vhx(-half_ow - 1.5), y_hfl - th * 0.7,
             height=th * 0.75, layer="CIVIL-HFL", color=5)
    if _VIEW_Y0 < vvy(scour_rl) < _VIEW_Y0 + _VIEW_H:
        y_sc = vvy(scour_rl)
        line(msp, (vhx(-half_ow - 1.5), y_sc), (vhx(half_ow + 1.5), y_sc),
             layer="CIVIL-SCOUR", color=1, linetype="DASHED2")
        text(msp, f"SCOUR RL {scour_rl:.3f}", vhx(half_ow + 1.5), y_sc - th * 0.7,
             height=th * 0.75, layer="CIVIL-SCOUR", color=1)


__all__ = ["generate"]
