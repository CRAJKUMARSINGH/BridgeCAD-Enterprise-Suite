"""
bridgecad_core.geometry.long_section — Longitudinal section geometry.
M1 Week 1 Day 4: HFL/LWL/scour level markers, soffit, top-of-deck, pile-tip,
and linear ground-profile interpolation along bridge length.
All Y values are real-world Reduced Levels (metres RL).
All X values are chainage relative to A1 abutment face (metres).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bridgecad_core.models import BridgeProject


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class LongSectionGeometry:
    """Longitudinal section level markers and profile points.

    All ``*_rl`` attributes are Reduced Levels in metres (absolute datum).
    ``*_y`` are synonyms kept for drawing-engine compatibility.
    ``ground_profile_pts`` is a list of (chainage_m, rl_m) tuples suitable
    for direct plotting as a polyline.
    """

    # ---- level markers (RL, metres) -------------------------------------
    hfl_rl: float          = 0.0   # Highest Flood Level
    lwl_rl: float          = 0.0   # Low Water Level
    scour_level_rl: float  = 0.0   # Design scour level (bottom of scour hole)
    soffit_rl: float       = 0.0   # Underside of deck / girder soffit
    top_of_deck_rl: float  = 0.0   # Road formation / top-of-wearing-coat level
    pile_tip_rl: float     = 0.0   # Bottom of longest pile

    # ---- chainage limits -----------------------------------------------
    chainage_start_m: float = 0.0
    chainage_end_m: float   = 0.0
    total_length_m: float   = 0.0

    # ---- span data (for drawing internal piers on the long section) -----
    span_lengths_m: list[float]                  = field(default_factory=list)
    pier_chainage_m: list[float]                 = field(default_factory=list)

    # ---- ground profile -------------------------------------------------
    ground_profile_pts: list[tuple[float, float]] = field(default_factory=list)
    """(chainage_m_from_a1, rl_m) pairs; 21 points by default."""

    # ---- freeboard check ------------------------------------------------
    freeboard_m: float = 0.0
    """Actual clearance: soffit_rl − hfl_rl  (positive = OK)."""

    # ---- pier datum reference (plan-northern deck-edge alignment) ------
    plan_northern_edge_reference_rl: float = 0.0
    """RL reference shared with Sheet 1 Plan northern deck-edge.
    Tied to top_of_deck_rl so reader can physically align pages across
    plan / elevation views and verify pier T.O.C. sits at correct offset.
    """

    pier_top_of_cap_rl_m: list[float] = field(default_factory=list)
    """Per-pier Top-Of-Concrete pier-cap RL; index aligned with pier_chainage_m.
    Derived from soffit_rl minus pedestal_h minus pier_cap_depth_m
    (substructure real values, not guesswork). For 0-internal-pier projects
    this list is empty — use abutment_top_of_rail_rl_m instead.
    """

    abutment_top_of_rail_rl_m: float = 0.0
    """Fallback reference RL for 0-internal-pier (single-span) projects;
    equals top_of_deck_rl (same datum as plan-northern-edge reference).
    """

    # ---- convenience aliases (y = rl for flat drawing baseline) ---------
    @property
    def hfl_y(self) -> float:
        return self.hfl_rl

    @property
    def lwl_y(self) -> float:
        return self.lwl_rl

    @property
    def scour_level_y(self) -> float:
        return self.scour_level_rl

    @property
    def soffit_y(self) -> float:
        return self.soffit_rl

    @property
    def top_of_deck_y(self) -> float:
        return self.top_of_deck_rl

    @property
    def pile_tip_y(self) -> float:
        return self.pile_tip_rl


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def compute_long_section_geometry(project: BridgeProject) -> LongSectionGeometry:
    """Derive longitudinal-section level markers from a validated BridgeProject.

    Parameters
    ----------
    project : BridgeProject
        Fully-validated Pydantic model instance.

    Returns
    -------
    LongSectionGeometry
        Populated dataclass with real-world RL metre values.
    """
    pm  = project.project_master
    gi  = project.geometry_input
    hd  = project.hydraulic_data
    fd  = project.foundation_details
    ss  = project.superstructure
    sub = project.substructure

    # ---- level values ----------------------------------------------------
    hfl_rl         = float(hd.hfl_m)
    lwl_rl         = float(hd.lwl_m)
    scour_level_rl = float(hd.scour_level_m)
    soffit_rl      = float(hd.actual_soffit_level_m)

    # Top-of-deck = road level from project master
    top_of_deck_rl = float(pm.road_level_rl_m) if pm.road_level_rl_m is not None else (
        soffit_rl
        + (float(ss.girder_depth_mm) / 1000.0 if ss.girder_depth_mm else 0.0)
        + (float(ss.deck_thickness_mm) / 1000.0 if ss.deck_thickness_mm else 0.0)
        + (float(ss.wearing_coat_thickness_mm) / 1000.0 if ss.wearing_coat_thickness_mm else 0.0)
    )

    # Pile tip level
    pile_cutoff = float(fd.pile_cutoff_level_m) if fd.pile_cutoff_level_m is not None else (
        float(pm.ground_level_rl_m) if pm.ground_level_rl_m is not None else scour_level_rl
    )
    pile_len = float(fd.pile_length_m) if fd.pile_length_m is not None else 0.0
    pile_tip_rl = pile_cutoff - pile_len

    # ---- chainage / span data -------------------------------------------
    total_len       = float(gi.total_length_m)
    span_lengths    = [float(s) for s in gi.span_lengths_m]

    ch_start = float(gi.chainage_start_km) * 1000.0  # km → m absolute
    ch_end   = float(gi.chainage_end_km)   * 1000.0

    # Pier chainages along bridge (relative to A1)
    pier_ch: list[float] = []
    cumul = 0.0
    for slen in span_lengths[:-1]:
        cumul += slen
        pier_ch.append(cumul)

    # ---- ground profile (21-point linear interpolation) -----------------
    ground_start = (
        float(pm.ground_level_rl_m) if pm.ground_level_rl_m is not None else hfl_rl - 1.5
    )
    # Assume ground at A2 slightly lower by 1% gradient (approximation)
    gradient_frac = float(gi.gradient_pct) / 100.0 if gi.gradient_pct is not None else 0.0
    ground_end = ground_start - total_len * gradient_frac

    n_pts = 20
    ground_profile_pts: list[tuple[float, float]] = []
    for i in range(n_pts + 1):
        t = i / n_pts
        ch_rel = t * total_len          # chainage from A1 face (0 → total_len)
        rl = ground_start + t * (ground_end - ground_start)
        ground_profile_pts.append((ch_rel, rl))

    # ---- freeboard -------------------------------------------------------
    freeboard_m = soffit_rl - hfl_rl

    # ---- plan-northern-edge datum + pier T.O.C. values ------------------
    plan_northern_edge_reference_rl = top_of_deck_rl

    pedestal_h = float(sub.pier_pedestal_height_m) if sub.pier_pedestal_height_m is not None else 0.20
    pier_cap_depth_m = float(sub.pier_cap_depth_m) if sub.pier_cap_depth_m is not None else 0.80
    pier_top_of_cap_rl_m: list[float] = [
        soffit_rl - pedestal_h - pier_cap_depth_m for _ in pier_ch
    ]

    abutment_top_of_rail_rl_m = top_of_deck_rl

    return LongSectionGeometry(
        hfl_rl=hfl_rl,
        lwl_rl=lwl_rl,
        scour_level_rl=scour_level_rl,
        soffit_rl=soffit_rl,
        top_of_deck_rl=top_of_deck_rl,
        pile_tip_rl=pile_tip_rl,
        chainage_start_m=ch_start,
        chainage_end_m=ch_end,
        total_length_m=total_len,
        span_lengths_m=span_lengths,
        pier_chainage_m=pier_ch,
        ground_profile_pts=ground_profile_pts,
        freeboard_m=freeboard_m,
        plan_northern_edge_reference_rl=plan_northern_edge_reference_rl,
        pier_top_of_cap_rl_m=pier_top_of_cap_rl_m,
        abutment_top_of_rail_rl_m=abutment_top_of_rail_rl_m,
    )


# ---------------------------------------------------------------------------
# Span / pier loops — the one place the counts are defined
# ---------------------------------------------------------------------------

def span_lengths_m(project: BridgeProject) -> list[float]:
    """Span lengths in metres, in order along increasing chainage.

    Reads the modelled list where present and falls back to nspan copies of a
    single span length, so a drafting override cannot leave the two out of step.
    """
    gi = project.geometry_input
    lengths = getattr(gi, "span_lengths_m", None)
    if lengths:
        return [float(x) for x in lengths]
    nspan = int(getattr(gi, "span_count", 1) or 1)
    single = getattr(gi, "span_length_m", None)
    if single is None:
        single = 12.0
    return [float(single)] * nspan


def span_boundaries(project: BridgeProject) -> list[float]:
    """Chainages of every span boundary, relative to the first abutment.

    CONTRACT: len(boundaries) == nspan + 1, monotonic, strictly increasing.
    """
    boundaries = [0.0]
    cumulative = 0.0
    for length in span_lengths_m(project):
        cumulative += length
        boundaries.append(cumulative)
    return boundaries


def pier_positions(project: BridgeProject) -> list[float]:
    """Chainages of INTERMEDIATE piers only — abutments are not piers.

    CONTRACT: len(piers) == max(nspan - 1, 0), each coincident with a boundary.
    """
    return span_boundaries(project)[1:-1]


__all__ = [
    "LongSectionGeometry", "compute_long_section_geometry",
    "span_lengths_m", "span_boundaries", "pier_positions",
]
