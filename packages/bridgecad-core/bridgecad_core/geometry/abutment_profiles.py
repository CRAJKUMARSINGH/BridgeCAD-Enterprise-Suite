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
import math

__all__ = [
    "Family",
    "family_for",
    "elevation_outline",
    "battered_side_outline",
    "BatteredSide",
]

Family = str

GRAVITY = "gravity"  # trapezoid mass wall, battered both faces
CANTILEVER = "cantilever"  # inverted-T: thin stem + projecting base footing
BATTERED = "battered"  # legacy rectangle block

_FOOTING_FRAC = 0.18  # base-slab depth as a height fraction (cantilever)
_STEM_FRAC = 0.5  # stem width as a width fraction (cantilever)
_TOP_BATTER_FRAC = 0.25  # face run-back at the top (gravity)


def family_for(abutment_type: Any) -> Family:
    """Map an AbutmentType (enum, .name, or .value) to a shape family.

    The fall-through is deliberate, not sloppiness.  An integral abutment
    (``INTEGRAL_ABUTMENT``) or an RCC portal frame is cast monolithic with the
    deck: a full-height wall carrying the deck directly, with no bearing shelf
    and no cantilever stem.  That elevation *is* the plain rectangle this module
    draws for BATTERED, so those types share it rather than inventing a fourth
    family that the JS mirror (``detailGeometry.js``) does not model.
    """
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


# ── LISP abt1() battered side profile ──────────────────────────────────────
# Faithful port of frontend/src/sheets/detailGeometry.js abutmentProfile().
# This is the SIDE (longitudinal) profile: riverside face batter and earthside
# (dirt-wall side) batter are DIFFERENT parameters — face 1:10 gentle, back
# 1:3 steep in the LISP defaults.

from dataclasses import dataclass


@dataclass(frozen=True)
class BatteredSide:
    """Resolved abt1() profile in metres; y measured up from footing bottom."""

    points: list[tuple[float, float]]  # closed polygon, sheet-x/y in metres
    cap_top_y: float  # RTL — top of the face upstand
    cap_bot_y: float  # cap soffit
    stem_bot_y: float  # altbl — top of footing / bottom of stem
    foot_bot_y: float  # y8 — underside of footing
    dirt_wall_x: float  # outer face of the dirt wall


def battered_side_outline(
    stem_h_m: float,
    *,
    cap_w_m: float = 0.75,
    cap_d_m: float = 1.2,
    face_batter_1n: float = 10.0,
    back_batter_1n: float = 3.0,
    toe_m: float = 1.5,
    foot_d_m: float = 1.0,
    above_m: float = 0.98,
    dirt_w_m: float = 0.3,
    front_break_h_m: float = 0.0,
    back_break_h_m: float = 0.0,
    toe_batter_1n: float = 1.0,
) -> BatteredSide:
    """LISP abt1() 14-vertex battered abutment side profile, in metres.

    ``stem_h_m`` is the stem height from cap soffit down to the footing top.
    ``face_batter_1n`` / ``back_batter_1n`` are the riverside and earthside
    batters as 1:n (horizontal run = height / n).  The polygon is drawn for
    the +x orientation (A2): face anchor at x=0, dirt wall outward at +x;
    mirror x for A1.

    Optional front/back break heights preserve the source's independent
    ``alfbl``/``albbl`` levels above footing top ``altbl``. Zero defaults keep
    the former simplified outline. ``toe_batter_1n`` is source ``altb``.
    These are geometry inputs, not a foundation design or a global default.
    """
    stem_h = max(float(stem_h_m), 0.5)
    for name, value in (("front_break_h_m", front_break_h_m), ("back_break_h_m", back_break_h_m)):
        if not math.isfinite(value) or not 0 <= value <= stem_h:
            raise ValueError(f"{name} must be finite and between 0 and stem height")
    for name, value in (("face_batter_1n", face_batter_1n), ("back_batter_1n", back_batter_1n), ("toe_batter_1n", toe_batter_1n)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    y_cap_bot = foot_d_m + stem_h  # cap soffit
    y_foot_top = foot_d_m  # altbl — stem bottom / footing top
    y_foot_bot = 0.0  # y8
    y_cap_top = y_cap_bot + cap_d_m
    y_rtl = y_cap_top + above_m

    x1 = 0.0  # riverside face anchor
    x3 = cap_w_m  # cap earth-side edge
    # abt1(): capb -> alfbl uses alfb, then alfbl -> altbl uses altb.
    # Break heights are measured above footing top, not absolute RL values.
    x5 = x3 + (stem_h - front_break_h_m) / face_batter_1n
    x6 = x5 + front_break_h_m / toe_batter_1n
    x7 = x6 + toe_m  # toe
    x14 = x1 - dirt_w_m  # dirt wall outer face (earthside, −x in this frame)
    x12 = x14 - (stem_h - back_break_h_m) / back_batter_1n
    x10 = x12 - toe_m

    pts = [
        (x1, y_rtl),
        (x1, y_cap_top),
        (x3, y_cap_top),
        (x3, y_cap_bot),
        (x5, y_foot_top + front_break_h_m),
        (x6, y_foot_top),
        (x7, y_foot_top),
        (x7, y_foot_bot),
        (x10, y_foot_bot),
        (x10, y_foot_top),
        (x12, y_foot_top),
        (x12, y_foot_top + back_break_h_m),
        (x14, y_cap_bot),
        (x14, y_rtl),
    ]
    return BatteredSide(
        points=pts,
        cap_top_y=y_cap_top,
        cap_bot_y=y_cap_bot,
        stem_bot_y=y_foot_top,
        foot_bot_y=y_foot_bot,
        dirt_wall_x=x14,
    )
