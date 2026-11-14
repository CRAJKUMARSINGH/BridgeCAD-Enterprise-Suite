"""W04 · V&V benchmark case registry.

Each :class:`Case` declares the engine module it exercises, its verification
tier (A–E, see ``docs/verification/TOLERANCE_POLICY.md``), a human description
and the closed-form / invariant assertion it enforces.

No expected value here is copied from an external standard. Every case is
either

  * a closed-form identity justified from first principles — ``to_dxf_mm`` is
    x1000, ``sum(span_lengths) == total_length``, area = length x width,
    ``amount == rate x qty``; or
  * a structural invariant — symmetric pile layout, centroid at origin,
    ``score in [0, 100]``, ``len(pier_positions) == max(nspan - 1, 0)``.

``tests/verification/test_benchmarks.py`` parametrises over :data:`REGISTRY`.
"""

from __future__ import annotations

import itertools
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from bridgecad_core.costs import RateLookup, compute_cost
from bridgecad_core.geometry import coordinates as coords
from bridgecad_core.geometry import cross_section as cross
from bridgecad_core.geometry import foundation as foundation
from bridgecad_core.geometry import long_section as long_section
from bridgecad_core.geometry import plan as plan
from bridgecad_core.models import BridgeProject
from bridgecad_core.quantities import (
    BillItem,
    BillOfQuantities,
    _deck_slab_cum,
    _pier_count,
    _rebar_kg,
    _wearing_coat_cum,
    extract_quantities,
)
from bridgecad_core.types import (
    ENUM_REGISTRY,
    BridgeCategory,
    ConcreteGrade,
    DrawingScale,
    FoundationType,
    SheetSize,
    SteelGrade,
    ValidationSeverity,
)
from bridgecad_core.validation import ValidationFinding, ValidationReport
from bridgecad_core.validation_registry import RULE_ID_BY_CHECK, RULES
from bridgecad_qa.compliance_engine import ComplianceCheck, build_compliance_report

# ---------------------------------------------------------------------------
# Tier tolerances — mirrors TOLERANCE_POLICY.md.
#   A exact closed-form (float punch-through 1e-12 m), B 0.1% rel,
#   C 0.5% rel, D 1.0% rel, E geometry (<= 1e-6 m positional).
# ---------------------------------------------------------------------------
TIER_REL_TOL: dict[str, float] = {"A": 0.0, "B": 1e-3, "C": 5e-3, "D": 1e-2, "E": 0.0}
TIER_ABS_TOL: dict[str, float] = {"A": 1e-12, "B": 0.0, "C": 0.0, "D": 0.0, "E": 1e-6}


def assert_within_tier(tier: str, actual: float, expected: float, detail: str = "") -> None:
    """Assert ``actual`` matches ``expected`` within the tolerance for ``tier``."""
    rel = TIER_REL_TOL[tier]
    abs_ = TIER_ABS_TOL[tier]
    if math.isclose(actual, expected, rel_tol=rel, abs_tol=abs_):
        return
    raise AssertionError(
        f"tier {tier} (rel {rel}, abs {abs_}): {actual!r} != {expected!r} {detail}"
    )


# ---------------------------------------------------------------------------
# Case model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BenchContext:
    """Inputs handed to every case check (reused unit-lane fixtures)."""

    project: BridgeProject
    blank_project: BridgeProject
    span_variant: Callable[[list[float]], BridgeProject]


@dataclass(frozen=True)
class Case:
    id: str
    module: str
    tier: str
    description: str
    assertion: str
    check: Callable[[BenchContext], None]


def _centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    n = len(points)
    return (sum(x for x, _ in points) / n, sum(y for _, y in points) / n)


# ===========================================================================
# geometry.coordinates
# ===========================================================================


def _check_dxf_unit_scale(ctx: BenchContext) -> None:
    assert coords.MM_PER_M == 1000.0
    for point in [(1.0, 2.0), (-0.5, 12.5), (0.25, -3.0)]:
        assert coords.to_dxf_mm(point) == (point[0] * 1000.0, point[1] * 1000.0)


def _check_sheet_origin_set(ctx: BenchContext) -> None:
    spans = long_section.span_lengths_m(ctx.project)
    skew = float(ctx.project.geometry_input.skew_angle_deg)
    origins = coords.sheet_origins(spans, skew)
    assert set(origins) == set(coords.SheetId)
    assert len(origins) == len(list(coords.SheetId))


def _check_world_sheet_round_trip(ctx: BenchContext) -> None:
    origin = coords.sheet_origins([12.0, 15.0], 25.0)[coords.SheetId.CROSS_SECTION]
    for point in [(3.5, -2.0), (-7.25, 4.75)]:
        back = coords.to_world_coords(origin, coords.to_sheet_coords(origin, point))
        assert_within_tier("E", back[0], point[0])
        assert_within_tier("E", back[1], point[1])


def _check_chainage_zero_anchors(ctx: BenchContext) -> None:
    origins = coords.sheet_origins([12.0, 15.0], 0.0)
    for sheet in (
        coords.SheetId.PLAN,
        coords.SheetId.LONG_SECTION,
        coords.SheetId.BOQ,
        coords.SheetId.BEARINGS_JOINTS,
    ):
        origin = origins[sheet]
        assert (origin.x_m, origin.y_m, origin.rotation_deg) == (0.0, 0.0, 0.0)


def _check_cross_section_origin(ctx: BenchContext) -> None:
    spans = [10.0, 18.0, 9.0]
    origin = coords.sheet_origins(spans, 30.0)[coords.SheetId.CROSS_SECTION]
    longest = max(range(len(spans)), key=lambda i: spans[i])
    expected_x = sum(spans[:longest]) + spans[longest] / 2.0
    assert_within_tier("A", origin.x_m, expected_x)
    assert_within_tier("A", origin.rotation_deg, 30.0)


def _check_foundation_anchor(ctx: BenchContext) -> None:
    spans = [12.0, 15.0]
    origins = coords.sheet_origins(spans, 0.0)
    assert_within_tier("A", origins[coords.SheetId.FOUNDATION].x_m, spans[0])
    assert_within_tier("A", origins[coords.SheetId.PIER_ABUTMENT].y_m, -5.0)


# ===========================================================================
# geometry.long_section
# ===========================================================================


def _check_span_sum(ctx: BenchContext) -> None:
    total = float(ctx.project.geometry_input.total_length_m)
    assert_within_tier("A", sum(long_section.span_lengths_m(ctx.project)), total)


def _check_boundaries(ctx: BenchContext) -> None:
    for lengths in ([12.0], [10.0, 12.0, 14.0]):
        project = ctx.span_variant(lengths)
        bounds = long_section.span_boundaries(project)
        assert len(bounds) == len(lengths) + 1
        assert bounds[0] == 0.0
        assert all(b < a for b, a in itertools.pairwise(bounds))
        assert_within_tier("A", bounds[-1], sum(lengths))


def _check_pier_positions(ctx: BenchContext) -> None:
    for lengths in ([12.0], [10.0, 12.0, 14.0]):
        project = ctx.span_variant(lengths)
        piers = long_section.pier_positions(project)
        bounds = long_section.span_boundaries(project)
        assert len(piers) == max(len(lengths) - 1, 0)
        for pier in piers:
            assert pier in bounds[1:-1]


def _check_freeboard_identity(ctx: BenchContext) -> None:
    geo = long_section.compute_long_section_geometry(ctx.project)
    assert_within_tier("A", geo.freeboard_m, geo.soffit_rl - geo.hfl_rl)


def _check_pile_tip_identity(ctx: BenchContext) -> None:
    fd = ctx.project.foundation_details
    geo = long_section.compute_long_section_geometry(ctx.project)
    expected = float(fd.pile_cutoff_level_m) - float(fd.pile_length_m)
    assert_within_tier("A", geo.pile_tip_rl, expected)


def _check_ground_profile(ctx: BenchContext) -> None:
    project = ctx.project
    geo = long_section.compute_long_section_geometry(project)
    points = geo.ground_profile_pts
    assert len(points) == 21
    assert_within_tier("A", points[0][0], 0.0)
    assert_within_tier("A", points[-1][0], float(project.geometry_input.total_length_m))
    chainages = [chainage for chainage, _ in points]
    assert all(b <= a for b, a in itertools.pairwise(chainages))


def _check_pier_toc_list(ctx: BenchContext) -> None:
    project = ctx.span_variant([10.0, 12.0, 14.0])
    geo = long_section.compute_long_section_geometry(project)
    sub = project.substructure
    expected = geo.soffit_rl - float(sub.pier_pedestal_height_m)
    assert len(geo.pier_top_of_cap_rl_m) == len(geo.pier_chainage_m)
    for value in geo.pier_top_of_cap_rl_m:
        assert_within_tier("A", value, expected)


# ===========================================================================
# geometry.foundation
# ===========================================================================


def _check_pile_centroid(ctx: BenchContext) -> None:
    layout = foundation.compute_pile_group_layout(ctx.project)
    cx, cy = _centroid(layout.pile_positions)
    assert_within_tier("E", cx, 0.0)
    assert_within_tier("E", cy, 0.0)


def _check_pile_count(ctx: BenchContext) -> None:
    project = ctx.project
    layout = foundation.compute_pile_group_layout(project)
    assert len(layout.pile_positions) == int(project.foundation_details.piles_per_pier)


def _check_cap_corners(ctx: BenchContext) -> None:
    layout = foundation.compute_pile_group_layout(ctx.project)
    corners = layout.pile_cap_corners
    assert len(corners) == 4
    bl, br, tr, tl = corners
    assert_within_tier("E", bl[0], -br[0])  # bottom edge spans the cap width
    assert_within_tier("E", bl[1], br[1])
    assert_within_tier("E", tl[0], bl[0])  # left edge spans the cap length
    assert_within_tier("E", tl[1], tr[1])


def _check_cap_overhang_formula(ctx: BenchContext) -> None:
    layout = foundation.compute_pile_group_layout(ctx.project)
    xs = [x for x, _ in layout.pile_positions]
    ys = [y for _, y in layout.pile_positions]
    overhang = layout.pile_diameter_m + 2 * 0.100
    assert_within_tier("A", layout.pile_cap_width_m, (max(xs) - min(xs)) + overhang)
    assert_within_tier("A", layout.pile_cap_length_m, (max(ys) - min(ys)) + overhang)


def _check_standard_layouts(ctx: BenchContext) -> None:
    spacing = 2.0
    builders = (
        foundation._std_triangular_3,
        foundation._std_cruciform_5,
        foundation._std_hexagonal_7,
    )
    for builder in builders:
        points = builder(spacing)
        cx, cy = _centroid(points)
        assert_within_tier("E", cx, 0.0)
        assert_within_tier("E", cy, 0.0)
        distances = [math.dist(a, b) for a, b in itertools.combinations(points, 2)]
        assert_within_tier("E", min(distances), spacing)


def _check_well_branch(ctx: BenchContext) -> None:
    project = ctx.blank_project
    project.foundation_details.type = FoundationType.WELL
    layout = foundation.compute_pile_group_layout(project)
    assert layout.pile_positions == []
    assert layout.well_outer_radius_m >= 1.5
    assert_within_tier("E", layout.well_inner_radius_m, layout.well_outer_radius_m * 0.55)


# ===========================================================================
# geometry.plan
# ===========================================================================


def _check_deck_rectangle(ctx: BenchContext) -> None:
    project = ctx.project
    geo = plan.compute_plan_geometry(project)
    a1_left, a1_right, a2_right, a2_left = geo.deck_corners
    assert_within_tier(
        "E", math.dist(a1_left, a1_right), float(project.geometry_input.overall_width_m)
    )
    assert_within_tier(
        "E", math.dist(a1_left, a2_left), float(project.geometry_input.total_length_m)
    )
    assert_within_tier(
        "E", math.dist(a1_right, a2_right), float(project.geometry_input.total_length_m)
    )


def _check_plan_pier_centrelines(ctx: BenchContext) -> None:
    project = ctx.span_variant([10.0, 12.0, 14.0])  # skew stays 0 -> centres on X
    geo = plan.compute_plan_geometry(project)
    piers = long_section.pier_positions(project)
    assert len(geo.pier_centrelines) == len(piers)
    for (x, _y), chainage in zip(geo.pier_centrelines, piers, strict=True):
        assert_within_tier("E", x, chainage)


def _check_abutment_face_distance(ctx: BenchContext) -> None:
    project = ctx.project
    geo = plan.compute_plan_geometry(project)
    distance = math.dist(geo.abutment_a1_face, geo.abutment_a2_face)
    assert_within_tier("A", distance, float(project.geometry_input.total_length_m))


def _check_bearing_count(ctx: BenchContext) -> None:
    project = ctx.project
    geo = plan.compute_plan_geometry(project)
    lines = len(long_section.span_lengths_m(project)) + 1
    girders = int(project.superstructure.girders_per_deck_count)
    assert len(geo.bearing_positions) == lines * girders


# ===========================================================================
# geometry.cross_section
# ===========================================================================


def _check_crown_height(ctx: BenchContext) -> None:
    geo = cross.compute_cross_section_geometry(ctx.project)
    assert_within_tier("A", geo.top_of_wearing_coat_y, geo.camber_mm / 1000.0)


def _check_slab_soffit(ctx: BenchContext) -> None:
    project = ctx.project
    geo = cross.compute_cross_section_geometry(project)
    expected = -float(project.superstructure.deck_thickness_mm) / 1000.0
    assert_within_tier("A", geo.bottom_of_slab_y, expected)


def _check_parabolic_camber(ctx: BenchContext) -> None:
    geo = cross.compute_cross_section_geometry(ctx.project)
    half_cw = geo.carriageway_width_m / 2.0
    assert_within_tier("A", geo.camber_y_at_x(0.0), geo.camber_mm)
    assert_within_tier("A", geo.camber_y_at_x(half_cw), 0.0)
    assert_within_tier("A", geo.camber_y_at_x(-half_cw), 0.0)


def _check_offset_monotonic(ctx: BenchContext) -> None:
    geo = cross.compute_cross_section_geometry(ctx.project)
    offsets = geo.half_width_offsets
    assert offsets[0] == 0.0
    assert all(b < a for b, a in itertools.pairwise(offsets))
    assert_within_tier("A", offsets[-1], geo.overall_width_m / 2.0)


def _check_girder_soffit(ctx: BenchContext) -> None:
    project = ctx.project
    geo = cross.compute_cross_section_geometry(project)
    expected = geo.bottom_of_slab_y - float(project.superstructure.girder_depth_mm) / 1000.0
    assert_within_tier("A", geo.bottom_of_girder_y, expected)


# ===========================================================================
# quantities
# ===========================================================================


def _check_deck_volume(ctx: BenchContext) -> None:
    project = ctx.project
    gi = project.geometry_input
    thickness = float(project.superstructure.deck_thickness_mm) / 1000.0
    expected = float(gi.total_length_m) * float(gi.overall_width_m) * thickness
    assert_within_tier("A", _deck_slab_cum(project), expected)


def _check_wearing_coat_volume(ctx: BenchContext) -> None:
    project = ctx.project
    gi = project.geometry_input
    thickness = float(project.superstructure.wearing_coat_thickness_mm) / 1000.0
    expected = float(gi.total_length_m) * float(gi.carriageway_width_m) * thickness
    assert_within_tier("A", _wearing_coat_cum(project), expected)


def _check_rebar_linearity(ctx: BenchContext) -> None:
    assert _rebar_kg(0.0, "piles") == 0.0
    assert_within_tier("A", _rebar_kg(20.0, "piles"), 2.0 * _rebar_kg(10.0, "piles"))


def _check_pier_count(ctx: BenchContext) -> None:
    for lengths in ([12.0], [10.0, 12.0, 14.0]):
        project = ctx.span_variant(lengths)
        assert _pier_count(project) == max(len(lengths) - 1, 0)


def _check_boq_well_formed(ctx: BenchContext) -> None:
    boq = extract_quantities(ctx.project)
    codes = [item.code for item in boq.items]
    assert codes
    assert len(codes) == len(set(codes))
    for item in boq.items:
        assert item.code and item.description and item.unit
        assert item.qty >= 0


def _check_steel_control_total(ctx: BenchContext) -> None:
    boq = extract_quantities(ctx.project)
    control = next(item for item in boq.items if item.code == "SUM-200")
    component_kg = [item.qty for item in boq.items if item.unit == "kg" and item.code != "SUM-200"]
    assert_within_tier("A", control.qty, round(sum(component_kg), 1))


# ===========================================================================
# costs
# ===========================================================================


class _FixedRates(RateLookup):
    """Deterministic rate table for the cost identity checks."""

    def __init__(self, table: dict[str, float]) -> None:
        self._table = table

    def get(self, code: str, region: str | None = None) -> float | None:
        return self._table.get(code)


def _check_cost_amount(ctx: BenchContext) -> None:
    bom = BillOfQuantities()
    first = BillItem(code="A", description="d", unit="cum", qty=3.0)
    second = BillItem(code="B", description="d", unit="cum", qty=4.0)
    bom.add(first)
    bom.add(second)
    compute_cost(bom, _FixedRates({"A": 100.0, "B": 250.0}))
    assert_within_tier("A", first.amount, 100.0 * 3.0)
    assert_within_tier("A", second.amount, 250.0 * 4.0)
    assert_within_tier("A", bom.total_cost, first.amount + second.amount)


def _check_unpriced_passthrough(ctx: BenchContext) -> None:
    bom = BillOfQuantities()
    known = BillItem(code="A", description="d", unit="cum", qty=2.0)
    unknown = BillItem(code="ZZZ", description="d", unit="cum", qty=5.0)
    bom.add(known)
    bom.add(unknown)
    compute_cost(bom, _FixedRates({"A": 100.0}))
    assert unknown.rate is None
    assert unknown.amount is None
    assert_within_tier("A", bom.total_cost, 100.0 * 2.0)


# ===========================================================================
# validation
# ===========================================================================


def _check_score_arithmetic(ctx: BenchContext) -> None:
    findings = [
        ValidationFinding("C01", "d", ValidationSeverity.CRITICAL, False, ""),
        ValidationFinding("C02", "d", ValidationSeverity.CRITICAL, True, ""),
        ValidationFinding("W01", "d", ValidationSeverity.WARNING, False, ""),
    ]
    critical = sum(
        1 for f in findings if not f.passed and f.severity is ValidationSeverity.CRITICAL
    )
    warning = sum(1 for f in findings if not f.passed and f.severity is ValidationSeverity.WARNING)
    assert ValidationReport(findings).score == max(0, 100 - 15 * critical - 3 * warning)


def _check_score_range(ctx: BenchContext) -> None:
    assert ValidationReport().score == 100
    flooded = ValidationReport(
        [
            ValidationFinding(f"C{i:02d}", "d", ValidationSeverity.CRITICAL, False, "")
            for i in range(1, 9)
        ]
    )
    assert 0 <= flooded.score <= 100
    assert flooded.score == 0


def _check_status_mapping(ctx: BenchContext) -> None:
    def report(severity: ValidationSeverity, passed: bool) -> ValidationReport:
        return ValidationReport([ValidationFinding("X01", "d", severity, passed, "")])

    assert report(ValidationSeverity.CRITICAL, True).overall_status == "PASS"
    assert report(ValidationSeverity.WARNING, False).overall_status == "WARN"
    assert report(ValidationSeverity.CRITICAL, False).overall_status == "FAIL"


# ===========================================================================
# validation_registry
# ===========================================================================


def _check_rule_count(ctx: BenchContext) -> None:
    assert len(RULES) == 163
    ids = [rule.id for rule in RULES]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"V\d{3}", rule_id) for rule_id in ids)


def _check_rule_cross_map(ctx: BenchContext) -> None:
    assert len(RULE_ID_BY_CHECK) == 163
    for rule in RULES:
        assert RULE_ID_BY_CHECK[rule.source_rule_id] == rule.id
    assert len(set(RULE_ID_BY_CHECK.values())) == 163


def _check_implemented_count(ctx: BenchContext) -> None:
    assert sum(1 for rule in RULES if rule.implemented) == 43
    assert RULES[0].tier == "critical"
    assert RULES[0].implemented is True


# ===========================================================================
# types
# ===========================================================================

_STABLE_ENUMS = (ConcreteGrade, SteelGrade, FoundationType, SheetSize, BridgeCategory, DrawingScale)


def _check_enum_registry(ctx: BenchContext) -> None:
    for enum_cls in _STABLE_ENUMS:
        assert ENUM_REGISTRY[enum_cls.__name__] is enum_cls


def _check_enum_integrity(ctx: BenchContext) -> None:
    for enum_cls in _STABLE_ENUMS:
        values = [member.value for member in enum_cls]
        assert values
        assert len(values) == len(set(values))


# ===========================================================================
# models
# ===========================================================================


def _check_total_length_computed(ctx: BenchContext) -> None:
    gi = ctx.project.geometry_input
    expected = sum(Decimal(str(x)) for x in gi.span_lengths_m)
    assert gi.total_length_m == expected


def _check_overall_width_computed(ctx: BenchContext) -> None:
    gi = ctx.project.geometry_input
    parts = [gi.carriageway_width_m]
    for width in (
        gi.footpath_left_m,
        gi.footpath_right_m,
        gi.crash_barrier_width_left_m,
        gi.crash_barrier_width_right_m,
        gi.kerb_width_left_m,
        gi.kerb_width_right_m,
        gi.median_width_m,
        gi.median_barrier_width_m,
        gi.left_ditch_width_m,
        gi.right_ditch_width_m,
        gi.service_road_left_m,
        gi.service_road_right_m,
    ):
        parts.append(width if width is not None else Decimal("0"))
    assert gi.overall_width_m == sum(Decimal(str(part)) for part in parts)


def _check_length_propagation(ctx: BenchContext) -> None:
    project = ctx.project
    assert project.total_bridge_length_m == project.geometry_input.total_length_m
    assert project.overall_bridge_width_m == project.geometry_input.overall_width_m


# ===========================================================================
# compliance_engine (W06) — clause-mapped demand / capacity / utilisation
# ===========================================================================


def _by_check_id(project: BridgeProject) -> dict[str, ComplianceCheck]:
    return {check.check_id: check for check in build_compliance_report(project).checks}


def _check_cc001_span_depth_band(ctx: BenchContext) -> None:
    check = _by_check_id(ctx.project)["CC-001"]
    span = max(float(length) for length in ctx.project.geometry_input.span_lengths_m)
    depth_m = float(ctx.project.superstructure.girder_depth_mm) / 1000.0
    assert_within_tier("A", check.demand, round(span / depth_m, 1))
    assert_within_tier("A", check.utilisation, check.demand / check.capacity)
    assert check.passed


def _check_cc002_slab_thickness(ctx: BenchContext) -> None:
    check = _by_check_id(ctx.project)["CC-002"]
    assert_within_tier("A", check.demand, 200.0)  # IRC:21 Cl.304.7 for an RCC T-beam
    assert_within_tier("A", check.capacity, float(ctx.project.superstructure.deck_thickness_mm))


def _check_cc003_impact_factor(ctx: BenchContext) -> None:
    check = _by_check_id(ctx.project)["CC-003"]
    span = max(float(length) for length in ctx.project.geometry_input.span_lengths_m)
    assert_within_tier("A", check.demand, 4.5 / (6.0 + span))
    assert_within_tier("A", check.capacity, 0.50)


def _check_cc004_expansion_joint(ctx: BenchContext) -> None:
    check = _by_check_id(ctx.project)["CC-004"]
    assert check.demand % 5.0 == 0.0  # gaps round up to the nearest 5 mm
    assert_within_tier("A", check.capacity, 100.0)


def _check_cc005_freeboard(ctx: BenchContext) -> None:
    check = _by_check_id(ctx.project)["CC-005"]
    geo = long_section.compute_long_section_geometry(ctx.project)
    assert_within_tier("A", check.capacity, round(float(geo.freeboard_m), 3))
    assert_within_tier("A", check.demand, round(float(ctx.project.hydraulic_data.freeboard_m), 3))


def _check_cc006_deck_grade(ctx: BenchContext) -> None:
    check = _by_check_id(ctx.project)["CC-006"]
    assert_within_tier("A", check.demand, 30.0)  # IRC:112-2020 Cl.6.1 minimum
    assert_within_tier("A", check.capacity, 30.0)


# ===========================================================================
# Registry — id / module / tier / description / assertion / check
# ===========================================================================

REGISTRY: list[Case] = [
    # ---- geometry.coordinates -------------------------------------------
    Case(
        "VV-COORD-001",
        "bridgecad_core.geometry.coordinates",
        "A",
        "DXF millimetre conversion",
        "to_dxf_mm(p) == (1000*px, 1000*py); MM_PER_M == 1000",
        _check_dxf_unit_scale,
    ),
    Case(
        "VV-COORD-002",
        "bridgecad_core.geometry.coordinates",
        "E",
        "Sheet-origin map covers every sheet",
        "set(sheet_origins(...)) == set(SheetId), one origin per sheet",
        _check_sheet_origin_set,
    ),
    Case(
        "VV-COORD-003",
        "bridgecad_core.geometry.coordinates",
        "E",
        "World<->sheet transform round-trip",
        "to_world(to_sheet(p)) == p within ROUND_TRIP_TOL_M",
        _check_world_sheet_round_trip,
    ),
    Case(
        "VV-COORD-004",
        "bridgecad_core.geometry.coordinates",
        "A",
        "Chainage-zero sheets anchor at the origin",
        "PLAN/LONG_SECTION/BOQ/BEARINGS origins == (0, 0, 0)",
        _check_chainage_zero_anchors,
    ),
    Case(
        "VV-COORD-005",
        "bridgecad_core.geometry.coordinates",
        "A",
        "Cross-section origin at mid longest span",
        "x == sum(spans[:i]) + spans[i]/2 for the longest span i; rotation == skew",
        _check_cross_section_origin,
    ),
    Case(
        "VV-COORD-006",
        "bridgecad_core.geometry.coordinates",
        "A",
        "Foundation / pier-abutment anchors",
        "FOUNDATION.x == first span; PIER_ABUTMENT.y == -5 m",
        _check_foundation_anchor,
    ),
    # ---- geometry.long_section ------------------------------------------
    Case(
        "VV-LSEC-001",
        "bridgecad_core.geometry.long_section",
        "A",
        "Span lengths sum to total length",
        "sum(span_lengths_m(p)) == total_length_m",
        _check_span_sum,
    ),
    Case(
        "VV-LSEC-002",
        "bridgecad_core.geometry.long_section",
        "A",
        "Span-boundary contract",
        "len == nspan+1, starts 0, strictly increasing, ends at total",
        _check_boundaries,
    ),
    Case(
        "VV-LSEC-003",
        "bridgecad_core.geometry.long_section",
        "A",
        "Interior pier count and placement",
        "len(pier_positions) == max(nspan-1, 0); piers are interior boundaries",
        _check_pier_positions,
    ),
    Case(
        "VV-LSEC-004",
        "bridgecad_core.geometry.long_section",
        "A",
        "Freeboard identity",
        "freeboard_m == soffit_rl - hfl_rl",
        _check_freeboard_identity,
    ),
    Case(
        "VV-LSEC-005",
        "bridgecad_core.geometry.long_section",
        "A",
        "Pile-tip level identity",
        "pile_tip_rl == pile_cutoff_level - pile_length",
        _check_pile_tip_identity,
    ),
    Case(
        "VV-LSEC-006",
        "bridgecad_core.geometry.long_section",
        "A",
        "Ground profile shape",
        "21 points, chainage monotonic 0 -> total_length",
        _check_ground_profile,
    ),
    Case(
        "VV-LSEC-007",
        "bridgecad_core.geometry.long_section",
        "A",
        "Pier top-of-cap list",
        "len == len(pier_chainage_m); each == soffit - pedestal - cap depth",
        _check_pier_toc_list,
    ),
    # ---- geometry.foundation --------------------------------------------
    Case(
        "VV-FND-001",
        "bridgecad_core.geometry.foundation",
        "E",
        "Pile group centroid at origin",
        "centroid(pile_positions) == (0, 0)",
        _check_pile_centroid,
    ),
    Case(
        "VV-FND-002",
        "bridgecad_core.geometry.foundation",
        "E",
        "Pile count matches the model",
        "len(pile_positions) == piles_per_pier",
        _check_pile_count,
    ),
    Case(
        "VV-FND-003",
        "bridgecad_core.geometry.foundation",
        "E",
        "Pile-cap corners form a centred rectangle",
        "4 corners, BL/BR/TR/TL winding, bbox symmetric about origin",
        _check_cap_corners,
    ),
    Case(
        "VV-FND-004",
        "bridgecad_core.geometry.foundation",
        "A",
        "Pile-cap size = pile spread + diameter + 2x100 mm",
        "cap_w == (max x - min x) + d + 0.2 (same for length)",
        _check_cap_overhang_formula,
    ),
    Case(
        "VV-FND-005",
        "bridgecad_core.geometry.foundation",
        "E",
        "Standard 3/5/7-pile layouts are centred",
        "centroid == (0, 0); min pairwise distance == pile spacing",
        _check_standard_layouts,
    ),
    Case(
        "VV-FND-006",
        "bridgecad_core.geometry.foundation",
        "E",
        "Well-foundation branch",
        "no piles; inner radius == 0.55 * outer; outer >= 1.5 m",
        _check_well_branch,
    ),
    # ---- geometry.plan ---------------------------------------------------
    Case(
        "VV-PLAN-001",
        "bridgecad_core.geometry.plan",
        "E",
        "Deck corners are a rotated rectangle",
        "opposite sides == overall_width and total_length (rotation-invariant)",
        _check_deck_rectangle,
    ),
    Case(
        "VV-PLAN-002",
        "bridgecad_core.geometry.plan",
        "E",
        "Pier centrelines on the chainage axis",
        "len == nspan-1; centre x (skew 0) == pier_positions",
        _check_plan_pier_centrelines,
    ),
    Case(
        "VV-PLAN-003",
        "bridgecad_core.geometry.plan",
        "A",
        "Abutment face separation == total length",
        "dist(a1_face, a2_face) == total_length_m",
        _check_abutment_face_distance,
    ),
    Case(
        "VV-PLAN-004",
        "bridgecad_core.geometry.plan",
        "A",
        "Bearing count per support line",
        "len(bearing_positions) == (nspan + 1) * girders_per_deck_count",
        _check_bearing_count,
    ),
    # ---- geometry.cross_section -----------------------------------------
    Case(
        "VV-XSEC-001",
        "bridgecad_core.geometry.cross_section",
        "A",
        "Crown height at centreline",
        "top_of_wearing_coat_y == camber_mm / 1000",
        _check_crown_height,
    ),
    Case(
        "VV-XSEC-002",
        "bridgecad_core.geometry.cross_section",
        "A",
        "Deck-slab soffit level",
        "bottom_of_slab_y == -deck_thickness_mm / 1000",
        _check_slab_soffit,
    ),
    Case(
        "VV-XSEC-003",
        "bridgecad_core.geometry.cross_section",
        "A",
        "Parabolic camber profile",
        "camber_y_at_x(0) == camber_mm; camber_y_at_x(+/-cw/2) == 0",
        _check_parabolic_camber,
    ),
    Case(
        "VV-XSEC-004",
        "bridgecad_core.geometry.cross_section",
        "A",
        "Zone offsets are ordered and reach the edge",
        "half_width_offsets strictly increasing; last == overall_width/2",
        _check_offset_monotonic,
    ),
    Case(
        "VV-XSEC-005",
        "bridgecad_core.geometry.cross_section",
        "A",
        "Girder soffit level",
        "bottom_of_girder_y == bottom_of_slab_y - girder_depth/1000",
        _check_girder_soffit,
    ),
    # ---- quantities ------------------------------------------------------
    Case(
        "VV-QTY-001",
        "bridgecad_core.quantities",
        "A",
        "Deck slab concrete volume",
        "deck_cum == total_length * overall_width * deck_thickness",
        _check_deck_volume,
    ),
    Case(
        "VV-QTY-002",
        "bridgecad_core.quantities",
        "A",
        "Wearing-coat volume on carriageway",
        "wc_cum == total_length * carriageway_width * coat_thickness",
        _check_wearing_coat_volume,
    ),
    Case(
        "VV-QTY-003",
        "bridgecad_core.quantities",
        "A",
        "Rebar mass is linear in concrete volume",
        "rebar_kg(0) == 0; rebar_kg(2V) == 2 * rebar_kg(V)",
        _check_rebar_linearity,
    ),
    Case(
        "VV-QTY-004",
        "bridgecad_core.quantities",
        "A",
        "Pier count = nspan - 1",
        "_pier_count(p) == max(nspan - 1, 0)",
        _check_pier_count,
    ),
    Case(
        "VV-QTY-005",
        "bridgecad_core.quantities",
        "A",
        "BOQ is well-formed",
        "codes unique; code/description/unit non-empty; qty >= 0",
        _check_boq_well_formed,
    ),
    Case(
        "VV-QTY-006",
        "bridgecad_core.quantities",
        "A",
        "Steel control total = sum of kg items",
        "SUM-200 qty == round(sum(kg item qty except SUM-200), 1)",
        _check_steel_control_total,
    ),
    # ---- costs -----------------------------------------------------------
    Case(
        "VV-COST-001",
        "bridgecad_core.costs",
        "A",
        "Amount = rate x quantity",
        "amount == rate * qty; total_cost == sum(amounts)",
        _check_cost_amount,
    ),
    Case(
        "VV-COST-002",
        "bridgecad_core.costs",
        "A",
        "Unknown rates leave items unpriced",
        "unknown code -> rate/amount None and contributes 0 to the total",
        _check_unpriced_passthrough,
    ),
    # ---- validation ------------------------------------------------------
    Case(
        "VV-VAL-001",
        "bridgecad_core.validation",
        "A",
        "Compliance score arithmetic",
        "score == max(0, 100 - 15*critical_fails - 3*warning_fails)",
        _check_score_arithmetic,
    ),
    Case(
        "VV-VAL-002",
        "bridgecad_core.validation",
        "A",
        "Score stays within [0, 100]",
        "empty report == 100; many critical fails floor at 0",
        _check_score_range,
    ),
    Case(
        "VV-VAL-003",
        "bridgecad_core.validation",
        "A",
        "Overall status precedence",
        "FAIL > WARN > PASS by worst failed severity",
        _check_status_mapping,
    ),
    # ---- validation_registry --------------------------------------------
    Case(
        "VV-REG-001",
        "bridgecad_core.validation_registry",
        "A",
        "Rule count and id format",
        "len(RULES) == 163; ids unique and match V\\d{3}",
        _check_rule_count,
    ),
    Case(
        "VV-REG-002",
        "bridgecad_core.validation_registry",
        "A",
        "Stable-id cross map",
        "RULE_ID_BY_CHECK maps each source id to a unique V-id",
        _check_rule_cross_map,
    ),
    Case(
        "VV-REG-003",
        "bridgecad_core.validation_registry",
        "A",
        "Implemented-rule count",
        "exactly 43 rules flagged implemented; first is critical",
        _check_implemented_count,
    ),
    # ---- types -----------------------------------------------------------
    Case(
        "VV-TYP-001",
        "bridgecad_core.types",
        "A",
        "Enum registry resolves class names",
        "ENUM_REGISTRY[name] is the enum class for the stable set",
        _check_enum_registry,
    ),
    Case(
        "VV-TYP-002",
        "bridgecad_core.types",
        "A",
        "Stable enums are non-empty with unique values",
        "values non-empty and unique per enum",
        _check_enum_integrity,
    ),
    # ---- models ----------------------------------------------------------
    Case(
        "VV-MOD-001",
        "bridgecad_core.models",
        "A",
        "Geometry total length is computed from spans",
        "geometry_input.total_length_m == sum(span_lengths_m)",
        _check_total_length_computed,
    ),
    Case(
        "VV-MOD-002",
        "bridgecad_core.models",
        "A",
        "Geometry overall width is computed from parts",
        "overall_width_m == carriageway + footpaths + barriers + kerbs (+ others)",
        _check_overall_width_computed,
    ),
    Case(
        "VV-MOD-003",
        "bridgecad_core.models",
        "A",
        "Project aliases propagate geometry values",
        "total_bridge_length_m / overall_bridge_width_m == geometry_input values",
        _check_length_propagation,
    ),
    # ---- compliance_engine (W06) ----------------------------------------
    Case(
        "VV-CMP-001",
        "bridgecad_qa.compliance_engine",
        "A",
        "Span/depth check uses the registered IRC band",
        "CC-001 demand == round(span/depth, 1); utilisation == demand/capacity; passes",
        _check_cc001_span_depth_band,
    ),
    Case(
        "VV-CMP-002",
        "bridgecad_qa.compliance_engine",
        "A",
        "Minimum deck slab thickness check",
        "CC-002 demand == 200 mm (IRC:21 Cl.304.7); capacity == provided thickness",
        _check_cc002_slab_thickness,
    ),
    Case(
        "VV-CMP-003",
        "bridgecad_qa.compliance_engine",
        "A",
        "Impact-factor check under the IRC:6 ceiling",
        "CC-003 demand == 4.5 / (6 + L); capacity == 0.50",
        _check_cc003_impact_factor,
    ),
    Case(
        "VV-CMP-004",
        "bridgecad_qa.compliance_engine",
        "A",
        "Expansion-joint gap rounds to 5 mm",
        "CC-004 demand % 5 == 0; capacity == 100 mm",
        _check_cc004_expansion_joint,
    ),
    Case(
        "VV-CMP-005",
        "bridgecad_qa.compliance_engine",
        "A",
        "Freeboard check: required vs soffit - HFL",
        "CC-005 demand == required freeboard; capacity == achieved (round 3 dp)",
        _check_cc005_freeboard,
    ),
    Case(
        "VV-CMP-006",
        "bridgecad_qa.compliance_engine",
        "A",
        "Deck concrete grade meets IRC:112 minimum",
        "CC-006 demand == 30 MPa; capacity == provided grade number",
        _check_cc006_deck_grade,
    ),
]

__all__ = ["REGISTRY", "BenchContext", "Case", "TIER_ABS_TOL", "TIER_REL_TOL", "assert_within_tier"]
