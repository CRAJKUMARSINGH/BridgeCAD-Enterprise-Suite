"""N7 guard — detail sheets must not style themselves through a shared class.

Sheets 04/05 render with inline attributes on the neutral ``.bcsheet`` root so
they are immune to the Sheet 01 rules in ``styles.css``. Reintroducing a shared
class silently re-arms the specificity clobbering bug.
"""

from __future__ import annotations

from pathlib import Path

SHEETS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "sheets"
FORBIDDEN = ("drawing-sheet", "sheet-bg", "sheet-border", "sheet-inner-border")


def test_no_shared_class():
    for name in ("Sheet04Foundation.tsx", "Sheet05PierAbutment.tsx", "SheetChrome.tsx"):
        body = (SHEETS / name).read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in body, f"{name} reintroduced shared class {token}"
