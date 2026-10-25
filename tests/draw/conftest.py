from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SHEETS = (
    "sheet1_plan",
    "sheet2_long_section",
    "sheet3_cross_section",
    "sheet4_foundation",
    "sheet5_pier_abutment_details",
    "sheet6_bearings_joints",
    "sheet7_bill_of_quantities",
)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO


@pytest.fixture
def sheet_names() -> tuple[str, ...]:
    return SHEETS
