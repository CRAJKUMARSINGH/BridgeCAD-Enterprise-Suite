"""
bridgecad_plugins.manifest_schema — Plugin manifest dataclass + validator.

Every plugin ships a manifest.json at its root. This module defines the
schema, validates it, and loads it from disk.

Manifest JSON schema:
{
  "plugin_id":    "rcc_tbeam",
  "version":      "1.0.0",
  "name":         "RCC T-Beam Bridge",
  "description":  "Simply-supported RCC T-beam girder bridge (IRC:21)",
  "bridge_types": ["RCC_TBEAM"],
  "span_range_m": [6, 30],
  "default_values_yaml": "defaults.yaml",
  "draw_overrides_module": "draw_overrides",
  "author":       "BridgeCAD Team",
  "requires_core": ">=0.1.0"
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PluginManifest:
    plugin_id:             str
    version:               str
    name:                  str
    description:           str
    bridge_types:          list[str]          = field(default_factory=list)
    span_range_m:          list[float]        = field(default_factory=lambda: [0, 999])
    default_values_yaml:   str                = "defaults.yaml"
    draw_overrides_module: str                = "draw_overrides"
    author:                str                = ""
    requires_core:         str                = ">=0.1.0"
    plugin_dir:            Path | None        = field(default=None, compare=False)

    # ---- validation -------------------------------------------------------
    def validate(self) -> list[str]:
        """Return list of error strings; empty = valid."""
        errors: list[str] = []
        if not self.plugin_id:
            errors.append("plugin_id is required")
        if not self.version:
            errors.append("version is required")
        if not self.name:
            errors.append("name is required")
        if len(self.span_range_m) != 2:
            errors.append("span_range_m must be [min, max]")
        elif self.span_range_m[0] >= self.span_range_m[1]:
            errors.append("span_range_m[0] must be < span_range_m[1]")
        return errors


def load_manifest(path: str | Path) -> PluginManifest:
    """Load and validate a plugin manifest.json.

    Parameters
    ----------
    path : str | Path
        Path to ``manifest.json`` (or the plugin directory containing it).

    Returns
    -------
    PluginManifest
        Validated manifest instance.

    Raises
    ------
    FileNotFoundError, ValueError
    """
    p = Path(path)
    if p.is_dir():
        p = p / "manifest.json"
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {p}")

    with p.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    manifest = PluginManifest(
        plugin_id             = data.get("plugin_id", ""),
        version               = data.get("version", "0.0.0"),
        name                  = data.get("name", ""),
        description           = data.get("description", ""),
        bridge_types          = data.get("bridge_types", []),
        span_range_m          = data.get("span_range_m", [0, 999]),
        default_values_yaml   = data.get("default_values_yaml", "defaults.yaml"),
        draw_overrides_module = data.get("draw_overrides_module", "draw_overrides"),
        author                = data.get("author", ""),
        requires_core         = data.get("requires_core", ">=0.1.0"),
        plugin_dir            = p.parent,
    )

    errors = manifest.validate()
    if errors:
        raise ValueError(f"Invalid manifest {p}: {'; '.join(errors)}")
    return manifest


__all__ = ["PluginManifest", "load_manifest"]
