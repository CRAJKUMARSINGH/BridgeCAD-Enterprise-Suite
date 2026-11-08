"""
bridgecad_core.geometry.abutment_profiles — abutment elevation SHAPE families.

The drawing engines emitted ONE elevation shape for all AbutmentType values, so
a GRAVITY mass wall and a CANTILEVER wall drew identically. This module maps an
abutment type to a shape FAMILY and returns its outline. Single source of truth
for both the Python DXF engine and the JS sheet, so the two cannot drift.

Coordinates: normalised — x in [0,1] across the width, y in [0,1] from founding
level (0) to road level (1). Callers scale to sheet mm.
"""

from __future__ import annotations

from typing import Any

__all__ = ["Family", "family_for", "elevation_outline"]

Family = str

GRAVITY = "gravity"  # trapezoid mass wall, battered both faces
CANTILEVER = "cantilever"  # inverted-T: thin stem + projecting base footing
BATTERED = "battered"  # legacy rectangle block

_FOOTING_FRAC = 0.18  # base-slab depth as a height fraction (cantilever)
_STEM_FRAC = 0.5  # stem width as a width fraction (cantilever)
_TOP_BATTER_FRAC = 0.25  # face run-back at the top (gravity)


def family_for(abutment_type: Any) -> Family:
    """Map an AbutmentType (enum, .name, or .value) to a shape family."""
    raw = getattr(abutment_type, "name", None) or getattr(abutment_type, "value", None)
    name = str(raw if raw is not None else abutment_type or "").upper()
    if "GRAVITY" in name:
        return GRAVITY
    if any(k in name for k in ("CANTILEVER", "COUNTERFORT", "BUTTRESS", "STUB")):
        return CANTILEVER
    return BATTERED


def elevation_outline(
    family: Family,
    *,
    footing_frac: float = _FOOTING_FRAC,
    stem_frac: float = _STEM_FRAC,
    top_batter_frac: float = _TOP_BATTER_FRAC,
) -> list[tuple[float, float]]:
    """Transverse-elevation outline for *family*, normalised [0,1], closed ring."""
    if family == GRAVITY:
        h = top_batter_frac
        return [(h, 1.0), (1.0 - h, 1.0), (1.0, 0.0), (0.0, 0.0)]
    if family == CANTILEVER:
        lo = (1.0 - stem_frac) / 2.0
        hi = 1.0 - lo
        fd = footing_frac
        return [
            (lo, 1.0),
            (hi, 1.0),
            (hi, fd),
            (1.0, fd),
            (1.0, 0.0),
            (0.0, 0.0),
            (0.0, fd),
            (lo, fd),
        ]
    # BATTERED / unknown — plain rectangle
    return [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
