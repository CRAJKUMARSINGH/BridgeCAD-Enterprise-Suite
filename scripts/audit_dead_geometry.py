"""Report pure expressions evaluated and discarded in the draw package.

A bare `float(x) / 1000 * scale` on its own line is a value nobody bound —
either the author meant to assign it, or meant to delete it.  Both are
defects worth a look; neither is caught by ruff B018 because a call is
assumed to have side effects.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

_SAFE_CALLS = {"float", "int", "str", "min", "max", "abs", "round", "len"}
_PURE = (
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Attribute,
    ast.IfExp,
    ast.Subscript,
    ast.Compare,
    ast.BoolOp,
)


def _pure(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        f = node.func
        return isinstance(f, ast.Name) and f.id in _SAFE_CALLS and all(_pure(a) for a in node.args)
    if not isinstance(node, _PURE):
        return False
    return all(_pure(c) for c in ast.iter_child_nodes(node))


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Ids of Expr nodes that are docstrings (first stmt of a body)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (
            isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            ids.add(id(body[0]))
    return ids


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else "packages/bridgecad-draw/bridgecad_draw")
    hits = 0
    for path in sorted(root.glob("sheet*.py")):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        docstrings = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if id(node) in docstrings:
                continue
            if not isinstance(node, ast.Expr) or not _pure(node.value):
                continue
            seg = ast.get_source_segment(text, node.value) or ""
            if len(seg) < 8:
                continue
            print(f"{path}:{node.lineno}: {seg}")
            hits += 1
    print(f"\n{hits} dead expression(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
