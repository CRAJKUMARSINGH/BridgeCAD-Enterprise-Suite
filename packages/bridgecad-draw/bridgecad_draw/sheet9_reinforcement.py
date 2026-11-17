"""
bridgecad_draw.sheet9_reinforcement — Sheet 9: Reinforcement Schedule & Steel Ledger.

Grid columns: MARK / ELEMENT-FACE / D / As,req / DESIGN / DIA / SPACING /
As,prov / UTIL / STATUS.  Utilisation above 100 % shades the status cell
orange; the ledger strip above the grid totals the steel.

Below the schedule the sheet carries a **bar-arrangement detail** — an abutment
shaft / cap / dirt-wall section with the main bars, links and bar-mark
call-outs.  A schedule alone is not detailing: the arrangement shows where the
scheduled bars sit, and every call-out value (dia @ spacing, section depth,
cover) is read from the detailing store or the declared model inputs, never
invented.  The detail is schematic, so it says so.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from bridgecad_core.detailing import ledger, store_for

from .dxf_engine import new_sheet, save
from .primitives import circle, line, rectangle, text
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
        # A bar schedule is a table, not a plotted view.
        scale_str="NTS",
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

    _draw_bar_detail(msp, project, items, th)


def _eff_dia_spacing(item: Any) -> tuple[int, int]:
    """Effective ``(dia_mm, spacing_mm)`` actually scheduled for *item*."""
    dia = item.dia_mm if item.dia_mm is not None else item.design_dia_mm
    spc = item.spacing_mm if item.spacing_mm is not None else item.design_spacing_mm
    return int(dia), int(spc)


def _cover_label(project: Any) -> str:
    """Nominal cover from the *declared* classification, never invented.

    ``Materials.concrete_cover_*`` carries a ``ConcreteCoverNominalClass`` whose
    value leads with the millimetre figure (``"30mm_SEVERE_M3"``).  A project
    that declares no cover gets a statement saying so rather than a fabricated
    default — an assumed cover is a design decision, not a drawing convenience.
    """
    mat = getattr(project, "materials", None)
    parts: list[str] = []
    for attr, label in (
        ("concrete_cover_superstructure_mm", "SUPERSTRUCTURE"),
        ("concrete_cover_substructure_mm", "SUBSTRUCTURE"),
        ("concrete_cover_foundation_mm", "FOUNDATION"),
    ):
        val = getattr(mat, attr, None) if mat is not None else None
        if val is None:
            continue
        raw = str(getattr(val, "value", val))
        m = re.match(r"\s*(\d+)", raw)
        if m:
            parts.append(f"{label} {m.group(1)} mm")
    if not parts:
        return "COVER / DURABILITY: NOT DECLARED IN PROJECT INPUTS — NO COVER ASSUMED."
    return "NOMINAL COVER: " + "  |  ".join(parts)


def _draw_bar_detail(msp: Any, project: Any, items: list[Any], th: float) -> None:
    """Bar-arrangement detail: shaft/cap/dirt-wall section with bar marks.

    Drawn schematically — the bar count is indicative of the declared spacing,
    and every call-out value is read from the detailing store.  The geometry
    lands on the registered ``REBAR`` / ``STRUC-DETAIL`` layers so the sheet
    carries real linework, not only table cells.
    """
    by_mark = {it.mark: it for it in items}

    # ── caption ───────────────────────────────────────────────────────────
    text(
        msp,
        "TYPICAL ABUTMENT / CAP REINFORCEMENT — TYPICAL SECTION  (SCHEMATIC, NOT TO SCALE)",
        30.0,
        404.0,
        height=th * 1.25,
        layer="TEXT-HEADER",
    )
    text(
        msp,
        "BAR MARKS REFER TO THE SCHEDULE ABOVE;  CALL-OUTS SHOW DIA (mm) @ SPACING (mm).",
        30.0,
        396.0,
        height=th * 0.9,
        layer="TEXT-SPEC",
    )

    # ── abutment shaft (transverse section) ───────────────────────────────
    sx0, sy0, sw, sh = 78.0, 100.0, 150.0, 210.0
    rectangle(msp, sx0, sy0, sw, sh, layer="STRUC-DETAIL", lw=35)

    n_bars = 7
    for i in range(n_bars):
        yy = sy0 + 12.0 + i * (sh - 24.0) / (n_bars - 1)
        circle(msp, sx0 + 9.0, yy, 2.2, layer="REBAR")
        circle(msp, sx0 + sw - 9.0, yy, 2.2, layer="REBAR")

    # links / stirrups
    rectangle(msp, sx0 + 9.0, sy0 + 12.0, sw - 18.0, sh - 24.0, layer="REBAR", lw=20)
    for i in range(1, 4):
        yy = sy0 + 12.0 + i * (sh - 24.0) / 4.0
        line(msp, (sx0 + 9.0, yy), (sx0 + sw - 9.0, yy), layer="REBAR")

    # ── abutment cap (sits on the shaft) ──────────────────────────────────
    cx0, cy0, cw, ch = 58.0, sy0 + sh, 190.0, 42.0
    rectangle(msp, cx0, cy0, cw, ch, layer="STRUC-DETAIL", lw=35)
    for i in range(8):
        xx = cx0 + 14.0 + i * (cw - 28.0) / 7.0
        circle(msp, xx, cy0 + ch - 13.0, 2.2, layer="REBAR")  # C1 top bars
        circle(msp, xx, cy0 + 13.0, 2.2, layer="REBAR")  # C2 bottom bars

    # ── dirt wall (behind the abutment) ───────────────────────────────────
    dx0, dy0, dw, dh = 34.0, 100.0, 36.0, 90.0
    rectangle(msp, dx0, dy0, dw, dh, layer="STRUC-DETAIL", lw=35)
    for xx in (dx0 + 10.0, dx0 + dw - 10.0):
        line(msp, (xx, dy0 + 8.0), (xx, dy0 + dh - 8.0), layer="REBAR")
    for i in range(1, 4):
        yy = dy0 + i * dh / 4.0
        line(msp, (dx0 + 6.0, yy), (dx0 + dw - 6.0, yy), layer="REBAR")

    # ── bar-mark call-outs (values read from the store) ───────────────────
    def _callout(
        mark: str, anchor: tuple[float, float], lbl_x: float, lbl_y: float, desc: str
    ) -> None:
        item = by_mark.get(mark)
        if item is None:
            return
        dia, spc = _eff_dia_spacing(item)
        line(msp, anchor, (lbl_x - 2.0, lbl_y + 0.8), layer="REBAR")
        text(
            msp,
            f"{mark}  {dia}Ø @ {spc}  ({desc})",
            lbl_x,
            lbl_y,
            height=th * 0.9,
            layer="TEXT-SPEC",
        )

    _callout("C1", (cx0 + cw - 10.0, cy0 + ch - 13.0), 270.0, 344.0, "CAP TOP BARS")
    _callout("C2", (cx0 + cw - 10.0, cy0 + 13.0), 270.0, 326.0, "CAP BOTTOM BARS")
    _callout("A1", (sx0 + sw - 9.0, 250.0), 270.0, 250.0, "SHAFT MAIN VERTICAL")
    _callout("A2", (sx0 + sw - 9.0, 232.0), 270.0, 232.0, "SHAFT LINKS")

    # dirt-wall call-outs sit below the wall so no leader crosses the shaft
    for mark, yy, desc in (
        ("D1", 88.0, "DIRT WALL VERTICAL"),
        ("D2", 78.0, "DIRT WALL HORIZONTAL"),
    ):
        item = by_mark.get(mark)
        if item is None:
            continue
        dia, spc = _eff_dia_spacing(item)
        text(
            msp,
            f"{mark}  {dia}Ø @ {spc}  ({desc})",
            dx0,
            yy,
            height=th * 0.9,
            layer="TEXT-SPEC",
        )

    # ── cover + section depths (derived, never invented) ──────────────────
    text(msp, _cover_label(project), 270.0, 110.0, height=th * 0.9, layer="TEXT-SPEC")
    a1 = by_mark.get("A1")
    c1 = by_mark.get("C1")
    if a1 is not None and c1 is not None:
        text(
            msp,
            f"SECTION DEPTH  SHAFT {a1.section_depth_mm} mm  |  CAP {c1.section_depth_mm} mm",
            270.0,
            92.0,
            height=th * 0.9,
            layer="TEXT-SPEC",
        )


__all__ = ["generate"]
