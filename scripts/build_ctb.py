#!/usr/bin/env python3
"""Build BRG-MONO.ctb from standards/plot/brg_mono.yaml.

The .ctb is binary, so it is generated, never hand-edited. Requires
ezdxf>=1.3 for its CTB writer.

    python scripts/build_ctb.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
SRC = ROOT / "standards" / "plot" / "brg_mono.yaml"
DEST = ROOT / "standards" / "plot" / "BRG-MONO.ctb"

try:
    from ezdxf.addons.drawing import ctb as ctb_mod
except ImportError:
    sys.exit("ezdxf>=1.3 is required for the CTB writer")

CLASS_TO_ACI = {
    "BORDER": [7],
    "STRUC-OUTLINE": [1, 2, 3, 4, 5, 6],
    "STRUC-SECTION": [1],
    "SUPER-DECK": [2],
    "SUPER-GIRDER": [1],
    "SUB-PIER": [2],
    "SUB-ABUT": [3],
    "FOUND-CAP": [2],
    "FOUND-PILE": [4],
    "STRUC-HIDDEN": [8],
    "DIM": [3],
    "TEXT": [7],
    "HATCH": [8, 9, 34],
}


def build() -> int:
    cfg = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    default = cfg["default"]

    styles = ctb_mod.ColorDependentPlotStyles()
    for aci in range(1, 256):
        styles.add_color_policy(
            aci,
            ctb_mod.ColorPolicy(
                color=default["color"],
                lineweight=int(default["lineweight"]),
                screening=int(default["screening"]),
            ),
        )

    for cls, override in cfg["by_layer_class"].items():
        for aci in CLASS_TO_ACI.get(cls, []):
            styles.add_color_policy(
                aci,
                ctb_mod.ColorPolicy(
                    color=override.get("color", default["color"]),
                    lineweight=int(override.get("lineweight", default["lineweight"])),
                    screening=int(override.get("screening", default["screening"])),
                ),
            )

    ctb = ctb_mod.CTBFile()
    ctb.set_styles(styles)
    ctb.save(str(DEST))
    print(f"  wrote {DEST.relative_to(ROOT)} ({DEST.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
