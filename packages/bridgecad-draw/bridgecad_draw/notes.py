"""Notes, legend and abbreviation blocks.

Content comes from standards/notes.yaml and standards/abbreviations.yaml so a
clause correction is one edit, not eight sheets. Every drawn note carries its
bracketed source, which is what `assert_notes_sourced` checks.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .primitives import line, text
from .text import TextClass, TextSizer

STANDARDS = Path(__file__).parents[3] / "standards"
NOTES_YAML = STANDARDS / "notes.yaml"
ABBREV_YAML = STANDARDS / "abbreviations.yaml"

NOTES_LAYER = "TEXT-SPEC"
LEGEND_LAYER = "TEXT-SPEC"
HEAD_LAYER = "TEXT-HEADER"


@dataclass(frozen=True)
class Note:
    id: str
    group: str
    text: str
    source: str
    sheets: tuple[int, ...]


@dataclass(frozen=True)
class Abbreviation:
    short: str
    expansion: str


@lru_cache(maxsize=1)
def _load_notes() -> dict[str, Note]:
    data = yaml.safe_load(NOTES_YAML.read_text(encoding="utf-8")) or {}
    out: dict[str, Note] = {}
    for nid, e in (data.get("notes") or {}).items():
        out[nid] = Note(
            id=nid,
            group=str(e.get("group", "general")),
            text=str(e["text"]),
            source=str(e["source"]),
            sheets=tuple(int(s) for s in e["sheets"]),
        )
    return out


@lru_cache(maxsize=1)
def _load_abbreviations() -> list[Abbreviation]:
    if not ABBREV_YAML.is_file():
        return []
    data = yaml.safe_load(ABBREV_YAML.read_text(encoding="utf-8")) or {}
    return [Abbreviation(str(k), str(v)) for k, v in (data.get("abbreviations") or {}).items()]


def notes_for(sheet_no: int, group: str | None = None) -> list[Note]:
    return sorted(
        (n for n in _load_notes().values()
         if sheet_no in n.sheets and (group is None or n.group == group)),
        key=lambda n: n.id,
    )


def _wrap(text_: str, width_chars: int) -> list[str]:
    words, lines, cur = text_.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def draw_notes(
    msp: Any,
    sheet_no: int,
    ts: TextSizer,
    x: float,
    y: float,
    *,
    width_mm: float = 120.0,
    char_width_ratio: float = 0.62,
    line_spacing: float = 1.6,
) -> float:
    """Draw the sheet's notes downward from (x, y). Returns the Y after the block."""
    notes = notes_for(sheet_no)
    if not notes:
        return y

    h = ts.h(TextClass.NOTE)
    chars = max(20, int(width_mm / (h * char_width_ratio)))
    pitch = h * line_spacing

    text(msp, "NOTES", x, y, height=ts.h(TextClass.SUBHEAD), layer=HEAD_LAYER)
    y -= pitch * 1.6

    for i, note in enumerate(notes, start=1):
        for j, chunk in enumerate(_wrap(note.text, chars)):
            prefix = f"{i}. " if j == 0 else "   "
            text(msp, prefix + chunk, x, y, height=h, layer=NOTES_LAYER)
            y -= pitch
        y -= pitch * 0.35
    return y


def draw_legend(
    msp: Any,
    used_layers: Iterable[str],
    ts: TextSizer,
    x: float,
    y: float,
    layer_meta: dict[str, Any],
    *,
    row: float | None = None,
) -> float:
    """Legend of only the layers actually drawn on this sheet."""
    used = sorted(set(used_layers))
    if not used:
        return y

    h = ts.h(TextClass.NOTE)
    pitch = row or h * 2.2
    text(msp, "LEGEND", x, y, height=ts.h(TextClass.SUBHEAD), layer=HEAD_LAYER)
    y -= pitch

    for name in used:
        meta = layer_meta.get(name)
        colour = getattr(meta, "color", 7)
        swatch = h * 2.0
        line(msp, (x, y + h * 0.4), (x + swatch, y + h * 0.4), layer=name, color=colour)
        desc = getattr(meta, "description", name)
        text(msp, desc, x + swatch * 1.4, y, height=h, layer=NOTES_LAYER)
        y -= pitch
    return y


def draw_abbreviations(msp: Any, ts: TextSizer, x: float, y: float, *, per_row: int = 2) -> float:
    abbrs = _load_abbreviations()
    if not abbrs:
        return y

    h = ts.h(TextClass.NOTE)
    pitch = h * 1.5
    text(msp, "ABBREVIATIONS", x, y, height=ts.h(TextClass.SUBHEAD), layer=HEAD_LAYER)
    y -= pitch

    col_w = h * 22
    for i, a in enumerate(abbrs):
        col, row_i = i % per_row, i // per_row
        text(
            msp,
            f"{a.short} — {a.expansion}",
            x + col * col_w,
            y - row_i * pitch,
            height=h,
            layer=NOTES_LAYER,
        )
    rows = (len(abbrs) + per_row - 1) // per_row
    return y - rows * pitch


__all__ = ["Note", "notes_for", "draw_notes", "draw_legend", "draw_abbreviations"]
