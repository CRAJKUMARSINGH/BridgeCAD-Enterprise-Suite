# tests/draw/test_budgets.py
"""Generation has to stay fast enough that people run it locally. A 4-minute
suite gets skipped; a 40-second one gets run."""
import time

import pytest

from . import contract

pytestmark = pytest.mark.draw

BUDGET_MS = 4000          # per sheet, cold
TOTAL_BUDGET_MS = 30000   # full set


@pytest.mark.parametrize("sheet", sorted(contract.SHEET_NAMES))
def test_sheet_generates_within_budget(sheet: str):
    project = contract.make_project("simple_12m")
    t0 = time.perf_counter()
    contract.build_sheet(project, sheet)
    ms = (time.perf_counter() - t0) * 1000
    assert ms < BUDGET_MS, f"{sheet}: {ms:.0f} ms exceeds the {BUDGET_MS} ms budget"


def test_full_set_generates_within_budget():
    project = contract.make_project("simple_12m")
    t0 = time.perf_counter()
    for sheet in sorted(contract.SHEET_NAMES):
        contract.build_sheet(project, sheet)
    ms = (time.perf_counter() - t0) * 1000
    assert ms < TOTAL_BUDGET_MS, f"full set: {ms:.0f} ms exceeds {TOTAL_BUDGET_MS} ms"
