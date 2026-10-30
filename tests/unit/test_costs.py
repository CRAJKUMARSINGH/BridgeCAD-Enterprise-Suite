"""Pure-function tests for ``bridgecad_core.costs``."""

from __future__ import annotations

import pytest

from bridgecad_core.costs import RateLookup, compute_cost
from bridgecad_core.quantities import BillItem, BillOfQuantities

RATES = {"A": 100.0, "B": 250.0}


class FixedRates(RateLookup):
    """Test double returning deterministic unit rates."""

    def get(self, code: str, region: str | None = None) -> float | None:
        return RATES.get(code)


def _bom(*items: BillItem) -> BillOfQuantities:
    boq = BillOfQuantities()
    for item in items:
        boq.add(item)
    return boq


def test_compute_cost_sets_rate_and_amount():
    item = BillItem(code="A", description="d", unit="cum", qty=3.0)
    bom = _bom(item)
    compute_cost(bom, FixedRates())
    assert item.rate == pytest.approx(100.0)
    assert item.amount == pytest.approx(300.0)


def test_compute_cost_totals_sum_of_amounts():
    bom = _bom(
        BillItem(code="A", description="d", unit="cum", qty=2.0),
        BillItem(code="B", description="d", unit="cum", qty=4.0),
    )
    compute_cost(bom, FixedRates())
    assert bom.total_cost == pytest.approx(2.0 * 100.0 + 4.0 * 250.0)


def test_unknown_code_left_unpriced():
    item = BillItem(code="ZZZ", description="d", unit="cum", qty=5.0)
    bom = _bom(item)
    compute_cost(bom, FixedRates())
    assert item.rate is None
    assert item.amount is None
    assert bom.total_cost == 0.0


def test_mixed_known_and_unknown_codes():
    known = BillItem(code="A", description="d", unit="cum", qty=1.0)
    unknown = BillItem(code="ZZZ", description="d", unit="cum", qty=1.0)
    bom = _bom(known, unknown)
    compute_cost(bom, FixedRates())
    assert bom.total_cost == pytest.approx(100.0)
    assert unknown.rate is None


def test_compute_cost_default_lookup_prices_nothing():
    item = BillItem(code="A", description="d", unit="cum", qty=1.0)
    bom = _bom(item)
    compute_cost(bom)
    assert item.rate is None
    assert bom.total_cost == 0.0


def test_compute_cost_returns_the_same_boq():
    bom = _bom(BillItem(code="A", description="d", unit="cum", qty=1.0))
    assert compute_cost(bom, FixedRates()) is bom
