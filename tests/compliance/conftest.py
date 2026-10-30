"""Shared fixtures for the W06 compliance lane.

Reuses the unit lane's project loader so no fixture logic is duplicated.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from bridgecad_core.models import BridgeProject

REPO = Path(__file__).resolve().parents[2]
UNIT_CONFTEST = REPO / "tests" / "unit" / "conftest.py"


def _unit():
    spec = importlib.util.spec_from_file_location("bridgecad_compliance_unit_conftest", UNIT_CONFTEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_UNIT = _unit()


@pytest.fixture(scope="session")
def project() -> BridgeProject:
    """Canonical 1 x 12 m project (from the unit loader)."""
    return _UNIT._load_project()


@pytest.fixture
def blank_project() -> BridgeProject:
    """Fresh isolated copy for mutation cases (from the unit loader)."""
    return _UNIT._load_project()
