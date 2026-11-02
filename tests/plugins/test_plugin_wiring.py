"""Every shipped plugin must be discoverable and complete.

A plugin directory that ships a marker file instead of a manifest is skipped by
``PluginRegistry.discover_builtin()``, so its bridge type becomes silently
unavailable. These tests fail if that happens again.
"""

from __future__ import annotations

import json
from pathlib import Path

from bridgecad_core.types import SuperstructureType
from bridgecad_plugins.manifest_schema import load_manifest
from bridgecad_plugins.registry import get_registry

PLUGINS = (
    Path(__file__).resolve().parents[2]
    / "packages/bridgecad-plugins/bridgecad_plugins/plugins"
)

BRACKET = "['manifest.json', 'draw_overrides.py', 'defaults.yaml']"
EXPECTED = {
    "arch_bridge",
    "box_culvert",
    "cable_stayed",
    "pipe_culvert",
    "psc_boxgirder",
    "psc_igirder",
    "rcc_tbeam",
    "solid_slab",
    "steel_composite",
    "voided_slab",
}


def _plugin_dirs() -> list[Path]:
    return sorted(p for p in PLUGINS.iterdir() if p.is_dir())


def test_no_stray_marker_file() -> None:
    assert not (PLUGINS / BRACKET).exists()


def test_every_plugin_has_a_manifest() -> None:
    missing = [p.name for p in _plugin_dirs() if not (p / "manifest.json").exists()]
    assert missing == []


def test_every_plugin_has_defaults_and_overrides() -> None:
    missing = [
        p.name
        for p in _plugin_dirs()
        if not (p / "defaults.yaml").exists() or not (p / "draw_overrides.py").exists()
    ]
    assert missing == []


def test_registry_discovers_every_plugin() -> None:
    found = {p.plugin_id for p in get_registry().all()}
    assert found == EXPECTED


def test_every_manifest_validates() -> None:
    for plugin_dir in _plugin_dirs():
        manifest = load_manifest(plugin_dir / "manifest.json")
        assert manifest.validate() == [], plugin_dir.name
        assert manifest.plugin_id == plugin_dir.name
        assert manifest.span_range_m[0] < manifest.span_range_m[1]


def test_bridge_types_are_real_enum_members_and_unique() -> None:
    valid = {member.value for member in SuperstructureType}
    seen: dict[str, str] = {}
    for plugin_dir in _plugin_dirs():
        data = json.loads((plugin_dir / "manifest.json").read_text(encoding="utf-8"))
        for bridge_type in data["bridge_types"]:
            assert bridge_type in valid, f"{bridge_type} is not a SuperstructureType member"
            assert bridge_type not in seen, f"{bridge_type} claimed twice"
            seen[bridge_type] = plugin_dir.name
