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

import math
from pathlib import Path
from typing import Any

from . import limits
from .dxf_engine import new_sheet, save
from .primitives import (
    circle,
    dim_linear_h,
    dim_linear_v,
    hatch_rect,
    level_tag,
    line,
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

    # The scale printed in the title block must be the scale the details are
    # drawn at.  ``sc`` is derived from the denominator rather than hard-coded
    # beside it, so a caller that asks for a different denominator gets a sheet
    # drawn at it (a hard-coded 20 mm/m under a requested 1:100 caption lied).
    denom = max(int(scale_denom), 1)

    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-004") or "GAD-004",
        drawing_title="FOUNDATION DETAILS — TYPICAL PIER",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        scale_str=f"1:{denom}",
        sheet_no="4",
        total_sheets="9",
    )

    sc = 1000.0 / denom  # mm per metre
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
        # Steining dimensions — outer and inner diameter across the well. The well
        # branch previously drew no dimension at all (only the pile branch did),
        # which left the sheet short of the >=8 DIMENSION contract on any fixture
        # without a pile group.
        dim_linear_h(
            msp,
            plan_cx - r_out,
            plan_cy - r_out - th * 5,
            plan_cx + r_out,
            plan_cy - r_out - th * 5,
            dim_y=plan_cy - r_out - th * 5,
            label=f"OD = {layout.well_outer_radius_m * 2:.2f} m",
            text_height=th,
        )
        dim_linear_v(
            msp,
            plan_cx + r_out + th * 3,
            plan_cy - r_out,
            plan_cx + r_out + th * 3,
            plan_cy + r_out,
            dim_x=plan_cx + r_out + th * 9,
            label=f"ID = {layout.well_inner_radius_m * 2:.2f} m",
            text_height=th,
        )
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
    # The elevation is FITTED, not fixed-scale: the paper distance between the
    # pile tip and the top of the pier stub is budgeted so the whole view — cap,
    # shafts and every RL tag — stays inside the A1 frame whatever the pile
    # length.  The old absolute 30 mm/m exaggeration ran a 15 m pile's pier stub
    # 111 mm past the top border.  Horizontal scale stays `sc * 1.5`.
    elev_cx = 560.0
    scour_rl = float(hd.scour_level_m or 0)
    pile_len = float(fd.pile_length_m or 15.0)

    # Founding levels come from the canonical §3 record, not from re-adding the
    # cap thickness here: ``footing_top = footing_bottom + footing_depth`` is
    # that record's equation alone. A pile cap IS the pier's footing —
    # ``pile_cutoff_level_m`` is its underside and ``pile_cap_thickness_mm`` its
    # thickness. When the record cannot resolve the foundation (a missing
    # thickness or cutoff), the sheet falls back to the raw model values so it
    # still renders a draft, but the level then carries no approved datum.
    from bridgecad_core.geometry.long_section import typical_pier_support_level

    _prec = typical_pier_support_level(project)
    if _prec.footing_top_rl_m is not None:
        pile_cut = float(_prec.footing_bottom_rl_m)
        cap_thk = float(_prec.footing_depth_m)
        cap_top = float(_prec.footing_top_rl_m)
    else:
        pile_cut = float(fd.pile_cutoff_level_m or 0) if fd.pile_cutoff_level_m else scour_rl + 2.0
        cap_thk = float(fd.pile_cap_thickness_mm or 1500) / 1000.0
        cap_top = pile_cut + cap_thk
    pile_tip = pile_cut - pile_len

    _EV_BOT = 200.0  # paper y of the pile tip (just above the inset band)
    _EV_TOP = 560.0  # highest paper y the elevation may occupy
    _ev_extent_m = max(1.0, (cap_top - pile_tip) + cap_thk * 2.2)
    _ev_vs = (_EV_TOP - _EV_BOT) / _ev_extent_m  # mm per metre (vertical)

    def evy(rl):
        return _EV_BOT + (rl - pile_tip) * _ev_vs

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
            _EV_TOP + th * 4.0,  # clears the pier stub, still inside the frame
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
    # Shows both abutments' cap and dirt wall in plan so site engineers can
    # set out the rear face, dirt wall, and weep holes directly from Sheet 4.
    # A2's approach side is +x, A1's is -x — the wall mirrors with the sign.
    sub = project.substructure
    s2 = 10.0  # inset scale mm per metre (independent of pile-plan scale)

    abt_w = float(getattr(sub, "abutment_width_m", None) or 1.2)
    abt_l = float(getattr(sub, "abutment_length_m", None) or 11.8)
    # The cap is asymmetric: the FRONT (bearing shelf) and REAR (dirt-wall seat)
    # projections are separate inputs and must not be averaged into one symmetric
    # offset — Sheet 5 already draws them apart, so a symmetric plan here would
    # put the dirt wall on the wrong side of the cap.
    cap_pf_inset = float(getattr(sub, "abutment_cap_projection_front_mm", None) or 300) / 1000.0
    cap_pr_inset = float(getattr(sub, "abutment_cap_projection_rear_mm", None) or 300) / 1000.0
    dirt_t_inset = float(getattr(sub, "dirt_wall_thickness_mm", None) or 300) / 1000.0

    cap_w_inset = (abt_w + cap_pf_inset + cap_pr_inset) * s2
    shaft_w_inset = abt_w * s2
    ln_inset = abt_l * s2
    # Weep holes across the dirt wall, spaced no wider than the IRC:78 drainage
    # limit. Take the count from the same helper the sheet self-audit row
    # (QA-DW-WEEP) reports, so the plan can never draw fewer holes than the
    # table claims nor drift past the limit — the old int(abt_l / 3) gave only
    # 3 holes at 3.07 m centres on a 9.2 m wall, breaching the 3.0 m rule.
    from bridgecad_core.geometry_extras import compute_dirt_wall_geometry

    n_weep_geom = compute_dirt_wall_geometry(project).weep_holes_count
    if n_weep_geom <= 0:  # abutment_length unset — fall back to the drawn length
        n_weep_geom = math.ceil(abt_l / limits.WEEP_HOLE_SPACING_M)
    n_weep_inset = max(1, n_weep_geom)

    # A2 on the right (+x rear face), A1 offset 150 mm to its left (-x rear)
    for label, sgn, i_cx in (("A2", +1.0, 680.0), ("A1", -1.0, 530.0)):
        i_y0 = 60.0

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

        # Cap — asymmetric: front (bearing shelf) on the river side, rear
        # (dirt-wall seat) on the approach side. sgn=+1 → approach to +x.
        cap_front_x = i_cx - sgn * (shaft_w_inset / 2 + cap_pf_inset * s2)
        cap_rear_x = i_cx + sgn * (shaft_w_inset / 2 + cap_pr_inset * s2)
        cap_x0 = min(cap_front_x, cap_rear_x)
        cap_x1 = max(cap_front_x, cap_rear_x)
        rectangle(msp, cap_x0, i_y0, cap_x1 - cap_x0, ln_inset, layer="SUB-ABUT", lw=40)

        # Dirt wall on the rear face in plan — inside the cap rear ledge
        if sgn > 0:
            dw_x_inset = cap_rear_x - dirt_t_inset * s2
        else:
            dw_x_inset = cap_rear_x
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
            cap_x0,
            i_y0 - th * 5,
            cap_x1,
            i_y0 - th * 5,
            dim_y=i_y0 - th * 5,
            label=f"CAP W={cap_w_inset / s2:.2f}m",
            text_height=th * 0.8,
        )
        dim_linear_v(
            msp,
            cap_x1 + th * 3,
            i_y0,
            cap_x1 + th * 3,
            i_y0 + ln_inset,
            dim_x=cap_x1 + th * 9,
            label=f"L={abt_l:.2f}m",
            text_height=th * 0.8,
        )
        dim_linear_h(
            msp,
            min(dw_x_inset, cap_x0),
            i_y0 + ln_inset + th * 4,
            max(dw_x_inset + dirt_t_inset * s2, cap_x1),
            i_y0 + ln_inset + th * 4,
            dim_y=i_y0 + ln_inset + th * 4,
            label=f"DW={dirt_t_inset:.2f}m",
            text_height=th * 0.75,
        )
        # Shaft width — a second horizontal staff below the cap overall width. It
        # is drawn unconditionally (both abutments always have a shaft), so this
        # sheet keeps >=8 real DIMENSION entities even on a culvert with neither a
        # pile group nor a well, which previously left only the 6 inset dims.
        dim_linear_h(
            msp,
            i_cx - shaft_w_inset / 2,
            i_y0 - th * 10,
            i_cx + shaft_w_inset / 2,
            i_y0 - th * 10,
            dim_y=i_y0 - th * 10,
            label=f"SH={abt_w:.2f}m",
            text_height=th * 0.8,
        )
        # Weep-hole spacing along the dirt wall (IRC:78 limit = 3.0 m)
        dim_linear_v(
            msp,
            cap_x0 - th * 9,
            i_y0,
            cap_x0 - th * 9,
            i_y0 + ln_inset / n_weep_inset,
            dim_x=cap_x0 - th * 3,
            label=f"WE={abt_l / n_weep_inset:.2f}m",
            text_height=th * 0.75,
        )

        text(
            msp,
            f"ABUTMENT {label} — CAP + DIRT WALL PLAN",
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
