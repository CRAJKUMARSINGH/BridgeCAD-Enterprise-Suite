"""
bridgecad_draw.sheet9_reinforcement — Sheet 9: Reinforcement Schedule & Steel Ledger.

Grid columns: MARK / ELEMENT-FACE / D / As,req / DESIGN / DIA / SPACING /
As,prov / UTIL / STATUS.  Utilisation above 100 % shades the status cell
orange; the ledger strip above the grid totals the steel.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bridgecad_core.detailing import ledger, store_for

from .dxf_engine import new_sheet, save
from .primitives import rectangle, text
from .titleblocks import draw_border, draw_title_block

_HEADERS = (
    "MARK",
    "ELEMENT-FACE",
    "D",
    "As,req",
    "DESIGN",
    "DIA",
    "SPACING",
    "As,prov",
    "UTIL",
    "STATUS",
)
_COLS = (14.0, 44.0, 12.0, 16.0, 16.0, 12.0, 16.0, 16.0, 12.0, 18.0)
_ROW_H = 7.0
_ORANGE = 30  # ACI orange-ish index for over-utilised cells


def generate(project: Any, output_path: str | Path, scale_denom: int = 1) -> Path:
    doc, msp = new_sheet("S9 Reinforcement")
    _draw(msp, project)
    return save(doc, output_path)


def _draw(msp: Any, project: Any) -> None:
    pm = project.project_master

    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-009") or "GAD-009",
        drawing_title="REINFORCEMENT SCHEDULE & STEEL LEDGER",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        sheet_no="9",
        total_sheets="9",
    )

    th = 2.4
    store = store_for(project)
    items = store.items()
    led = ledger(project)

    # ── Ledger strip ──────────────────────────────────────────────────────
    ledger_y = 520.0
    strip = (
        f"TOTAL STEEL {led.total_kg:.0f} kg   |   AUTO {led.design_kg:.0f} kg   |   "
        f"DELTA {led.delta_kg:+.0f} kg ({led.delta_pct:+.1f}%)   |   "
        f"{led.kg_per_m3:.1f} kg/m3   |   USER-DEFINED {led.user_defined_count}   |   "
        f"FAILING {led.failing_count}"
    )
    rectangle(msp, 25.0, ledger_y, 790.0, 12.0, layer="TITLEBLK-BOX", lw=30)
    text(msp, strip, 30.0, ledger_y + 4.0, height=th, layer="TEXT-HEADER")
    if led.failing_count:
        text(
            msp,
            "!! ITEMS OVER-UTILISED — REVIEW BEFORE ISSUE",
            815.0,
            ledger_y + 4.0,
            height=th,
            layer="TEXT-HEADER",
            color=_ORANGE,
            halign="RIGHT",
        )

    # ── Grid ──────────────────────────────────────────────────────────────
    grid_x = 25.0
    grid_y = ledger_y - 10.0 - _ROW_H * (len(items) + 1)

    cx = grid_x
    for head, w in zip(_HEADERS, _COLS, strict=True):
        rectangle(msp, cx, grid_y + _ROW_H * len(items), w, _ROW_H, layer="TITLEBLK-BOX", lw=30)
        text(
            msp,
            head,
            cx + 1.2,
            grid_y + _ROW_H * len(items) + 2.2,
            height=th * 0.85,
            layer="TEXT-HEADER",
        )
        cx += w

    for ri, item in enumerate(items):
        ry = grid_y + _ROW_H * (len(items) - 1 - ri)
        util = float(item.utilisation)
        ok = util <= 1.0
        dia = item.dia_mm if item.dia_mm is not None else item.design_dia_mm
        spc = item.spacing_mm if item.spacing_mm is not None else item.design_spacing_mm
        cells = (
            item.mark,
            f"{item.element}/{item.face}",
            str(item.section_depth_mm),
            f"{float(item.as_required_mm2_per_m):.0f}",
            f"{item.design_dia_mm}@{item.design_spacing_mm}",
            str(dia),
            str(spc),
            f"{float(item.as_provided_mm2_per_m):.0f}",
            f"{util:.2f}",
            "OK" if ok else "OVER",
        )
        cx = grid_x
        for ci, (cell, w) in enumerate(zip(cells, _COLS, strict=True)):
            shade = ci == 9 and not ok
            rectangle(
                msp,
                cx,
                ry,
                w,
                _ROW_H,
                layer="TITLEBLK-BOX",
                color=_ORANGE if shade else None,
                lw=30,
            )
            text(
                msp,
                cell,
                cx + 1.2,
                ry + 2.2,
                height=th * 0.85,
                layer="TEXT-SPEC",
                color=_ORANGE if shade else None,
            )
            cx += w

    # ── Notes ─────────────────────────────────────────────────────────────
    notes = [
        "As,prov = 1000/spacing x pi x (dia/2)^2 mm2/m.  Utilisation = As,req / As,prov; <= 1.0 adequate.",
        "As,req source: minima_table_v1 (IRC:112-2020 minimum steel) — GAD-stage, not a design value.",
        "User-defined rows are reviewer overrides on the detailing store; Reset restores design values.",
    ]
    for i, note in enumerate(notes):
        text(msp, note, 25.0, grid_y - 8.0 - i * 6.0, height=th * 0.9, layer="TEXT-SPEC")


__all__ = ["generate"]
