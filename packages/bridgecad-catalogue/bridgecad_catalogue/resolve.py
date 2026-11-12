"""Compose a type card + engineer overrides into a buildable parameter set."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal
from typing import cast

from .schema import VARIABLES, Kind, Violation

WEARING_COAT_M = Decimal("0.075")
DECK_MIN_RATIO = {
    "RCC_SOLID_SLAB": 20,
    "RCC_T_BEAM": 16,
    "PSC_I_GIRDER": 15,
    "PSC_BOX": 18,
    "RCC_BOX_CELL": 22,
    "RCC_PORTAL": 22,
    "RCC_ARCH": 18,
}
EMBEDMENT_ROCK_M = Decimal("0.60")
EMBEDMENT_SOIL_M = Decimal("2.00")


class ResolvedParams(dict):  # type: ignore[type-arg]
    """A buildable parameter set, with the audit trail that produced it."""

    trace: list[dict]
    warnings: list[str]

    def __init__(self, mapping: Mapping[str, object] | None = None) -> None:
        super().__init__(mapping or {})
        self.trace = []
        self.warnings = []

    def note(self, key: str, old: object, new: object, why: str) -> None:
        self.trace.append({"field": key, "from": str(old), "to": str(new), "why": why})


def _derive(p: ResolvedParams) -> None:
    """Derived fields, in dependency order.  Order matters — do not shuffle."""
    lens = cast("list[Decimal]", p["span_lengths"])
    span_count = cast("int", p["span_count"])
    if len(lens) != span_count:
        raise Violation(f"span_count={span_count} but {len(lens)} span lengths supplied")
    p.note("total_length_m", p.get("total_length_m"), sum(lens), "Σ span_lengths")
    p["total_length_m"] = sum(lens)

    ss = cast("str", p["superstructure_type"])
    # A box cell IS its own substructure — there are no piers to count.
    p["pier_count"] = 0 if ss == "RCC_BOX_CELL" else span_count - 1

    deck = Decimal(str(p["deck_thickness_mm"])) / 1000
    gird = Decimal(str(p.get("girder_depth_mm") or 0)) / 1000
    wc = WEARING_COAT_M if ss != "RCC_BOX_CELL" else Decimal("0")

    # A box cell has no wearing course and no girder: its soffit is the box
    # slab underside, so it is RTL − deck and nothing else.
    if ss == "RCC_BOX_CELL":
        soffit = Decimal(str(p["road_level"])) - deck
    else:
        soffit = Decimal(str(p["road_level"])) - deck - wc - gird
    p.note("soffit_level", p.get("soffit_level"), soffit, "RTL − deck − WC − girder")
    p["soffit_level"] = soffit

    hfl = Decimal(str(p["hfl_m"]))
    scour = Decimal(str(p["scour_depth_m"]))
    fnd = cast("str", p["foundation_type"])
    if fnd == "OPEN":
        fl = hfl - scour - EMBEDMENT_ROCK_M
    elif fnd == "PILE":
        fl = hfl - scour - EMBEDMENT_SOIL_M - Decimal(str(p["pile_length_m"]))
    elif fnd == "WELL":
        fl = hfl - scour - Decimal("1.5") - Decimal("6.0")
    else:  # RAFT
        fl = hfl - scour - Decimal("1.0")
    p.note("foundation_level", p.get("foundation_level"), fl, f"{fnd} embedment")
    p["foundation_level"] = fl

    # bearing follows superstructure + span, never the card
    if ss in ("RCC_ARCH", "RCC_BOX_CELL", "RCC_PORTAL"):
        p["bearing_type"] = "NONE"  # bearingless / monolithic
    elif ss in ("PSC_I_GIRDER", "PSC_BOX") or max(lens) > 25:
        p["bearing_type"] = "POT"
    else:
        p["bearing_type"] = "ELASTOMERIC"

    # girders must actually carry the carriageway
    if p.get("girders_per_deck"):
        need = math.ceil(
            float(str(p["carriageway_width"])) / float(str(p["girder_spacing_m"]))
        ) + 1
        if cast("int", p["girders_per_deck"]) < need:
            p.note("girders_per_deck", p["girders_per_deck"], need, "spacing vs carriageway")
            p["girders_per_deck"] = need


def _check(p: ResolvedParams) -> None:
    ss = cast("str", p["superstructure_type"])
    span = max(cast("list[Decimal]", p["span_lengths"]))
    deck = Decimal(str(p["deck_thickness_mm"])) / 1000
    girder = Decimal(str(p.get("girder_depth_mm") or 0)) / 1000
    depth = deck + girder

    ratio = DECK_MIN_RATIO[ss]
    if p.get("approximation"):
        # 004 / 014 / 015 have no engine primitive yet (a multi-unit box cell,
        # an arch coordinate schedule, a precast block arch).  Their span/depth
        # governor is not meaningful, so it is reported rather than faked.
        p.warnings.append(f"{ss}: approximation — span/depth governor not applied")
    elif depth < span / ratio:
        raise Violation(
            f"depth {depth:.3f} m < span/{ratio} = {span / ratio:.3f} m for {ss} "
            f"@ {span} m span"
        )
    soffit = Decimal(str(p["soffit_level"]))
    hfl = Decimal(str(p["hfl_m"]))
    freeboard = Decimal(str(p["freeboard_m"]))
    if p["submersible"]:
        if soffit > hfl + freeboard:
            p.warnings.append("submersible: soffit above HFL+freeboard — check afflux")
    elif soffit < hfl + freeboard:
        raise Violation(
            f"soffit {soffit:.3f} < HFL+freeboard "
            f"{hfl + freeboard:.3f} m — raise RTL or reduce deck"
        )
    if p["foundation_type"] == "OPEN" and cast("Decimal", p["sbc_t_per_m2"]) < 20:
        raise Violation("OPEN foundation needs SBC ≥ 20 t/m² — switch to PILE/WELL/RAFT")
    if p["foundation_type"] == "PILE" and not p.get("pile_diameter_mm"):
        raise Violation("PILE foundation needs pile_diameter_mm")
    if ss == "RCC_BOX_CELL" and cast("int", p["span_count"]) > 3:
        p.warnings.append("box-cell types are normally ≤ 3 units")


def resolve(card: Mapping[str, object], overrides: Mapping[str, object], *, force: bool = False) -> ResolvedParams:
    p = ResolvedParams({k: v for k, v in card.items() if k != "id"})
    p["span_lengths"] = [Decimal(str(s)) for s in cast("list[object]", card.get("span_lengths", []))]

    for key, raw in overrides.items():
        spec = VARIABLES.get(key)
        if spec is None:
            raise Violation(f"unknown variable {key!r}")
        if spec.kind is Kind.LOCKED and not force:
            raise Violation(f"{key} is booklet-locked — pass --force to override")
        if key == "span_length_m":
            p["span_lengths"] = [spec.coerce(raw)] * cast("int", p["span_count"])
            continue
        p[key] = spec.coerce(raw)

    _derive(p)
    _check(p)
    return p
