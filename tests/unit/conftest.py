"""Shared fixtures for the pure-function unit lane (``tests/unit``).

No heavy I/O: the only file read is the canonical fixture JSON, loaded once
per session through the existing e2e loader (the same importlib technique
``tests/draw/contract.py`` uses in ``_build_from_fixture``).
"""

from __future__ import annotations

import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "e2e" / "fixtures" / "simple_12m.json"
E2E_RUNNER = REPO / "tests" / "e2e" / "run_e2e.py"


def _load_project():
    """Build a validated BridgeProject from the canonical fixture JSON.

    Reuses ``tests/e2e/run_e2e.py:_build_from_fixture`` via importlib so the
    loader lives in exactly one place.
    """
    spec = importlib.util.spec_from_file_location("bridgecad_e2e_fixtures_unit", E2E_RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return module._build_from_fixture(data)


@pytest.fixture(scope="session")
def project():
    """A valid BridgeProject (1 x 12 m simple span) shared across the session."""
    return _load_project()


@pytest.fixture
def blank_project():
    """A fresh, isolated copy of the canonical project for mutation tests."""
    return _load_project()


@pytest.fixture
def span_variant(project):
    """Factory returning a deep copy of ``project`` with a new span layout.

    Rewrites ``geometry_input`` keeping ``span_count`` consistent with
    ``len(span_lengths_m)`` (the model validates the two against each other).
    """

    def _make(lengths: list[float]):
        clone = project.model_copy(deep=True)
        clone.geometry_input = clone.geometry_input.model_copy(
            update={
                "span_count": len(lengths),
                "span_lengths_m": [Decimal(str(x)) for x in lengths],
            }
        )
        return clone

    return _make
