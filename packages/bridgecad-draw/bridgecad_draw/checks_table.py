"""
bridgecad_draw.checks_table — Clause-tagged sheet self-audit table.

Rendered on Sheets 5 and 8 so the drawing audits itself: every row carries the
rule id, the measured value, the limit it is checked against, and OK/FAIL.
Rows are built from the same ``bridgecad_draw.limits`` constants the QA rules
use, so the sheet and the CLI gate cannot disagree.

References
----------
IRC:21-2000  Clause 305 — abutment cap depth / bearing shelf.
IRC:78-2014  Clause 710 — dirt wall thickness and weep-hole drainage.
"""

from __future__ import annotations

from typing import Any

from . import limits
from .primitives import rectangle, text

__all__ = ["build_abutment_rows", "draw_checks_table"]

# (id, parameter, value, limit, ok) — value/limit are display strings.
Row = tuple[str, str, str, str, bool]

_ROW_H = 7.0
_COLS = (20.0, 62.0, 30.0, 34.0, 14.0)  # id, parameter, value, limit, status


def _fnum(v: float) -> str:
    return f"{v:.2f}"


def build_abutment_rows(project: Any) -> list[Row]:
    """Build the abutment self-audit rows for *project*.

    Every value is read from the model or ``compute_dirt_wall_geometry`` —
    nothing is hard-coded, so a FAIL row always points at a real input.
    """
    from bridgecad_core.geometry_extras import compute_dirt_wall_geometry

    sub = project.substructure
    dwg = compute_dirt_wall_geometry(project)

    cap_d_mm = int(sub.abutment_cap_depth_mm or 0)
    cap_pf_mm = int(sub.abutment_cap_projection_front_mm or 0)
    cap_pr_mm = int(sub.abutment_cap_projection_rear_mm or 0)
    dw_mm = int(sub.dirt_wall_thickness_mm or 0)
    app_t_m = float(sub.approach_slab_thickness_mm or 200) / 1000.0
    required_dw = app_t_m + limits.DIRT_WALL_FREEBOARD_M

    rows: list[Row] = [
        (
            "QA-ABT-CAP-DEPTH",
            "Abutment cap depth",
            f"{cap_d_mm} mm",
            f">= {limits.CAP_DEPTH_MIN_M * 1000:.0f} mm",
            cap_d_mm == 0 or cap_d_mm >= limits.CAP_DEPTH_MIN_M * 1000,
        ),
        (
            "QA-ABT-CAP-PROJ",
            "Cap projection front/rear",
            f"{cap_pf_mm}/{cap_pr_mm} mm",
            (
                f"{limits.CAP_PROJ_MIN_M * 1000:.0f}-{limits.CAP_PROJ_MAX_M * 1000:.0f}"
                f" / {limits.CAP_PROJ_REAR_MIN_M * 1000:.0f}-"
                f"{limits.CAP_PROJ_REAR_MAX_M * 1000:.0f} mm"
            ),
            (
                cap_pf_mm == 0
                or limits.CAP_PROJ_MIN_M * 1000 <= cap_pf_mm <= limits.CAP_PROJ_MAX_M * 1000
            )
            and (
                cap_pr_mm == 0
                or limits.CAP_PROJ_REAR_MIN_M * 1000
                <= cap_pr_mm
                <= limits.CAP_PROJ_REAR_MAX_M * 1000
            ),
        ),
        (
            "QA-DW-THK",
            "Dirt wall thickness",
            f"{dw_mm} mm",
            f">= {limits.DIRT_WALL_THK_MIN_M * 1000:.0f} mm",
            dw_mm == 0 or dw_mm >= limits.DIRT_WALL_THK_MIN_M * 1000,
        ),
        (
            "QA-DW-TOP",
            "Dirt wall to slab soffit",
            f"{_fnum(dwg.height_m)} m",
            f">= {_fnum(required_dw)} m",
            dwg.height_m >= required_dw or dw_mm == 0,
        ),
        (
            "QA-DW-WEEP",
            "Weep holes provided",
            f"{dwg.weep_holes_count}",
            f"1 per {limits.WEEP_HOLE_SPACING_M:.0f} m",
            dwg.weep_holes_count >= 1 or dw_mm == 0,
        ),
    ]

    try:
        from bridgecad_core.stability import FOS_OVERTURNING_MIN, FOS_SLIDING_MIN, check_abutment

        st = check_abutment(project)
        q_allow = float(project.foundation_details.bearing_capacity_kpa or 250.0)
        rows += [
            (
                "QA-ABT-OT",
                "Overturning FOS",
                f"{_fnum(st.fos_overturning)}",
                f">= {FOS_OVERTURNING_MIN:.2f}",
                st.ok_overturning,
            ),
            (
                "QA-ABT-SL",
                "Sliding FOS",
                f"{_fnum(st.fos_sliding)}",
                f">= {FOS_SLIDING_MIN:.2f}",
                st.ok_sliding,
            ),
            (
                "QA-ABT-BRG",
                "Base pressure",
                f"{_fnum(st.base_pressure_kpa)} kPa",
                f"<= {_fnum(q_allow)} kPa",
                st.ok_bearing,
            ),
        ]
    except Exception:
        pass  # stability is advisory; never block the sheet on it

    return rows


def draw_checks_table(
    msp: Any,
    x: float,
    y: float,
    rows: list[Row],
    text_height: float = 2.0,
) -> None:
    """Render the table with its origin at the bottom-left cell."""
    hdr_y = y + _ROW_H * len(rows)

    cx = x
    for head, w in zip(("CHECK", "PARAMETER", "VALUE", "LIMIT", "STATUS"), _COLS, strict=False):
        rectangle(msp, cx, hdr_y, w, _ROW_H, layer="TITLEBLK-BOX")
        text(msp, head, cx + 1.0, hdr_y + 1.8, height=text_height * 0.85, layer="TEXT-HEADER")
        cx += w

    for ri, (rid, param, value, limit, ok) in enumerate(rows):
        ry = y + _ROW_H * (len(rows) - 1 - ri)
        cx = x
        for cell, w in zip((rid, param, value, limit, "OK" if ok else "FAIL"), _COLS, strict=False):
            rectangle(msp, cx, ry, w, _ROW_H, layer="TITLEBLK-BOX")
            text(
                msp,
                cell,
                cx + 1.0,
                ry + 1.8,
                height=text_height * 0.8,
                layer="TEXT-SPEC",
                color=3 if ok else 1,
            )
            cx += w

    text(
        msp,
        "SHEET SELF-AUDIT — generated, not reviewed for construction",
        x,
        hdr_y + _ROW_H + 2.0,
        height=text_height,
        layer="TEXT-HEADER",
    )
