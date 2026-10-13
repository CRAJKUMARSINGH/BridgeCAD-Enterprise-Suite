"""
bridgecad_plugins — Bridge type plugin system (M4).

Quick start:
    from bridgecad_plugins.registry import get_registry
    registry = get_registry()          # auto-discovers built-ins
    print([p.plugin_id for p in registry.all()])
    # ['rcc_tbeam', 'psc_igirder', 'box_culvert']

    from bridgecad_plugins.runner import run_plugin
    updated = run_plugin("rcc_tbeam", project_dict)
"""
from .registry import get_registry, PluginRegistry
from .runner   import PluginRunner, run_plugin
from .manifest_schema import PluginManifest, load_manifest

__version__ = "0.1.0-rc1"
__all__ = [
    "get_registry", "PluginRegistry",
    "PluginRunner", "run_plugin",
    "PluginManifest", "load_manifest",
]
