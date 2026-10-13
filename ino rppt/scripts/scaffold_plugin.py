"""
Scaffold a new plugin package.

Usage:
    python scripts/scaffold_plugin.py <name> [--output ./plugins/<name>]

Creates:
    plugins/<name>/manifest.json
    plugins/<name>/draw_overrides.py
    plugins/<name>/defaults.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE_MANIFEST = """{{
  "name": "{name}",
  "version": "0.1.0",
  "description": "BridgeCAD plugin — {name}",
  "supported_bridge_types": [],
  "entry_overrides": {{
    "draw_plan": null,
    "draw_long_section": null
  }},
  "defaults_yaml": "defaults.yaml"
}}
"""

TEMPLATE_OVERRIDES = '''"""
Plugin {name} — drawing overrides.

Each `draw_*` function receives the project, the default drawing document,
and an optional plugin-specific parameters dict. It returns the mutated doc.
"""

from __future__ import annotations

# from bridgecad_core.models import BridgeProject


def draw_plan(project, doc, params=None):
    """Apply per-bridge-type plan-view overrides (M4 implementation)."""
    return doc


def draw_long_section(project, doc, params=None):
    """Apply long-section overrides (M4 implementation)."""
    return doc
'''

TEMPLATE_DEFAULTS = """# {name} plugin — default parameters
name: {name}
version: "0.1.0"
bridge_type: {name}
typical:
  span_m: 12.0
  width_m: 9.0
  deck_material: M35
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a new BridgeCAD plugin.")
    parser.add_argument("name", help="Plugin short name, e.g. flyover_bridge")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output directory (default: plugins/<name>)")
    args = parser.parse_args()

    outdir = args.output or (Path.cwd() / "plugins" / args.name)
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "manifest.json").write_text(
        TEMPLATE_MANIFEST.format(name=args.name), encoding="utf-8"
    )
    (outdir / "draw_overrides.py").write_text(
        TEMPLATE_OVERRIDES.format(name=args.name), encoding="utf-8"
    )
    (outdir / "defaults.yaml").write_text(
        TEMPLATE_DEFAULTS.format(name=args.name), encoding="utf-8"
    )
    print(f"✔ Plugin '{args.name}' scaffolded at: {outdir}")


if __name__ == "__main__":
    main()
