"""Wing-21 — formula behaviour across a range, not just at the reference points.

VALIDATION vs EXTRAPOLATION
    At a reference bridge's parameters, a match is validation — a drawing agrees.
    Between and beyond them, a match is only internal consistency. Both are worth
    testing; they are not the same claim, and the ids say which is which.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from . import contract

pytestmark = pytest.mark.draw

from bridgecad_draw.contract import wing_wall_geometry  # noqa: E402


def _project(**kw):
    return contract.make_project("blank", **kw)


@pytest.mark.parametrize("nspan", [2, 3, 4, 5, 6])
def test_pier_count_is_nspan_minus_one(nspan: int):
    """Extrapolation beyond the corpus (max 4). If this breaks at 6, the corpus
    would never have told you."""
    p = _project(nspan=nspan, span_m="12.0")
    assert len(p.geometry.pier_positions()) == nspan - 1


@pytest.mark.parametrize("splay", ["30", "35", "40", "45", "50", "55", "60"])
def test_wall_length_increases_with_splay(splay: str):
    """Extrapolation. At fixed face run a steeper splay means a longer wall along
    the face; monotonicity is the property, not any single value."""
    lengths = []
    for s in ("30", splay):
        p = _project(abtl_m="13.000", carriageway_m="7.500", splay_deg=s)
        lengths.append(wing_wall_geometry(p)[0].length_m)
    assert lengths[1] >= lengths[0]


def test_zero_face_run_when_abtl_equals_carriageway():
    """Boundary. ABTL == carriageway is degenerate and the corpus does not
    contain it — a known gap, tested anyway."""
    p = _project(abtl_m="8.000", carriageway_m="8.000", splay_deg="45")
    w = wing_wall_geometry(p)[0]
    assert w.face_run_m == 0
    assert w.length_m == 0


def test_wall_length_is_face_run_over_cos_splay():
    """The formula, restated independently of the implementation's internals."""
    import math
    for face, splay in ((Decimal("2.750"), Decimal("45")), (Decimal("1.250"), Decimal("30")),
                        (Decimal("2.250"), Decimal("60"))):
        p = _project(abtl_m=str(face * 2 + Decimal("7.500")), carriageway_m="7.500",
                     splay_deg=str(splay))
        w = wing_wall_geometry(p)[0]
        expected = face / Decimal(str(math.cos(math.radians(float(splay)))))
        assert abs(w.length_m - expected) < Decimal("0.001"), (face, splay)
