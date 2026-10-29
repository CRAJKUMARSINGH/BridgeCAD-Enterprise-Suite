#!/usr/bin/env python3
"""Every layer a sheet module draws must appear in TRACEABILITY.md.

Week-44 instrument. Blocks on a missing row; warns on an unverified row.

    python scripts/check_traceability.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
MATRIX = ROOT / "docs" / "upgrade" / "TRACEABILITY.md"
DRAW_DIR = ROOT / "packages" / "bridgecad-draw" / "bridgecad_draw"

LAYER_RE = re.compile(r'layer\s*=\s*["\']([A-Z][A-Z0-9-]+)["\']')
ROW_RE = re.compile(r"^\|\s*`?([A-Z][A-Z0-9-]+)`?\s*\|", re.M)


def drawn_layers() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for p in sorted(DRAW_DIR.glob("sheet*.py")):
        found = set(LAYER_RE.findall(p.read_text(encoding="utf-8")))
        if found:
            out[p.name] = found
    return out


def main() -> int:
    if not MATRIX.is_file():
        print(f"  missing {MATRIX.relative_to(ROOT)}")
        return 1

    text = MATRIX.read_text(encoding="utf-8")
    documented = set(ROW_RE.findall(text))
    verified = {
        m.group(1)
        for m in re.finditer(r"^\|\s*`?([A-Z][A-Z0-9-]+)`?\|.*\|\s*☑\s*\|", text, re.M)
    }

    drawn = drawn_layers()
    all_drawn = set().union(*drawn.values()) if drawn else set()

    missing = sorted(all_drawn - documented)
    unverified = sorted(all_drawn & documented - verified)

    for sheet, layers in drawn.items():
        for layer in sorted(layers & set(missing)):
            print(f"  [missing row] {sheet}: {layer}")
    for layer in unverified:
        print(f"  [unverified]  {layer}")

    covered = len(all_drawn) - len(missing)
    pct = 100.0 * covered / len(all_drawn) if all_drawn else 100.0
    print(f"\n  coverage: {covered}/{len(all_drawn)} layers ({pct:.0f}%)")

    if missing:
        return 1
    if pct < 90.0:
        print("  below the 90% gate")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
