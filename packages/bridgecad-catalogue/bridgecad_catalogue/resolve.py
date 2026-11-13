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
#: The value model floors ``carriageway_width_m`` at 3.5 m (the IRC vehicular
#: minimum).  A pedestrian F.O.B. (type 014) is 2.0 m in the booklet.
MIN_CARRIAGEWAY_M = Decimal("3.5")
#: Superstructures that carry discrete longitudinal girders, and so must have a
#: girder count the value model will accept (``girders_per_deck_count >= 1``).
GIRDER_SST = frozenset({"RCC_T_BEAM", "PSC_I_GIRDER", "PSC_BOX", "PSC_BOX_GIRDER"})
#: Superstructures whose span is carried in thrust or in a deep cell rather than
#: by the bending depth of the deck slab, so the span/depth governor — a girder
#: / slab rule — does not apply to them.
NON_BENDING_SS = frozenset({"RCC_ARCH", "RCC_BOX_CELL"})


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


def _derive(p: ResolvedParams, *, cw_overridden: bool = False) -> None:
    """Derived fields, in dependency order.  Order matters — do not shuffle."""
    lens = cast("list[Decimal]", p["span_lengths"])
    span_count = cast("int", p["span_count"])
    if len(lens) != span_count:
        raise Violation(f"span_count={span_count} but {len(lens)} span lengths supplied")
    p.note("total_length_m", p.get("total_length_m"), sum(lens), "Σ span_lengths")
    p["total_length_m"] = sum(lens)

    # The value model floors the carriageway at 3.5 m.  Type 014 is a 2.0 m
    # pedestrian F.O.B. in the booklet, which is below that floor: the card
    # keeps the booklet value and the engine geometry is clamped, with the
    # deviation stated rather than hidden.
    cw = Decimal(str(p["carriageway_width"]))
    if cw < MIN_CARRIAGEWAY_M:
        p.note("carriageway_width", cw, MIN_CARRIAGEWAY_M,
               "below the 3.5 m model carriageway floor — clamped")
        p.warnings.append(
            f"carriageway {cw} m is below the 3.5 m model floor — clamped to "
            "3.5 m (deviation stated, not hidden)"
        )
        p["carriageway_width"] = MIN_CARRIAGEWAY_M

    ss = cast("str", p["superstructure_type"])
    fnd = cast("str", p["foundation_type"])
    # A box cell IS its own substructure — there are no piers to count.
    p["pier_count"] = 0 if ss == "RCC_BOX_CELL" else span_count - 1

    # GAP 04 — pier batter default: IRC practice is 1:10 batter for open/pile piers.
    # The pier_batter_1n field was added in the Venice-patch; fixtures leave it None
    # so the tapered-trapezoid branch in sheet5 never fires. Derive a default here.
    if p.get("pier_batter_1n") is None and fnd in ("OPEN", "PILE"):
        p.note("pier_batter_1n", None, Decimal("10"), "IRC practice default 1:10 batter")
        p["pier_batter_1n"] = Decimal("10")

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

    # Girders must carry the carriageway.  A card that states its girder count
    # is stating a booklet identity — 007/008 are "THREE GIRDER" decks (3 @
    # 2.0 m per their booklet fixtures), 009/010 are "4-GIRDER" decks (4 @
    # 2.5 m) — and no (carriageway, spacing) formula reproduces both, so the
    # card value wins at the baseline.  A *carriageway override* re-checks
    # capacity (a wider deck must gain girders), and a card that is silent
    # still gets a buildable minimum.
    if ss in GIRDER_SST:
        spacing = Decimal(str(p.get("girder_spacing_m") or "2.5"))
        stated = int(p.get("girders_per_deck") or 0)
        if cw_overridden or not stated:
            need = math.ceil(float(str(p["carriageway_width"])) / float(spacing)) + 1
            if stated < need:
                p.note("girders_per_deck", p.get("girders_per_deck"), need,
                       "spacing vs carriageway")
                p["girders_per_deck"] = need

    # GAP 09 — camber default: derive L/1000 (minimum 10 mm) so the dashed
    # camber parabola appears on cross-sections as the PDF shows.
    if not p.get("camber_mm"):
        cam = max(10, int(float(str(max(lens))) * 1000 / 1000))
        p.note("camber_mm", None, cam, "L/1000 default, min 10 mm")
        p["camber_mm"] = cam


def _check(p: ResolvedParams) -> None:
    ss = cast("str", p["superstructure_type"])
    span = max(cast("list[Decimal]", p["span_lengths"]))
    deck = Decimal(str(p["deck_thickness_mm"])) / 1000
    girder = Decimal(str(p.get("girder_depth_mm") or 0)) / 1000
    depth = deck + girder

    ratio = DECK_MIN_RATIO[ss]
    # The span/depth governor is a girder / slab rule: it asks whether the deck
    # is deep enough to bend across its own span.  Two families do not bend
    # that way and the rule does not reach them — an arch carries its span in
    # thrust (a legitimate F.O.B. rib is span/70, so testing the 350 mm deck
    # against span/18 would reject every arch in the booklet) and a multi-cell
    # box carries it in the height of the cell, not in the deck slab.  Their
    # structural depth is asserted by their own primitive and sheet instead.
    if ss not in NON_BENDING_SS and depth < span / ratio:
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

    _derive(p, cw_overridden="carriageway_width" in overrides)
    _check(p)
    return p
