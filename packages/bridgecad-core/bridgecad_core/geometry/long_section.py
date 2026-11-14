"""
bridgecad_core.geometry.long_section — Longitudinal section geometry.
M1 Week 1 Day 4: HFL/LWL/scour level markers, soffit, top-of-deck, pile-tip,
and linear ground-profile interpolation along bridge length.
All Y values are real-world Reduced Levels (metres RL).
All X values are chainage relative to A1 abutment face (metres).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

from .support_levels import (
    AuthorityMode,
    SupportLevelInput,
    SupportLevelRecord,
    resolve_support_levels,
)

if TYPE_CHECKING:
    from bridgecad_core.models import BridgeProject

_MM_PER_M = Decimal("1000")


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
    hfl_rl: float = 0.0  # Highest Flood Level
    lwl_rl: float = 0.0  # Low Water Level
    scour_level_rl: float = 0.0  # Design scour level (bottom of scour hole)
    soffit_rl: float = 0.0  # Underside of deck / girder soffit
    top_of_deck_rl: float = 0.0  # Road formation / top-of-wearing-coat level
    pile_tip_rl: float = 0.0  # Bottom of longest pile

    # ---- chainage limits -----------------------------------------------
    chainage_start_m: float = 0.0
    chainage_end_m: float = 0.0
    total_length_m: float = 0.0

    # ---- span data (for drawing internal piers on the long section) -----
    span_lengths_m: list[float] = field(default_factory=list)
    pier_chainage_m: list[float] = field(default_factory=list)

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
    Derived from soffit_rl minus pedestal_h (cap depth lies below this level)
    (substructure real values, not guesswork). For 0-internal-pier projects
    this list is empty — use abutment_top_of_rail_rl_m instead.
    """

    abutment_top_of_rail_rl_m: float = 0.0
    """Fallback reference RL for 0-internal-pier (single-span) projects;
    equals top_of_deck_rl (same datum as plan-northern-edge reference).
    """

    support_level_records: list[SupportLevelRecord] = field(default_factory=list)
    """Canonical §3 support-level contract, one record per intermediate pier,
    index-aligned with ``pier_chainage_m``. Sheets 1/2/4/5/8 take their RLs
    from these records instead of re-deriving them.
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


def _dec_or_none(value: object) -> Decimal | None:
    """Coerce an optional model value to ``Decimal`` (``None`` stays ``None``)."""
    if value is None:
        return None
    return Decimal(str(value)) if not isinstance(value, Decimal) else value


def _pier_support_level_input(
    project: "BridgeProject",
    *,
    support_id: str,
    top_of_deck_rl: float,
    soffit_rl: float | None,
) -> SupportLevelInput:
    """Build the canonical §3 input for one intermediate pier from the model.

    The seat is the SEPARATE topology: ``bearing_depth_mm`` (a real bearing
    unit) sits above ``pier_pedestal_height_m``. An undeclared bearing depth
    becomes an explicit zero marked ASSUMED, so the historical
    ``soffit − pedestal`` datum is reproduced from one contract rather than
    re-derived by each renderer. The pier foundation is the pile cap:
    ``pile_cutoff_level_m`` is its underside and ``pile_cap_thickness_mm`` its
    thickness; when either is absent the footing stays UNRESOLVED rather than
    inventing a depth.
    """
    ss = project.superstructure
    sub = project.substructure
    fd = project.foundation_details
    pm = project.project_master
    hd = project.hydraulic_data

    bearing_mm = getattr(ss, "bearing_depth_mm", None)
    bearing = (
        Decimal("0") if bearing_mm is None else Decimal(str(bearing_mm)) / _MM_PER_M
    )

    wearing_m = Decimal(str(ss.wearing_coat_thickness_mm or 0)) / _MM_PER_M
    structural_m = Decimal(str(ss.deck_thickness_mm or 0)) / _MM_PER_M
    if getattr(ss, "girder_depth_mm", None):
        structural_m += Decimal(str(ss.girder_depth_mm)) / _MM_PER_M

    cap_thk_mm = getattr(fd, "pile_cap_thickness_mm", None)
    return SupportLevelInput(
        support_id=support_id,
        road_rl_m=Decimal(str(top_of_deck_rl)),
        wearing_depth_m=wearing_m,
        structural_depth_m=structural_m,
        supplied_soffit_rl_m=(
            None if soffit_rl is None else Decimal(str(soffit_rl))
        ),
        bearing_depth_m=bearing,
        bearing_depth_assumed=bearing_mm is None,
        pedestal_height_m=_dec_or_none(getattr(sub, "pier_pedestal_height_m", None))
        or Decimal("0.20"),
        cap_depth_m=_dec_or_none(getattr(sub, "pier_cap_depth_m", None)),
        footing_bottom_rl_m=_dec_or_none(getattr(fd, "pile_cutoff_level_m", None)),
        footing_depth_m=(
            None if cap_thk_mm is None else Decimal(str(cap_thk_mm)) / _MM_PER_M
        ),
        ground_level_rl_m=_dec_or_none(getattr(pm, "ground_level_rl_m", None)),
        scour_level_rl_m=_dec_or_none(getattr(hd, "scour_level_m", None)),
        pile_cutoff_rl_m=_dec_or_none(getattr(fd, "pile_cutoff_level_m", None)),
        authority=AuthorityMode.LEVEL_CONTROLLED,
    )


def typical_pier_support_level(project: "BridgeProject") -> SupportLevelRecord:
    """The canonical §3 record for a *typical* pier.

    Sheet 4 (Foundation Details) details one typical pier. On a multi-span
    bridge that is the first real pier's record; on a single-span bridge there
    is no intermediate pier, so the same input builder derives a nominal one.
    Either way the sheet reads its pile-cap (footing) top from one contract
    rather than re-adding the cap thickness itself.
    """
    ls = compute_long_section_geometry(project)
    if ls.support_level_records:
        return ls.support_level_records[0]
    hd = project.hydraulic_data
    return resolve_support_levels(
        _pier_support_level_input(
            project,
            support_id="P-typical",
            top_of_deck_rl=ls.top_of_deck_rl,
            soffit_rl=(
                float(hd.actual_soffit_level_m)
                if hd.actual_soffit_level_m is not None
                else None
            ),
        )
    )


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
    pm = project.project_master
    gi = project.geometry_input
    hd = project.hydraulic_data
    fd = project.foundation_details
    ss = project.superstructure
    sub = project.substructure

    # ---- level values ----------------------------------------------------
    hfl_rl = float(hd.hfl_m) if hd.hfl_m is not None else 0.0
    lwl_rl = float(hd.lwl_m) if hd.lwl_m is not None else 0.0
    scour_level_rl = float(hd.scour_level_m) if hd.scour_level_m is not None else 0.0
    soffit_rl = float(hd.actual_soffit_level_m) if hd.actual_soffit_level_m is not None else 0.0

    # Top-of-deck = road level from project master
    top_of_deck_rl = (
        float(pm.road_level_rl_m)
        if pm.road_level_rl_m is not None
        else (
            soffit_rl
            + (float(ss.girder_depth_mm) / 1000.0 if ss.girder_depth_mm else 0.0)
            + (float(ss.deck_thickness_mm) / 1000.0 if ss.deck_thickness_mm else 0.0)
            + (
                float(ss.wearing_coat_thickness_mm) / 1000.0
                if ss.wearing_coat_thickness_mm
                else 0.0
            )
        )
    )

    # Pile tip level
    pile_cutoff = (
        float(fd.pile_cutoff_level_m)
        if fd.pile_cutoff_level_m is not None
        else (float(pm.ground_level_rl_m) if pm.ground_level_rl_m is not None else scour_level_rl)
    )
    pile_len = float(fd.pile_length_m) if fd.pile_length_m is not None else 0.0
    pile_tip_rl = pile_cutoff - pile_len

    # ---- chainage / span data -------------------------------------------
    total_len = float(gi.total_length_m)
    span_lengths = [float(s) for s in gi.span_lengths_m]

    # km → m absolute
    ch_start = float(gi.chainage_start_km) * 1000.0 if gi.chainage_start_km is not None else 0.0
    ch_end = float(gi.chainage_end_km) * 1000.0 if gi.chainage_end_km is not None else 0.0

    # Pier chainages along bridge (relative to A1)
    pier_ch: list[float] = []
    cumul = 0.0
    for slen in span_lengths[:-1]:
        cumul += slen
        pier_ch.append(cumul)

    # ---- ground profile (21-point linear interpolation) -----------------
    ground_start = float(pm.ground_level_rl_m) if pm.ground_level_rl_m is not None else hfl_rl - 1.5
    # Assume ground at A2 slightly lower by 1% gradient (approximation)
    gradient_frac = float(gi.gradient_pct) / 100.0 if gi.gradient_pct is not None else 0.0
    ground_end = ground_start - total_len * gradient_frac

    n_pts = 20
    ground_profile_pts: list[tuple[float, float]] = []
    for i in range(n_pts + 1):
        t = i / n_pts
        ch_rel = t * total_len  # chainage from A1 face (0 → total_len)
        rl = ground_start + t * (ground_end - ground_start)
        ground_profile_pts.append((ch_rel, rl))

    # ---- freeboard -------------------------------------------------------
    freeboard_m = soffit_rl - hfl_rl

    # ---- plan-northern-edge datum + pier T.O.C. values ------------------
    plan_northern_edge_reference_rl = top_of_deck_rl

    # Canonical §3 contract: one resolver computes every pier's cap datum.
    # Sheets read these records; they must not re-derive ``soffit − pedestal``.
    support_records: list[SupportLevelRecord] = [
        resolve_support_levels(
            _pier_support_level_input(
                project,
                support_id=f"P{i + 1}",
                top_of_deck_rl=top_of_deck_rl,
                soffit_rl=(
                    float(hd.actual_soffit_level_m)
                    if hd.actual_soffit_level_m is not None
                    else None
                ),
            )
        )
        for i in range(len(pier_ch))
    ]
    pier_top_of_cap_rl_m: list[float] = [
        float(rec.cap_top_rl_m) for rec in support_records if rec.cap_top_rl_m is not None
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
        support_level_records=support_records,
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
    "LongSectionGeometry",
    "compute_long_section_geometry",
    "typical_pier_support_level",
    "span_lengths_m",
    "span_boundaries",
    "pier_positions",
]
