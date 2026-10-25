"""
bridgecad_draw.sheet6_bearings_joints — Sheet 6: Bearings & Expansion Joints.

Draws:
  1. Bearing schedule table (all rows from BearingsJoints model)
  2. Bearing pad plan + section sketches (elastomeric / POT / spherical)
  3. Expansion joint schedule table
  4. Expansion joint section sketch (strip seal / modular)
  5. Notes on installation, maintenance intervals
  6. Title block + border (Sheet 6 of 7)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dxf_engine import new_sheet, save
from .primitives import circle, dim_linear_h, dim_linear_v, hatch_rect, rectangle, text
from .titleblocks import draw_border, draw_title_block


def generate(project: Any, output_path: str | Path, scale_denom: int = 20) -> Path:
    doc, msp = new_sheet("S6 Bearings & Joints")
    _draw(msp, project, scale_denom)
    return save(doc, output_path)


def _draw(msp: Any, project: Any, scale_denom: int = 20) -> None:
    bj = project.bearings_joints
    pm = project.project_master

    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-006") or "GAD-006",
        drawing_title="BEARINGS AND EXPANSION JOINTS SCHEDULE",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        sheet_no="6",
        total_sheets="8",
    )

    th = 2.8

    # ── BEARING SCHEDULE TABLE ────────────────────────────────────────────
    tx, ty = 25.0, 490.0
    b_headers = [
        "Location",
        "Type",
        "Size X\n(mm)",
        "Size Y\n(mm)",
        "Load\n(kN)",
        "Movement",
        "Layers",
        "Qty",
    ]
    b_col_w = [55, 45, 20, 20, 22, 30, 18, 14]
    row_h = 10.0

    text(msp, "BEARING SCHEDULE (IRC:83)", tx, ty + row_h * 2, height=th * 1.2, layer="TEXT-HEADER")
    _table(msp, tx, ty, b_headers, b_col_w, row_h, th)

    rows = getattr(bj, "bearing_schedule", [])
    for i, br in enumerate(rows):
        y = ty - (i + 1) * row_h
        vals = [
            getattr(br, "location", "") or "",
            getattr(getattr(br, "bearing_type", None), "name", "") or "",
            str(getattr(br, "size_x_mm", "") or ""),
            str(getattr(br, "size_y_mm", "") or ""),
            str(float(getattr(br, "design_load_kn", 0) or 0)),
            getattr(br, "fixed_or_guide_or_free", "") or "",
            str(getattr(br, "elastomeric_layers_count", "") or ""),
            str(getattr(br, "quantity", 1)),
        ]
        x = tx
        for val, cw in zip(vals, b_col_w, strict=False):
            rectangle(msp, x, y, cw, row_h, layer="TITLEBLK-BOX")
            text(msp, str(val)[:12], x + 1.5, y + 2.5, height=th * 0.85, layer="TEXT-GENERAL")
            x += cw

    # ── BEARING SKETCH (elastomeric pad) ──────────────────────────────────
    bx, by = 530.0, 420.0
    sc = 15.0  # mm per 100mm
    bw = 450 * sc / 100
    450 * sc / 100
    bt = 60 * sc / 100
    # ── Audit-required STRUC-OUTLINE layer bounding box around bearing sketches ──
    rectangle(msp, bx - 15, by - 15, bw + 30, 250, layer="STRUC-OUTLINE", lw=30)
    rectangle(msp, bx, by, bw, bt, layer="SUB-BEARING", lw=40)
    hatch_rect(msp, bx, by, bw, bt, pattern="ANSI31", scale=sc * 0.02, layer="STRUC-HATCHING")
    text(
        msp,
        "ELASTOMERIC PAD",
        bx + bw / 2,
        by + bt + th,
        height=th,
        layer="TEXT-GENERAL",
        halign="CENTER",
    )
    dim_linear_h(
        msp,
        bx,
        by - th * 3,
        bx + bw,
        by - th * 3,
        dim_y=by - th * 3,
        label=f"{int(bw/sc*100)} mm",
        text_height=th * 0.85,
    )
    dim_linear_v(
        msp,
        bx + bw + th * 3,
        by,
        bx + bw + th * 3,
        by + bt,
        dim_x=bx + bw + th * 9,
        label=f"{int(bt/sc*100)} mm",
        text_height=th * 0.85,
    )

    # POT bearing sketch
    px2, py2 = 530.0, 330.0
    25 * sc / 100
    circle(msp, px2 + bw / 2, py2 + bw / 2, bw / 2, layer="SUB-BEARING")
    circle(msp, px2 + bw / 2, py2 + bw / 2, bw / 2 * 0.6, layer="SUB-BEARING")
    text(
        msp,
        "POT / PTFE BEARING — PLAN",
        px2 + bw / 2,
        py2 + bw + th * 1.5,
        height=th,
        layer="TEXT-GENERAL",
        halign="CENTER",
    )

    # ── EXPANSION JOINT SCHEDULE TABLE ───────────────────────────────────
    ej_tx, ej_ty = 25.0, 280.0
    ej_headers = [
        "Location",
        "Type",
        "Width\n(mm)",
        "Movement\n(±mm)",
        "Gap\n(mm)",
        "Length\n(m)",
        "Qty",
    ]
    ej_col_w = [55, 50, 22, 28, 18, 22, 14]

    text(
        msp,
        "EXPANSION JOINT SCHEDULE (IRC SP:55)",
        ej_tx,
        ej_ty + row_h * 2,
        height=th * 1.2,
        layer="TEXT-HEADER",
    )
    _table(msp, ej_tx, ej_ty, ej_headers, ej_col_w, row_h, th)

    ej_rows = getattr(bj, "expansion_joint_schedule", [])
    for i, er in enumerate(ej_rows):
        y = ej_ty - (i + 1) * row_h
        vals = [
            getattr(er, "location", "") or "",
            getattr(getattr(er, "joint_type", None), "name", "") or "",
            str(getattr(er, "width_mm", "") or ""),
            str(getattr(er, "movement_range_mm", "") or ""),
            str(getattr(er, "gap_mm", "") or ""),
            str(float(getattr(er, "transverse_length_m", 0) or 0)),
            str(getattr(er, "quantity", 1)),
        ]
        x = ej_tx
        for val, cw in zip(vals, ej_col_w, strict=False):
            rectangle(msp, x, y, cw, row_h, layer="TITLEBLK-BOX")
            text(msp, str(val)[:12], x + 1.5, y + 2.5, height=th * 0.85, layer="TEXT-GENERAL")
            x += cw

    # ── EXPANSION JOINT SKETCH (strip seal) ───────────────────────────────
    jx, jy = 530.0, 220.0
    jw = 80 * sc / 100
    jt = 40 * sc / 100
    for side in [-1, 1]:
        sx = jx + bw / 2 + side * (jw * 1.2)
        rectangle(msp, sx - jw / 4, jy, jw / 2, jt * 2, layer="SUB-EXPJOINT", lw=35)
        hatch_rect(
            msp,
            sx - jw / 4,
            jy,
            jw / 2,
            jt * 2,
            pattern="ANSI31",
            scale=sc * 0.015,
            layer="STRUC-HATCHING",
        )
    # Seal
    text(
        msp,
        "STRIP SEAL",
        jx + bw / 2,
        jy + jt * 3,
        height=th,
        layer="TEXT-GENERAL",
        halign="CENTER",
    )
    text(
        msp,
        "▼ GAP ▼",
        jx + bw / 2,
        jy + jt,
        height=th * 0.85,
        layer="SUB-EXPJOINT",
        halign="CENTER",
    )

    # ── Notes ─────────────────────────────────────────────────────────────
    notes_y = 130.0
    notes = [
        "BEARING & EXPANSION JOINT NOTES:",
        "1. Bearings shall conform to IRC:83 (Parts I, II, III) as applicable.",
        "2. Elastomeric bearings: shore hardness 60±5, compression set ≤25%.",
        "3. POT bearings: pot pressure ≤35 MPa; PTFE sliding surface Ra≤0.4μm.",
        "4. Strip seal joints: neoprene seal ASTM D2000; anchor steel S355JR HDG.",
        "5. Bearing replacement provision: jacking sockets at each bearing seat.",
        "6. Inspect bearings every 5 years; replace elastomeric pads at 25 years.",
    ]
    for i, n in enumerate(notes):
        text(
            msp,
            n,
            25.0,
            notes_y - i * 7.5,
            height=th * (1.0 if i == 0 else 0.85),
            layer="TEXT-SPEC" if i > 0 else "TEXT-GENERAL",
        )


def _table(msp, tx, ty, headers, col_w, row_h, th):
    x = tx
    for h, cw in zip(headers, col_w, strict=False):
        rectangle(msp, x, ty, cw, row_h, layer="TITLEBLK-BOX")
        text(msp, h.replace("\n", " "), x + 1.5, ty + 2.5, height=th * 0.85, layer="TEXT-GENERAL")
        x += cw


__all__ = ["generate"]
