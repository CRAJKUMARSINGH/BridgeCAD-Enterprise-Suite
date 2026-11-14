"""
bridgecad_core.abutment_stack — the single datum ladder at an abutment.

WHY THIS EXISTS
    Before this module every downstream element was positioned off another
    element's top by raw arithmetic (``cap_top = app_bot - 0.3`` here, a
    different constant there). One missed edit and the wearing coat, the deck,
    the approach slab, the cup and the bearings disagree. That is the class of
    bug that keeps returning.

    ``resolve_abutment_stack`` collapses the whole vertical stack into one
    ordered object. Every element — cap, dirt wall, approach slab, bearing seat,
    continuous wearing coat — takes its RL from this object and from nowhere
    else.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .geometry.support_levels import (
    AuthorityMode,
    BearingTopology,
    SupportLevelInput,
    SupportLevelRecord,
    resolve_support_levels,
)

__all__ = ["AbutmentStack", "resolve_abutment_stack"]

_MM = Decimal("1000")

# Fallbacks used only when a project leaves an optional field unset, so the
# resolver is total: it never raises and never returns ``None``.
_DEFAULT_WC_MM = Decimal("65")
_DEFAULT_DECK_MM = Decimal("200")
_DEFAULT_APP_MM = Decimal("200")
_DEFAULT_CAP_MM = Decimal("600")
_DEFAULT_PED_M = Decimal("0.15")


def _dec(value: Any, default: Decimal) -> Decimal:
    """Coerce *value* to :class:`Decimal`, substituting *default* when ``None``."""
    if value is None:
        return default
    return Decimal(str(value))


@dataclass(frozen=True)
class AbutmentStack:
    """The resolved RL ladder at an abutment, top of road down to bearing seat.

    ``wc_bot``    underside of the wearing coat
    ``slab_top``  top of the deck slab (equals ``wc_bot``)
    ``deck_bot``  underside of the deck slab
    ``app_bot``   underside of the approach slab
    ``cap_top``   top of the abutment cap
    ``cap_bot``   underside of the abutment cap
    ``bear_rl``   bearing seat RL
    ``record``    the canonical §3 :class:`SupportLevelRecord` this ladder was
                  read from, so a consumer can cite the provenance/authority
                  instead of re-deriving a level
    """

    wc_bot: Decimal
    slab_top: Decimal
    deck_bot: Decimal
    app_bot: Decimal
    cap_top: Decimal
    cap_bot: Decimal
    bear_rl: Decimal
    record: SupportLevelRecord | None = None

    @property
    def dirt_wall_h(self) -> Decimal:
        """Derived dirt-wall height: cap top up to the approach-slab soffit."""
        return self.app_bot - self.cap_top


def resolve_abutment_stack(project: Any, support_id: str = "A1") -> AbutmentStack:
    """Resolve the abutment RL ladder from the road level down.

    Every downstream element takes its RL from the returned object; no element
    may be positioned off another element's top by raw arithmetic.
    """
    road_rl = _dec(project.project_master.road_level_rl_m, Decimal("0"))
    wc_t = _dec(project.superstructure.wearing_coat_thickness_mm, _DEFAULT_WC_MM) / _MM
    deck_t = _dec(project.superstructure.deck_thickness_mm, _DEFAULT_DECK_MM) / _MM
    # The deck underside is the GIRDER soffit where girders exist, so the
    # structural depth must include them or the abutment's deck lands a girder
    # depth above the long section's.
    girder_t = _dec(getattr(project.superstructure, "girder_depth_mm", None), Decimal("0")) / _MM
    app_t = _dec(project.substructure.approach_slab_thickness_mm, _DEFAULT_APP_MM) / _MM
    cap_d = _dec(project.substructure.abutment_cap_depth_mm, _DEFAULT_CAP_MM) / _MM
    ped_h = _dec(project.substructure.abutment_pedestal_height_m, _DEFAULT_PED_M)

    # The wearing coat and slab underside come from the canonical §3 record, so
    # the abutment view and the long section share one soffit definition rather
    # than each subtracting the same two thicknesses. An undeclared bearing
    # depth is an explicit assumed zero — the apron/skew convention here.
    bearing_mm = getattr(project.superstructure, "bearing_depth_mm", None)
    supplied_soffit = getattr(project.hydraulic_data, "actual_soffit_level_m", None)
    footing_bottom = getattr(project.foundation_details, "pile_cutoff_level_m", None)
    footing_mm = getattr(project.foundation_details, "pile_cap_thickness_mm", None)
    record = resolve_support_levels(
        SupportLevelInput(
            support_id=support_id,
            road_rl_m=road_rl,
            wearing_depth_m=wc_t,
            structural_depth_m=deck_t + girder_t,
            supplied_soffit_rl_m=(
                None if supplied_soffit is None else _dec(supplied_soffit, Decimal("0"))
            ),
            topology=BearingTopology.SEPARATE_BEARING_PEDESTAL,
            bearing_depth_m=(
                Decimal("0") if bearing_mm is None else Decimal(str(bearing_mm)) / _MM
            ),
            bearing_depth_assumed=bearing_mm is None,
            pedestal_height_m=ped_h,
            cap_depth_m=cap_d,
            footing_bottom_rl_m=(
                None if footing_bottom is None else _dec(footing_bottom, Decimal("0"))
            ),
            footing_depth_m=(
                None if footing_mm is None else Decimal(str(footing_mm)) / _MM
            ),
            authority=AuthorityMode.LEVEL_CONTROLLED,
        )
    )

    wc_bot = road_rl - wc_t
    slab_top = wc_bot
    deck_bot = (
        record.structural_soffit_rl_m
        if record.structural_soffit_rl_m is not None
        else slab_top - deck_t
    )
    app_bot = slab_top - app_t
    # §3: the cap top is the canonical record's — soffit − bearing − pedestal —
    # so the abutment and the piers share one seat datum. The earlier
    # ``app_bot − dirt_wall_height`` chain put the abutment cap a fabricated
    # bearing-plus-pedestal depth above the pier cap and above its own soffit.
    cap_top = (
        record.cap_top_rl_m if record.cap_top_rl_m is not None else deck_bot - ped_h
    )
    cap_bot = (
        record.cap_bottom_rl_m
        if record.cap_bottom_rl_m is not None
        else cap_top - cap_d
    )
    # Bearing seat = top of the pedestal = soffit minus the bearing unit once.
    bear_rl = deck_bot - ped_h
    return AbutmentStack(
        wc_bot, slab_top, deck_bot, app_bot, cap_top, cap_bot, bear_rl, record
    )
