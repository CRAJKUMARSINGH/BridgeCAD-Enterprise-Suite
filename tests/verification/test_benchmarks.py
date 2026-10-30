"""W04 · V&V benchmark runner over :data:`cases.REGISTRY`.

One pytest case per benchmark; each runs against the canonical project built by
the reused unit-lane loader (``tests/unit/conftest.py``).  The tier asserted is
the one declared on the :class:`~tests.verification.cases.Case` and checked by
``assert_within_tier``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from bridgecad_core.models import BridgeProject

from .cases import REGISTRY, BenchContext, Case

REPO = Path(__file__).resolve().parents[2]
UNIT_CONFTEST = REPO / "tests" / "unit" / "conftest.py"

CASE_IDS = [case.id for case in REGISTRY]


def _load_unit_conftest():
    """Load ``tests/unit/conftest.py`` so this lane reuses its project loader."""
    spec = importlib.util.spec_from_file_location("bridgecad_vv_unit_conftest", UNIT_CONFTEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_UNIT = _load_unit_conftest()


@pytest.fixture(scope="session")
def project() -> BridgeProject:
    """Canonical 1 x 12 m project shared across the lane (from the unit loader)."""
    return _UNIT._load_project()


@pytest.fixture
def blank_project() -> BridgeProject:
    """Fresh isolated copy for mutation cases (from the unit loader)."""
    return _UNIT._load_project()


@pytest.fixture
def span_variant(project):
    """Span-layout factory reused from the unit conftest fixture."""
    return getattr(_UNIT.span_variant, "__wrapped__", _UNIT.span_variant)(project)


@pytest.mark.parametrize("case", REGISTRY, ids=CASE_IDS)
def test_benchmark_case(case: Case, project, blank_project, span_variant) -> None:
    context = BenchContext(project=project, blank_project=blank_project, span_variant=span_variant)
    case.check(context)
