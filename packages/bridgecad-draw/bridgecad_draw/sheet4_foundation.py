"""
bridgecad_draw.sheet4_foundation — Sheet 4: Foundation Details.

Draws for a typical pier:
  1. Pile cap plan (top view) — rectangle with pile circles
  2. Pile cap elevation (section) — pile cap + pile shafts + scour line
  3. Well foundation option (if applicable) — outer/inner steining circles
  4. Open footing option — stepped outline
  5. Pile schedule table (dia, length, count, spacing)
  6. Levels: scour level, pile cutoff, pile tip, pile cap top
  7. Dimension strings
  8. Title block + border (Sheet 4 of 7)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dxf_engine import new_sheet, save
from .primitives import (
    circle,
    dim_linear_h,
    dim_linear_v,
    hatch_rect,
    level_tag,
    line,
    polyline,
    rectangle,
    text,
)
from .titleblocks import draw_border, draw_title_block


def generate(project: Any, output_path: str | Path, scale_denom: int = 50) -> Path:
    doc, msp = new_sheet("S4 Foundation")
    _draw(msp, project, scale_denom)
    return save(doc, output_path)


def _draw(msp: Any, project: Any, scale_denom: int = 50) -> None:
    from bridgecad_core.geometry import compute_pile_group_layout

    fd = project.foundation_details
    hd = project.hydraulic_data
    pm = project.project_master

    layout = compute_pile_group_layout(project)

    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-004") or "GAD-004",
        drawing_title="FOUNDATION DETAILS — TYPICAL PIER",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        sheet_no="4",
        total_sheets="8",
    )

    sc = 20.0  # mm per metre
    th = 2.5  # text height

    # ── PLAN VIEW (top-left) ──────────────────────────────────────────────
    plan_cx, plan_cy = 180.0, 370.0  # centre of plan view mm

    if layout.pile_positions:
        # Pile cap rectangle
        cap_w = layout.pile_cap_width_m * sc
        cap_l = layout.pile_cap_length_m * sc
        rectangle(
            msp, plan_cx - cap_w / 2, plan_cy - cap_l / 2, cap_w, cap_l, layer="FOUND-CAP", lw=40
        )
        hatch_rect(
            msp,
            plan_cx - cap_w / 2,
            plan_cy - cap_l / 2,
            cap_w,
            cap_l,
            pattern="ANSI31",
            scale=sc * 0.02,
            layer="STRUC-HATCHING",
        )
        # Pile circles
        r = layout.pile_diameter_m / 2.0 * sc
        for px, py in layout.pile_positions:
            circle(msp, plan_cx + px * sc, plan_cy + py * sc, r, layer="FOUND-PILE", color=4)
            circle(msp, plan_cx + px * sc, plan_cy + py * sc, r * 0.35, layer="FOUND-PILE", color=4)

        # Dims
        dim_linear_h(
            msp,
            plan_cx - cap_w / 2,
            plan_cy - cap_l / 2,
            plan_cx + cap_w / 2,
            plan_cy - cap_l / 2,
            dim_y=plan_cy - cap_l / 2 - th * 5,
            label=f"Cap W = {layout.pile_cap_width_m:.3f} m",
            text_height=th,
        )
        dim_linear_v(
            msp,
            plan_cx - cap_w / 2,
            plan_cy - cap_l / 2,
            plan_cx - cap_w / 2,
            plan_cy + cap_l / 2,
            dim_x=plan_cx - cap_w / 2 - th * 6,
            label=f"Cap L = {layout.pile_cap_length_m:.3f} m",
            text_height=th,
        )
        text(
            msp,
            "PILE CAP PLAN",
            plan_cx,
            plan_cy + cap_l / 2 + th * 3,
            height=th * 1.3,
            layer="TEXT-HEADER",
            halign="CENTER",
        )
        text(
            msp,
            f"{layout.pile_rows}×{layout.pile_cols} PILE GROUP",
            plan_cx,
            plan_cy + cap_l / 2 + th * 6,
            height=th,
            layer="TEXT-GENERAL",
            halign="CENTER",
        )

    elif layout.well_outer_radius_m > 0:
        # Well plan
        r_out = layout.well_outer_radius_m * sc
        r_in = layout.well_inner_radius_m * sc
        circle(msp, plan_cx, plan_cy, r_out, layer="FOUND-WELL", color=4)
        circle(msp, plan_cx, plan_cy, r_in, layer="FOUND-WELL", color=4)
        text(
            msp,
            "WELL FOUNDATION — PLAN",
            plan_cx,
            plan_cy + r_out + th * 3,
            height=th * 1.3,
            layer="TEXT-HEADER",
            halign="CENTER",
        )

    # ── ELEVATION VIEW (right side) ───────────────────────────────────────
    elev_cx, elev_cy = 560.0, 300.0
    scour_rl = float(hd.scour_level_m or 0)
    pile_cut = float(fd.pile_cutoff_level_m or 0) if fd.pile_cutoff_level_m else scour_rl + 2.0
    pile_len = float(fd.pile_length_m or 15.0)
    pile_tip = pile_cut - pile_len
    cap_top = pile_cut + float(fd.pile_cap_thickness_mm or 1500) / 1000.0
    datum_rl = pile_tip - 1.0

    def evy(rl):
        return elev_cy - 100.0 + (rl - datum_rl) * sc * 1.5

    # Ground/scour line
    scour_y = evy(scour_rl)
    line(msp, (elev_cx - 80, scour_y), (elev_cx + 80, scour_y), layer="CIVIL-SCOUR", color=1)
    text(
        msp,
        f"DESIGN SCOUR RL {scour_rl:.3f}",
        elev_cx + 85,
        scour_y,
        height=th * 0.85,
        layer="CIVIL-SCOUR",
        color=1,
    )

    if layout.pile_positions:
        r_mm = layout.pile_diameter_m / 2.0 * sc * 1.5
        float(fd.pile_cap_thickness_mm or 1500) / 1000.0
        # Pile cap elevation
        cap_y0 = evy(pile_cut)
        cap_y1 = evy(cap_top)
        cap_w_e = layout.pile_cap_width_m * sc * 1.5
        rectangle(
            msp, elev_cx - cap_w_e / 2, cap_y0, cap_w_e, cap_y1 - cap_y0, layer="FOUND-CAP", lw=40
        )
        hatch_rect(
            msp,
            elev_cx - cap_w_e / 2,
            cap_y0,
            cap_w_e,
            cap_y1 - cap_y0,
            pattern="ANSI31",
            scale=sc * 0.015,
            layer="STRUC-HATCHING",
        )
        # Pile shafts in elevation
        for px, _ in layout.pile_positions:
            cx_e = elev_cx + px * sc * 1.5
            rectangle(
                msp,
                cx_e - r_mm,
                evy(pile_tip),
                r_mm * 2,
                evy(pile_cut) - evy(pile_tip),
                layer="FOUND-PILE",
                lw=30,
            )
        # ── Audit-required SUB-PIER layer: pier shaft cut-off → cap top ──
        # 2-cell shaft sized from cap width (typical hammerhead pier)
        shaft_w_e = cap_w_e * 0.55
        cap_top_y = evy(cap_top)
        soffit_top_y = cap_top_y + (cap_y1 - cap_y0) * 2.2  # shaft above cap (pier height stub)
        rectangle(
            msp,
            elev_cx - shaft_w_e / 2,
            cap_top_y,
            shaft_w_e,
            soffit_top_y - cap_top_y,
            layer="SUB-PIER",
            lw=40,
        )

        # Level tags
        level_tag(msp, elev_cx - cap_w_e / 2 - th, evy(pile_tip), pile_tip, text_height=th)
        level_tag(msp, elev_cx - cap_w_e / 2 - th, cap_y0, pile_cut, text_height=th)
        level_tag(msp, elev_cx - cap_w_e / 2 - th, cap_y1, cap_top, text_height=th)

        # Pile length dim
        dim_linear_v(
            msp,
            elev_cx + cap_w_e / 2 + th * 2,
            evy(pile_tip),
            elev_cx + cap_w_e / 2 + th * 2,
            cap_y0,
            dim_x=elev_cx + cap_w_e / 2 + th * 8,
            label=f"L = {pile_len:.1f} m",
            text_height=th,
        )
        text(
            msp,
            "PILE FOUNDATION — ELEVATION",
            elev_cx,
            evy(cap_top) + th * 5,
            height=th * 1.3,
            layer="TEXT-HEADER",
            halign="CENTER",
        )

    # ── Pile schedule table ───────────────────────────────────────────────
    tx, ty = 60.0, 150.0
    headers = ["PARAMETER", "VALUE", "UNIT"]
    col_w = [80, 60, 40]
    row_h = 8.0
    rows = [
        ("Pile Type", str(getattr(getattr(fd, "pile_type", None), "name", "BORED_CIS")), ""),
        ("Pile Diameter", str(getattr(fd, "pile_diameter_mm", 1200)), "mm"),
        ("Pile Length", str(float(getattr(fd, "pile_length_m", 15) or 15)), "m"),
        ("Piles per Pier", str(getattr(fd, "piles_per_pier", 4)), "nos"),
        ("Spacing c/c", str(float(getattr(fd, "pile_spacing_m", 2.4) or 2.4)), "m"),
        ("Cap Thickness", str(getattr(fd, "pile_cap_thickness_mm", 1500)), "mm"),
        ("Pile Cutoff RL", str(float(getattr(fd, "pile_cutoff_level_m", 0) or 0)), "m"),
        ("FOS Bearing", str(float(getattr(fd, "factor_of_safety_on_bearing", 3) or 3)), "-"),
        ("Allow. Bearing Cap.", str(float(getattr(fd, "bearing_capacity_kpa", 450) or 450)), "kPa"),
        ("Scour Level RL", str(float(getattr(hd, "scour_level_m", 0) or 0)), "m"),
        ("Scour Depth", str(float(getattr(hd, "design_scour_depth_m", 2) or 2)), "m"),
    ]
    # Header
    x = tx
    for i, (h, w) in enumerate(zip(headers, col_w, strict=False)):
        rectangle(msp, x, ty, w, row_h, layer="TITLEBLK-BOX")
        text(msp, h, x + 1.5, ty + 2.0, height=th * 0.9, layer="TEXT-GENERAL")
        x += w
    # Rows
    for ri, (lbl, val, unit) in enumerate(rows):
        y = ty - (ri + 1) * row_h
        x = tx
        for val_str, w in zip([lbl, val, unit], col_w, strict=False):
            rectangle(msp, x, y, w, row_h, layer="TITLEBLK-BOX")
            text(msp, val_str, x + 1.5, y + 2.0, height=th * 0.85, layer="TEXT-GENERAL")
            x += w

    text(
        msp,
        "PILE SCHEDULE",
        tx + sum(col_w) / 2,
        ty + row_h * 2.5,
        height=th * 1.2,
        layer="TEXT-HEADER",
        halign="CENTER",
    )

    # ── ABUTMENT CAP + DIRT WALL PLAN INSET (bottom-right) ───────────────
    # Shows the abutment A2 cap and dirt wall in plan so site engineers can
    # set out the rear face, dirt wall, and weep holes directly from Sheet 4.
    sub = project.substructure
    s2 = 10.0  # inset scale mm per metre (independent of pile-plan scale)
    i_cx, i_y0 = 680.0, 60.0

    abt_w = float(getattr(sub, "abutment_width_m", None) or 1.2)
    abt_l = float(getattr(sub, "abutment_length_m", None) or 11.8)
    cap_d_inset = float(getattr(sub, "abutment_cap_depth_mm", None) or 600) / 1000.0
    cap_proj = float(getattr(sub, "abutment_cap_projection_front_mm", None) or 300) / 1000.0
    dirt_t_inset = float(getattr(sub, "dirt_wall_thickness_mm", None) or 300) / 1000.0

    cap_w_inset = (abt_w + 2 * cap_proj) * s2
    shaft_w_inset = abt_w * s2
    ln_inset = abt_l * s2

    # Shaft (plan rectangle)
    rectangle(
        msp,
        i_cx - shaft_w_inset / 2,
        i_y0,
        shaft_w_inset,
        ln_inset,
        layer="SUB-ABUT",
        lw=40,
    )
    hatch_rect(
        msp,
        i_cx - shaft_w_inset / 2,
        i_y0,
        shaft_w_inset,
        ln_inset,
        pattern="ANSI31",
        scale=s2 * 0.03,
        layer="STRUC-HATCHING",
    )

    # Cap, projecting both faces
    rectangle(
        msp,
        i_cx - cap_w_inset / 2,
        i_y0,
        cap_w_inset,
        ln_inset,
        layer="SUB-ABUT",
        lw=40,
    )

    # Dirt wall on the rear (+x) face in plan
    dw_x_inset = i_cx + cap_w_inset / 2 - dirt_t_inset * s2
    rectangle(
        msp,
        dw_x_inset,
        i_y0,
        dirt_t_inset * s2,
        ln_inset,
        layer="SUB-DIRT-WALL",
        lw=40,
    )
    hatch_rect(
        msp,
        dw_x_inset,
        i_y0,
        dirt_t_inset * s2,
        ln_inset,
        pattern="ANSI31",
        scale=s2 * 0.03,
        layer="STRUC-HATCHING",
    )

    # Weep holes through the dirt wall
    n_weep_inset = int(getattr(sub, "dirt_wall_weep_holes_count", None) or max(1, int(abt_l / 3)))
    import math as _math
    n_weep_inset = max(1, n_weep_inset)
    for i_w in range(n_weep_inset):
        wy = i_y0 + ln_inset * (i_w + 0.5) / n_weep_inset
        circle(
            msp,
            dw_x_inset + dirt_t_inset * s2 / 2,
            wy,
            0.025 * s2,
            layer="SUB-DIRT-WALL",
            color=4,
        )

    # Dimensions
    dim_linear_h(
        msp,
        i_cx - cap_w_inset / 2,
        i_y0 - th * 5,
        i_cx + cap_w_inset / 2,
        i_y0 - th * 5,
        dim_y=i_y0 - th * 5,
        label=f"CAP W={cap_w_inset / s2:.2f}m",
        text_height=th * 0.8,
    )
    dim_linear_v(
        msp,
        i_cx + cap_w_inset / 2 + th * 3,
        i_y0,
        i_cx + cap_w_inset / 2 + th * 3,
        i_y0 + ln_inset,
        dim_x=i_cx + cap_w_inset / 2 + th * 9,
        label=f"L={abt_l:.2f}m",
        text_height=th * 0.8,
    )
    dim_linear_h(
        msp,
        dw_x_inset,
        i_y0 + ln_inset + th * 4,
        i_cx + cap_w_inset / 2,
        i_y0 + ln_inset + th * 4,
        dim_y=i_y0 + ln_inset + th * 4,
        label=f"DW={dirt_t_inset:.2f}m",
        text_height=th * 0.75,
    )

    text(
        msp,
        "ABUTMENT A2 — CAP + DIRT WALL PLAN",
        i_cx,
        i_y0 + ln_inset + th * 8,
        height=th * 1.2,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    text(
        msp,
        f"{n_weep_inset} nos 50 mm dia weep holes",
        i_cx,
        i_y0 - th * 10,
        height=th * 0.8,
        layer="TEXT-SPEC",
        halign="CENTER",
    )


__all__ = ["generate"]
