"""Sheet 5/8 layout guards — the checks table must clear the views (C2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "e2e" / "fixtures" / "simple_12m.json"


@pytest.fixture(scope="module")
def project():
    from . import contract

    return contract._build_from_fixture(
        contract._fixture_data("tests/e2e/fixtures/simple_12m.json")
    )


def test_sheet8_checks_table_clears_views():
    from bridgecad_draw import sheet8_side_elevations as s8

    assert s8._CHECKS_Y + s8._CHECKS_ROWS_H < s8._VIEW_Y0


def test_sheet5_checks_table_clears_pier_dims(project):
    """Table top (origin y=80 + 7 mm/row + header) must stay below the pier
    elevation dimension band (~237 mm)."""
    from bridgecad_draw.checks_table import build_abutment_rows

    n = len(build_abutment_rows(project))
    table_top = 80.0 + 7.0 * (n + 1)
    assert table_top < 237.0, f"checks table top {table_top:.0f} collides with pier dims"
