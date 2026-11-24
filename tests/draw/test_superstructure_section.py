"""tests/draw/test_superstructure_section.py — behaviour tests for the
conditional superstructure renderer (audit fixes R1 + R2).

Pure data-level tests; no ezdxf required.
"""
from __future__ import annotations

import pytest

from bridgecad_draw.sheets.superstructure_section import (
    SectionSpec,
    girder_positions,
    section_primitives,
)

X0, X1 = 0.0, 9000.0          # 9 m deck in model mm
Y_DECK, Y_WEAR, Y_GBOT = 0.0, 65.0, -1200.0


def _spec(bridge_type: str, **kw) -> SectionSpec:
    return SectionSpec(
        bridge_type=bridge_type,
        deck_t_mm=230, wear_t_mm=65,
        girder_d_mm=kw.get("girder_d_mm", 1200),
        girder_spacing_m=kw.get("girder_spacing_m", 2.5),
        girders_per_deck=kw.get("girders_per_deck", 4),
    )


def test_slab_bridge_draws_no_girders():
    prims = section_primitives(_spec("SLAB"), X0, X1, Y_DECK, Y_WEAR, Y_GBOT)
    assert not any(r.layer == "SUPER-GIRDER" for r in prims.rects)
    assert not any("GIRDER" in l.text.upper() for l in prims.labels)
    assert not any("GIRDER" in d.text.upper() for d in prims.dims)


def test_tbeam_bridge_draws_modelled_girders():
    spec = _spec("T_BEAM", girder_spacing_m=2.0, girders_per_deck=4)
    xs = girder_positions(spec, X0, X1)
    assert len(xs) == 4
    # modelled spacing, not even spread: consecutive centres exactly 2000 mm
    assert xs[1] - xs[0] == 2000.0
    # group symmetric about the deck centreline
    assert abs((xs[0] + xs[-1]) / 2.0 - (X0 + X1) / 2.0) < 1e-6
    prims = section_primitives(spec, X0, X1, Y_DECK, Y_WEAR, Y_GBOT)
    assert sum(1 for r in prims.rects if r.layer == "SUPER-GIRDER") == 4
    assert any("T-BEAM" in l.text.upper() for l in prims.labels)


def test_box_cell_draws_no_girders_but_cells():
    prims = section_primitives(_spec("BOX_CELL", girders_per_deck=4), X0, X1, Y_DECK, Y_WEAR, Y_GBOT)
    assert not any(r.layer == "SUPER-GIRDER" for r in prims.rects)
    assert any("BOX" in l.text.upper() for l in prims.labels)


def test_unknown_type_is_explicit_not_invented():
    prims = section_primitives(_spec("suspension"), X0, X1, Y_DECK, Y_WEAR, Y_GBOT)
    assert not any(r.layer == "SUPER-GIRDER" for r in prims.rects)
    assert any("not declared" in n for n in prims.notes)


def test_spacing_that_does_not_fit_is_rejected():
    spec = _spec("I_GIRDER", girder_spacing_m=3.0, girders_per_deck=5)
    with pytest.raises(ValueError, match="Girder centres must fit"):
        girder_positions(spec, X0, X1)


def test_slab_note_present():
    prims = section_primitives(_spec("SLAB"), X0, X1, Y_DECK, Y_WEAR, Y_GBOT)
    assert any("Solid slab" in n for n in prims.notes)