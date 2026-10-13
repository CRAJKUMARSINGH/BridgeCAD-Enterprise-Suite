"""
bridgecad_plugins.registry — Plugin discovery, registration, and lookup.

Plugins are discovered from two sources (in priority order):
  1. Built-in plugins shipped inside this package under ``plugins/``
  2. User-installed plugins discovered via importlib entry-points
     (group ``bridgecad.plugins``)

The registry maps ``plugin_id → PluginManifest``.
"""
from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Iterator

from .manifest_schema import PluginManifest, load_manifest

logger = logging.getLogger(__name__)

# Where built-in plugins live (relative to this file)
_BUILTIN_PLUGINS_DIR = Path(__file__).parent / "plugins"


class PluginRegistry:
    """Central registry for all discovered plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginManifest] = {}

    # ---- population --------------------------------------------------------

    def discover_builtin(self) -> int:
        """Scan the built-in plugins directory and register all valid manifests.

        Returns
        -------
        int
            Number of plugins registered.
        """
        count = 0
        if not _BUILTIN_PLUGINS_DIR.exists():
            return 0
        for subdir in sorted(_BUILTIN_PLUGINS_DIR.iterdir()):
            if not subdir.is_dir():
                continue
            manifest_path = subdir / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                m = load_manifest(manifest_path)
                self._plugins[m.plugin_id] = m
                count += 1
                logger.debug("Registered built-in plugin: %s v%s", m.plugin_id, m.version)
            except Exception as exc:
                logger.warning("Failed to load plugin %s: %s", subdir.name, exc)
        return count

    def register(self, manifest: PluginManifest) -> None:
        """Manually register a manifest (used by installer and tests)."""
        self._plugins[manifest.plugin_id] = manifest
        logger.info("Registered plugin: %s v%s", manifest.plugin_id, manifest.version)

    # ---- lookup ------------------------------------------------------------

    def get(self, plugin_id: str) -> PluginManifest | None:
        return self._plugins.get(plugin_id)

    def all(self) -> list[PluginManifest]:
        return list(self._plugins.values())

    def __iter__(self) -> Iterator[PluginManifest]:
        return iter(self._plugins.values())

    def __len__(self) -> int:
        return len(self._plugins)

    def find_for_type(self, bridge_type: str) -> list[PluginManifest]:
        """Return all plugins that declare support for *bridge_type*."""
        return [p for p in self._plugins.values()
                if bridge_type in p.bridge_types]

    def find_for_span(self, span_m: float) -> list[PluginManifest]:
        """Return all plugins whose span_range includes *span_m*."""
        return [p for p in self._plugins.values()
                if p.span_range_m[0] <= span_m <= p.span_range_m[1]]


# Module-level singleton
_REGISTRY = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Return the module-level singleton registry (auto-discovers built-ins)."""
    if len(_REGISTRY) == 0:
        _REGISTRY.discover_builtin()
    return _REGISTRY


__all__ = ["PluginRegistry", "get_registry"]
