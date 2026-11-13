"""
bridgecad_draw.titleblocks — IRC / NHAI / MORTH title block generator.

A title block occupies the bottom-right corner of the sheet.
Standard dimensions (A1 landscape, 841 × 594 mm):
  - Sheet border:     inner margin 10 mm from edge
  - Title block:      180 mm wide × 55 mm tall, bottom-right
  - Revision table:   50 mm wide × full title-block height, left of title block

All coordinates are in mm (model space, 1 unit = 1 mm).
"""

from __future__ import annotations

from typing import Any

from .coordinates import TITLE_BLOCK, check_declared
from .primitives import rectangle, text

# ---------------------------------------------------------------------------
# Sheet size constants (mm)
# ---------------------------------------------------------------------------
_SHEET_SIZES: dict[str, tuple[float, float]] = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
}

_MARGIN = 10.0  # mm outer margin
_TB_H = 55.0  # title block height mm
_TB_W = 185.0  # title block width mm
_REV_W = 45.0  # revision strip width mm

#: Legible text height on PAPER, in millimetres. Model-space text is this
#: multiplied by the sheet's plot scale — see ``draw_sheet_frame``.
TEXT_HEIGHT_MM = 2.5

#: Measured advance of the sheet text style: millimetres of run per millimetre
#: of text height, including the inter-character space.  It is used to keep a
#: long caption inside its cell instead of running it past the frame —
#: "DRAWING TITLE: GENERAL ARRANGEMENT — LONGITUDINAL SECTION" (57 characters)
#: at 3.8 mm measured 185 mm of run and ended 2 mm past the 831 mm border.
_ADVANCE_FRAC = 0.86

#: Height of the bold DRAWING TITLE caption.  Reduced from 3.8 so the longest
#: sheet title fits the 185 mm block untruncated.
_DRAWING_TITLE_H = 3.2


def _clip(s: str, max_w_mm: float, h_mm: float) -> str:
    """Truncate *s* to the characters that cannot run past *max_w_mm*.

    A best-effort guard, not a text engine: it stops a long project name or
    drawing title from bleeding off the sheet, which a plot clips silently.
    """
    room = int(max_w_mm / max(_ADVANCE_FRAC * h_mm, 0.01))
    return s if len(s) <= room else s[: max(1, room)]


def draw_border(msp: Any, sheet_size: str = "A1") -> tuple[float, float]:
    """Draw outer and inner sheet borders.

    Returns
    -------
    (sheet_w, sheet_h) : tuple
        Full sheet dimensions in mm.
    """
    sw, sh = _SHEET_SIZES.get(sheet_size.upper(), _SHEET_SIZES["A1"])
    m = _MARGIN
    # Outer border
    rectangle(msp, 0, 0, sw, sh, layer="BORDER-OUTER")
    # Inner border (drawing area)
    rectangle(msp, m, m, sw - 2 * m, sh - 2 * m, layer="BORDER-INNER")
    return sw, sh


def draw_title_block(
    msp: Any,
    project_title: str = "",
    bridge_name: str = "",
    drawing_no: str = "GAD-001",
    drawing_title: str = "GENERAL ARRANGEMENT DRAWING",
    revision: str = "R0",
    date_str: str = "",
    designed_by: str = "",
    checked_by: str = "",
    approved_by: str = "",
    client: str = "",
    consultant: str = "",
    scale_str: str = "",
    sheet_no: str = "1",
    total_sheets: str = "1",
    sheet_size: str = "A1",
) -> None:
    """Draw the IRC SP:55-2019 standard title block in the bottom-right corner.

    Layout (5 rows, bottom to top):
      Row 0 (10mm): DRG | REVISION | DATE | SHEET n OF m
      Row 1 (10mm): DRAWN | CHECKED | APPROVED
      Row 2 (10mm): SCALE | CLIENT
      Row 3 (12mm): CONSULTANT
      Row 4 (13mm): DRAWING TITLE (bold)
    Plus PROJECT + BRIDGE name text ABOVE the block.

    Every field is emitted with its LABEL, so the block is self-describing and
    the DXF-contract check (``assert_title_block_filled`` /
    ``assert_sheet_annotation``) can find ``PROJECT``, ``DRAWING TITLE``,
    ``SCALE``, ``DRAWN``, ``CHECKED``, ``REVISION`` and ``SHEET n OF m`` as text
    rather than having to infer them from bare values.
    """
    sw, sh = _SHEET_SIZES.get(sheet_size.upper(), _SHEET_SIZES["A1"])
    m = _MARGIN

    tb_x0 = sw - m - _TB_W
    tb_y0 = m
    sw - m
    tb_y1 = m + _TB_H

    # Outer box — heavy border
    rectangle(msp, tb_x0, tb_y0, _TB_W, _TB_H, layer="TITLEBLK-BOX", lw=50)

    row_h = [10.0, 10.0, 10.0, 12.0, 13.0]
    ys = [tb_y0]
    for rh in row_h:
        ys.append(ys[-1] + rh)

    def _cell(
        x0: float,
        y0: float,
        w: float,
        h: float,
        val: str,
        th: float = 2.8,
        layer: str = "TITLEBLK-TEXT",
        bold: bool = False,
    ) -> None:
        rectangle(msp, x0, y0, w, h, layer="TITLEBLK-BOX", lw=18)
        if val:
            display = _clip(str(val), w - 3.0, th)
            lyr = "TEXT-TITLE" if bold else "TITLEBLK-TEXT"
            text(msp, display, x0 + 1.5, y0 + h / 2 - th / 2, height=th, layer=lyr)

    # ── Row 0: drg number / revision / date / sheet ─────────────────────────
    r0y, r0h = ys[0], row_h[0]
    _cell(tb_x0, r0y, 65, r0h, f"DRG: {drawing_no}", th=2.8)
    _cell(tb_x0 + 65, r0y, 30, r0h, f"REVISION: {revision}", th=2.8)
    _cell(tb_x0 + 95, r0y, 45, r0h, f"DATE: {date_str}", th=2.8)
    _cell(tb_x0 + 140, r0y, _TB_W - 140, r0h, f"SHEET {sheet_no} OF {total_sheets}", th=2.8)

    # ── Row 1: drawn / checked / approved ────────────────────────────────────
    r1y, r1h = ys[1], row_h[1]
    _cell(tb_x0, r1y, 62, r1h, f"DRAWN: {designed_by}", th=2.5)
    _cell(tb_x0 + 62, r1y, 62, r1h, f"CHECKED: {checked_by}", th=2.5)
    _cell(tb_x0 + 124, r1y, _TB_W - 124, r1h, f"APPROVED: {approved_by}", th=2.5)

    # ── Row 2: scale / client ────────────────────────────────────────────────
    r2y, r2h = ys[2], row_h[2]
    _cell(tb_x0, r2y, 55, r2h, f"SCALE: {scale_str}", th=2.8)
    _cell(tb_x0 + 55, r2y, _TB_W - 55, r2h, f"CLIENT: {client}", th=2.8)

    # ── Row 3: consultant ────────────────────────────────────────────────────
    r3y, r3h = ys[3], row_h[3]
    _cell(tb_x0, r3y, _TB_W, r3h, f"CONSULTANT: {consultant}", th=3.0)

    # ── Row 4 (top): drawing title — bold + larger ───────────────────────────
    r4y, r4h = ys[4], row_h[4]
    rectangle(msp, tb_x0, r4y, _TB_W, r4h, layer="TITLEBLK-BOX", lw=30)
    text(
        msp,
        _clip(f"DRAWING TITLE: {drawing_title}", _TB_W - 3.5, _DRAWING_TITLE_H),
        tb_x0 + 2.0,
        r4y + r4h / 2 - 2.0,
        height=_DRAWING_TITLE_H,
        layer="TEXT-TITLE",
    )

    # ── Project title + bridge name above block ───────────────────────────────
    _cap_w = sw - m - tb_x0 - 1.0
    text(
        msp,
        _clip(f"PROJECT: {project_title}", _cap_w, 3.2),
        tb_x0,
        tb_y1 + 3.5,
        height=3.2,
        layer="TEXT-TITLE",
    )
    text(
        msp,
        _clip(f"BRIDGE: {bridge_name}", _cap_w, 2.8),
        tb_x0,
        tb_y1 + 8.5,
        height=2.8,
        layer="TITLEBLK-TEXT",
    )


def draw_revision_strip(
    msp: Any,
    revisions: list[tuple[str, str, str]] | None = None,
    sheet_size: str = "A1",
) -> None:
    """Draw the revision history strip to the left of the title block.

    *revisions* is a list of (rev_tag, date, description) tuples.
    """
    sw, sh = _SHEET_SIZES.get(sheet_size.upper(), _SHEET_SIZES["A1"])
    m = _MARGIN
    strip_x0 = sw - m - _TB_W - _REV_W
    strip_y0 = m
    strip_h = _TB_H

    rectangle(msp, strip_x0, strip_y0, _REV_W, strip_h, layer="TITLEBLK-BOX", lw=25)

    # Header
    hh = 6.0
    rectangle(msp, strip_x0, strip_y0 + strip_h - hh, _REV_W, hh, layer="TITLEBLK-BOX", lw=25)
    text(
        msp,
        "REVISION HISTORY",
        strip_x0 + 1.5,
        strip_y0 + strip_h - hh + 1.5,
        height=2.5,
        layer="TITLEBLK-TEXT",
    )

    row_h = 8.0
    y = strip_y0 + strip_h - hh - row_h
    for rev, dt, desc in (revisions or [])[:5]:
        rectangle(msp, strip_x0, y, _REV_W, row_h, layer="TITLEBLK-BOX", lw=13)
        text(
            msp,
            f"{rev}  {dt}  {desc[:20]}",
            strip_x0 + 1.5,
            y + 2.0,
            height=2.2,
            layer="TITLEBLK-TEXT",
        )
        y -= row_h


def draw_sheet_frame(
    msp: Any,
    sheet: str,
    *,
    drawing_no: str = "GAD-001",
    drawing_title: str = "GENERAL ARRANGEMENT DRAWING",
    sheet_index: int = 1,
    total_sheets: int = 7,
    revision: str = "R0",
    date_str: str = "",
    drawn_by: str = "",
    checked_by: str = "",
    approved_by: str = "",
    project_title: str = "BRIDGE PROJECT",
    bridge_name: str = "",
    client: str = "",
    consultant: str = "",
) -> tuple[float, float]:
    """Draw the border and title block for *sheet*, in MODEL millimetres.

    THE UNIT RULE
        Model space is 1:1 millimetre, so a 1:100 sheet draws 100 mm of model
        per paper millimetre. Every length here is therefore a paper length
        multiplied by ``frame.plot_scale`` — the frame, the margin, the title
        block, and every text height. Getting this backwards is invisible on
        screen and unreadable in print.

    Returns ``(frame_w, frame_h)`` in model millimetres: the usable frame is the
    declared drawing region, ``width`` x ``height - title block height``.
    """
    frame = check_declared(sheet)
    s = float(frame.plot_scale)
    th = TEXT_HEIGHT_MM * s

    w = frame.width_mm * s
    h = (frame.height_mm - TITLE_BLOCK["height_mm"]) * s

    rectangle(msp, 0.0, 0.0, w, h, layer="BORDER-OUTER")
    margin = _MARGIN * s
    rectangle(msp, margin, margin, w - 2 * margin, h - 2 * margin, layer="BORDER-INNER")

    tb_w = TITLE_BLOCK["width_mm"] * s
    tb_h = TITLE_BLOCK["height_mm"] * s
    tb_x0 = w - margin - tb_w
    tb_y0 = margin

    rectangle(msp, tb_x0, tb_y0, tb_w, tb_h, layer="TITLEBLK-BOX", lw=50)

    rows = (
        f"PROJECT: {project_title}",
        f"BRIDGE: {bridge_name}" if bridge_name else "BRIDGE: -",
        f"DRAWING TITLE: {drawing_title}",
        f"DRG: {drawing_no}",
        f"REVISION: {revision}",
        f"DATE: {date_str or '-'}",
        f"SHEET {sheet_index} OF {total_sheets}",
        f"SCALE: 1:{frame.plot_scale}",
        f"DRAWN: {drawn_by or '-'}",
        f"CHECKED: {checked_by or '-'}",
        f"APPROVED: {approved_by or '-'}",
        f"CLIENT: {client or '-'}",
        f"CONSULTANT: {consultant or '-'}",
    )
    row_h = tb_h / len(rows)
    for i, label in enumerate(rows):
        y = tb_y0 + tb_h - (i + 1) * row_h + (row_h - th) / 2
        text(msp, label, tb_x0 + th * 0.4, y, height=th, layer="TITLEBLK-TEXT", halign="LEFT")

    return w, h


__all__ = [
    "draw_border",
    "draw_title_block",
    "draw_revision_strip",
    "draw_sheet_frame",
    "TEXT_HEIGHT_MM",
    "_SHEET_SIZES",
]
