"""JSON ↔ BridgeProject adapter.

Public functions
----------------
to_json(project, path=None, indent=2, exclude=None) -> str
from_json(src) -> BridgeProject
dump_project(project, path) -> Path          (alias used by the facade / 11-span script)
load_project(path) -> BridgeProject          (alias used by ``python -m bridgecad qa``)
project_schema() -> dict                      (JSON Schema for BridgeProject — W08)

BridgeProject sub-models use ``extra="forbid"`` and expose ``@computed_field``
values (``total_length_m``, ``overall_width_m`` …). ``model_dump`` writes those
computed values, so a naive ``model_validate`` of our own output fails. This
adapter strips computed fields on both dump and load, making the round-trip
lossless and keeping older JSON files (which contain them) loadable.
"""

from __future__ import annotations

import json
import typing
from pathlib import Path
from typing import Any

from .exceptions import JsonParseError


def _bp_cls() -> Any:
    from bridgecad_core import BridgeProject

    return BridgeProject


def _model_types(annotation: Any) -> list[type]:
    """Return every pydantic model class reachable inside *annotation*."""
    from pydantic import BaseModel

    out: list[type] = []
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        out.append(annotation)
    for arg in typing.get_args(annotation):
        out.extend(_model_types(arg))
    return out


def _strip_computed(model_cls: Any, data: Any) -> Any:
    """Recursively drop computed-field keys that ``extra='forbid'`` would reject."""
    if not isinstance(data, dict):
        return data
    computed = set(getattr(model_cls, "model_computed_fields", {}) or {})
    fields = getattr(model_cls, "model_fields", {}) or {}
    clean: dict[str, Any] = {}
    for key, value in data.items():
        if key in computed and key not in fields:
            continue
        info = fields.get(key)
        if info is not None:
            models = _model_types(info.annotation)
            if models:
                sub = models[0]
                if isinstance(value, list):
                    value = [_strip_computed(sub, v) for v in value]
                elif isinstance(value, dict):
                    # dict value may be the sub-model itself or a mapping of sub-models
                    if set(value) & (set(sub.model_fields) | set(sub.model_computed_fields)):
                        value = _strip_computed(sub, value)
                    else:
                        value = {k: _strip_computed(sub, v) for k, v in value.items()}
        clean[key] = value
    return clean


def project_to_dict(project: Any, exclude: set[str] | None = None) -> dict:
    """BridgeProject → plain JSON-safe dict without computed fields."""
    data = project.model_dump(mode="json", exclude=exclude)
    return _strip_computed(type(project), data)


def project_from_dict(data: dict) -> Any:
    """Plain dict → validated BridgeProject (computed fields tolerated)."""
    cls = _bp_cls()
    try:
        return cls.model_validate(_strip_computed(cls, data))
    except Exception as exc:  # pydantic.ValidationError and friends
        raise JsonParseError(f"Invalid BridgeProject JSON: {exc}") from exc


def to_json(
    project: Any,
    path: str | Path | None = None,
    indent: int = 2,
    exclude: set[str] | None = None,
) -> str:
    """Serialise *project* to a JSON string; also write it to *path* if given."""
    text = json.dumps(project_to_dict(project, exclude=exclude), indent=indent, ensure_ascii=False)
    if path is not None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return text


def from_json(src: str | Path) -> Any:
    """Load a BridgeProject from a JSON string or a path to a ``.json`` file."""
    if isinstance(src, Path) or (isinstance(src, str) and not src.lstrip().startswith("{")):
        p = Path(src)
        if not p.exists():
            raise JsonParseError(f"JSON file not found: {p}")
        text = p.read_text(encoding="utf-8")
    else:
        text = src
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise JsonParseError(f"Malformed JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise JsonParseError("BridgeProject JSON must be an object at top level")
    return project_from_dict(data)


def dump_project(project: Any, path: str | Path, indent: int = 2) -> Path:
    """Write *project* to *path* as JSON and return the path."""
    to_json(project, path=path, indent=indent)
    return Path(path)


def load_project(path: str | Path) -> Any:
    """Read a BridgeProject JSON file."""
    return from_json(Path(path))


def project_schema() -> dict:
    """Return the published JSON Schema (Draft 2020-12) for ``BridgeProject``.

    This is the single source of truth for the on-disk ``.bridgecad.json``
    document; ``scripts/export_project_schema.py`` writes it to
    ``docs/schema/bridgeproject.schema.json`` and a drift gate keeps the two in
    step. Computed fields stay in the schema — they are present in exported
    documents and optional on import.
    """
    cls = _bp_cls()
    return cls.model_json_schema(mode="serialization")


__all__ = [
    "dump_project",
    "from_json",
    "load_project",
    "project_from_dict",
    "project_schema",
    "project_to_dict",
    "to_json",
]
