#!/usr/bin/env python3
"""Keep the checklists and the harness honest about each other.

Fails when:
  1. an AUTO row names an assertion that does not exist
  2. an assertion exists that no checklist row uses (orphan coverage)
  3. a SCRIPT row names a missing script
  4. a MANUAL row has no reason
  5. a sheet module uses a layer its checklist does not list
  6. a checklist exists for a sheet with no module, or vice versa
  7. a checklist has no sign-off block

    python scripts/check_checklists.py
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
CHECKLISTS = ROOT / "docs" / "checklists"
ASSERTS = ROOT / "tests" / "draw" / "dxf_assert.py"
DRAW = ROOT / "packages" / "bridgecad-draw" / "bridgecad_draw"

ROW_RE = re.compile(r"^\|\s*([A-Z]\d+)\s*\|\s*(.+?)\s*\|\s*`([^`]+)`\s*\|\s*(AUTO|SCRIPT|MANUAL)\s*\|", re.M)
LAYER_ROW_RE = re.compile(r"^\|\s*L\d+\s*\|\s*`([A-Z][A-Z0-9-]+)`", re.M)
MODULE_LAYERS_RE = re.compile(r"LAYERS_USED[^=]*=\s*\((.*?)\)", re.S)
LAYER_LIT_RE = re.compile(r'"([A-Z][A-Z0-9-]+)"')
SIGNOFF_RE = re.compile(r"^## Sign-off", re.M)


def _assert_functions() -> set[str]:
    tree = ast.parse(ASSERTS.read_text(encoding="utf-8"))
    return {
        n.name.removeprefix("assert_")
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name.startswith("assert_")
    }


def _module_layers(path: Path) -> set[str]:
    m = MODULE_LAYERS_RE.search(path.read_text(encoding="utf-8"))
    return set(LAYER_LIT_RE.findall(m.group(1))) if m else set()


def main() -> int:
    known = _assert_functions()
    errors: list[str] = []
    used_assertions: set[str] = set()

    sheets = {p.stem: p for p in sorted(DRAW.glob("sheet*.py"))}
    checklists = {p.stem: p for p in sorted(CHECKLISTS.glob("sheet*.md"))}

    for stem, path in checklists.items():
        text = path.read_text(encoding="utf-8")
        if not SIGNOFF_RE.search(text):
            errors.append(f"{stem}: no sign-off block")

        for row_id, _requirement, target, mode in ROW_RE.findall(text):
            if mode == "AUTO":
                if target not in known:
                    errors.append(f"{stem}:{row_id}: unknown assertion {target!r}")
                used_assertions.add(target)
            elif mode == "SCRIPT":
                if not (ROOT / target).is_file():
                    errors.append(f"{stem}:{row_id}: missing script {target!r}")
            else:
                if not target.startswith("MANUAL:"):
                    errors.append(f"{stem}:{row_id}: MANUAL row needs a 'MANUAL: <reason>'")

        if stem not in sheets:
            errors.append(f"{stem}: checklist has no sheet module")
            continue

        listed = set(LAYER_ROW_RE.findall(text))
        actual = _module_layers(sheets[stem])
        for layer in sorted(actual - listed):
            errors.append(f"{stem}: module uses unlisted layer {layer!r}")
        for layer in sorted(listed - actual):
            errors.append(f"{stem}: checklist lists unused layer {layer!r}")

    for stem in sorted(set(sheets) - set(checklists)):
        errors.append(f"{stem}: sheet module has no checklist")

    for orphan in sorted(known - used_assertions):
        errors.append(f"orphan assertion: assert_{orphan} used by no checklist")

    for e in errors:
        print(f"  [FAIL] {e}")

    print()
    print(f"  checklists {len(checklists)} · assertions {len(known)} · "
          f"covered {len(used_assertions)}")
    if errors:
        print(f"  checklists: FAIL ({len(errors)} issue(s))")
        return 1
    print("  checklists: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
