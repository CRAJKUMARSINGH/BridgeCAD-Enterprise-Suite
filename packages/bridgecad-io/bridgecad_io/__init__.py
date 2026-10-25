"""
BridgeCAD Enterprise — bridgecad-io (Excel / CSV / JSON ↔ BridgeProject serialization).

Public surface (AC-7: these 8 names re-exported at package top level):
  - read_excel, write_excel, generate_template  ← workbook round-trip
  - to_json, from_json                          ← JSON payload / transport
  - to_csv, from_csv                            ← CSV sub-model roster
  - exceptions                                  ← BridgeCADError / IOError / ExcelParseError / ...

All submodules use LAZY import of bridgecad_core so `import bridgecad_io`
always succeeds even if core is missing (important for package smoke tests).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import exceptions  # public package surface
from .exceptions import (
    BridgeCADError,
    CsvParseError,
    ExcelParseError,
    IOError,
    JsonParseError,
)

__version__ = "0.2.0-m2"

if TYPE_CHECKING:  # pragma: no cover - Type hints only; never evaluated
    from bridgecad_core import BridgeProject  # type: ignore[import-not-found]


# ---------------------------------------------------------------------------
# Lazy import bridgecad_core + submodules (call-on-demand only)
# ---------------------------------------------------------------------------

def _bp_type() -> type:
    """Return the BridgeProject class without importing at top-level."""
    from bridgecad_core import BridgeProject  # (imported for caller)
    return BridgeProject


def _er() -> Any:
    from . import excel_reader as _m
    return _m


def _et() -> Any:
    from . import excel_template as _m
    return _m


def _ew() -> Any:
    from . import excel_writer as _m
    return _m


def _ja() -> Any:
    from . import json_adapter as _m
    return _m


def _ca() -> Any:
    from . import csv_adapter as _m
    return _m


# ---------------------------------------------------------------------------
# Public API  (lazy — nothing heavy runs until someone calls these)
# ---------------------------------------------------------------------------

def read_excel(path: str | Path) -> Any:
    """Parse a 14-sheet BridgeCAD workbook → validated BridgeProject."""
    return _er().read_excel(path)


def write_excel(project: Any, output_path: str | Path) -> Path:
    """Write BridgeProject → 14-sheet canonical Excel workbook."""
    return _ew().write_excel(project, output_path)


def generate_template(output_path: str | Path, project: Any = None,
                      title: str = "BridgeCAD Enterprise — 14-Sheet GAD Workbook",
                      _fast_mode: bool = False) -> Path:
    """Generate a 14-sheet styled workbook; optionally pre-filled with *project*."""
    return _et().generate_template(output_path, project=project, title=title,
                                    _fast_mode=_fast_mode)


def to_json(project: Any, path: str | Path | None = None, indent: int = 2,
            exclude: set[str] | None = None) -> str:
    """Dump BridgeProject → JSON (Decimal→string, Enum→value; stable ordering)."""
    return _ja().to_json(project, path=path, indent=indent, exclude=exclude)


def from_json(src: str | Path) -> Any:
    """Load BridgeProject ← JSON string or Path."""
    return _ja().from_json(src)


def to_csv(project: Any, out_dir: str | Path) -> list[Path]:
    """Write 14 sub-model CSVs + 2 schedule CSVs → returns list of paths."""
    return _ca().to_csv(project, out_dir)


def from_csv(in_dir: str | Path) -> Any:
    """Load BridgeProject ← a directory of 16 CSV files written by to_csv()."""
    return _ca().from_csv(in_dir)


__all__ = [
    # public 8 names  (AC-7  (a) requires all 8 be present)
    "read_excel", "write_excel", "generate_template",
    "to_json", "from_json", "to_csv", "from_csv", "exceptions",
    # plus 5 public exception types re-exported for convenience
    "BridgeCADError", "IOError", "ExcelParseError", "JsonParseError", "CsvParseError",
    "__version__",
]
