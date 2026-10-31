#!/usr/bin/env python3
"""Audit the drawing layer registry against the ISO 13567-2 naming scheme.

Rules, from W07 and `docs/drafting-standard.md` §3–4:
  1. every registry layer except ``"0"`` has an ISO 13567-2 name
  2. no two layers share an ISO name (a colliding code is worse than no scheme)
  3. every ISO name matches ``<Agent>-<MajorGroup>-<MinorGroup>-<Status>``
  4. every ISO name carries this project's agent and status letters
  5. every layer line weight is in the ISO 128 series (a weight off the series
     is a typo, not a drafting decision)
  6. every layer has a description and a registered linetype

The ``"0"`` layer is the CAD baseline, not a project layer, and is exempt from
rule 1 — it carries no project geometry.

    python scripts/audit_layers.py [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
_DRAW = ROOT / "packages" / "bridgecad-draw"
if _DRAW.exists() and str(_DRAW) not in sys.path:
    sys.path.insert(0, str(_DRAW))

BASELINE_LAYER = "0"


def audit() -> tuple[list[str], dict[str, int]]:
    from bridgecad_draw import layers

    errors: list[str] = []
    registry = layers.LAYER_REGISTRY
    names = layers.ISO_13567_NAMES

    project_layers = {k for k in registry if k != BASELINE_LAYER}

    # 1. coverage
    for layer in sorted(project_layers):
        if layer not in names:
            errors.append(f"layer {layer} has no ISO 13567-2 name")

    # 2. uniqueness (only meaningful once coverage is complete)
    seen: dict[str, str] = {}
    for layer in sorted(names):
        iso = names[layer]
        if iso in seen:
            errors.append(f"ISO name {iso} claimed by both {seen[iso]} and {layer}")
        else:
            seen[iso] = layer

    # 3. pattern + 4. agent/status
    for layer in sorted(names):
        iso = names[layer]
        if not layers.ISO_13567_PATTERN.match(iso):
            errors.append(f"{layer}: ISO name {iso!r} does not match the scheme")
            continue
        if not iso.startswith(f"{layers.ISO_13567_AGENT}-"):
            errors.append(f"{layer}: ISO name {iso!r} has the wrong agent")
        if not iso.endswith(f"-{layers.ISO_13567_STATUS}"):
            errors.append(f"{layer}: ISO name {iso!r} has the wrong status")

    # 5. line weights
    for layer, ld in sorted(registry.items()):
        if ld.lineweight not in layers.ISO_128_LINEWEIGHTS:
            errors.append(
                f"{layer}: line weight {ld.lineweight / 100:.2f} mm is off the ISO 128 series"
            )

    # 6. descriptions and linetypes
    for layer, ld in sorted(registry.items()):
        if not ld.description.strip():
            errors.append(f"{layer} has no description")
        if not ld.linetype.strip():
            errors.append(f"{layer} has no linetype")

    stats = {
        "layers": len(registry),
        "project_layers": len(project_layers),
        "iso_names": len(names),
        "distinct_iso_names": len(set(names.values())),
        "distinct_weights": len({ld.lineweight for ld in registry.values()}),
    }
    return errors, stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = ap.parse_args(argv)

    errors, stats = audit()

    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "stats": stats}, indent=2))
        return 1 if errors else 0

    for e in errors:
        print(f"  [FAIL] {e}")
    print()
    if errors:
        print(f"  layers: FAIL ({len(errors)} defect(s))")
        return 1
    print(
        f"  layers: PASS ({stats['project_layers']} project layers, "
        f"{stats['distinct_iso_names']} ISO names, "
        f"{stats['distinct_weights']} weights)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
