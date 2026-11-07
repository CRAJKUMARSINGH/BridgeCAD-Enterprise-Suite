"""Static check: every dim_along axis literal must be permitted by its view.

Parses each sheet module, maps ``dim_along(<view_var>, ..., "AXIS")`` calls to
the ``view_spec("name")`` bound to ``<view_var>``, and fails when the literal
axis is not in that view's ``allowed`` set.  Wire into ``make lint``.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRAW = REPO / "packages" / "bridgecad-draw" / "bridgecad_draw"

sys.path.insert(0, str(DRAW.parent))
sys.path.insert(0, str(REPO / "packages" / "bridgecad-core"))

from bridgecad_draw.contract import VIEW_SPECS  # noqa: E402


def _literal_axis(call: ast.Call) -> str | None:
    """The axis argument is positional arg 3 (0=view,1=p1,2=p2,3=axis)."""
    if len(call.args) >= 4 and isinstance(call.args[3], ast.Constant):
        return str(call.args[3].value)
    for kw in call.keywords:
        if kw.arg == "axis" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return None


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    # var -> view name, from `_x = view_spec("name")` or direct calls
    var_views: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if (
                isinstance(tgt, ast.Name)
                and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", getattr(node.value.func, "attr", ""))
                in ("view_spec",)
                and node.value.args
                and isinstance(node.value.args[0], ast.Constant)
            ):
                var_views[tgt.id] = str(node.value.args[0].value)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = getattr(node.func, "id", getattr(node.func, "attr", ""))
        if fname != "dim_along" or not node.args:
            continue
        view_var = node.args[0]
        view_name = None
        if isinstance(view_var, ast.Name):
            view_name = var_views.get(view_var.id)
        elif isinstance(view_var, ast.Call):
            f2 = getattr(view_var.func, "id", getattr(view_var.func, "attr", ""))
            if f2 == "view_spec" and view_var.args and isinstance(view_var.args[0], ast.Constant):
                view_name = str(view_var.args[0].value)
        axis = _literal_axis(node)
        if view_name is None or axis is None:
            continue  # dynamic — the runtime AxisError still guards it
        spec = VIEW_SPECS.get(view_name)
        if spec is None:
            problems.append(f"{path.name}:{node.lineno}: unknown view '{view_name}'")
            continue
        if axis not in {a.value for a in spec.allowed}:
            problems.append(
                f"{path.name}:{node.lineno}: {view_name} does not permit {axis} "
                f"(allowed: {sorted(a.value for a in spec.allowed)})"
            )
    return problems


def main() -> int:
    problems: list[str] = []
    for path in sorted(DRAW.glob("sheet*.py")):
        problems.extend(check_file(path))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        print(f"\n{len(problems)} view-axis violation(s)", file=sys.stderr)
        return 1
    print("view-axis check clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
