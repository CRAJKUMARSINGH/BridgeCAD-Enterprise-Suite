"""
bridgecad_io._fields — Shared flat-field introspection for the Excel bridge.

The 14-sheet workbook is a flat ``Field | Value | Unit | Description``
serialisation of the ``BridgeProject`` sub-models (bearings and expansion
joints are the one tabular exception). Both the reader and the writer need the
same two answers:

  * is a model field representable as a single workbook cell?
  * how is its value converted to and from that cell?

Keeping both rules in one place is what makes the workbook round-trip lossless
*by construction* rather than by carefully duplicating field lists on each side.

W08 interoperability.
"""

from __future__ import annotations

import logging
import types
import typing
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, get_args, get_origin

logger = logging.getLogger(__name__)

_UNION_ORIGINS = (types.UnionType, typing.Union)


def base_annotation(annotation: Any) -> Any:
    """Unwrap ``X | None`` / ``Optional[X]`` to the remaining single type."""
    origin = get_origin(annotation)
    if origin in _UNION_ORIGINS:
        args = tuple(a for a in get_args(annotation) if a is not type(None))
        if len(args) == 1:
            return base_annotation(args[0])
    return annotation


def list_element(annotation: Any) -> Any | None:
    """Return ``X`` for a ``list[X]`` annotation, else ``None``."""
    if get_origin(annotation) is list:
        args = get_args(annotation)
        if args:
            return base_annotation(args[0])
    return None


def flat_kind(annotation: Any) -> str | None:
    """Classify a field annotation as a workbook-serialisable flat type.

    Returns one of ``enum``, ``enum_list``, ``bool``, ``int``, ``float``,
    ``decimal``, ``date`` or ``str`` — or ``None`` when the field cannot be
    represented by a single cell (nested models, plain lists of scalars, ...).
    """
    elem = list_element(annotation)
    if elem is not None:
        if isinstance(elem, type) and issubclass(elem, Enum):
            return "enum_list"
        return None
    base = base_annotation(annotation)
    if isinstance(base, type):
        if issubclass(base, Enum):
            return "enum"
        # bool is a subclass of int — test it first.
        if base is bool:
            return "bool"
        if base is int:
            return "int"
        if base is float:
            return "float"
        if base is Decimal:
            return "decimal"
        if base is date:
            return "date"
        if base is str:
            return "str"
    return None


# ---------------------------------------------------------------------------
# Value coercion (workbook cell -> Python)
# ---------------------------------------------------------------------------


def coerce(value: Any, python_type: type) -> Any:
    """Best-effort coercion from an Excel cell value to *python_type*."""
    if value is None:
        return None
    if python_type is bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().upper() in {"TRUE", "YES", "1", "Y"}
    if python_type is int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
    if python_type is float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if python_type is Decimal:
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    if python_type is date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value).strip())
        except (ValueError, TypeError):
            return None
    if python_type is str:
        return str(value).strip() if value is not None else None
    return value


def lookup_enum(enum_cls: Any, raw: Any) -> Any:
    """Find an enum member by name or value; return ``None`` if not found."""
    if raw is None:
        return None
    s = str(raw).strip()
    for m in enum_cls:
        if m.name.upper() == s.upper():
            return m
    for m in enum_cls:
        if str(m.value).upper() == s.upper():
            return m
    logger.warning("Could not resolve %s member from %r", enum_cls.__name__, raw)
    return None


def cell_to_value(raw: Any, annotation: Any) -> Any:
    """Coerce one workbook cell to the type a flat model field expects."""
    kind = flat_kind(annotation)
    if kind is None or raw is None:
        return None
    if kind == "enum":
        return lookup_enum(base_annotation(annotation), raw)
    if kind == "enum_list":
        elem = list_element(annotation)
        members = [
            m for m in (lookup_enum(elem, part.strip()) for part in str(raw).split(",")) if m
        ]
        return members or None
    if kind == "date":
        return coerce(raw, date)
    return coerce(
        raw, {"bool": bool, "int": int, "float": float, "decimal": Decimal, "str": str}[kind]
    )


# ---------------------------------------------------------------------------
# Value serialisation (Python -> workbook cell)
# ---------------------------------------------------------------------------


def value_to_cell(value: Any, annotation: Any) -> Any:
    """Convert a model value to a workbook cell value for a flat field."""
    kind = flat_kind(annotation)
    if kind is None or value is None:
        return None
    if kind == "enum":
        return getattr(value, "name", None)
    if kind == "enum_list":
        return ",".join(m.name for m in value)
    if kind == "bool":
        return bool(value)
    if kind == "int":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if kind in ("float", "decimal"):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if kind == "date":
        return value.isoformat() if isinstance(value, date) else str(value)
    return str(value)


__all__ = [
    "base_annotation",
    "cell_to_value",
    "coerce",
    "flat_kind",
    "list_element",
    "lookup_enum",
    "value_to_cell",
]
