"""SS3 §A1–A4 — Sheet 2 scale honesty, exaggeration and presence gates.

These drive the *production* sheet (``bridgecad_draw.sheet2_long_section``),
not the ``sheets/`` scaffold the older wing tests use, because the caption lie
this file exists to prevent lives in the production path.

The 270 m nine-span is the fixture that proves the point: it used to be drawn at
about 1:382 under a "1:100" caption. Every assertion here is measured from the
generated DXF, so it cannot pass if the printed scale and the geometry disagree.
"""
from __future__ import annotations

import ezdxf
import pytest

from bridgecad_draw import sheet2_long_section as S2
from bridgecad_draw.fit import LADDER, MIN_TEXT_MM, choose_fit

from . import contract

pytestmark = pytest.mark.draw

# The booklet type 010 shape: nine 30 m spans.
NSPAN, SPAN_M = 9, 30.0
TOTAL_M = NSPAN * SPAN_M


def _render(tmp_path, *, v_exag: float = 1.0, **overrides):
    """Generate Sheet 2 from a blank model with *overrides*, return (doc, project)."""
    project = contract.make_project("blank", nspan=NSPAN, span_m=SPAN_M, **overrides)
    out = tmp_path / "Sheet2_LongSection.dxf"
    S2.generate(project, out, v_exag=v_exag)
    return ezdxf.readfile(str(out)), project


def _texts(doc) -> list[str]:
    out = []
    for e in doc.modelspace():
        if e.dxftype() == "TEXT":
            out.append(e.dxf.text)
        elif e.dxftype() == "MTEXT":
            out.append(e.text)
    return out


def _caption(doc) -> str:
    """The line that states the drawn scale (H ladder rung + V fit)."""
    for t in _texts(doc):
        if "H Scale" in t:
            return t
    raise AssertionError(f"no scale caption on the sheet: {_texts(doc)[:20]}")


def _printed_h_denom(doc) -> int:
    import re

    m = re.search(r"H Scale 1:(\d+)", _caption(doc))
    assert m, f"caption does not name an H scale: {_caption(doc)!r}"
    return int(m.group(1))


def _h_lines(doc, layer: str):
    return [
        e
        for e in doc.modelspace()
        if e.dxftype() == "LINE"
        and e.dxf.layer == layer
        and abs(e.dxf.start.y - e.dxf.end.y) < 1e-6
        and e.dxf.end.x > e.dxf.start.x
    ]


def _deck_slab_lines(doc):
    """Horizontal slab top and soffit, including each split span."""
    return _h_lines(doc, "SUPER-DECK")


@pytest.mark.parametrize(("family", "girder_depth"), [("SOLID_SLAB", None), ("RCC_TBEAM", 1150), ("PSC_IGIRDER", 1800)])
def test_dirt_wall_tops_match_both_slabs_in_booklet_drawings(tmp_path, family, girder_depth):
    from bridgecad_core.types import SuperstructureType
    from bridgecad_draw import sheet5_pier_abutment_details as S5

    project = contract.make_project("blank", nspan=2, span_m=12)
    project.superstructure = project.superstructure.model_copy(update={
        "type": SuperstructureType(family), "girder_depth_mm": girder_depth,
    })

    def tops(doc, *layers):
        return sorted(max(y for _, y in e.get_points("xy")) for e in doc.modelspace().query("LWPOLYLINE")
                      if e.dxf.layer in layers)

    elevation = ezdxf.readfile(S2.generate(project, tmp_path / "elevation.dxf"))
    deck_top = max(line.dxf.start.y for line in _deck_slab_lines(elevation))
    assert tops(elevation, "CIVIL-ROAD") == pytest.approx([deck_top, deck_top])
    assert tops(elevation, "SUB-DIRT-WALL") == pytest.approx([deck_top, deck_top])

    detail_scale = 100
    detail = ezdxf.readfile(S5.generate(project, tmp_path / "details.dxf", scale_denom=detail_scale))
    assert len(tops(detail, "CIVIL-ROAD")) == 2
    assert tops(detail, "ABUT-PROF", "SUB-DIRT-WALL") == pytest.approx(tops(detail, "CIVIL-ROAD"))
    approach_spans = []
    for slab in detail.modelspace().query('LWPOLYLINE[layer=="CIVIL-ROAD"]'):
        xs = [x for x, _ in slab.get_points("xy")]
        approach_spans.append(max(xs) - min(xs))
    assert sorted(approach_spans) == pytest.approx(sorted([
        float(project.substructure.approach_slab_length_m or 3.5) * 1000 / detail_scale,
        float(project.geometry_input.overall_width_m) * 1000 / detail_scale,
    ]))


def test_270m_fits_a_ladder_rung_without_breaking(tmp_path):
    doc, _ = _render(tmp_path)
    denom = _printed_h_denom(doc)
    assert denom in LADDER, f"printed 1:{denom} is not a ladder rung"
    assert denom != 500, "the 270 m section must fit a rung coarser than the ladder end"


def test_printed_scale_matches_the_geometry(tmp_path):
    """The deck line is drawn at exactly 1000/denom mm per metre — no drift."""
    doc, _ = _render(tmp_path)
    denom = _printed_h_denom(doc)
    edges = _deck_slab_lines(doc)
    assert edges, "no horizontal SUPER-DECK line — the section did not draw a deck"
    x0 = min(e.dxf.start.x for e in edges)
    x1 = max(e.dxf.end.x for e in edges)
    drawn_mm_per_m = (x1 - x0) / TOTAL_M
    assert drawn_mm_per_m == pytest.approx(1000.0 / denom, rel=1e-6), (
        f"deck drawn at {drawn_mm_per_m:.4f} mm/m but captioned 1:{denom}"
    )


def test_caption_agrees_with_the_shared_fit(tmp_path):
    """The rung printed is the one ``choose_fit`` would pick for this view."""
    doc, project = _render(tmp_path)
    app_l = float(project.substructure.approach_slab_length_m or 3.5)
    # Same draw width the sheet uses: sheet width less the level axis, margins
    # and the right-hand label gutter.
    draw_w = 841.0 - (10.0 + 30.0 + 5.0) - 10.0 - 60.0
    expected = choose_fit(TOTAL_M + 2 * app_l, draw_w, NSPAN + 2)
    assert _printed_h_denom(doc) == expected.denom


def test_text_never_plunges_below_the_legibility_floor(tmp_path):
    """Every glyph clears the hard IRC floor, and the *base* height still
    targets ``fit.MIN_TEXT_MM``.

    Two different numbers are in play and conflating them is how this test
    first went wrong. ``fit.MIN_TEXT_MM`` (2.5) is the *annotation target* the
    ladder is chosen against; the primitive funnel clamps every height to
    ``primitives.MIN_TEXT_HEIGHT_MM`` (1.8), the IRC SP:55 hard floor. Sheet 2
    deliberately demotes a few sub-labels (the survey RLs at ``th * 0.55``)
    below the target — that is allowed — but no glyph may fall through the
    floor, and the pier label (drawn at the base ``th``) must stay at target.
    """
    from bridgecad_draw.primitives import MIN_TEXT_HEIGHT_MM as FLOOR

    doc, _ = _render(tmp_path)
    heights = [
        e.dxf.height
        for e in doc.modelspace()
        if e.dxftype() == "TEXT" and e.dxf.get("height")
    ]
    assert heights, "no text on the sheet"
    assert min(heights) >= FLOOR - 1e-9, f"text height {min(heights)} below IRC floor {FLOOR}"

    pier = [e for e in doc.modelspace() if e.dxftype() == "TEXT" and e.dxf.text == "P1"]
    assert pier, "no P1 pier label — cannot measure the base annotation height"
    assert pier[0].dxf.height >= MIN_TEXT_MM - 1e-9, (
        f"base annotation height {pier[0].dxf.height} under the {MIN_TEXT_MM} target"
    )


def test_vertical_exaggeration_is_actually_applied(tmp_path):
    """A thickness drawn through ``sy()`` scales with ``v_exag``; the old form
    cancelled it and drew a flat section under an exaggerated caption."""
    plain, _ = _render(tmp_path, v_exag=1.0)

    def deck_thickness_mm(doc) -> float:
        ys = {round(e.dxf.start.y, 6) for e in _deck_slab_lines(doc)}
        assert len(ys) == 2, f"expected slab-top and soffit, got {sorted(ys)}"
        return abs(sorted(ys)[1] - sorted(ys)[0])

    ex = tmp_path / "ex.dxf"
    project = contract.make_project("blank", nspan=NSPAN, span_m=SPAN_M)
    S2.generate(project, ex, v_exag=2.0)
    doubled = ezdxf.readfile(str(ex))

    assert deck_thickness_mm(doubled) == pytest.approx(2.0 * deck_thickness_mm(plain), rel=1e-6)


def test_delta_reference_is_one_table_row_per_pier(tmp_path):
    """SS3 §A2 — the eight inline `ΔREF=` strings became one table row each."""
    import re

    doc, _ = _render(tmp_path)
    inline = [t for t in _texts(doc) if t.startswith("ΔREF=")]
    assert not inline, f"inline ΔREF strings survived: {inline[:2]}"
    assert any("T.O.C.RL" in t for t in _texts(doc)), "no consolidated pier table header"
    # One row per internal pier: "P1  100.915  +0.00" — the pier *label* is a
    # bare "P1", which the \\s+\\d distinguishes from a table row.
    rows = [t for t in _texts(doc) if re.match(r"^P\d+\s+\d", t)]
    assert len(rows) == NSPAN - 1, f"expected {NSPAN - 1} pier rows, got {len(rows)}"


def test_a_raft_foundation_draws_no_piles(tmp_path):
    """SS3 §A4 — only a PILE foundation draws piles.

    The blank fixture is itself a pile job, so the gate has to be proven by
    *changing* the foundation type, not by trusting a default that has none.
    """
    from bridgecad_core import types as T

    project = contract.make_project("blank", nspan=NSPAN, span_m=SPAN_M)
    assert project.foundation_details.type == T.FoundationType.PILE, "fixture premise"
    project.foundation_details.type = T.FoundationType.RAFT

    out = tmp_path / "raft.dxf"
    S2.generate(project, out)
    doc = ezdxf.readfile(str(out))
    assert not [e for e in doc.modelspace() if e.dxf.layer == "FOUND-PILE"], (
        "a raft foundation drew a pile group — SS3 §A4 gate is not wired"
    )


def test_box_cell_superstructure_draws_no_piers(tmp_path):
    """A box cell is monolithic: no separate pier shaft or cap."""
    from bridgecad_core import types as T

    project = contract.make_project("blank", nspan=NSPAN, span_m=SPAN_M)
    project.superstructure.type = T.SuperstructureType.BOX_CELL_MULTI
    out = tmp_path / "box.dxf"
    S2.generate(project, out)
    doc = ezdxf.readfile(str(out))
    layers = {e.dxf.layer for e in doc.modelspace()}
    assert "SUB-PIER" not in layers


@pytest.mark.parametrize("valid_cutoff", [False, True])
def test_pile_cutoff_geometry_uses_declared_level(tmp_path, valid_cutoff):
    from decimal import Decimal

    project = contract._build_from_fixture(
        contract._fixture_data("tests/e2e/fixtures/gad_3x18m_skew15.json")
    )
    project.hydraulic_data.actual_soffit_level_m = Decimal("103.8")
    project.project_master.road_level_rl_m = Decimal("105.85")
    project.foundation_details.pile_cutoff_level_m = Decimal(
        "95.0" if valid_cutoff else "110.5"
    )
    out = tmp_path / "checked-cutoff.dxf"
    S2.generate(project, out)
    doc = ezdxf.readfile(out)
    piles = list(doc.modelspace().query('LINE[layer=="FOUND-PILE"]'))
    if not valid_cutoff:
        assert not piles
        assert any("PILE DETAIL OMITTED" in t for t in _texts(doc))
        return

    import re
    denom = float(re.search(r"V Scale 1:([\d.]+)", _caption(doc)).group(1))
    assert piles
    for e in piles:
        y1, y2 = e.dxf.start.y, e.dxf.end.y
        assert y1 > y2
        assert (y1-y2) * denom / 1000 == pytest.approx(
            float(project.foundation_details.pile_length_m), abs=.002
        )


def test_tbeam_span_labels_and_breaks_are_drawn_for_both_articulations(tmp_path):
    from decimal import Decimal
    from bridgecad_core.types import SpanConfiguration

    project = contract._build_from_fixture(
        contract._fixture_data("tests/e2e/fixtures/gad_3x18m_skew15.json")
    )
    project.geometry_input.span_lengths_m = [Decimal("18.75")] * 3
    project.geometry_input.skew_angle_deg = Decimal(0)
    for mode in (SpanConfiguration.SIMPLY_SUPPORTED, SpanConfiguration.CONTINUOUS):
        project.bridge_selection.span_configuration = mode
        out = tmp_path / f"{mode.name}.dxf"
        S2.generate(project, out, scale_denom=100)
        doc = ezdxf.readfile(out)
        assert _texts(doc).count("18.75 m") == 3
        x0 = min(line.dxf.start.x for line in _deck_slab_lines(doc))
        stations = sorted(
            (e.dxf.start.x - x0) / 10
            for e in doc.modelspace().query('LINE[layer=="SUB-EXPJOINT"]')
        )
        assert stations == pytest.approx([18.75, 37.5])
