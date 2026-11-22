"""bridgecad_draw.sheets.sheet5B_abutment_enlarged — in-memory builder shim (EP-2026-12).

Delegates to ``sheet5_enlarged_details.generate`` via a temporary file so the
contract test harness (which calls ``mod.build(project)``) can exercise Sheet 5B
without knowing about the generate/save API.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any


SHEET = "sheet5B_abutment_enlarged"
TITLE = "S5B Enlarged Abutment Details"
INDEX = "5B"


def build(project: Any):
    """Build Sheet 5B in a temp file and return the ezdxf doc."""
    import ezdxf
    from bridgecad_draw.sheet5_enlarged_details import generate

    with tempfile.TemporaryDirectory() as td:
        p = generate(project, Path(td) / "s5B.dxf", part="abutment")
        return ezdxf.readfile(str(p))
