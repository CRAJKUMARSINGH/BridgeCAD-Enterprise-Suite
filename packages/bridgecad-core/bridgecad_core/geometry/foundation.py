"""
bridgecad_core.geometry.foundation — Foundation layout geometry.
M1 Week 1 Day 4: N×M pile group grid, pile cap corners,
well-foundation outer circle, open-footing stepped outline.
All outputs in metres, centred at (0, 0) of the pier/abutment centreline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bridgecad_core.models import BridgeProject


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------


@dataclass
class PileGroupLayout:
    """Pile group and pile-cap geometry centred at (0, 0).

    Coordinate convention
    ---------------------
    - X is transverse (parallel to the bridge axis at plan view).
    - Y is longitudinal (perpendicular to the bridge axis, toward the river).
    - (0, 0) is the pier / abutment centreline at top of pile cap.
    """

    # ---- pile data -------------------------------------------------------
    pile_diameter_m: float = 0.0
    pile_spacing_m: float = 0.0
    piles_per_group: int = 0
    pile_rows: int = 0
    pile_cols: int = 0

    pile_positions: list[tuple[float, float]] = field(default_factory=list)
    """(x, y) centre of each pile (metres from group centroid)."""

    # ---- pile cap --------------------------------------------------------
    pile_cap_width_m: float = 0.0  # transverse
    pile_cap_length_m: float = 0.0  # longitudinal
    pile_cap_thickness_m: float = 0.0
    pile_cap_corners: list[tuple[float, float]] = field(default_factory=list)
    """4 corners of pile cap rectangle (x, y): BL, BR, TR, TL."""

    # ---- well foundation (if used instead of piles) ----------------------
    well_outer_radius_m: float = 0.0
    well_inner_radius_m: float = 0.0
    well_total_depth_m: float = 0.0

    # ---- open footing stepped outline -----------------------------------
    open_footing_steps: list[tuple[float, float, float, float]] = field(default_factory=list)
    """List of (x_left, y_bottom, width, height) for each footing step."""


# ---------------------------------------------------------------------------
# Internal helpers — standard non-grid pile layouts
# ---------------------------------------------------------------------------


def _std_triangular_3(spacing: float) -> list[tuple[float, float]]:
    """Equilateral triangle — apex up, base below (standard 3-pile pier cap).

    Piles are numbered: [top-centre, bottom-left, bottom-right] so the
    centroid of the three positions is exactly at (0, 0).
    """
    h = spacing * math.sqrt(3.0) / 2.0  # height of equilateral triangle
    return [
        (0.0, h * 2.0 / 3.0),  # apex   (1/3 of total h above centre)
        (-spacing / 2.0, -h / 3.0),  # bottom-left
        (spacing / 2.0, -h / 3.0),  # bottom-right
    ]


def _std_cruciform_5(spacing: float) -> list[tuple[float, float]]:
    """5-pile 'plus' / cruciform — centre + four cardinal directions.

    Standard arrangement for medium-load single-column hammerhead piers.
    All outer piles at *spacing* from centre.
    """
    return [
        (0.0, 0.0),  # centre
        (-spacing, 0.0),  # west
        (spacing, 0.0),  # east
        (0.0, -spacing),  # south
        (0.0, spacing),  # north
    ]


def _std_hexagonal_7(spacing: float) -> list[tuple[float, float]]:
    """7-pile hexagon + centre — standard for heavily-loaded 2-column piers.

    Six outer piles on a regular hexagon of side *spacing*, centred on the
    origin.  Angle for first vertex: 0° (east).
    """
    positions: list[tuple[float, float]] = [(0.0, 0.0)]  # centre
    for k in range(6):
        theta = math.radians(60.0 * k)
        positions.append((spacing * math.cos(theta), spacing * math.sin(theta)))
    return positions


def _rectangular_grid(n_piles: int, spacing: float) -> tuple[int, int, list[tuple[float, float]]]:
    """Fallback rectangular rows × cols layout used for any non-standard N.

    Returns ``(rows, cols, positions)``.  The grid is nearly square and
    positions are centred on (0, 0).
    """
    cols = max(1, math.ceil(math.sqrt(n_piles)))
    rows = max(1, math.ceil(n_piles / cols))
    while rows * cols < n_piles:
        cols += 1
    positions: list[tuple[float, float]] = []
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= n_piles:
                break
            x = (c - (cols - 1) / 2.0) * spacing
            y = (r - (rows - 1) / 2.0) * spacing
            positions.append((x, y))
    return rows, cols, positions


def _standard_pile_positions(
    n_piles: int,
    spacing: float,
) -> tuple[int, int, list[tuple[float, float]]]:
    """Return ``(rows, cols, positions)`` preferring standard arrangements.

    Standard IRC / IS:2911 layouts are selected for N ∈ {3, 5, 7}; every
    other N falls through to the rectangular grid.  ``rows`` and ``cols``
    for non-rectangular layouts are nominal bounding-box dimensions used
    downstream to size the pile cap conservatively.
    """
    if n_piles == 3:
        return 2, 2, _std_triangular_3(spacing)
    if n_piles == 5:
        return 3, 3, _std_cruciform_5(spacing)
    if n_piles == 7:
        return 3, 3, _std_hexagonal_7(spacing)
    return _rectangular_grid(n_piles, spacing)


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


def compute_pile_group_layout(project: BridgeProject) -> PileGroupLayout:
    """Derive pile group geometry for the primary pier from a validated BridgeProject.

    Parameters
    ----------
    project : BridgeProject
        Fully-validated Pydantic model instance.

    Returns
    -------
    PileGroupLayout
        Populated dataclass.  For well / open foundations the pile_positions
        list is empty and the relevant well/footing fields are set instead.
    """
    fd = project.foundation_details
    sub = project.substructure

    from bridgecad_core.types import FoundationType

    foundation_type = fd.type

    # ---- pile foundation ------------------------------------------------
    if foundation_type == FoundationType.PILE:
        pile_dia_m = float(fd.pile_diameter_mm) / 1000.0 if fd.pile_diameter_mm else 1.2
        pile_spacing = float(fd.pile_spacing_m) if fd.pile_spacing_m else 2.4
        n_piles = int(fd.piles_per_pier) if fd.piles_per_pier else 4
        cap_thick_m = float(fd.pile_cap_thickness_mm) / 1000.0 if fd.pile_cap_thickness_mm else 1.5

        # --- rows × cols + positions (standard IRC layouts preferred) ------
        rows, cols, pile_positions = _standard_pile_positions(n_piles, pile_spacing)

        # --- pile cap bounding box from real positions + 100 mm overhang -
        # Using the min/max of the actual pile centres guarantees correct
        # sizing for triangular, cruciform and hexagonal layouts as well as
        # the rectangular grid fallback.
        if pile_positions:
            xs = [p[0] for p in pile_positions]
            ys = [p[1] for p in pile_positions]
            cap_w = (max(xs) - min(xs)) + pile_dia_m + 2 * 0.100
            cap_l = (max(ys) - min(ys)) + pile_dia_m + 2 * 0.100
        else:
            cap_w = (cols - 1) * pile_spacing + pile_dia_m + 2 * 0.100
            cap_l = (rows - 1) * pile_spacing + pile_dia_m + 2 * 0.100
        half_w = cap_w / 2.0
        half_l = cap_l / 2.0

        cap_corners = [
            (-half_w, -half_l),  # BL
            (half_w, -half_l),  # BR
            (half_w, half_l),  # TR
            (-half_w, half_l),  # TL
        ]

        return PileGroupLayout(
            pile_diameter_m=pile_dia_m,
            pile_spacing_m=pile_spacing,
            piles_per_group=n_piles,
            pile_rows=rows,
            pile_cols=cols,
            pile_positions=pile_positions,
            pile_cap_width_m=cap_w,
            pile_cap_length_m=cap_l,
            pile_cap_thickness_m=cap_thick_m,
            pile_cap_corners=cap_corners,
        )

    # ---- well (caisson) foundation --------------------------------------
    from bridgecad_core.types import FoundationType

    if foundation_type in (FoundationType.WELL, FoundationType.WELL_PLUS_PILE):
        # Well outer diameter inferred from pier shaft width (approx 2.5× shaft)
        pier_shaft_w = float(sub.pier_shaft_width_m) if sub.pier_shaft_width_m else 2.0
        outer_r = max(pier_shaft_w, 1.5)  # minimum 1.5 m outer radius
        inner_r = outer_r * 0.55  # steining thickness ≈ 0.45 × outer_r
        # Depth from scour level to pile cutoff (approximate)
        pile_cut = (
            float(project.foundation_details.pile_cutoff_level_m) if fd.pile_cutoff_level_m else 0.0
        )
        well_depth = max(0.0, float(project.hydraulic_data.scour_level_m) - pile_cut + 5.0)

        return PileGroupLayout(
            well_outer_radius_m=outer_r,
            well_inner_radius_m=inner_r,
            well_total_depth_m=well_depth,
        )

    # ---- open / raft foundation -----------------------------------------
    # Build stepped outline: base footing + wall footing (2-step common)
    footing_width_base = float(sub.pier_shaft_width_m) * 3.0 if sub.pier_shaft_width_m else 3.0
    footing_width_top = float(sub.pier_shaft_width_m) * 1.8 if sub.pier_shaft_width_m else 1.8
    step_height = 0.3  # 300 mm per step (typical)

    steps = [
        (-(footing_width_base / 2), 0.0, footing_width_base, step_height),  # base
        (-(footing_width_top / 2), step_height, footing_width_top, step_height),  # top step
    ]

    return PileGroupLayout(
        open_footing_steps=steps,
    )


__all__ = ["PileGroupLayout", "compute_pile_group_layout"]
