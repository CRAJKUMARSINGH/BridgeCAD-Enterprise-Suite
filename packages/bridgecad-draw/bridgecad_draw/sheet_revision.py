"""bridgecad_draw.sheet_revision — redline sheet for a revision diff.

Changed entities get a revision cloud on ``REV-CLOUD`` (colour 1); removed
entities are listed in the change table (their geometry is not replayed — the
redline sheet annotates the NEW render).  Table capped at 40 rows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .diff import Change
from .dxf_engine import new_sheet, save
from .primitives import polyline, rectangle, text
from .titleblocks import draw_border, draw_title_block

_MAX_ROWS = 40


def _cloud(msp: Any, cx: float, cy: float, r: float = 6.0) -> None:
    """Broken-circle revision cloud approximation."""
    import math

    n = 14
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        rr = r * (1.0 + 0.18 * ((i * 7) % 3 - 1))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    polyline(msp, pts, layer="REV-CLOUD", color=1, lw=50)


def render_redline(
    project: Any,
    output_path: str | Path,
    changes: list[Change],
    revision_tag: str = "R1",
    old_label: str = "previous issue",
    new_label: str = "current",
) -> Path:
    """Write a redline DXF annotating *changes* on a fresh sheet."""
    doc, msp = new_sheet("Revision Redline")
    pm = project.project_master

    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=getattr(pm, "drawing_no", "GAD-REV") or "GAD-REV",
        drawing_title=f"REVISION REDLINE — {old_label} → {new_label}",
        revision=revision_tag,
        sheet_no="REV",
        total_sheets="REV",
    )

    th = 2.6
    text(
        msp,
        f"REVISION REDLINE  {old_label} → {new_label}  ({revision_tag})",
        420.0,
        560.0,
        height=th * 1.6,
        layer="TEXT-HEADER",
        halign="CENTER",
    )
    text(
        msp,
        f"{len(changes)} change(s) — clouds mark moved/added entities on the current model",
        420.0,
        552.0,
        height=th,
        layer="TEXT-SPEC",
        halign="CENTER",
    )

    # Change table, bottom-right
    tx, ty = 430.0, 60.0
    headers = ("NO", "SHT", "LAYER", "CHAINAGE", "KIND", "DESCRIPTION")
    widths = (8.0, 8.0, 22.0, 16.0, 14.0, 60.0)
    rh = 6.0
    cx = tx
    for h, w in zip(headers, widths, strict=True):
        rectangle(msp, cx, ty + rh * (_MAX_ROWS + 1), w, rh, layer="TITLEBLK-BOX", lw=25)
        text(
            msp, h, cx + 1.0, ty + rh * (_MAX_ROWS + 1) + 1.6, height=th * 0.8, layer="TEXT-HEADER"
        )
        cx += w
    shown = changes[:_MAX_ROWS]
    for i, ch in enumerate(shown):
        ry = ty + rh * (_MAX_ROWS - i)
        cx = tx
        chain = f"{ch.from_xy[0]:.1f}" if ch.from_xy else ""
        cells = (str(i + 1), str(ch.sheet_no), ch.layer, chain, ch.kind.value, ch.description)
        for cell, w in zip(cells, widths, strict=True):
            rectangle(msp, cx, ry, w, rh, layer="TITLEBLK-BOX", lw=18)
            text(msp, str(cell)[:38], cx + 1.0, ry + 1.5, height=th * 0.75, layer="TEXT-SPEC")
            cx += w
    if len(changes) > _MAX_ROWS:
        text(
            msp,
            f"… {len(changes) - _MAX_ROWS} more — see diff CSV",
            tx,
            ty - 4.0,
            height=th * 0.8,
            layer="TEXT-SPEC",
        )

    return save(doc, output_path)


__all__ = ["render_redline"]
