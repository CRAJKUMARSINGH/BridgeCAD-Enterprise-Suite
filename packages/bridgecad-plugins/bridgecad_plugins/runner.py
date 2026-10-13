"""
bridgecad_plugins.runner — Execute a plugin's draw_overrides against a BridgeProject.

Each plugin may optionally ship a ``draw_overrides.py`` module that exposes:

  def apply_defaults(project_dict: dict) -> dict:
      '''Merge plugin-specific default values into a project parameter dict.'''

  def get_typical_values() -> dict:
      '''Return a dict of typical field values for this bridge type.'''

  def describe() -> str:
      '''Return a human-readable description of the plugin's bridge type.'''

All functions are optional; runner gracefully skips absent ones.
"""
from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any

from .manifest_schema import PluginManifest

logger = logging.getLogger(__name__)


class PluginRunner:
    """Loads and executes a plugin's draw_overrides module."""

    def __init__(self, manifest: PluginManifest) -> None:
        self.manifest = manifest
        self._module: Any | None = None

    def _load_module(self) -> Any | None:
        if self._module is not None:
            return self._module
        if self.manifest.plugin_dir is None:
            return None
        mod_path = (self.manifest.plugin_dir /
                    f"{self.manifest.draw_overrides_module}.py")
        if not mod_path.exists():
            return None
        spec = importlib.util.spec_from_file_location(
            f"bridgecad_plugin_{self.manifest.plugin_id}.draw_overrides",
            mod_path,
        )
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)   # type: ignore[union-attr]
            self._module = mod
        except Exception as exc:
            logger.warning("Plugin %s draw_overrides load failed: %s",
                           self.manifest.plugin_id, exc)
        return self._module

    def apply_defaults(self, project_dict: dict) -> dict:
        """Merge plugin defaults into *project_dict*; returns updated dict."""
        mod = self._load_module()
        if mod and hasattr(mod, "apply_defaults"):
            try:
                return mod.apply_defaults(project_dict)
            except Exception as exc:
                logger.warning("apply_defaults failed in %s: %s",
                               self.manifest.plugin_id, exc)
        return project_dict

    def get_typical_values(self) -> dict:
        """Return typical default values dict for this plugin's bridge type."""
        mod = self._load_module()
        if mod and hasattr(mod, "get_typical_values"):
            try:
                return mod.get_typical_values()
            except Exception as exc:
                logger.warning("get_typical_values failed in %s: %s",
                               self.manifest.plugin_id, exc)
        return {}

    def describe(self) -> str:
        """Return description string."""
        mod = self._load_module()
        if mod and hasattr(mod, "describe"):
            try:
                return mod.describe()
            except Exception:
                pass
        return self.manifest.description

    def load_defaults_yaml(self) -> dict:
        """Load the plugin's defaults.yaml into a plain dict."""
        if self.manifest.plugin_dir is None:
            return {}
        yaml_path = self.manifest.plugin_dir / self.manifest.default_values_yaml
        if not yaml_path.exists():
            return {}
        try:
            import yaml  # type: ignore[import]
            with yaml_path.open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # PyYAML not installed — read as JSON fallback
            import json
            json_path = yaml_path.with_suffix(".json")
            if json_path.exists():
                with json_path.open() as f:
                    return json.load(f)
        except Exception as exc:
            logger.warning("Could not load defaults for %s: %s",
                           self.manifest.plugin_id, exc)
        return {}


def run_plugin(plugin_id: str, project_dict: dict) -> dict:
    """Convenience: look up plugin and apply its defaults to *project_dict*.

    Returns
    -------
    dict
        Updated project_dict with plugin defaults merged in.
    """
    from .registry import get_registry
    registry = get_registry()
    manifest = registry.get(plugin_id)
    if manifest is None:
        raise KeyError(f"Plugin not found: {plugin_id!r}. "
                       f"Available: {[p.plugin_id for p in registry.all()]}")
    runner = PluginRunner(manifest)
    return runner.apply_defaults(project_dict)


__all__ = ["PluginRunner", "run_plugin"]
