"""Public exception hierarchy for bridgecad-io.

Hierarchy
---------
BridgeCADError(Exception)          # top-level package marker
└── IOError(BridgeCADError)
    ├── ExcelParseError(IOError)
    ├── JsonParseError(IOError)
    └── CsvParseError(IOError)

All subclasses accept (message, *, file=None, sheet=None, field=None,
line=None, suggestion=None) and include every context item in the string
representation so CLI users get actionable hints.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class BridgeCADError(Exception):
    """Top-level marker exception — anything thrown by BridgeCAD Enterprise
    Enterprise Suite packages (core / io / draw / qa) eventually inherits
    from this."""


# NOTE: we intentionally *do not* call the builtin OSError alias IOError;
# creating our own subclass keeps bridgecad-io free of errno semantics.
class _IOError(BridgeCADError):
    """Base for all file-format adapters (Excel/JSON/CSV)."""

    fmt_prefix = "IO error"

    def __init__(
        self,
        message: str,
        *,
        file: str | Path | None = None,
        sheet: str | None = None,
        field: str | None = None,
        line: int | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.message = str(message)
        self.file = str(file) if file else None
        self.sheet = sheet
        self.field = field
        self.line = line
        self.suggestion = suggestion
        parts: list[str] = [f"{self.fmt_prefix}: {self.message}"]
        if self.file:
            parts.append(f"file={self.file}")
        if self.sheet:
            parts.append(f"sheet={self.sheet}")
        if self.field:
            parts.append(f"field={self.field}")
        if self.line is not None:
            parts.append(f"line={int(self.line)}")
        if self.suggestion:
            parts.append(f"hint: {self.suggestion}")
        super().__init__(" | ".join(parts))


# Re-export as 'IOError' for callers — same symbol as the built-in alias, but
# outside this module callers use  bridgecad_io.exceptions.IOError  so there
# is never any ambiguity with the builtin.
IOError = _IOError


class ExcelParseError(_IOError):
    """Raised by excel_reader when a 14-sheet workbook cannot be parsed
    into a valid BridgeProject."""

    fmt_prefix = "Excel parse error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class JsonParseError(_IOError):
    """Raised by json_adapter when JSON payloads are malformed or fail
    Pydantic validation."""

    fmt_prefix = "JSON parse error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class CsvParseError(_IOError):
    """Raised by csv_adapter for malformed CSV rows or missing sub-model
    files during from_csv()."""

    fmt_prefix = "CSV parse error"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


__all__ = [
    "BridgeCADError",
    "IOError",
    "ExcelParseError",
    "JsonParseError",
    "CsvParseError",
]
