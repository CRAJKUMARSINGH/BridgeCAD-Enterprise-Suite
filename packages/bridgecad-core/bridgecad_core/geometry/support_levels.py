"""
bridgecad_core.geometry.support_levels — the ONE canonical vertical contract.

WHY THIS EXISTS
    Every renderer used to position a pier or abutment off another element's top
    by raw arithmetic (``cap_top = soffit - pedestal`` in the long section,
    ``bear_rl = deck_bot - ped`` in the abutment stack, ``HFL - pier_height`` for
    a shaft base somewhere else). One missed edit and the views disagree.

    ``resolve_support_levels`` collapses the whole vertical stack at one support
    into one ordered, named record. Every consumer — long section, abutment
    stack, production sheets — takes its RL from that record and from nowhere
    else. Nothing here draws; nothing here is float; nothing here guesses.

EXPLICIT TOPOLOGY AND EQUATIONS (separate bearing + pedestal)
    structural_soffit_RL = road_RL - wearing_depth - structural_depth
    cap_top_RL           = structural_soffit_RL - bearing_depth - pedestal_height
    cap_bottom_RL        = cap_top_RL - cap_depth
    shaft_top_RL         = cap_bottom_RL
    footing_top_RL       = footing_bottom_RL + footing_depth
    shaft_base_RL        = footing_top_RL
    shaft_height         = shaft_top_RL - shaft_base_RL

    A slab and a slab-plus-girder are different depths: the caller passes the
    total structural depth and must not add a girder depth on top. A monolithic
    (integral) joint is a zero-bearing topology, not a fake bearing pad.

AUTHORITY POLICY
    1. LEVEL_CONTROLLED — footing bottom/top RL and thickness supplied; the
       shaft height is derived. A supplied incompatible shaft height is a
       CONFLICT, not a second view.
    2. HEIGHT_CONTROLLED — shaft height supplied; the shaft base and a
       *proposed* founding RL are derived and marked assumed/proposed.
    3. Missing foundation thickness or topology is UNRESOLVED. Never draw an
       apparently complete footing or silently choose its depth.

    HFL is a hydraulic datum, not a pier's height origin. Founding bottom, shaft
    base and the ground/scour surface are different surfaces and stay distinct.

``Decimal`` metres throughout; convert to drawing coordinates only at the
render boundary (:meth:`SupportLevelRecord.to_drawing_floats`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

__all__ = [
    "AuthorityMode",
    "ResolutionStatus",
    "FieldSource",
    "BearingTopology",
    "SupportLevelIssue",
    "SupportLevelInput",
    "SupportLevelRecord",
    "resolve_support_levels",
    "LEVEL_TOLERANCE_M",
]

#: Computational tolerance for pure-resolver equality (metres). NOT a
#: construction tolerance — see the specification's note on tolerances.
LEVEL_TOLERANCE_M = Decimal("0.000001")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class AuthorityMode(str, Enum):
    """Which supplied group governs the vertical geometry."""

    LEVEL_CONTROLLED = "LEVEL_CONTROLLED"
    HEIGHT_CONTROLLED = "HEIGHT_CONTROLLED"


class ResolutionStatus(str, Enum):
    """Outcome of one support-level resolution."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICT = "CONFLICT"


class FieldSource(str, Enum):
    """Provenance of one resolved level."""

    SUPPLIED = "SUPPLIED"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"
    PROPOSED = "PROPOSED"
    UNRESOLVED = "UNRESOLVED"


class BearingTopology(str, Enum):
    """How the seat between deck soffit and cap top is physically built."""

    #: Separate elastomeric/pot bearing pad AND a pedestal block.
    SEPARATE_BEARING_PEDESTAL = "SEPARATE_BEARING_PEDESTAL"
    #: One combined seat height; never also subtract bearing + pedestal.
    COMBINED_SEAT = "COMBINED_SEAT"
    #: Monolithic/integral joint — no bearing pad, zero seat depth.
    MONOLITHIC = "MONOLITHIC"


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SupportLevelInput:
    """Everything the resolver needs, and nothing it must guess.

    ``*_assumed`` flags mark a value the caller invented (a documented default
    rather than a designed or surveyed figure) so the record can carry the
    assumption into the title block instead of hiding it.
    """

    support_id: str
    road_rl_m: Decimal
    wearing_depth_m: Decimal
    structural_depth_m: Decimal
    #: An authoritative soffit RL supplied by the project (e.g. a surveyed or
    #: hydraulic actual-soffit level). When given it wins over the derived
    #: value; a disagreement beyond tolerance is a CONFLICT.
    supplied_soffit_rl_m: Decimal | None = None
    topology: BearingTopology = BearingTopology.SEPARATE_BEARING_PEDESTAL

    # --- seat (topology-dependent) ---
    bearing_depth_m: Decimal | None = None
    bearing_depth_assumed: bool = False
    pedestal_height_m: Decimal | None = None
    pedestal_height_assumed: bool = False
    combined_seat_height_m: Decimal | None = None

    # --- cap / shaft ---
    cap_depth_m: Decimal | None = None

    # --- foundation (one of the two authority groups) ---
    footing_bottom_rl_m: Decimal | None = None
    footing_depth_m: Decimal | None = None
    shaft_height_m: Decimal | None = None

    # --- carried-through reference surfaces (never conflated with shaft base) ---
    ground_level_rl_m: Decimal | None = None
    scour_level_rl_m: Decimal | None = None

    # --- optional pile / well references ---
    pile_cutoff_rl_m: Decimal | None = None
    pile_tip_rl_m: Decimal | None = None

    authority: AuthorityMode | None = None
    tolerance_m: Decimal = LEVEL_TOLERANCE_M


@dataclass(frozen=True)
class SupportLevelIssue:
    """One reason a support is not fully resolved."""

    code: str
    field_name: str
    message: str


@dataclass(frozen=True)
class SupportLevelRecord:
    """The canonical, named Reduced Levels for one support.

    Every level is ``Decimal`` metres on the project datum, or ``None`` when the
    inputs did not permit it. ``provenance`` says where each level came from;
    ``issues`` explains every ``None`` and every conflict.
    """

    support_id: str
    status: ResolutionStatus
    authority: AuthorityMode
    topology: BearingTopology

    structural_soffit_rl_m: Decimal | None
    derived_soffit_rl_m: Decimal | None
    cap_top_rl_m: Decimal | None
    cap_bottom_rl_m: Decimal | None
    shaft_top_rl_m: Decimal | None
    shaft_base_rl_m: Decimal | None
    shaft_height_m: Decimal | None
    footing_top_rl_m: Decimal | None
    footing_bottom_rl_m: Decimal | None
    footing_depth_m: Decimal | None

    ground_level_rl_m: Decimal | None
    scour_level_rl_m: Decimal | None
    pile_cutoff_rl_m: Decimal | None
    pile_tip_rl_m: Decimal | None

    provenance: dict[str, FieldSource] = field(default_factory=dict)
    issues: tuple[SupportLevelIssue, ...] = ()

    # -- convenience -------------------------------------------------------
    @property
    def is_resolved(self) -> bool:
        return self.status is ResolutionStatus.RESOLVED

    def levels(self) -> dict[str, Decimal | None]:
        """All named levels, in top-to-bottom order."""
        return {
            "structural_soffit_rl_m": self.structural_soffit_rl_m,
            "derived_soffit_rl_m": self.derived_soffit_rl_m,
            "cap_top_rl_m": self.cap_top_rl_m,
            "cap_bottom_rl_m": self.cap_bottom_rl_m,
            "shaft_top_rl_m": self.shaft_top_rl_m,
            "shaft_base_rl_m": self.shaft_base_rl_m,
            "footing_top_rl_m": self.footing_top_rl_m,
            "footing_bottom_rl_m": self.footing_bottom_rl_m,
            "ground_level_rl_m": self.ground_level_rl_m,
            "scour_level_rl_m": self.scour_level_rl_m,
            "pile_cutoff_rl_m": self.pile_cutoff_rl_m,
            "pile_tip_rl_m": self.pile_tip_rl_m,
        }

    def to_drawing_floats(self) -> dict[str, float | None]:
        """Render-boundary conversion: the only place these become floats."""
        return {
            key: (None if value is None else float(value))
            for key, value in self.levels().items()
        }

    def to_json(self) -> dict[str, Any]:
        """Serialisable form for ``artifacts/.../params.resolved.json``."""
        return {
            "support_id": self.support_id,
            "status": self.status.value,
            "authority": self.authority.value,
            "topology": self.topology.value,
            "levels_m": {
                key: (None if value is None else str(value))
                for key, value in self.levels().items()
            },
            "shaft_height_m": (
                None if self.shaft_height_m is None else str(self.shaft_height_m)
            ),
            "footing_depth_m": (
                None if self.footing_depth_m is None else str(self.footing_depth_m)
            ),
            "provenance": {k: v.value for k, v in self.provenance.items()},
            "issues": [
                {"code": i.code, "field": i.field_name, "message": i.message}
                for i in self.issues
            ],
        }


# ---------------------------------------------------------------------------
# Coercion
# ---------------------------------------------------------------------------
def _dec(value: Any) -> Decimal | None:
    """Coerce to a finite :class:`Decimal`, or ``None`` on anything unusable."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        out = value
    elif isinstance(value, bool):
        return None
    else:
        try:
            out = Decimal(str(value))
        except Exception:  # noqa: BLE001 - any uncoercible value is "absent"
            return None
    return out if out.is_finite() else None


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------
def resolve_support_levels(inp: SupportLevelInput) -> SupportLevelRecord:
    """Resolve one support's vertical stack, purely, from explicit inputs."""
    tol = _dec(inp.tolerance_m) or LEVEL_TOLERANCE_M
    prov: dict[str, FieldSource] = {}
    issues: list[SupportLevelIssue] = []

    def miss(code: str, name: str, message: str) -> None:
        prov[name] = FieldSource.UNRESOLVED
        issues.append(SupportLevelIssue(code=code, field_name=name, message=message))

    road = _dec(inp.road_rl_m)
    wearing = _dec(inp.wearing_depth_m)
    depth = _dec(inp.structural_depth_m)
    if road is None or wearing is None or depth is None:
        miss(
            "E-MISSING-DECK-INPUTS",
            "structural_soffit_rl_m",
            "road RL, wearing depth and structural depth are all required",
        )
        return SupportLevelRecord(
            support_id=inp.support_id,
            status=ResolutionStatus.UNRESOLVED,
            authority=inp.authority or AuthorityMode.LEVEL_CONTROLLED,
            topology=inp.topology,
            structural_soffit_rl_m=None,
            derived_soffit_rl_m=None,
            cap_top_rl_m=None,
            cap_bottom_rl_m=None,
            shaft_top_rl_m=None,
            shaft_base_rl_m=None,
            shaft_height_m=None,
            footing_top_rl_m=None,
            footing_bottom_rl_m=None,
            footing_depth_m=None,
            ground_level_rl_m=_dec(inp.ground_level_rl_m),
            scour_level_rl_m=_dec(inp.scour_level_rl_m),
            pile_cutoff_rl_m=_dec(inp.pile_cutoff_rl_m),
            pile_tip_rl_m=_dec(inp.pile_tip_rl_m),
            provenance=prov,
            issues=tuple(issues),
        )

    soffit = road - wearing - depth
    prov["structural_soffit_rl_m"] = FieldSource.DERIVED
    derived_soffit = soffit

    supplied_soffit = _dec(inp.supplied_soffit_rl_m)
    if supplied_soffit is not None:
        # An authoritative surveyed soffit wins. A difference from the derived
        # value is legitimate — a gradient or camber puts the minimum-span
        # soffit at a different chainage than the centreline road RL — so both
        # values are kept visible rather than declared a conflict.
        soffit = supplied_soffit
        prov["structural_soffit_rl_m"] = FieldSource.SUPPLIED

    # ---- seat depth (topology-dependent) ---------------------------------
    if inp.topology is BearingTopology.MONOLITHIC:
        seat = Decimal("0")
        prov["cap_top_rl_m"] = FieldSource.DERIVED
        if _dec(inp.combined_seat_height_m) not in (None, Decimal("0")):
            issues.append(
                SupportLevelIssue(
                    code="W-MONOLITHIC-IGNORES-SEAT",
                    field_name="combined_seat_height_m",
                    message="monolithic joint has no seat; combined-seat height ignored",
                )
            )
    elif inp.topology is BearingTopology.COMBINED_SEAT:
        combined = _dec(inp.combined_seat_height_m)
        if combined is None:
            miss(
                "E-MISSING-COMBINED-SEAT",
                "cap_top_rl_m",
                "combined-seat topology needs a combined seat height",
            )
            seat = None
        else:
            seat = combined
            prov["cap_top_rl_m"] = FieldSource.DERIVED
    else:  # SEPARATE_BEARING_PEDESTAL
        bearing = _dec(inp.bearing_depth_m)
        pedestal = _dec(inp.pedestal_height_m)
        if bearing is None or pedestal is None:
            miss(
                "E-MISSING-SEAT-PIECES",
                "cap_top_rl_m",
                "separate-bearing topology needs both bearing depth and pedestal height",
            )
            seat = None
        else:
            seat = bearing + pedestal
            prov["bearing_depth_m"] = (
                FieldSource.ASSUMED if inp.bearing_depth_assumed else FieldSource.SUPPLIED
            )
            prov["pedestal_height_m"] = (
                FieldSource.ASSUMED
                if inp.pedestal_height_assumed
                else FieldSource.SUPPLIED
            )
            prov["cap_top_rl_m"] = FieldSource.DERIVED

    cap_top = None if seat is None else soffit - seat

    # ---- cap --------------------------------------------------------------
    cap_depth = _dec(inp.cap_depth_m)
    if cap_top is None:
        cap_bottom = None
    elif cap_depth is None:
        cap_bottom = None
        miss("E-MISSING-CAP-DEPTH", "cap_bottom_rl_m", "cap depth is required")
    else:
        cap_bottom = cap_top - cap_depth
        prov["cap_bottom_rl_m"] = FieldSource.DERIVED
        prov["cap_depth_m"] = FieldSource.SUPPLIED

    shaft_top = cap_bottom

    # ---- foundation: authority policy ------------------------------------
    footing_bottom = _dec(inp.footing_bottom_rl_m)
    footing_depth = _dec(inp.footing_depth_m)
    given_height = _dec(inp.shaft_height_m)

    if inp.authority is not None:
        authority = inp.authority
    elif footing_bottom is not None and footing_depth is not None:
        authority = AuthorityMode.LEVEL_CONTROLLED
    elif given_height is not None:
        authority = AuthorityMode.HEIGHT_CONTROLLED
    else:
        authority = AuthorityMode.LEVEL_CONTROLLED

    footing_top: Decimal | None = None
    shaft_base: Decimal | None = None
    shaft_height: Decimal | None = None

    if authority is AuthorityMode.LEVEL_CONTROLLED:
        if footing_bottom is None or footing_depth is None:
            miss(
                "E-MISSING-FOUNDATION",
                "shaft_base_rl_m",
                "level-controlled mode needs footing bottom RL and footing depth",
            )
            # Fail closed: do not hand a renderer half a footing to draw.
            footing_bottom = None
            footing_depth = None
            prov["footing_bottom_rl_m"] = FieldSource.UNRESOLVED
            prov["footing_depth_m"] = FieldSource.UNRESOLVED
        else:
            footing_top = footing_bottom + footing_depth
            shaft_base = footing_top
            prov["footing_bottom_rl_m"] = FieldSource.SUPPLIED
            prov["footing_depth_m"] = FieldSource.SUPPLIED
            prov["footing_top_rl_m"] = FieldSource.DERIVED
            prov["shaft_base_rl_m"] = FieldSource.DERIVED
            if shaft_top is None:
                miss(
                    "E-MISSING-SHAFT-TOP",
                    "shaft_height_m",
                    "shaft height needs a resolved shaft top",
                )
            else:
                shaft_height = shaft_top - shaft_base
                prov["shaft_height_m"] = FieldSource.DERIVED

        # A supplied height that disagrees with the derived height is a
        # CONFLICT, not a second view.
        if (
            given_height is not None
            and shaft_height is not None
            and abs(given_height - shaft_height) > tol
        ):
            issues.append(
                SupportLevelIssue(
                    code="E-CONFLICT-SHAFT-HEIGHT",
                    field_name="shaft_height_m",
                    message=(
                        "supplied shaft height "
                        f"{given_height} m conflicts with the derived "
                        f"{shaft_height} m (tolerance {tol} m)"
                    ),
                )
            )
    else:  # HEIGHT_CONTROLLED
        if given_height is None:
            miss(
                "E-MISSING-HEIGHT",
                "shaft_base_rl_m",
                "height-controlled mode needs a shaft height",
            )
        elif shaft_top is None:
            miss(
                "E-MISSING-SHAFT-TOP",
                "shaft_base_rl_m",
                "shaft base needs a resolved shaft top",
            )
        else:
            shaft_height = given_height
            shaft_base = shaft_top - given_height
            footing_top = shaft_base
            prov["shaft_height_m"] = FieldSource.SUPPLIED
            prov["shaft_base_rl_m"] = FieldSource.DERIVED
            prov["footing_top_rl_m"] = FieldSource.DERIVED
            if footing_depth is None:
                miss(
                    "E-MISSING-FOOTING-DEPTH",
                    "footing_bottom_rl_m",
                    "cannot propose a founding RL without a footing depth",
                )
            else:
                footing_bottom = footing_top - footing_depth
                prov["footing_bottom_rl_m"] = FieldSource.PROPOSED
                prov["footing_depth_m"] = FieldSource.SUPPLIED
                issues.append(
                    SupportLevelIssue(
                        code="W-PROPOSED-FOUNDING",
                        field_name="footing_bottom_rl_m",
                        message=(
                            "founding RL derived from the supplied shaft height; "
                            "proposed, not an approved founding level"
                        ),
                    )
                )

    # ---- status ----------------------------------------------------------
    if any(i.code.startswith("E-CONFLICT") for i in issues):
        status = ResolutionStatus.CONFLICT
    elif issues:
        status = ResolutionStatus.UNRESOLVED
    else:
        status = ResolutionStatus.RESOLVED

    return SupportLevelRecord(
        support_id=inp.support_id,
        status=status,
        authority=authority,
        topology=inp.topology,
        structural_soffit_rl_m=soffit,
        derived_soffit_rl_m=derived_soffit,
        cap_top_rl_m=cap_top,
        cap_bottom_rl_m=cap_bottom,
        shaft_top_rl_m=shaft_top,
        shaft_base_rl_m=shaft_base,
        shaft_height_m=shaft_height,
        footing_top_rl_m=footing_top,
        footing_bottom_rl_m=footing_bottom,
        footing_depth_m=footing_depth,
        ground_level_rl_m=_dec(inp.ground_level_rl_m),
        scour_level_rl_m=_dec(inp.scour_level_rl_m),
        pile_cutoff_rl_m=_dec(inp.pile_cutoff_rl_m),
        pile_tip_rl_m=_dec(inp.pile_tip_rl_m),
        provenance=prov,
        issues=tuple(issues),
    )
