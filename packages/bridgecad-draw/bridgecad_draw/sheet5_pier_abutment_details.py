"""
bridgecad_draw.sheet5_pier_abutment_details — Sheet 5: Pier & Abutment Details.

Left half: Pier elevation + cross-section
Right half: Abutment elevation + cross-section + wing wall
Bottom: Pedestal / bearing seat details
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dxf_engine import new_sheet, save
from .primitives import (
    circle,
    dim_along,
    hatch_poly,
    hatch_rect,
    line,
    polyline,
    rectangle,
    text,
)
from .titleblocks import draw_border, draw_title_block


def _family_for(abutment_type: Any) -> str:
    """Shape family for an AbutmentType. Source: abutment_profiles."""
    from bridgecad_core.geometry.abutment_profiles import family_for

    return family_for(abutment_type)


def generate(project: Any, output_path: str | Path, scale_denom: int = 50) -> Path:
    doc, msp = new_sheet("S5 Pier Abutment Details")
    _draw(msp, project, scale_denom)
    return save(doc, output_path)


def _draw(msp: Any, project: Any, scale_denom: int = 50) -> None:
    from bridgecad_core.abutment_stack import resolve_abutment_stack

    sub = project.substructure
    hd = project.hydraulic_data
    pm = project.project_master
    stack = resolve_abutment_stack(project)

    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-005") or "GAD-005",
        drawing_title="PIER AND ABUTMENT DETAILS",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        sheet_no="5",
        total_sheets="8",
    )

    sc = 12.0  # mm per metre
    th = 2.5

    # ══════════════════════════════════════════════════════════════════════
    # PIER ELEVATION (left, upper)
    # ══════════════════════════════════════════════════════════════════════
    pier_cx = 140.0
    pier_by = 250.0
    pier_h = float(sub.pier_height_typical_m or 8.0)
    pier_sw = float(sub.pier_shaft_width_m or 1.5)
    pier_sl = float(sub.pier_shaft_length_m or 11.5)
    cap_w = float(sub.pier_cap_width_m or 2.0)
    cap_d = float(sub.pier_cap_depth_m or 0.8)
    ped_h = float(sub.pier_pedestal_height_m or 0.2)

    pier_h_mm = pier_h * sc
    pier_sw_mm = pier_sw * sc
    pier_sl_mm = pier_sl * sc
    cap_d_mm = cap_d * sc
    cap_w_mm = cap_w * sc
    ped_h_mm = ped_h * sc

    # Pier shaft (front elevation — width dimension shown)
    rectangle(
        msp, pier_cx - pier_sw_mm / 2, pier_by, pier_sw_mm, pier_h_mm, layer="SUB-PIER", lw=50
    )
    hatch_rect(
        msp,
        pier_cx - pier_sw_mm / 2,
        pier_by,
        pier_sw_mm,
        pier_h_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )

    # Pier cap
    cap_bot_y = pier_by + pier_h_mm
    rectangle(msp, pier_cx - cap_w_mm / 2, cap_bot_y, cap_w_mm, cap_d_mm, layer="SUB-PIER", lw=50)
    hatch_rect(
        msp,
        pier_cx - cap_w_mm / 2,
        cap_bot_y,
        cap_w_mm,
        cap_d_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )

    # Pedestal + bearing pad on the cap
    ped_w = pier_sw_mm * 0.7
    rectangle(
        msp, pier_cx - ped_w / 2, cap_bot_y + cap_d_mm, ped_w, ped_h_mm, layer="SUB-PIER", lw=30
    )
    rectangle(
        msp,
        pier_cx - ped_w / 2 - sc * 0.05,
        cap_bot_y + cap_d_mm + ped_h_mm,
        ped_w + sc * 0.1,
        sc * 0.06,
        layer="SUB-BEARING",
        lw=15,
    )

    # Dimensions — axis-checked against the pier_elevation view spec
    from .contract import view_spec

    _pier_elev = view_spec("pier_elevation")
    dim_along(
        _pier_elev,
        (pier_cx - cap_w_mm / 2, pier_by - th * 5),
        (pier_cx + cap_w_mm / 2, pier_by - th * 5),
        "TRANSVERSE",
        msp=msp,
        dim_y=pier_by - th * 5,
        label=f"Cap={cap_w:.2f}m",
        text_height=th,
    )
    dim_along(
        _pier_elev,
        (pier_cx + cap_w_mm / 2 + th * 3, pier_by),
        (pier_cx + cap_w_mm / 2 + th * 3, cap_bot_y),
        "VERTICAL",
        msp=msp,
        dim_x=pier_cx + cap_w_mm / 2 + th * 9,
        label=f"H={pier_h:.2f}m",
        text_height=th,
    )
    dim_along(
        _pier_elev,
        (pier_cx - pier_sw_mm / 2, pier_by + pier_h_mm / 2),
        (pier_cx + pier_sw_mm / 2, pier_by + pier_h_mm / 2),
        "TRANSVERSE",
        msp=msp,
        dim_y=pier_by + pier_h_mm / 2 - th * 4,
        label=f"Shaft={pier_sw:.2f}m",
        text_height=th * 0.85,
    )

    # HFL line on pier
    hfl_rl = float(hd.hfl_m or 0)
    gnd_rl = float(getattr(pm, "ground_level_rl_m", hfl_rl - pier_h * 0.3) or 0)
    hfl_y_on_pier = pier_by + (hfl_rl - gnd_rl) * sc
    if 0 < hfl_y_on_pier < pier_by + pier_h_mm:
        line(
            msp,
            (pier_cx - cap_w_mm / 2 - th * 5, hfl_y_on_pier),
            (pier_cx + cap_w_mm / 2 + th * 5, hfl_y_on_pier),
            layer="CIVIL-HFL",
            color=5,
        )
        text(
            msp,
            f"HFL RL {hfl_rl:.3f}",
            pier_cx + cap_w_mm / 2 + th * 6,
            hfl_y_on_pier,
            height=th * 0.85,
            layer="CIVIL-HFL",
            color=5,
        )

    text(
        msp,
        "PIER ELEVATION",
        pier_cx,
        cap_bot_y + cap_d_mm + ped_h_mm + th * 4,
        height=th * 1.3,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    text(
        msp,
        f"Scale 1:{scale_denom}",
        pier_cx,
        cap_bot_y + cap_d_mm + ped_h_mm + th * 7,
        height=th,
        layer="TEXT-SPEC",
        halign="CENTER",
    )

    # ══════════════════════════════════════════════════════════════════════
    # PIER SECTION (left, lower) — plan through the shaft
    # ══════════════════════════════════════════════════════════════════════
    psec_cx = 140.0
    psec_by = 120.0
    rectangle(
        msp, psec_cx - pier_sl_mm / 2, psec_by, pier_sl_mm, pier_sw_mm, layer="SUB-PIER", lw=40
    )
    hatch_rect(
        msp,
        psec_cx - pier_sl_mm / 2,
        psec_by,
        pier_sl_mm,
        pier_sw_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )
    _pier_sec = view_spec("pier_section")
    dim_along(
        _pier_sec,
        (psec_cx - pier_sl_mm / 2, psec_by - th * 4),
        (psec_cx + pier_sl_mm / 2, psec_by - th * 4),
        "TRANSVERSE",
        msp=msp,
        dim_y=psec_by - th * 4,
        label=f"L={pier_sl:.2f}m",
        text_height=th * 0.85,
    )
    dim_along(
        _pier_sec,
        (psec_cx + pier_sl_mm / 2 + th * 3, psec_by),
        (psec_cx + pier_sl_mm / 2 + th * 3, psec_by + pier_sw_mm),
        "LONGITUDINAL",
        msp=msp,
        dim_x=psec_cx + pier_sl_mm / 2 + th * 9,
        label=f"THK={pier_sw:.2f}m",
        text_height=th * 0.85,
    )
    text(
        msp,
        "PIER SECTION",
        psec_cx,
        psec_by + pier_sw_mm + th * 3.5,
        height=th * 1.2,
        layer="TEXT-HEADER",
        halign="CENTER",
    )

    # ══════════════════════════════════════════════════════════════════════
    # Abutment parameters (resolved once — guide #1 step 3)
    # ══════════════════════════════════════════════════════════════════════
    abt_len = float(sub.abutment_length_m or 11.8)
    abt_w = float(sub.abutment_width_m or 1.2)
    abt_h = float(sub.abutment_height_m or 3.2)
    cap_ab_d = float(sub.abutment_cap_depth_mm or 600) / 1000.0
    cap_pf = float(sub.abutment_cap_projection_front_mm or 300) / 1000.0
    cap_pr = float(sub.abutment_cap_projection_rear_mm or 300) / 1000.0
    dw_t = float(sub.dirt_wall_thickness_mm or 300) / 1000.0
    dw_h = float(stack.app_bot) - float(stack.cap_top)
    weephole_d = float(sub.weep_hole_diameter_mm or 100) / 1000.0
    weephole_s = float(sub.weep_hole_spacing_m or 1.5)
    app_l = float(sub.approach_slab_length_m or 3.5)
    app_t = float(sub.approach_slab_thickness_mm or 200) / 1000.0
    ret_l = float(sub.return_wall_length_m or 4.0)
    ret_h = float(sub.return_wall_height_m or 3.0)
    ww_l = float(sub.wing_wall_splay_length_m or 3.0)
    ped_a_h = float(sub.abutment_pedestal_height_m or 0.15)
    wc_t = float(project.superstructure.wearing_coat_thickness_mm or 65) / 1000.0

    cap_ab_d_mm = cap_ab_d * sc
    ped_a_h_mm = ped_a_h * sc

    # ══════════════════════════════════════════════════════════════════════
    # ABUTMENT ELEVATION — transverse (right, upper). Width = abutment_length
    # ══════════════════════════════════════════════════════════════════════
    abt_cx = 560.0
    abt_by = 250.0
    L_mm = abt_len * sc
    # `abutment_height_m` is the TOTAL height, GL to deck soffit (models.py).
    # The cap is stacked on top of the shaft further down, so the shaft itself
    # is one cap depth shorter — otherwise this view shows an abutment a full
    # cap depth taller than the longitudinal view beside it, and the dirt-wall
    # / approach-slab / wearing-coat stack floats one cap depth too high.
    H_mm = max(abt_h - cap_ab_d, 0.2) * sc

    # ── Family-aware shaft outline (Artefact ④) ────────────────────────
    # GRAVITY → battered trapezoid; CANTILEVER → inverted-T; else rectangle.
    from bridgecad_core.geometry.abutment_profiles import elevation_outline

    _fam = _family_for(getattr(sub, "abutment_type", None))
    _norm_pts = elevation_outline(_fam)
    _shaft_pts = [(abt_cx - L_mm / 2 + nx * L_mm, abt_by + ny * H_mm) for nx, ny in _norm_pts]
    polyline(msp, _shaft_pts, layer="SUB-ABUT", close=True, lw=50)
    hatch_poly(msp, _shaft_pts, pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")

    # Cap beam across the full transverse length
    cap_el_bot = abt_by + H_mm
    rectangle(msp, abt_cx - L_mm / 2, cap_el_bot, L_mm, cap_ab_d_mm, layer="SUB-ABUT", lw=50)
    hatch_rect(
        msp,
        abt_cx - L_mm / 2,
        cap_el_bot,
        L_mm,
        cap_ab_d_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )
    cap_el_top = cap_el_bot + cap_ab_d_mm

    # Dirt wall behind the cap (dashed — retained fill face)
    line(
        msp,
        (abt_cx - L_mm / 2, cap_el_top),
        (abt_cx + L_mm / 2, cap_el_top),
        layer="ABUT-PROF",
        linetype="DASHED",
        color=4,
    )

    # Pedestals + bearings on the cap
    for i in range(3):
        px = abt_cx + (i - 1) * (L_mm * 0.35)
        pw = 0.6 * sc
        rectangle(msp, px - pw / 2, cap_el_top, pw, ped_a_h_mm, layer="SUB-BEARING", lw=25)

    # Wing walls — top falls at 1:10 from the full cap top
    for side in (-1.0, 1.0):
        x0 = abt_cx + side * L_mm / 2
        ww_pts = [
            (x0, cap_el_top),
            (x0 + side * ww_l * sc, cap_el_top - ww_l * sc / 10.0),
            (x0 + side * ww_l * sc, abt_by),
            (x0, abt_by),
        ]
        polyline(msp, ww_pts, layer="SUB-ABUT", close=True, lw=35)
        hatch_poly(msp, ww_pts, pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")

    # Rear stack, edge-on in transverse elevation: dirt wall on the cap rear
    # ledge → approach slab → continuous wearing coat.  Heights come from the
    # resolved abutment stack (dw_h / app_t / wc_t already bound above).
    dw_mm_e = dw_h * sc
    app_t_mm_e = app_t * sc
    wc_mm_e = wc_t * sc
    stack_l = L_mm * 0.96  # inset from wing-wall toes
    stack_x0 = abt_cx - stack_l / 2
    # dirt wall band (cap top → approach slab soffit)
    rectangle(msp, stack_x0, cap_el_top, stack_l, dw_mm_e, layer="ABUT-PROF", lw=30)
    hatch_rect(
        msp,
        stack_x0,
        cap_el_top,
        stack_l,
        dw_mm_e,
        pattern="ANSI31",
        scale=sc * 0.01,
        layer="STRUC-HATCHING",
    )
    # approach slab band
    rectangle(msp, stack_x0, cap_el_top + dw_mm_e, stack_l, app_t_mm_e, layer="CIVIL-ROAD", lw=25)
    # wearing coat — continuous over the approach slab
    rectangle(
        msp,
        stack_x0,
        cap_el_top + dw_mm_e + app_t_mm_e,
        stack_l,
        wc_mm_e,
        layer="SUPER-WEARING",
        lw=20,
    )
    # level tags on the stack
    text(
        msp,
        f"DW {dw_h * 1000:.0f}",
        stack_x0 + stack_l + th * 2,
        cap_el_top + dw_mm_e / 2,
        height=th * 0.8,
        layer="TEXT-SPEC",
        color=4,
    )

    # Weep holes through the dirt wall (elevation: dots on the wall face)
    for i in range(2):
        wy_e = cap_el_top + dw_mm_e * (i + 1) / 3.0
        circle(msp, abt_cx, wy_e, 0.05 * sc, layer="ABUT-PROF", color=4)

    _abt_elev = view_spec("abutment_elevation")
    dim_along(
        _abt_elev,
        (abt_cx - L_mm / 2, abt_by - th * 5),
        (abt_cx + L_mm / 2, abt_by - th * 5),
        "TRANSVERSE",
        msp=msp,
        dim_y=abt_by - th * 5,
        label=f"L={abt_len:.2f}m",
        text_height=th,
    )
    dim_along(
        _abt_elev,
        (abt_cx - L_mm / 2 - ww_l * sc, abt_by - th * 10),
        (abt_cx - L_mm / 2, abt_by - th * 10),
        "TRANSVERSE",
        msp=msp,
        dim_y=abt_by - th * 10,
        label=f"WW={ww_l:.1f}m",
        text_height=th * 0.85,
    )
    dim_along(
        _abt_elev,
        (abt_cx - L_mm / 2 - th * 4, abt_by),
        (abt_cx - L_mm / 2 - th * 4, cap_el_top),
        "VERTICAL",
        msp=msp,
        dim_x=abt_cx - L_mm / 2 - th * 9,
        label=f"H={abt_h:.2f}m",
        text_height=th,
    )
    text(
        msp,
        "ABUTMENT ELEVATION (TRANSVERSE)",
        abt_cx,
        cap_el_top + th * 6,
        height=th * 1.3,
        layer="TEXT-HEADER",
        halign="CENTER",
    )

    # ══════════════════════════════════════════════════════════════════════
    # ABUTMENT SECTION — longitudinal (right, lower)
    # ══════════════════════════════════════════════════════════════════════
    ls_cx = 620.0
    ls_by = 100.0
    w_mm = abt_w * sc
    wall_h_mm = max(abt_h - cap_ab_d, 0.2) * sc
    wall_l = ls_cx - w_mm / 2
    wall_r = ls_cx + w_mm / 2
    cap_bot_ly = ls_by + wall_h_mm
    cap_top_ly = cap_bot_ly + cap_ab_d_mm
    dw_mm = dw_h * sc
    app_t_mm = app_t * sc

    # Abutment body — GRAVITY family draws the LISP abt1() battered side
    # profile (different riverside/earthside batters); other families keep the
    # rectangular stem + cap + dirt wall stack.
    _fam_sec = _family_for(getattr(sub, "abutment_type", None))
    _cap_w_m = abt_w + cap_pf + cap_pr
    if _fam_sec == "gravity":
        from bridgecad_core.geometry.abutment_profiles import battered_side_outline

        _foot_d_m = 1.0
        _face_n = float(sub.abutment_face_batter_1n or 10)
        _back_n = float(sub.abutment_back_batter_1n or 3)
        _prof = battered_side_outline(
            max(abt_h - cap_ab_d, 0.5),
            cap_w_m=_cap_w_m,
            cap_d_m=cap_ab_d,
            face_batter_1n=_face_n,
            back_batter_1n=_back_n,
            toe_m=1.5,
            foot_d_m=_foot_d_m,
            above_m=dw_h,
            dirt_w_m=dw_t,
        )
        # Earthside (+x sheet) = −x in profile frame; dirt-wall outer face on wall_r
        _x0 = wall_r - (-_prof.dirt_wall_x) * sc
        # Stem + footing only (profile indices 3..12): the cap, dirt wall,
        # approach slab and wearing coat keep their certified stack geometry.
        _stem_pts = _prof.points[3:13]
        _pts = [(_x0 - px * sc, ls_by + (py - _foot_d_m) * sc) for px, py in _stem_pts]
        _pts.append(_pts[0])  # close across the stem top (x14..x3 at cap soffit)
        polyline(msp, _pts, layer="SUB-ABUT", close=True, lw=50)
        hatch_poly(msp, _pts, pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")
        # Cap keeps the standard position — its rear projection covers the
        # dirt-wall seat on the exposed stem-top ledge.
        cap_sec_l = wall_l - cap_pf * sc
        cap_sec_r = wall_r + cap_pr * sc
        rectangle(
            msp, cap_sec_l, cap_bot_ly, cap_sec_r - cap_sec_l, cap_ab_d_mm, layer="SUB-ABUT", lw=50
        )
        hatch_rect(
            msp,
            cap_sec_l,
            cap_bot_ly,
            cap_sec_r - cap_sec_l,
            cap_ab_d_mm,
            pattern="ANSI31",
            scale=sc * 0.015,
            layer="STRUC-HATCHING",
        )
        _ped_centered = True
        text(
            msp,
            f"BATTERED PROFILE — FACE 1:{_face_n:.0f} (RIVER) / BACK 1:{_back_n:.0f} (EARTH)",
            ls_cx,
            ls_by - _foot_d_m * sc - th * 4,
            height=th * 0.9,
            layer="TEXT-SPEC",
            halign="CENTER",
        )
    else:
        # Abutment wall (thickness = abutment_width_m)
        rectangle(msp, wall_l, ls_by, w_mm, wall_h_mm, layer="SUB-ABUT", lw=50)
        hatch_rect(
            msp,
            wall_l,
            ls_by,
            w_mm,
            wall_h_mm,
            pattern="ANSI31",
            scale=sc * 0.015,
            layer="STRUC-HATCHING",
        )

        # Cap — projects front (bearing shelf) and rear (dirt wall seat)
        cap_sec_l = wall_l - cap_pf * sc
        cap_sec_r = wall_r + cap_pr * sc
        rectangle(
            msp, cap_sec_l, cap_bot_ly, cap_sec_r - cap_sec_l, cap_ab_d_mm, layer="SUB-ABUT", lw=50
        )
        hatch_rect(
            msp,
            cap_sec_l,
            cap_bot_ly,
            cap_sec_r - cap_sec_l,
            cap_ab_d_mm,
            pattern="ANSI31",
            scale=sc * 0.015,
            layer="STRUC-HATCHING",
        )
        _ped_centered = False

    # Pedestal + bearing on the bearing shelf
    ped_a_w = 0.5 * sc
    ped_a_x = (
        (cap_sec_l + cap_sec_r) / 2.0 - ped_a_w / 2.0 if _ped_centered else cap_sec_l + 0.06 * sc
    )
    rectangle(msp, ped_a_x, cap_top_ly, ped_a_w, ped_a_h_mm, layer="SUB-BEARING", lw=25)
    rectangle(
        msp,
        ped_a_x - sc * 0.05,
        cap_top_ly + ped_a_h_mm,
        ped_a_w + sc * 0.1,
        sc * 0.05,
        layer="SUB-BEARING",
        lw=15,
    )

    # Dirt wall — sits ON the cap rear ledge: its earthside face is flush with
    # the cap rear edge (wall_r + cap_pr), so the wall occupies the rear
    # projection, not the shaft face.  Approach slab starts behind the wall.
    dw_x = wall_r + cap_pr * sc - dw_t * sc
    app_x = dw_x + dw_t * sc  # = wall_r + cap_pr*sc — cap rear edge
    # Granular sub-base (GSB) under the dirt wall — prewallcivil construction
    # sequence: the wall is built on a 100 mm compacted granular layer on the
    # cap rear ledge, then the earth wall is placed in compacted layers.
    gsb_t = 0.10  # m
    gsb_mm = gsb_t * sc
    if gsb_mm < dw_mm:
        rectangle(msp, dw_x, cap_top_ly, dw_t * sc, gsb_mm, layer="SUB-BACKFILL", lw=20)
        hatch_rect(
            msp,
            dw_x,
            cap_top_ly,
            dw_t * sc,
            gsb_mm,
            pattern="ANSI31",
            scale=sc * 0.02,
            layer="STRUC-HATCHING",
        )
        text(
            msp,
            "GSB 100",
            dw_x + dw_t * sc / 2.0,
            cap_top_ly + gsb_mm / 2.0,
            height=th * 0.6,
            layer="TEXT-SPEC",
            halign="CENTER",
        )
    dw_wall_bot = cap_top_ly + min(gsb_mm, dw_mm * 0.5)
    rectangle(
        msp,
        dw_x,
        dw_wall_bot,
        dw_t * sc,
        cap_top_ly + dw_mm - dw_wall_bot,
        layer="ABUT-PROF",
        lw=40,
    )
    hatch_rect(
        msp,
        dw_x,
        dw_wall_bot,
        dw_t * sc,
        cap_top_ly + dw_mm - dw_wall_bot,
        pattern="ANSI31",
        scale=sc * 0.01,
        layer="STRUC-HATCHING",
    )
    # Construction joint at the dirt wall / cap interface (monolithic pour
    # separated by a CJ with 150 mm PVC water bar — Indian standard practice)
    line(
        msp,
        (dw_x, cap_top_ly),
        (dw_x + dw_t * sc, cap_top_ly),
        layer="SUB-DIRT-WALL",
        lw=35,
    )
    for _jy in (cap_top_ly + dw_mm * 0.35, cap_top_ly + dw_mm * 0.65):
        line(
            msp,
            (dw_x - th * 0.6, _jy - th * 0.6),
            (dw_x + th * 0.6, _jy + th * 0.6),
            layer="SUB-DIRT-WALL",
            lw=18,
        )

    # Weep holes through the dirt wall — filter media packed on the earthside
    for i in range(2):
        wy = dw_wall_bot + (cap_top_ly + dw_mm - dw_wall_bot) * (i + 1) / 3.0
        circle(msp, dw_x + dw_t * sc / 2.0, wy, weephole_d * sc / 2.0, layer="ABUT-PROF", color=4)
    text(
        msp,
        f"Ø{sub.weep_hole_diameter_mm or 100} PVC WEEP HOLES @ {weephole_s:.1f}m c/c",
        dw_x + dw_t * sc + th,
        cap_top_ly + dw_mm * 0.5,
        height=th * 0.8,
        layer="TEXT-SPEC",
        color=4,
    )

    # Approach slab behind the dirt wall (its wearing coat is drawn once, as a
    # single continuous band, further down with the deck stub)
    app_x = dw_x + dw_t * sc
    rectangle(msp, app_x, cap_top_ly + dw_mm, app_l * sc, app_t_mm, layer="CIVIL-ROAD", lw=25)
    hatch_rect(
        msp,
        app_x,
        cap_top_ly + dw_mm,
        app_l * sc,
        app_t_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )

    # Return wall along the embankment at the rear of the approach slab
    ret_x = app_x + app_l * sc
    rectangle(
        msp,
        ret_x,
        cap_top_ly + dw_mm,
        ret_l * sc,
        max(ret_h, 0.5) * sc * 0.5,
        layer="SUB-ABUT",
        lw=25,
    )

    # Deck slab at the front (bearing seat up to deck top) — resolved stack
    deck_bot_off = (float(stack.deck_bot) - float(stack.cap_top)) * sc
    deck_top_off = (float(stack.slab_top) - float(stack.cap_top)) * sc
    deck_len = 4.0 * sc
    rectangle(
        msp,
        cap_sec_l - deck_len,
        cap_top_ly + deck_bot_off,
        deck_len,
        deck_top_off - deck_bot_off,
        layer="SUPER-DECK",
        lw=40,
    )
    # Wearing coat — ONE continuous band end to end: from the deck stub,
    # across the abutment cap and the dirt-wall seat, over the full approach
    # slab to the embankment.  Sheet 2 draws the same unbroken band
    # ("CONTINUOUS WEARING COAT OVER APPROACH SLABS"), so the two views can
    # never disagree; the coat is not broken by the abutment joint.
    coat_x0 = cap_sec_l - deck_len
    coat_x1 = app_x + app_l * sc
    rectangle(
        msp,
        coat_x0,
        cap_top_ly + deck_top_off,
        coat_x1 - coat_x0,
        wc_t * sc,
        layer="SUPER-WEARING",
        lw=20,
    )

    _abt_sec = view_spec("abutment_section")
    dim_along(
        _abt_sec,
        (wall_l, ls_by - th * 5),
        (wall_r, ls_by - th * 5),
        "LONGITUDINAL",
        msp=msp,
        dim_y=ls_by - th * 5,
        label=f"THK={abt_w:.2f}m",
        text_height=th * 0.85,
    )
    dim_along(
        _abt_sec,
        (ret_x + th * 3, cap_top_ly + dw_mm),
        (ret_x + th * 3, cap_top_ly + dw_mm + app_t_mm),
        "VERTICAL",
        msp=msp,
        dim_x=ret_x + th * 8,
        label=f"APP THK={app_t:.2f}m",
        text_height=th * 0.85,
    )
    text(
        msp,
        "ABUTMENT SECTION (LONGITUDINAL)",
        ls_cx + 20.0,
        cap_top_ly + dw_mm + th * 12,
        height=th * 1.3,
        layer="TEXT-HEADER",
        halign="CENTER",
    )

    # ── Notes ─────────────────────────────────────────────────────────────
    notes = [
        "1. All dimensions in metres unless stated.",
        f"2. Concrete grade pier/abut: {getattr(getattr(sub,'pier_material',None),'name','M30')}.",
        f"3. Backfill: {getattr(sub,'backfill_type','SELECT MOORUM')}.",
        "4. Approach slab reinforced with Fe500D bars @ 150 c/c both ways.",
        "5. All exposed surfaces to have 2-coat epoxy waterproofing.",
        f"6. Dirt wall {int(dw_t * 1000)} mm thk on 100 mm GSB; {int(sub.weep_hole_diameter_mm or 100)} mm dia PVC weep holes @ {float(sub.weep_hole_spacing_m or 1.5):.1f} m c/c with graded granular filter + drainage on earthside (prewallcivil ref.).",
        f"7. Abutment cap {int(cap_ab_d * 1000)} mm deep, projecting {int(cap_pf * 1000)} mm front / {int(cap_pr * 1000)} mm rear beyond shaft face.",
        "8. Construction joint at dirt wall / cap interface with 150 mm PVC water bar; dirt wall cast monolithically with cap otherwise.",
        "9. Cast sequence: pile cap -> abutment -> abutment cap -> dirt wall (compacted earth layers, geogrid, stone pitching face).",
        "10. Dirt wall retains approach embankment; finish with stone pitching/vegetation and final grading to embankment.",
    ]
    for i, note in enumerate(notes):
        text(msp, note, 25.0, 226.0 - i * 7.0, height=th * 0.9, layer="TEXT-SPEC")

    # ── Sheet self-audit table (clause-tagged checks) ─────────────────────
    from .checks_table import build_abutment_rows, draw_checks_table

    draw_checks_table(msp, 240.0, 80.0, build_abutment_rows(project), text_height=th * 0.8)


__all__ = ["generate"]
