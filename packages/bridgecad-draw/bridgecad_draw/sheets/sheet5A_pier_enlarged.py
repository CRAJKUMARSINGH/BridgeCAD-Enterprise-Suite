# ruff: noqa: N999
# Keep the existing sheet import path.

"""bridgecad_draw.sheets.sheet5A_pier_enlarged — in-memory builder shim (EP-2026-12).

Delegates to ``sheet5_enlarged_details.generate`` via a temporary file so the
contract test harness (which calls ``mod.build(project)``) can exercise Sheet 5A
without knowing about the generate/save API.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

SHEET = "sheet5A_pier_enlarged"
TITLE = "S5A Enlarged Pier Details"
INDEX = "5A"


def build(project: Any):
    """Build Sheet 5A in a temp file and return the ezdxf doc."""
    import ezdxf

    from bridgecad_draw.sheet5_enlarged_details import generate

    with tempfile.TemporaryDirectory() as td:
        p = generate(project, Path(td) / "s5A.dxf", part="pier")
        return ezdxf.readfile(str(p))
