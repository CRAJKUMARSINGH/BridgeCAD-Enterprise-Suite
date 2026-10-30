"""W05 · Formula correctness — Hypothesis property tests over the formula modules.

Each test states a *property* that must hold for every input in a domain, not
one worked example. The domains are the physically meaningful ranges a source
workbook uses, so a counterexample is a real engineering input, not a float
edge case. ``max_examples`` is bounded to keep the lane well under 30 s.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from itertools import pairwise

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from bridgecad_core.costs import RateLookup, compute_cost
from bridgecad_core.geometry import coordinates as coords
from bridgecad_core.geometry.foundation import compute_pile_group_layout
from bridgecad_core.geometry.long_section import pier_positions, span_boundaries
from bridgecad_core.models import GeometryInput
from bridgecad_core.quantities import BillItem, BillOfQuantities, extract_quantities
from bridgecad_core.types import FoundationType, ValidationSeverity
from bridgecad_core.validation import ValidationFinding, ValidationReport

_SETTINGS = settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)

SKEW_DEG = st.floats(min_value=-60.0, max_value=60.0, allow_nan=False, allow_infinity=False)
COORD_M = st.floats(min_value=-1e4, max_value=1e4, allow_nan=False, allow_infinity=False)
POINT_M = st.tuples(COORD_M, COORD_M)

SPAN_M = st.floats(min_value=1.0, max_value=150.0, allow_nan=False, allow_infinity=False)
SPAN_LAYOUT = st.lists(SPAN_M, min_size=1, max_size=6)

NONNEG_QTY = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
RATE = st.floats(min_value=0.0, max_value=1e5, allow_nan=False, allow_infinity=False)

# Pile counts the engine documents as centred: the standard IRC arrangements
# (3 triangular / 5 cruciform / 7 hexagonal) plus full rectangular grids. The
# fallback grid is not index-symmetric for a partial last row, so those counts
# are deliberately outside the asserted contract.
CENTRED_PILE_COUNTS = st.sampled_from([1, 3, 4, 5, 6, 7, 9])

_FINDING = st.builds(
    ValidationFinding,
    check_id=st.sampled_from(["C01", "W01", "ERR"]),
    description=st.just("d"),
    severity=st.sampled_from(list(ValidationSeverity)),
    passed=st.booleans(),
    message=st.just(""),
)


# ---------------------------------------------------------------------------
# Coordinates
# ---------------------------------------------------------------------------


@_SETTINGS
@given(skew=SKEW_DEG, point=POINT_M)
def test_to_world_coords_inverts_to_sheet_coords(skew, point):
    """Sheet-local <-> world is an exact round trip within ROUND_TRIP_TOL_M."""
    origin = coords.sheet_origins([12.0, 15.0], skew)[coords.SheetId.CROSS_SECTION]
    back = coords.to_world_coords(origin, coords.to_sheet_coords(origin, point))
    assert back[0] == pytest.approx(point[0], abs=coords.ROUND_TRIP_TOL_M)
    assert back[1] == pytest.approx(point[1], abs=coords.ROUND_TRIP_TOL_M)


@_SETTINGS
@given(p=POINT_M, q=POINT_M)
def test_to_dxf_mm_is_linear_in_metres(p, q):
    """to_dxf_mm is metres x MM_PER_M and additive over the point space."""
    a = coords.to_dxf_mm(p)
    b = coords.to_dxf_mm(q)
    summed = coords.to_dxf_mm((p[0] + q[0], p[1] + q[1]))
    assert summed[0] == pytest.approx(a[0] + b[0], rel=1e-9, abs=1e-9)
    assert summed[1] == pytest.approx(a[1] + b[1], rel=1e-9, abs=1e-9)
    assert a[0] == pytest.approx(p[0] * coords.MM_PER_M, rel=1e-12, abs=1e-9)
    assert a[1] == pytest.approx(p[1] * coords.MM_PER_M, rel=1e-12, abs=1e-9)


# ---------------------------------------------------------------------------
# Span / pier contract
# ---------------------------------------------------------------------------


@_SETTINGS
@given(lengths=SPAN_LAYOUT)
def test_span_and_pier_contract(span_variant, lengths):
    """len(boundaries) == nspan+1; len(piers) == nspan-1; chainage monotonic."""
    project = span_variant(lengths)
    boundaries = span_boundaries(project)
    piers = pier_positions(project)

    assert len(boundaries) == len(lengths) + 1
    assert len(piers) == max(len(lengths) - 1, 0)
    assert boundaries[0] == 0.0
    assert all(later > earlier for earlier, later in pairwise(boundaries))
    assert boundaries[-1] == pytest.approx(sum(lengths))
    assert piers == pytest.approx(boundaries[1:-1])


# ---------------------------------------------------------------------------
# Foundation pile group
# ---------------------------------------------------------------------------


@_SETTINGS
@given(n=CENTRED_PILE_COUNTS)
def test_pile_group_is_centred_and_symmetric(pile_variant, n):
    """Pile centres average to the origin and mirror across the centreline."""
    positions = compute_pile_group_layout(pile_variant(n)).pile_positions
    assert len(positions) == n
    assert sum(x for x, _ in positions) / n == pytest.approx(0.0, abs=1e-9)
    assert sum(y for _, y in positions) / n == pytest.approx(0.0, abs=1e-9)
    for x, y in positions:
        assert any(abs(mx + x) < 1e-9 and abs(my - y) < 1e-9 for mx, my in positions)


# ---------------------------------------------------------------------------
# Bill of quantities
# ---------------------------------------------------------------------------


@_SETTINGS
@given(qtys=st.lists(NONNEG_QTY, max_size=12))
def test_boq_add_accumulates_items_in_order(qtys):
    """add() appends every item, so the running total equals the sum of items."""
    boq = BillOfQuantities()
    for i, qty in enumerate(qtys):
        boq.add(BillItem(code=f"C{i:02d}", description="d", unit="cum", qty=qty))
    assert [item.qty for item in boq.items] == qtys
    assert sum(item.qty for item in boq.items) == pytest.approx(sum(qtys))


def test_boq_rebar_control_total_equals_sum_of_kg_items(project):
    """The SUM-200 control total is the sum of the kg line items."""
    boq = extract_quantities(project)
    kg_items = [it for it in boq.items if it.unit == "kg" and it.code != "SUM-200"]
    control = next(it for it in boq.items if it.code == "SUM-200")
    assert control.qty == pytest.approx(sum(it.qty for it in kg_items), abs=0.05)


# ---------------------------------------------------------------------------
# Validation score
# ---------------------------------------------------------------------------


@_SETTINGS
@given(findings=st.lists(_FINDING, max_size=25))
def test_validation_score_is_bounded(findings):
    """The compliance score never leaves [0, 100], however many findings fail."""
    assert 0 <= ValidationReport(list(findings)).score <= 100


@_SETTINGS
@given(findings=st.lists(_FINDING, max_size=25), extra=_FINDING)
def test_validation_score_is_monotonic_in_failures(findings, extra):
    """Adding a failing finding never raises the score."""
    base = ValidationReport(list(findings)).score
    worse = ValidationReport([*findings, replace(extra, passed=False)]).score
    assert worse <= base


# ---------------------------------------------------------------------------
# Cost = rate x quantity
# ---------------------------------------------------------------------------


class _Rates(RateLookup):
    """Test double returning a caller-supplied table of unit rates."""

    def __init__(self, table: dict[str, float]) -> None:
        self._table = table

    def get(self, code: str, region: str | None = None) -> float | None:
        return self._table.get(code)


@_SETTINGS
@given(qty=NONNEG_QTY, rate=RATE)
def test_cost_is_rate_times_quantity(qty, rate):
    item = BillItem(code="X", description="d", unit="cum", qty=qty)
    bom = BillOfQuantities()
    bom.add(item)
    compute_cost(bom, _Rates({"X": rate}))
    assert item.rate == pytest.approx(rate)
    assert item.amount == pytest.approx(rate * qty)
    assert bom.total_cost == pytest.approx(rate * qty)


@_SETTINGS
@given(pairs=st.lists(st.tuples(NONNEG_QTY, RATE), max_size=8))
def test_cost_total_is_sum_of_item_amounts(pairs):
    bom = BillOfQuantities()
    table: dict[str, float] = {}
    for i, (qty, rate) in enumerate(pairs):
        code = f"C{i}"
        table[code] = rate
        bom.add(BillItem(code=code, description="d", unit="cum", qty=qty))
    compute_cost(bom, _Rates(table))
    assert bom.total_cost == pytest.approx(sum(it.amount for it in bom.items))


# ---------------------------------------------------------------------------
# Input-domain validation (guards that protect the formula modules)
# ---------------------------------------------------------------------------


@_SETTINGS
@given(bad=st.floats(max_value=1.0, exclude_max=True, allow_nan=False, allow_infinity=False))
def test_geometry_input_rejects_span_below_one_metre(bad):
    """A non-positive / sub-metre span is outside the IRC domain [1 m, 150 m]."""
    with pytest.raises(ValidationError):
        GeometryInput(
            span_count=1,
            span_lengths_m=[Decimal(str(bad))],
            carriageway_width_m=Decimal("7.5"),
        )


@_SETTINGS
@given(bad=st.floats(max_value=0.0, exclude_max=True, allow_nan=False, allow_infinity=False))
def test_geometry_input_rejects_non_positive_carriageway_width(bad):
    """A negative carriageway width violates the field's >= 3.5 m floor."""
    with pytest.raises(ValidationError):
        GeometryInput(carriageway_width_m=Decimal(str(bad)))


def test_zero_piles_is_domain_not_applicable(pile_variant):
    """piles_per_pier == 0 means "not applicable" (open/well) -> documented group."""
    assert len(compute_pile_group_layout(pile_variant(0)).pile_positions) == 4


def test_well_foundation_yields_no_pile_positions(project):
    clone = project.model_copy(deep=True)
    clone.foundation_details = clone.foundation_details.model_copy(
        update={"type": FoundationType.WELL}
    )
    layout = compute_pile_group_layout(clone)
    assert layout.pile_positions == []
    assert layout.well_outer_radius_m > 0.0
