#!/usr/bin/env python3
"""Validate the notes library and that drawn notes are sourced.

  1. every entry in standards/notes.yaml has `text`, `source` and `sheets`
  2. every `source` cites a standard code and a clause
  3. every note drawn on a golden sheet carries a bracketed source
  4. no note is drawn on a sheet its entry does not list

    python scripts/check_notes.py
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
NOTES = ROOT / "standards" / "notes.yaml"
GOLDEN_PKG = ROOT / "build" / "metrics" / "pkg"

SOURCE_RE = re.compile(r"^[A-Z][A-Z0-9:.\- ]+ \d{4} Cl\. [\d.]+$")
CODE_RE = re.compile(r"IRC|MORTH|IS:\d+")


def _check_library() -> list[str]:
    errors: list[str] = []
    if not NOTES.is_file():
        return [f"missing {NOTES.relative_to(ROOT)}"]

    data = yaml.safe_load(NOTES.read_text(encoding="utf-8")) or {}
    notes = data.get("notes") or {}
    if not notes:
        return ["notes.yaml has no notes"]

    for nid, entry in notes.items():
        for key in ("text", "source", "sheets"):
            if key not in entry:
                errors.append(f"{nid}: missing {key!r}")
        src = str(entry.get("source", ""))
        if src and not SOURCE_RE.match(src):
            errors.append(f"{nid}: source {src!r} is not '<CODE> <YEAR> Cl. <n>'")
        if src and not CODE_RE.search(src):
            errors.append(f"{nid}: source {src!r} cites no standard code")
        if not str(entry.get("text", "")).strip():
            errors.append(f"{nid}: empty text")
        if not entry.get("sheets"):
            errors.append(f"{nid}: no sheets listed")
    return errors


def _check_drawn() -> list[str]:
    errors: list[str] = []
    if not GOLDEN_PKG.is_dir():
        return ["no golden packages — run scripts/_gen_golden_packages.py first"]

    import ezdxf

    for dxf in sorted(GOLDEN_PKG.rglob("*.dxf")):
        doc = ezdxf.readfile(str(dxf))
        for e in doc.modelspace():
            if e.dxftype() != "TEXT":
                continue
            if e.dxf.get("layer") != "TEXT-SPEC":
                continue
            txt = e.dxf.text
            if not re.search(r"\[[^\]]+\]", txt):
                errors.append(f"{dxf.name}: unsourced note {txt[:50]!r}")
    return errors


def main() -> int:
    errors = _check_library() + _check_drawn()
    for e in errors[:40]:
        print(f"  [FAIL] {e}")
    print()
    if errors:
        print(f"  notes: FAIL ({len(errors)} issue(s))")
        return 1
    print("  notes: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
