"""Wing-22 — property-based parameter fuzzing (GUIDE.md §12 Phase 2).

The golden corpus (`tests/draw/golden`) covers four bridges; the sweeps in
`test_formula_sweep` cover hand-picked ranges. Neither can claim that *no*
combination in the real input space breaks the invariants. This module draws
NSPAN, span, ABTL, carriageway and splay across the ranges a source workbook
uses and asserts the structural invariants the drawing engine depends on.

The bug classes it targets are the ones `00- abstract of bugs.txt` documents:
the NSPAN=1 off-by-one (zero piers, never a negative count) and the ABTL
degenerate abutment that produced a zero-length wing wall in a real DXF.
"""

from __future__ import annotations

import math
from itertools import pairwise

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from . import contract

pytestmark = pytest.mark.draw

#: Physically meaningful draw ranges. `ABTL < carriageway` is included on
#: purpose: the engine must clamp it to a zero-length (never negative) wall.
NSPAN = st.integers(min_value=1, max_value=8)
SPAN_M = st.floats(min_value=6.0, max_value=45.0, allow_nan=False, allow_infinity=False)
ABTL_M = st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)
SPLAY_DEG = st.floats(min_value=0.0, max_value=30.0, allow_nan=False, allow_infinity=False)
CARRIAGEWAY_M = st.floats(min_value=3.75, max_value=12.0, allow_nan=False, allow_infinity=False)

_SETTINGS = settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


def _project(nspan, span_m, abtl_m, splay_deg, carriageway_m):
    return contract.make_project(
        "blank",
        nspan=nspan,
        span_m=f"{span_m:.3f}",
        abtl_m=f"{abtl_m:.3f}",
        splay_deg=f"{splay_deg:.3f}",
        carriageway_m=f"{carriageway_m:.3f}",
    )


@_SETTINGS
@given(NSPAN, SPAN_M, ABTL_M)
def test_span_loop_invariants(nspan, span_m, abtl_m):
    """NSPAN -> piers and boundaries, across the whole range."""
    p = _project(nspan, span_m, abtl_m, 45.0, 7.5)

    # NSPAN=1 must give ZERO intermediate piers, never -1 (the historic bug).
    assert len(p.geometry.pier_positions()) == max(nspan - 1, 0)
    assert len(p.geometry.span_boundaries()) == nspan + 1

    bounds = p.geometry.span_boundaries()
    assert bounds[0] == pytest.approx(0.0, abs=1e-6)
    assert all(b >= 0.0 for b in bounds)
    assert all(b2 >= b1 for b1, b2 in pairwise(bounds))  # non-decreasing
    assert all(0.0 <= pier <= bounds[-1] for pier in p.geometry.pier_positions())

    lengths = p.geometry.span_lengths_m()
    assert len(lengths) == nspan
    assert all(length >= 0.0 for length in lengths)
    assert sum(lengths) == pytest.approx(p.geometry.total_length_m, abs=1e-6)


@_SETTINGS
@given(ABTL_M, CARRIAGEWAY_M, SPLAY_DEG)
def test_wing_wall_invariants(abtl_m, carriageway_m, splay_deg):
    """No negative geometry, and the trig identities hold at every splay."""
    p = _project(2, 12.0, abtl_m, splay_deg, carriageway_m)

    walls = contract.wing_wall_geometry(p)
    assert walls, "every abutment draws two wing walls (left/right)"

    for w in walls:
        assert w.face_run_m >= 0.0
        assert w.length_m >= 0.0
        assert w.return_m >= 0.0
        # length = face / cos(splay); return = length * sin(splay).
        # Evaluate against the engine's own reported splay so a defaulted splay
        # cannot make the identity look violated.
        rad = math.radians(w.splay_deg)
        assert w.length_m == pytest.approx(w.face_run_m / math.cos(rad), abs=1e-6)
        assert w.return_m == pytest.approx(w.length_m * math.sin(rad), abs=1e-6)
