#!/usr/bin/env python3
"""Keep the standard and the code saying the same numbers.

The standard is the authority; the code is generated to match. This fails when
they diverge, so nobody arbitrates by memory.

    python scripts/check_drafting_standard.py
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DRAW = ROOT / "packages" / "bridgecad-draw" / "bridgecad_draw"
STANDARD = ROOT / "docs" / "drafting-standard.md"
TEXT = DRAW / "text.py"
LAYERS = DRAW / "layers.py"

HEIGHT_ROW = re.compile(r"^\|\s*`(TITLE|SUBTITLE|SUBHEAD|NOTE|DIM|SMALL)`\s*\|\s*([\d.]+)\s*\|", re.M)
WEIGHT_ROW = re.compile(r"^\|\s*([\d.]+)\s*\|\s*(.+?)\s*\|$", re.M)
BACKTICK = re.compile(r"`([A-Z][A-Z0-9-]+)`")
LAYER_WEIGHT = re.compile(r'"([A-Z][A-Z0-9-]+)"\s*:\s*([\d.]+)')


def _code_heights() -> dict[str, float]:
    tree = ast.parse(TEXT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TextClass":
            out: dict[str, float] = {}
            for stmt in node.body:
                if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                        and isinstance(stmt.targets[0], ast.Name)
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, float)):
                    out[stmt.targets[0].id] = stmt.value.value
            return out
    raise SystemExit("TextClass not found in text.py")


def _code_weights() -> dict[str, float]:
    return dict(LAYER_WEIGHT.findall(LAYERS.read_text(encoding="utf-8")))


def main() -> int:
    doc = STANDARD.read_text(encoding="utf-8")
    errors: list[str] = []

    doc_heights = {k: float(v) for k, v in HEIGHT_ROW.findall(doc)}
    code_heights = _code_heights()
    for cls, value in doc_heights.items():
        if cls not in code_heights:
            errors.append(f"standard has class {cls}, TextClass does not")
        elif abs(code_heights[cls] - value) > 1e-9:
            errors.append(f"{cls}: standard {value} mm, code {code_heights[cls]} mm")
    for cls in sorted(set(code_heights) - set(doc_heights)):
        errors.append(f"TextClass has {cls}, standard does not document it")

    declared = set(doc_heights.values())
    if len(declared) != 6:
        errors.append(f"standard declares {len(declared)} distinct heights, not 6")

    doc_weights = {name: float(w) for w, names in WEIGHT_ROW.findall(doc)
                   for name in BACKTICK.findall(names)}
    code_weights = _code_weights()
    for layer, weight in sorted(doc_weights.items()):
        if layer not in code_weights:
            errors.append(f"standard assigns weight to unknown layer {layer}")
        elif abs(code_weights[layer] - weight) > 1e-9:
            errors.append(f"{layer}: standard {weight} mm, code {code_weights[layer]} mm")
    for layer in sorted(set(code_weights) - set(doc_weights)):
        errors.append(f"layer {layer} has no weight in the standard")

    for e in errors:
        print(f"  [FAIL] {e}")
    print()
    if errors:
        print(f"  standard: FAIL ({len(errors)} drift(s))")
        return 1
    print(f"  standard: PASS ({len(doc_heights)} heights, {len(doc_weights)} layers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
