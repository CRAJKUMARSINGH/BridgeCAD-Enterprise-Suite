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
    """

    wc_bot: Decimal
    slab_top: Decimal
    deck_bot: Decimal
    app_bot: Decimal
    cap_top: Decimal
    cap_bot: Decimal
    bear_rl: Decimal


def resolve_abutment_stack(project: Any) -> AbutmentStack:
    """Resolve the abutment RL ladder from the road level down.

    Every downstream element takes its RL from the returned object; no element
    may be positioned off another element's top by raw arithmetic.
    """
    road_rl = _dec(project.project_master.road_level_rl_m, Decimal("0"))
    wc_t = _dec(project.superstructure.wearing_coat_thickness_mm, _DEFAULT_WC_MM) / _MM
    deck_t = _dec(project.superstructure.deck_thickness_mm, _DEFAULT_DECK_MM) / _MM
    app_t = _dec(project.substructure.approach_slab_thickness_mm, _DEFAULT_APP_MM) / _MM
    # An unset dirt wall defaults to the approach-slab thickness — the thinnest
    # wall the ABT-005 rule allows, so the default can never fail its own gate.
    dw_h = _dec(project.substructure.dirt_wall_height_m, app_t)
    cap_d = _dec(project.substructure.abutment_cap_depth_mm, _DEFAULT_CAP_MM) / _MM
    ped_h = _dec(project.substructure.abutment_pedestal_height_m, _DEFAULT_PED_M)

    wc_bot = road_rl - wc_t
    slab_top = wc_bot
    deck_bot = slab_top - deck_t
    app_bot = slab_top - app_t
    cap_top = app_bot - dw_h
    cap_bot = cap_top - cap_d
    bear_rl = deck_bot - ped_h
    return AbutmentStack(wc_bot, slab_top, deck_bot, app_bot, cap_top, cap_bot, bear_rl)
