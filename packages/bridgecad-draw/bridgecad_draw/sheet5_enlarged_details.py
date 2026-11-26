"""bridgecad_draw.sheet5_enlarged_details — Sheets 5A / 5B enlarged details.

Shortcoming fixed: Sheet 5 squeezes pier elevation, pier section, abutment
elevation/section and wing wall into one A1 at 1:75, so 2.5 mm annotations and
thin members are barely legible on a print. These sheets lift the pier half
(5A) and the abutment half (5B) of Sheet 5 onto their own A1 at the largest
standard scale that fits, so geometry and text grow together.

The geometry is *not* redrawn: Sheet 5 is built once at its own scale, the
half's entities are copied and uniformly scaled. Pier and abutment stay
byte-for-byte consistent with Sheet 5.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from ezdxf import bbox
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Matrix44

from .dxf_engine import new_sheet, save
from .titleblocks import draw_border, draw_title_block

Part = Literal["pier", "abutment"]

#: Standard enlarged-detail rungs, largest first.
SCALE_RUNGS = (10, 20, 25, 30, 40, 50)
_SHEET5_DENOM = 75
_SKIP_PREFIXES = ("BORDER", "TITLEBLK", "TEXT-TITLE")
_STALE_SCALE = re.compile(r"scale\s*:?\s*1\s*:\s*\d+", re.I)
#: Usable A1 drawing area (mm) left of the title block, inside the border.
_AREA = (20.0, 60.0, 640.0, 560.0)  # x0, y0, x1, y1


def _sheet5_doc(project: Any):
    from . import sheet5_pier_abutment_details as s5

    doc, msp = new_sheet("S5 source")
    s5._draw(msp, project, _SHEET5_DENOM)
    return doc, msp


def _copy_missing_arrow_blocks(src_doc: Any, dst_doc: Any) -> None:
    """Unused stub kept as documentation placeholder. See EP-2026-12 notes."""
    pass


def _split_x(msp: Any) -> float:
    border = [e for e in msp if e.dxf.layer == "BORDER-INNER"]
    ext = bbox.extents(border) if border else bbox.extents(msp)
    return (ext.extmin.x + ext.extmax.x) / 2.0


def _select(msp: Any, part: Part) -> list:
    split = _split_x(msp)
    out = []
    for e in msp:
        if e.dxf.layer.upper().startswith(_SKIP_PREFIXES):
            continue
        if e.dxftype() in ("TEXT", "MTEXT") and _STALE_SCALE.search(e.dxf.text or ""):
            continue  # Sheet 5's own 1:75 caption would be wrong here
        ext = bbox.extents([e])
        if not ext.has_data:
            continue
        cx = (ext.extmin.x + ext.extmax.x) / 2.0
        if (cx < split) == (part == "pier"):
            out.append(e)
    return out


def pick_scale(width_mm_at_75: float, height_mm_at_75: float) -> int:
    aw, ah = _AREA[2] - _AREA[0], _AREA[3] - _AREA[1]
    for denom in SCALE_RUNGS:
        k = _SHEET5_DENOM / denom
        if width_mm_at_75 * k <= aw and height_mm_at_75 * k <= ah:
            return denom
    return _SHEET5_DENOM


def generate(project: Any, output_path: str | Path, part: Part = "pier") -> Path:
    if part not in ("pier", "abutment"):
        raise ValueError("part must be 'pier' or 'abutment'")
    src_doc, src = _sheet5_doc(project)
    ents = _select(src, part)
    if not ents:
        raise RuntimeError(f"no {part} geometry found on Sheet 5")
    ext = bbox.extents(ents)
    denom = pick_scale(ext.size.x, ext.size.y)
    k = _SHEET5_DENOM / denom

    doc, msp = new_sheet(f"S5{'A' if part == 'pier' else 'B'} Enlarged {part}")
    pm = project.project_master
    draw_border(msp, "A1")
    draw_title_block(
        msp,
        project_title=getattr(pm, "project_title", "") or "",
        bridge_name=getattr(pm, "bridge_name", "") or "",
        drawing_no=(getattr(pm, "drawing_no", "GAD-005") or "GAD-005") + ("A" if part == "pier" else "B"),
        drawing_title=f"ENLARGED {part.upper()} DETAILS",
        revision=getattr(getattr(pm, "revision", None), "name", "R0") or "R0",
        scale_str=f"1:{denom}",
        sheet_no="5A" if part == "pier" else "5B",
        total_sheets="9",
    )
    cx_t = (_AREA[0] + _AREA[2]) / 2.0
    cy_t = (_AREA[1] + _AREA[3]) / 2.0
    m = (
        Matrix44.translate(-ext.center.x, -ext.center.y, 0)
        @ Matrix44.scale(k, k, k)
        @ Matrix44.translate(cx_t, cy_t, 0)
    )
    for e in ents:
        c = e.copy()
        c.transform(m)
        msp.add_entity(c)

    # Copied DIMENSION entities carry INSERT references to arrow-head blocks
    # (e.g. ``_CLOSEDFILLED``) that live in the source document.  The blocks
    # do not follow the copy, so ezdxf raises DXFStructureError when any tool
    # tries to traverse the entity graph (bbox, audit, CAD open).
    #
    # Fix: re-render every DIMENSION in the new document.  ``render()`` builds
    # a fresh anonymous geometry block in the target document's block table,
    # replacing the stale cross-document INSERT references.  Any dimension whose
    # render fails is left as-is; it still represents the correct measurement,
    # it just won't have arrow geometry.
    from .dim_style import DimStyleConfig, apply_native_dimensions

    apply_native_dimensions(doc, DimStyleConfig(units="m", decimals=3), denom)

    msp.add_text(
        f"ENLARGED {part.upper()} DETAILS  —  SCALE 1:{denom}",
        height=5.0,
        dxfattribs={"layer": "TEXT-TITLE", "style": "BRIDGE_BOLD"},
    ).set_placement((cx_t, _AREA[1] - 25.0), align=TextEntityAlignment.MIDDLE_CENTER)
    return save(doc, output_path)
