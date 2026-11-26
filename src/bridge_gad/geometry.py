"""Geometry calculations for bridge components."""

import math
from typing import List


def compute_bending_moment(span: float, load: float) -> float:
    """Compute maximum bending moment for a simply supported beam."""
    return (load * span ** 2) / 8.0


def compute_shear_force(load: float, span: float) -> float:
    """Compute maximum shear force at supports."""
    return load * span / 2.0


def compute_deflection(span: float, load: float, E: float, I: float) -> float:  # noqa: E741
    """Compute maximum deflection for a simply supported beam under UDL."""
    return (5 * load * span ** 4) / (384 * E * I)


def summarize(span: float, load: float, E: float, I: float) -> dict:  # noqa: E741
    """Return all computed parameters as a dict."""
    return {
        "BendingMoment": compute_bending_moment(span, load),
        "ShearForce": compute_shear_force(load, span),
        "Deflection": compute_deflection(span, load, E, I),
    }


def compute_bridge_geometry(
    span_lengths: List[float],
    deck_width: float,
    girder_spacing: float
) -> dict:
    """Compute basic bridge geometry parameters.

    Args:
        span_lengths: List of span lengths for each span (m)
        deck_width: Width of bridge deck (m)
        girder_spacing: Spacing between girders (m)

    Returns:
        Dictionary with computed geometry parameters
    """
    total_length = sum(span_lengths)
    num_girders = math.ceil(deck_width / girder_spacing) + 1

    return {
        "total_length": total_length,
        "num_spans": len(span_lengths),
        "span_lengths": span_lengths,
        "deck_width": deck_width,
        "num_girders": num_girders,
        "girder_spacing": girder_spacing
    }
