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
    dim_linear_h,
    dim_linear_v,
    hatch_poly,
    hatch_rect,
    line,
    polyline,
    rectangle,
    text,
)
from .titleblocks import draw_border, draw_title_block


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

    # Dimensions
    dim_linear_h(
        msp,
        pier_cx - cap_w_mm / 2,
        pier_by - th * 5,
        pier_cx + cap_w_mm / 2,
        pier_by - th * 5,
        dim_y=pier_by - th * 5,
        label=f"Cap={cap_w:.2f}m",
        text_height=th,
    )
    dim_linear_v(
        msp,
        pier_cx + cap_w_mm / 2 + th * 3,
        pier_by,
        pier_cx + cap_w_mm / 2 + th * 3,
        cap_bot_y,
        dim_x=pier_cx + cap_w_mm / 2 + th * 9,
        label=f"H={pier_h:.2f}m",
        text_height=th,
    )
    dim_linear_h(
        msp,
        pier_cx - pier_sw_mm / 2,
        pier_by + pier_h_mm / 2,
        pier_cx + pier_sw_mm / 2,
        pier_by + pier_h_mm / 2,
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
    rectangle(msp, psec_cx - pier_sl_mm / 2, psec_by, pier_sl_mm, pier_sw_mm, layer="SUB-PIER", lw=40)
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
    dim_linear_h(
        msp,
        psec_cx - pier_sl_mm / 2,
        psec_by - th * 4,
        psec_cx + pier_sl_mm / 2,
        psec_by - th * 4,
        dim_y=psec_by - th * 4,
        label=f"L={pier_sl:.2f}m",
        text_height=th * 0.85,
    )
    dim_linear_v(
        msp,
        psec_cx + pier_sl_mm / 2 + th * 3,
        psec_by,
        psec_cx + pier_sl_mm / 2 + th * 3,
        psec_by + pier_sw_mm,
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
    H_mm = abt_h * sc

    # Abutment wall face (full transverse length)
    rectangle(msp, abt_cx - L_mm / 2, abt_by, L_mm, H_mm, layer="SUB-ABUT", lw=50)
    hatch_rect(
        msp,
        abt_cx - L_mm / 2,
        abt_by,
        L_mm,
        H_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )

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

    dim_linear_h(
        msp,
        abt_cx - L_mm / 2,
        abt_by - th * 5,
        abt_cx + L_mm / 2,
        abt_by - th * 5,
        dim_y=abt_by - th * 5,
        label=f"L={abt_len:.2f}m",
        text_height=th,
    )
    dim_linear_h(
        msp,
        abt_cx - L_mm / 2 - ww_l * sc,
        abt_by - th * 10,
        abt_cx - L_mm / 2,
        abt_by - th * 10,
        dim_y=abt_by - th * 10,
        label=f"WW={ww_l:.1f}m",
        text_height=th * 0.85,
    )
    dim_linear_v(
        msp,
        abt_cx - L_mm / 2 - th * 4,
        abt_by,
        abt_cx - L_mm / 2 - th * 4,
        cap_el_top,
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

    # Pedestal + bearing on the bearing shelf
    ped_a_w = 0.5 * sc
    ped_a_x = cap_sec_l + 0.06 * sc
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

    # Dirt wall — cap top up to the approach slab soffit
    dw_x = wall_r - dw_t * sc
    rectangle(msp, dw_x, cap_top_ly, dw_t * sc, dw_mm, layer="ABUT-PROF", lw=40)
    hatch_rect(
        msp,
        dw_x,
        cap_top_ly,
        dw_t * sc,
        dw_mm,
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

    # Weep holes through the dirt wall
    for i in range(2):
        wy = cap_top_ly + dw_mm * (i + 1) / 3.0
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

    # Approach slab behind the dirt wall + continuous wearing coat over it
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
    rectangle(
        msp,
        app_x,
        cap_top_ly + dw_mm + app_t_mm,
        app_l * sc,
        wc_t * sc,
        layer="SUPER-WEARING",
        lw=20,
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

    dim_linear_h(
        msp,
        wall_l,
        ls_by - th * 5,
        wall_r,
        ls_by - th * 5,
        dim_y=ls_by - th * 5,
        label=f"THK={abt_w:.2f}m",
        text_height=th * 0.85,
    )
    dim_linear_v(
        msp,
        ret_x + th * 3,
        cap_top_ly + dw_mm,
        ret_x + th * 3,
        cap_top_ly + dw_mm + app_t_mm,
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
        f"6. Dirt wall {int(dw_t * 1000)} mm thk; {int(sub.weep_hole_diameter_mm or 100)} mm dia PVC weep holes @ {float(sub.weep_hole_spacing_m or 1.5):.1f} m c/c with 300 mm graded granular filter behind stem.",
        f"7. Abutment cap {int(cap_ab_d * 1000)} mm deep, projecting {int(cap_pf * 1000)} mm front / {int(cap_pr * 1000)} mm rear beyond shaft face.",
        "8. Construction joint at dirt wall / cap interface with 150 mm PVC water bar; dirt wall cast monolithically with cap otherwise.",
    ]
    for i, note in enumerate(notes):
        text(msp, note, 25.0, 226.0 - i * 7.0, height=th * 0.9, layer="TEXT-SPEC")


__all__ = ["generate"]
