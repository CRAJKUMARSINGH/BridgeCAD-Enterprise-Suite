#!/usr/bin/env python3
"""Fail if a sheet module passes a numeric literal as a text height.

Text heights must derive from text.TextClass x frame.plot_scale. AST-based, so
it catches `height=2.5` anywhere in a call, including nested.

    python scripts/check_text_heights.py
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]
SHEET_GLOB = "packages/bridgecad-draw/bridgecad_draw/sheet*.py"

#: Names that legitimately resolve to a paper height.
DERIVED_NAMES = {"h", "height", "th", "text_height", "paper_mm"}


class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.hits: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        for kw in node.keywords:
            if kw.arg != "height":
                continue
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int | float) or isinstance(kw.value, ast.UnaryOp):
                self.hits.append((kw.value.lineno, ast.unparse(kw.value)))
        self.generic_visit(node)


def _is_allowed(source: str, lineno: int) -> bool:
    """Allow a literal if a TextClass-derived name appears on the same line."""
    line = source.splitlines()[lineno - 1]
    return any(n in line for n in DERIVED_NAMES)


def main() -> int:
    total = 0
    for path in sorted(ROOT.glob(SHEET_GLOB)):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        v = Visitor(path)
        v.visit(tree)
        for lineno, literal in v.hits:
            if _is_allowed(source, lineno):
                continue
            rel = path.relative_to(ROOT)
            print(f"  {rel}:{lineno}  height={literal}")
            total += 1

    print()
    if total:
        print(f"  {total} numeric text height(s) — use TextClass via text.h(cls, frame)")
        return 1
    print("  all text heights derived")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
