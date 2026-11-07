"""bridgecad_core.skew — skew transform for plan, section and bearing seats.

A support line is the pier/abutment line rotated about the alignment
centreline by the skew angle.  ``skew=0`` must reproduce the square geometry
exactly — every consumer branches on ``angle_deg == 0`` implicitly through the
trigonometry.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .types import SkewDirection


@dataclass(frozen=True)
class SupportLine:
    chainage_m: Decimal
    angle_deg: Decimal  # signed, +ve = clockwise from normal
    p_left: tuple[Decimal, Decimal]
    p_right: tuple[Decimal, Decimal]


def _skew_rad(project: Any) -> float:
    gi = project.geometry_input
    deg = float(getattr(gi, "skew_angle_deg", 0.0) or 0.0)
    direction = getattr(gi, "skew_direction", SkewDirection.NONE)
    sign = 1.0
    if direction == SkewDirection.LEFT:
        sign = -1.0
    elif direction == SkewDirection.RIGHT:
        sign = 1.0
    return math.radians(sign * deg)


def support_line(project: Any, chainage_m: Decimal) -> SupportLine:
    """Pier/abutment line at *chainage_m*, rotated by the project skew."""
    gi = project.geometry_input
    theta = _skew_rad(project)
    half_w = float(gi.overall_width_m or 0.0) / 2.0
    c = float(chainage_m)
    # Support-line direction: unrotated it runs along y (transverse); the skew
    # rotates it by theta about the centreline point (c, 0).
    ux, uy = math.sin(theta), math.cos(theta)
    p_left = (
        Decimal(str(c - ux * half_w)),
        Decimal(str(-uy * half_w)),
    )
    p_right = (
        Decimal(str(c + ux * half_w)),
        Decimal(str(uy * half_w)),
    )
    deg = Decimal(str(math.degrees(theta)))
    return SupportLine(
        chainage_m=Decimal(str(c)),
        angle_deg=deg,
        p_left=p_left,
        p_right=p_right,
    )


def clear_span_m(project: Any, span_index: int) -> Decimal:
    """Geometric clear span of *span_index* (0-based) in metres."""
    spans = list(project.geometry_input.span_lengths_m or [])
    if 0 <= span_index < len(spans):
        return Decimal(str(spans[span_index]))
    return Decimal("0")


def effective_span_m(project: Any, span_index: int) -> Decimal:
    """IRC skew reduction: effective span = clear span × cos(skew).

    At skew 0 this returns the clear span exactly.
    """
    span = clear_span_m(project, span_index)
    if span <= 0:
        return span
    theta = abs(_skew_rad(project))
    return Decimal(str(float(span) * math.cos(theta))).quantize(Decimal("0.001"))


def obtuse_corner_is_left(project: Any) -> bool:
    """True when the obtuse (wide) corner of the deck sits on the left side.

    ``skew_direction`` names the acute side; the obtuse corner is opposite.
    """
    direction = getattr(project.geometry_input, "skew_direction", SkewDirection.NONE)
    return direction == SkewDirection.RIGHT


def check_curve_radius(project: Any) -> None:
    """Reject degenerate curved-deck radii with a clear message."""
    gi = project.geometry_input
    if not getattr(gi, "curved_bridge_flag", False):
        return
    radius = getattr(gi, "curve_radius_m", None)
    if radius is None:
        return  # insufficient data — the sheet draws the tangent fallback
    if float(radius) < 30.0:
        raise ValueError(
            f"curve_radius_m={float(radius):.1f} is below the 30 m minimum — "
            "refusing to draw a degenerate arc"
        )


__all__ = [
    "SupportLine",
    "support_line",
    "clear_span_m",
    "effective_span_m",
    "obtuse_corner_is_left",
    "check_curve_radius",
]
