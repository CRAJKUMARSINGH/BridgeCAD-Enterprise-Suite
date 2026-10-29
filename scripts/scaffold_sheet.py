#!/usr/bin/env python3
"""Create a new sheet module that cannot be born non-compliant.

Emits the module, its frame entry, its manifest entry and its checklist stub.
The module comes with the frame call, the CoordMapper, the TextSizer, dimstyles,
notes, legend and abbreviations already wired, so the only thing left to write
is the view.

    python scripts/scaffold_sheet.py --no 9 --name side_elevations_alt \
        --title "SIDE ELEVATIONS" --scale 200 --layers SUPER-DECK,SUB-PIER

    python scripts/scaffold_sheet.py ... --dry-run
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parents[1]
DRAW = ROOT / "packages" / "bridgecad-draw" / "bridgecad_draw"
COORDS = DRAW / "coordinates.py"
BOOKLET = DRAW / "booklet.py"
CHECKLISTS = ROOT / "docs" / "checklists"
TEMPLATE = CHECKLISTS / "_TEMPLATE.md"

FRAMES_MARKER = "# <scaffold:frames>"
MANIFEST_MARKER = "# <scaffold:manifest>"

MODULE_TEMPLATE = '''"""Sheet {no} — {title}.

Scaffolded by scripts/scaffold_sheet.py on {today}. Fill the TODO block; do not
add layers to LAYERS_USED without a matching checklist row.
"""

from __future__ import annotations

from typing import Any

from .coordinates import CoordMapper, check_declared
from .dimstyles import setup_dimstyles
from .layers import LAYERS
from .notes import draw_abbreviations, draw_legend, draw_notes
from .primitives import line, text
from .text import TextClass as T, TextSizer
from .titleblocks import TitleBlockData, draw_sheet_frame, draw_title_block

SHEET_KEY = "{frame_key}"
SHEET_NO = {no}
DRAWING_TITLE = "{title}"

#: Layers this sheet is permitted to use. Anything else is a defect.
LAYERS_USED: tuple[str, ...] = (
{layers}
)


def draw(msp: Any, pm: Any, tbd: TitleBlockData, *, allow_blank: bool = False) -> None:
    frame = check_declared(SHEET_KEY)
    ts = TextSizer.from_frame(frame)
    setup_dimstyles(msp.doc, frame)

    region = draw_sheet_frame(msp, SHEET_KEY, tbd, allow_blank=allow_blank)
    cm = CoordMapper(frame)

    used: set[str] = set()

    # ── TODO: the view ────────────────────────────────────────────────
    # Map every model coordinate through cm before drawing. Heights come from
    # ts.h(T.<class>). Every drawn layer must be added to `used`.
    #
    #   x, y = cm.to_paper(chainage_m * 1000.0, rl_m * 1000.0)
    #   line(msp, (x, y), (x2, y2), layer="SUPER-DECK")
    #   used.add("SUPER-DECK")
    #
    # A layer in LAYERS_USED that stays unused is a defect, not a spare.

    # ── sidebar: notes, legend, abbreviations ─────────────────────────
    side = frame.sidebar_mm
    y = side.top - ts.h(T.SUBHEAD)
    y = draw_notes(msp, SHEET_NO, ts, side.left, y, width_mm=side.width)
    y -= ts.h(T.NOTE) * 3
    y = draw_legend(msp, used, ts, side.left, y, LAYERS)
    y -= ts.h(T.NOTE) * 3
    draw_abbreviations(msp, ts, side.left, y)

    # ── title block last, so it sits on top ───────────────────────────
    draw_title_block(msp, tbd, frame, allow_blank=allow_blank)
'''


def _frame_key(name: str) -> str:
    return f"sheet{name}"


def _module_name(no: str, name: str) -> str:
    return f"sheet{no}_{name}"


def _layers_block(layers: list[str]) -> str:
    unknown = [layer for layer in layers if layer not in _known_layers()]
    if unknown:
        raise SystemExit(f"unknown layer(s) not in layers.py: {unknown}")
    return "".join(f'    "{layer}",\n' for layer in layers)


_KNOWN: set[str] | None = None


def _known_layers() -> set[str]:
    global _KNOWN
    if _KNOWN is None:
        src = (DRAW / "layers.py").read_text(encoding="utf-8")
        _KNOWN = set(re.findall(r'["\']([A-Z][A-Z0-9-]+)["\']', src))
    return _KNOWN


def _insert_after_marker(path: Path, marker: str, text: str, fallback: str) -> bool:
    src = path.read_text(encoding="utf-8")
    if marker not in src:
        print(f"  [!] no {marker} in {path.name} — insert manually:\n{fallback}")
        return False
    path.write_text(src.replace(marker, marker + "\n" + text, 1), encoding="utf-8")
    return True


def _content_rows(title: str) -> str:
    rows = [
        ("D1", f"{title} view drawn at the declared scale", "MANUAL: content presence"),
        ("D2", "Every element traces to a model field", "MANUAL: traceability review"),
        ("D3", "Levels match the model within 1 mm", "MANUAL: level check"),
        ("D4", "Section/plan orientation consistent with adjacent sheets", "MANUAL: orientation check"),
    ]
    return "\n".join(
        f"| {i} | {r} | `{a}` | MANUAL | ☐ |" for i, r, a in rows
    )


def _layer_rows(layers: list[str]) -> str:
    return "\n".join(f"| L{i} | `{layer}` used and correctly populated | `layer_used` | AUTO | ☐ |"
                     for i, layer in enumerate(layers, 1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--scale", type=int, default=100)
    ap.add_argument("--layers", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    layers = [layer.strip() for layer in args.layers.split(",") if layer.strip()]
    module = _module_name(args.no, args.name)
    frame_key = _frame_key(args.no)
    dest = DRAW / f"{module}.py"
    checklist = CHECKLISTS / f"sheet{args.no}.md"

    if dest.exists():
        raise SystemExit(f"{dest.name} already exists")
    if checklist.exists():
        raise SystemExit(f"{checklist.name} already exists")

    print(f"  module    {dest.relative_to(ROOT)}")
    print(f"  frame     {frame_key} at 1:{args.scale}")
    print(f"  checklist {checklist.relative_to(ROOT)}")
    print(f"  layers    {layers or '(none)'}")

    if args.dry_run:
        print("\n  dry run")
        return 0

    dest.write_text(
        MODULE_TEMPLATE.format(
            no=args.no, title=args.title, frame_key=frame_key,
            today=date.today().isoformat(), layers=_layers_block(layers),
        ),
        encoding="utf-8",
    )

    checklist.write_text(
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{N}", args.no)
        .replace("{TITLE}", args.title)
        .replace("{FRAME_KEY}", frame_key)
        .replace("{MODULE}", f"{module}.py")
        .replace("{SCALE}", f"1:{args.scale}")
        .replace("{CONTENT_ROWS}", _content_rows(args.title))
        .replace("{LAYER_ROWS}", _layer_rows(layers) or "| — | none | — | — | ☐ |")
        .replace("{CROSS_ROWS}", "| X1 | Alignment with adjacent sheets | `cross_sheet_alignment` | AUTO | ☐ |"),
        encoding="utf-8",
    )

    _insert_after_marker(
        COORDS, FRAMES_MARKER,
        f'    "{frame_key}": SheetFrame("A1", 1.0, 0.0, {args.scale}),',
        f'    "{frame_key}": SheetFrame("A1", 1.0, 0.0, {args.scale}),',
    )
    _insert_after_marker(
        BOOKLET, MANIFEST_MARKER,
        f'    ("{frame_key}", {args.no}, "{args.title}"),',
        f'    ("{frame_key}", {args.no}, "{args.title}"),',
    )

    print("\n  next:")
    print(f"    1. fill the TODO block in {dest.name}")
    print("    2. add rows for any layer you add to LAYERS_USED")
    print("    3. add golden-case xfails to tests/draw/test_golden_current.py")
    print("    4. pytest tests/draw/test_dxf_assert.py && python scripts/check_checklists.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
