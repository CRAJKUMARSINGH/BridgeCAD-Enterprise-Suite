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
    sub = project.substructure
    hd = project.hydraulic_data
    pm = project.project_master

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

    # ── PIER ELEVATION (left, x=120-280 mm) ───────────────────────────────
    pier_cx = 170.0
    pier_by = 250.0  # base Y on sheet
    pier_h = float(sub.pier_height_typical_m or 8.0)
    pier_sw = float(sub.pier_shaft_width_m or 1.5)
    float(sub.pier_shaft_length_m or 11.5)
    cap_w = float(sub.pier_cap_width_m or 2.0)
    float(sub.pier_cap_length_m or 11.5)
    cap_d = float(sub.pier_cap_depth_m or 0.8)
    ped_h = float(sub.pier_pedestal_height_m or 0.2)

    pier_h_mm = pier_h * sc
    pier_sw_mm = pier_sw * sc
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
    cap_top_y = pier_by + pier_h_mm
    rectangle(msp, pier_cx - cap_w_mm / 2, cap_top_y, cap_w_mm, cap_d_mm, layer="SUB-PIER", lw=50)
    hatch_rect(
        msp,
        pier_cx - cap_w_mm / 2,
        cap_top_y,
        cap_w_mm,
        cap_d_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )

    # Pedestal
    ped_w = pier_sw_mm * 0.7
    rectangle(
        msp, pier_cx - ped_w / 2, cap_top_y + cap_d_mm, ped_w, ped_h_mm, layer="SUB-PIER", lw=30
    )

    # Dims
    dim_linear_h(
        msp,
        pier_cx - cap_w_mm / 2,
        pier_by - th * 5,
        pier_cx + cap_w_mm / 2,
        pier_by - th * 5,
        dim_y=pier_by - th * 5,
        label=f"Cap W={cap_w:.2f}m",
        text_height=th,
    )
    dim_linear_v(
        msp,
        pier_cx + cap_w_mm / 2 + th * 3,
        pier_by,
        pier_cx + cap_w_mm / 2 + th * 3,
        cap_top_y,
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
        cap_top_y + cap_d_mm + ped_h_mm + th * 4,
        height=th * 1.3,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    text(
        msp,
        f"Scale 1:{scale_denom}",
        pier_cx,
        cap_top_y + cap_d_mm + ped_h_mm + th * 7,
        height=th,
        layer="TEXT-SPEC",
        halign="CENTER",
    )

    # ── ABUTMENT ELEVATION (right, x=450-650 mm) ──────────────────────────
    abt_cx = 560.0
    abt_by = 250.0
    abt_w = float(sub.abutment_width_m or 1.2)
    float(sub.abutment_length_m or 11.8)
    abt_h = float(sub.abutment_height_m or 3.2)
    ww_l = float(sub.wing_wall_splay_length_m or 3.0)
    ww_h = float(sub.wing_wall_height_m or 2.5)
    float(sub.return_wall_length_m or 4.0)

    abt_w_mm = abt_w * sc
    abt_h_mm = abt_h * sc

    # Abutment wall (elevation)
    rectangle(msp, abt_cx - abt_w_mm / 2, abt_by, abt_w_mm, abt_h_mm, layer="SUB-ABUT", lw=50)
    hatch_rect(
        msp,
        abt_cx - abt_w_mm / 2,
        abt_by,
        abt_w_mm,
        abt_h_mm,
        pattern="ANSI31",
        scale=sc * 0.015,
        layer="STRUC-HATCHING",
    )

    # Wing wall (left side, simplified)
    ww_pts = [
        (abt_cx - abt_w_mm / 2, abt_by + abt_h_mm * 0.8),
        (abt_cx - abt_w_mm / 2 - ww_l * sc, abt_by + ww_h * sc),
        (abt_cx - abt_w_mm / 2 - ww_l * sc, abt_by),
        (abt_cx - abt_w_mm / 2, abt_by),
    ]
    polyline(msp, ww_pts, layer="SUB-ABUT", close=True, lw=35)
    hatch_poly(msp, ww_pts, pattern="ANSI31", scale=sc * 0.015, layer="STRUC-HATCHING")

    # Approach slab
    app_l = float(sub.approach_slab_length_m or 3.5)
    app_t = float(sub.approach_slab_thickness_mm or 200) / 1000.0
    rectangle(
        msp,
        abt_cx + abt_w_mm / 2,
        abt_by + abt_h_mm - app_t * sc,
        app_l * sc,
        app_t * sc,
        layer="CIVIL-ROAD",
        lw=25,
    )

    # Dims
    dim_linear_v(
        msp,
        abt_cx + abt_w_mm / 2 + th * 3,
        abt_by,
        abt_cx + abt_w_mm / 2 + th * 3,
        abt_by + abt_h_mm,
        dim_x=abt_cx + abt_w_mm / 2 + th * 9,
        label=f"H={abt_h:.2f}m",
        text_height=th,
    )
    dim_linear_h(
        msp,
        abt_cx - abt_w_mm / 2,
        abt_by - th * 5,
        abt_cx + abt_w_mm / 2,
        abt_by - th * 5,
        dim_y=abt_by - th * 5,
        label=f"W={abt_w:.2f}m",
        text_height=th,
    )
    dim_linear_h(
        msp,
        abt_cx - abt_w_mm / 2 - ww_l * sc,
        abt_by - th * 10,
        abt_cx - abt_w_mm / 2,
        abt_by - th * 10,
        dim_y=abt_by - th * 10,
        label=f"WW={ww_l:.1f}m",
        text_height=th,
    )

    text(
        msp,
        "ABUTMENT ELEVATION",
        abt_cx,
        abt_by + abt_h_mm + th * 5,
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
    ]
    for i, note in enumerate(notes):
        text(msp, note, 60.0, 100.0 - i * 8.0, height=th * 0.9, layer="TEXT-SPEC")


__all__ = ["generate"]
