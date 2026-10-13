"""
bridgecad_core.geometry.plan — Plan-view geometry.
M1 Week 1 Day 4: skew-aware deck corners, pier centrelines, bearing positions,
abutment face coordinates.  All outputs in metres (real-world).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bridgecad_core.models import BridgeProject


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class BridgePlanGeometry:
    """Plan-view coordinate set derived from a BridgeProject.

    All coordinates are in metres from the A1-abutment centreline datum:
      - X axis runs along the bridge centreline (increasing toward A2).
      - Y axis runs transversely (positive toward the left when facing A2).

    For a skewed bridge the corners are rotated by *-skew_angle* around the
    left carriageway edge.
    """

    # ---- inputs (stored for reference) -----------------------------------
    total_length_m: float
    overall_width_m: float
    skew_angle_deg: float
    span_lengths_m: list[float]

    # ---- computed outputs -------------------------------------------------
    deck_corners: list[tuple[float, float]] = field(default_factory=list)
    """4 corners in order: A1-left, A1-right, A2-right, A2-left (looking toward A2)."""

    pier_centrelines: list[tuple[float, float]] = field(default_factory=list)
    """Centreline point (x, 0.0) of each internal pier."""

    bearing_positions: list[tuple[float, float]] = field(default_factory=list)
    """Approximate bearing pad centres (x, y) for all piers + abutments."""

    abutment_a1_face: tuple[float, float] = field(default=(0.0, 0.0))
    """A1 (start) abutment front face centreline point."""

    abutment_a2_face: tuple[float, float] = field(default=(0.0, 0.0))
    """A2 (end) abutment front face centreline point."""


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def _rotate(x: float, y: float, theta_rad: float) -> tuple[float, float]:
    """Rotate point (x, y) by theta_rad counter-clockwise."""
    cos_t = math.cos(theta_rad)
    sin_t = math.sin(theta_rad)
    return (x * cos_t - y * sin_t, x * sin_t + y * cos_t)


def compute_plan_geometry(project: "BridgeProject") -> BridgePlanGeometry:
    """Derive plan-view geometry from a validated BridgeProject instance.

    Parameters
    ----------
    project : BridgeProject
        Fully-validated Pydantic model instance.

    Returns
    -------
    BridgePlanGeometry
        Populated dataclass with real-world metre coordinates.
    """
    gi = project.geometry_input
    ss = project.superstructure

    total_len = float(gi.total_length_m)          # computed field
    overall_w = float(gi.overall_width_m)          # computed field
    skew_deg = float(gi.skew_angle_deg)
    span_lengths = [float(s) for s in gi.span_lengths_m]
    span_count = gi.span_count

    half_w = overall_w / 2.0
    theta = -math.radians(skew_deg)               # skew rotates deck clockwise

    # ---- deck corners (pre-rotation) -------------------------------------
    # A1: x=0,  A2: x=total_len
    # Left side: y = +half_w,  Right side: y = -half_w  (IRC convention)
    raw_corners = [
        (0.0,         +half_w),   # A1-left
        (0.0,         -half_w),   # A1-right
        (total_len,   -half_w),   # A2-right
        (total_len,   +half_w),   # A2-left
    ]
    deck_corners = [_rotate(x, y, theta) for x, y in raw_corners]

    # ---- pier centrelines ------------------------------------------------
    # Simply-supported: pier between every pair of adjacent spans (N-1 piers)
    pier_centrelines: list[tuple[float, float]] = []
    cumulative = 0.0
    for i, slen in enumerate(span_lengths[:-1]):   # no pier after last span
        cumulative += slen
        px, py = _rotate(cumulative, 0.0, theta)
        pier_centrelines.append((px, py))

    # ---- bearing positions -----------------------------------------------
    # Girder spacing drives bearing y-offsets; fall back to equal spacing.
    bearing_positions: list[tuple[float, float]] = []

    # Number of bearings per support cross-line
    girder_count = getattr(ss, "girders_per_deck_count", None) or 4
    girder_spacing = float(getattr(ss, "girder_spacing_m", None) or
                           (overall_w / (girder_count + 1)))

    y_offsets = [
        (i - (girder_count - 1) / 2.0) * girder_spacing
        for i in range(girder_count)
    ]

    # A1 abutment bearings (x=0)
    for yo in y_offsets:
        bx, by = _rotate(0.0, yo, theta)
        bearing_positions.append((bx, by))

    # Pier bearings
    cumulative = 0.0
    for slen in span_lengths[:-1]:
        cumulative += slen
        for yo in y_offsets:
            bx, by = _rotate(cumulative, yo, theta)
            bearing_positions.append((bx, by))

    # A2 abutment bearings (x=total_len)
    for yo in y_offsets:
        bx, by = _rotate(total_len, yo, theta)
        bearing_positions.append((bx, by))

    # ---- abutment face points -------------------------------------------
    a1_x, a1_y = _rotate(0.0, 0.0, theta)
    a2_x, a2_y = _rotate(total_len, 0.0, theta)

    return BridgePlanGeometry(
        total_length_m=total_len,
        overall_width_m=overall_w,
        skew_angle_deg=skew_deg,
        span_lengths_m=span_lengths,
        deck_corners=deck_corners,
        pier_centrelines=pier_centrelines,
        bearing_positions=bearing_positions,
        abutment_a1_face=(a1_x, a1_y),
        abutment_a2_face=(a2_x, a2_y),
    )


__all__ = ["BridgePlanGeometry", "compute_plan_geometry"]
