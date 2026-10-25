"""
bridgecad_core.geometry.abutment — abutment total length and wing wall geometry.

Two facts live here, both with a single definition:

  1. ABTL (abutment total length) resolution ladder. The parameter is named
     differently in every source workbook, so the ladder tries each name in a
     fixed order and reports which rung fired. A silent default once produced
     abutments with no dimensionable length; the source label is the audit trail.

         ABTL -> FUTL -> FOOTL -> FUTRL -> ALCL -> ALCW -> 13.0 (default)

  2. Wing wall geometry, measured FROM THE ABUTMENT FACE:

         face_run_m = (abtl_m - carriageway_width_m) / 2
         length_m   = face_run_m / cos(radians(splay_deg))
         return_m   = length_m * sin(radians(splay_deg))

All arithmetic is Decimal so the drawing, the hand-check and the reference
corpus agree to the millimetre instead of to a float's last bit.
"""

from __future__ import annotations

import contextlib
import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

# Ladder order is fixed. Each rung is a parameter name in the source data.
LADDER: tuple[str, ...] = ("ABTL", "FUTL", "FOOTL", "FUTRL", "ALCL", "ALCW")
TERMINAL_DEFAULT_M = Decimal("13.0")
DEFAULT_SPLAY_DEG = Decimal("45")

#: Wing wall top is dropped this far below the deck level (kerb + slab).
TOP_DROP_M = Decimal("1.2")
#: Wing wall base is carried this far below the governing scour level.
BASE_BELOW_SCOUR_M = Decimal("0.5")


@dataclass(frozen=True)
class WingWall:
    """One wing wall. side is "left" or "right" looking along increasing chainage."""

    side: str
    length_m: Decimal
    face_run_m: Decimal
    return_m: Decimal
    splay_deg: Decimal
    top_level_m: Decimal
    base_level_m: Decimal
    toe_offset_m: Decimal


# ---------------------------------------------------------------------------
# Small helpers — the model may be a validated BridgeProject or a drafting view
# ---------------------------------------------------------------------------
def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    try:
        return getattr(obj, name)
    except AttributeError:
        return default


def _set_attr(obj: Any, name: str, value: Any) -> None:
    """Write back a resolved value. A validated model may refuse; that is fine."""
    with contextlib.suppress(Exception):  # a read-only model is not an error here
        setattr(obj, name, value)


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        d = value
    else:
        try:
            d = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    if not d.is_finite():
        return None
    return d


# ---------------------------------------------------------------------------
# ABTL ladder
# ---------------------------------------------------------------------------
def _resolve_abtl_decimal(project: Any) -> tuple[Decimal, str]:
    """Decimal-precision resolver: the form ``wing_wall_geometry`` needs.

    Tries each ladder rung in order, skipping absent, zero and negative values.
    The winning value is written back to the ``ABTL`` slot so a second call
    cannot disagree with the first, and so downstream drawers re-read a fact
    rather than re-derive one.
    """
    fd = _attr(project, "foundation_details")
    for rung in LADDER:
        value = _dec(_attr(fd, rung.lower()))
        if value is not None and value > 0:
            _set_attr(fd, rung.lower(), value)
            if rung != "ABTL":
                _set_attr(fd, "abtl", value)
            return value, rung

    _set_attr(fd, "abtl", TERMINAL_DEFAULT_M)
    return TERMINAL_DEFAULT_M, "default"


def resolve_abtl(project: Any) -> tuple[float, str]:
    """Resolve the abutment total length.

    Returns ``(value_m, source)`` where ``source`` is the upper-case parameter
    name that fired, or ``"default"`` for the terminal fallback. The value is a
    float because callers add metre-scale tolerances (``abtl + 1e-9``) and a
    Decimal cannot be added to a float; the Decimal form stays internal so the
    wing geometry keeps its precision.
    """
    value, source = _resolve_abtl_decimal(project)
    return float(value), source


# ---------------------------------------------------------------------------
# Wing wall geometry
# ---------------------------------------------------------------------------
def _carriageway_m(project: Any) -> Decimal:
    direct = _dec(_attr(project, "carriageway_m"))
    if direct is not None:
        return direct
    gi = _attr(project, "geometry_input")
    width = _dec(_attr(gi, "carriageway_width_m"))
    return width if width is not None else Decimal("7.5")


def _splay_deg(project: Any) -> Decimal:
    """Splay is measured from the abutment face.

    A drafting override on the drawing control wins; otherwise the project's
    direct value; otherwise the substructure's declared wing wall angle.
    """
    for holder, name in ((_attr(project, "drawing_control"), "splay_deg"),
                         (project, "splay_deg"),
                         (_attr(project, "substructure"), "wing_wall_angle_deg")):
        value = _dec(_attr(holder, name))
        if value is not None:
            return value
    return DEFAULT_SPLAY_DEG


def _levels(project: Any) -> tuple[Decimal, Decimal]:
    gi = _attr(project, "geometry_input")
    hd = _attr(project, "hydraulic_data")
    deck = _dec(_attr(gi, "deck_level_m"))
    if deck is None:
        deck = _dec(_attr(_attr(project, "project_master"), "road_level_rl_m"))
    if deck is None:
        levels = _attr(project, "levels")
        deck = _dec(_attr(levels, "deck_level_m"))
    scour = _dec(_attr(hd, "scour_level_m"))
    if scour is None:
        levels = _attr(project, "levels")
        scour = _dec(_attr(levels, "founding_level_m"))
    return deck or Decimal("0"), scour or Decimal("0")


def wing_wall_geometry(project: Any) -> list[WingWall]:
    """Both wing walls, left and right, on the given project."""
    abtl, _source = _resolve_abtl_decimal(project)
    carriageway = _carriageway_m(project)
    splay = _splay_deg(project)
    # The formula is only defined on [0, 90); clamp rather than produce a wall
    # mirrored through infinity.
    splay = max(Decimal("0"), min(splay, Decimal("88.999999")))

    face_run = (abtl - carriageway) / 2
    if face_run < 0:
        face_run = Decimal("0")

    cos_s = Decimal(str(math.cos(math.radians(float(splay)))))
    sin_s = Decimal(str(math.sin(math.radians(float(splay)))))
    length = face_run / cos_s if cos_s else Decimal("0")
    ret = length * sin_s

    deck, scour = _levels(project)
    top = deck - TOP_DROP_M
    base = min(scour, top) - BASE_BELOW_SCOUR_M

    return [
        WingWall(
            side=side,
            length_m=length,
            face_run_m=face_run,
            return_m=ret,
            splay_deg=splay,
            top_level_m=top,
            base_level_m=base,
            toe_offset_m=Decimal("0"),
        )
        for side in ("left", "right")
    ]


__all__ = [
    "LADDER", "TERMINAL_DEFAULT_M", "WingWall",
    "resolve_abtl", "wing_wall_geometry",
]
