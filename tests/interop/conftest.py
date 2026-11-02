"""W08 interoperability lane — shared fixtures.

The verification command from the W08 issue is ``pytest -q tests/interop``. The
lane measures the per-format loss budget stated in ``docs/interop.md`` against
the same five pinned fixtures the drawing lane uses, so "round-trip" here means
the exact projects whose geometry is already baselined.

``tests/`` is put on ``sys.path`` so this lane reuses the product-facade
adapters (``draw.contract``) instead of duplicating the fixture→model mapping.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_TESTS = REPO / "tests"
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

#: The pinned fixtures the per-format loss budget is measured against.
#: ``tests/draw/golden/<slug>.json`` names the project fixture behind each one.
PINNED_SLUGS = (
    "continuous_3x12m",
    "pp05_30m_psc",
    "simple_12m",
    "skew15_3x18m",
    "well_0_600",
)


@pytest.fixture(scope="session")
def make_model():
    """Return ``slug -> validated BridgeProject``, built once per session.

    The builder is the repo's canonical fixture-JSON → BridgeProject adapter in
    ``tests/draw/contract.py``, reached through the same golden slugs the W07
    lane pins. No overrides are applied: a round-trip must be measured on the
    fixture as written, not on a drafting view of it.
    """
    from draw import contract

    cache: dict[str, object] = {}

    def _make(slug: str):
        if slug not in cache:
            golden = contract.load_golden(slug)
            cache[slug] = contract._build_from_fixture(contract._fixture_data(golden["fixture"]))
        return cache[slug]

    return _make


@pytest.fixture(scope="session", params=PINNED_SLUGS)
def pinned(request, make_model):
    """One pinned project per parametrisation, identified by ``request.param``."""
    return make_model(request.param)
