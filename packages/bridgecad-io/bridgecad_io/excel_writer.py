"""BridgeProject → styled 14-sheet Excel workbook.

The pre-filled template builder in :mod:`bridgecad_io.excel_template` already
writes every sheet from a project, so the writer delegates to it — one code
path for both blank templates and filled workbooks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_excel(project: Any, output_path: str | Path) -> Path:
    """Write *project* to a canonical 14-sheet workbook and return its path."""
    if project is None:
        raise ValueError("write_excel requires a BridgeProject (use generate_template for blanks)")
    from .excel_template import generate_template

    return generate_template(output_path, project=project)


__all__ = ["write_excel"]
