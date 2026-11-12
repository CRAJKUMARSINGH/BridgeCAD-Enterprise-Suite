"""tests/test_asset_pack.py — the asset PDFs must be reproducible as DXF.

Each test asserts a *fact read off the source PDF* against the geometry the
generator places, so a future edit that silently changes a dimension (the
failure mode a plotted PDF cannot catch) fails here instead of at review.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from bridgecad_draw.asset_pack import COVERAGE, build_asset_pack  # noqa: E402
from bridgecad_draw.asset_specs import AMARWADA_SINGLE, PMGSY_SLAB  # noqa: E402


# ---------------------------------------------------------------------------
# Spec-level arithmetic — every value comes from the source sheet
# ---------------------------------------------------------------------------


def test_pmgsy_schedule_is_self_consistent():
    """FRL - BL must reproduce the scheduled 5.015 m height."""
    assert PMGSY_SLAB.height_m == pytest.approx(5.015, abs=1e-6)


def test_pmgsy_soffit_derivation():
    """Soffit = FRL - (75 wearing + 600 slab) = 102.625 - 0.675 = 101.950."""
    assert PMGSY_SLAB.soffit == pytest.approx(101.950, abs=1e-6)


def test_pmgsy_width_stack_closes():
    """Overall 8400 = 7500 carriageway + 2 x 450 kerb."""
    pm = PMGSY_SLAB
    assert pm.deck_width_m * 1000 == pytest.approx(pm.carriageway_m * 1000 + 2 * pm.kerb_mm)


def test_pmgsy_footing_envelopes_match_source():
    """9.3 / 9.9 / 10.5 / 11.1 m are dimensioned on page 3."""
    assert PMGSY_SLAB.pier_steps_m == (9.3, 9.9, 10.5, 11.1)
    for a, b in zip(PMGSY_SLAB.pier_steps_m, PMGSY_SLAB.pier_steps_m[1:]):
        assert b - a == pytest.approx(2 * PMGSY_SLAB.pier_step_m)


def test_pmgsy_pier_count_and_chainages():
    assert len(PMGSY_SLAB.pier_chainages()) == PMGSY_SLAB.spans - 1
    assert PMGSY_SLAB.pier_chainages()[0] == pytest.approx(9.0)
    assert PMGSY_SLAB.length_m == pytest.approx(63.0)


def test_amarwada_levels():
    s = AMARWADA_SINGLE
    assert s.deck_thickness_m == pytest.approx(0.675, abs=1e-6)  # 158.820 - 158.145
    assert sum(s.abut_steps_mm) == pytest.approx(s.abut_face_mm)  # 1523+700+2135 = 4358
    assert s.found_level < s.bed_level < s.hfl < s.soffit < s.frl


# ---------------------------------------------------------------------------
# Generated DXF
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pack(tmp_path_factory) -> dict[str, Path]:
    out = tmp_path_factory.mktemp("asset_pack")
    paths = build_asset_pack(out)
    return {p.stem.replace("ASSET_", ""): p for p in paths}


@pytest.mark.parametrize("stem", list(COVERAGE))
def test_sheet_generates(pack, stem):
    assert stem in pack, f"{stem} not produced"
    p = pack[stem]
    assert p.exists() and p.stat().st_size > 20_000


def test_four_sheets_cover_four_source_pages(pack):
    assert len(pack) == 4


@pytest.mark.parametrize("stem", list(COVERAGE))
def test_sheet_is_a3_and_inside_its_frame(pack, stem):
    doc = ezdxf.readfile(str(pack[stem]))
    msp = doc.modelspace()
    xs, ys = [], []
    for e in msp:
        try:
            if e.dxftype() == "LINE":
                xs += [e.dxf.start.x, e.dxf.end.x]
                ys += [e.dxf.start.y, e.dxf.end.y]
            elif e.dxftype() in ("LWPOLYLINE", "POLYLINE"):
                for pt in e.get_points("xy") if e.dxftype() == "LWPOLYLINE" else []:
                    xs.append(pt[0])
                    ys.append(pt[1])
            elif e.dxftype() in ("TEXT", "MTEXT"):
                ip = e.dxf.insert
                xs.append(ip.x)
                ys.append(ip.y)
            elif e.dxftype() == "CIRCLE":
                xs.append(e.dxf.center.x)
                ys.append(e.dxf.center.y)
        except Exception:
            continue
    assert xs and ys
    assert min(xs) >= -1.0 and max(xs) <= 421.0, f"{stem} escapes the A3 frame in X"
    assert min(ys) >= -1.0 and max(ys) <= 298.0, f"{stem} escapes the A3 frame in Y"


@pytest.mark.parametrize("stem", list(COVERAGE))
def test_sheet_carries_a_filled_title_block(pack, stem):
    doc = ezdxf.readfile(str(pack[stem]))
    texts = [e.dxf.text for e in doc.modelspace().query("TEXT")]
    blob = " ".join(texts).upper()
    for required in ("CLIENT", "DRAWING NO", "SHEET", "SCALE", "TITLE"):
        assert required in blob, f"{stem} title block missing {required!r}"
    assert any("GENERAL ARRANGEMENT" in t.upper() for t in texts)


def test_pmgsy_sheets_quote_the_source_levels(pack):
    """The four scheduled levels must appear verbatim on the PMGSY sheets."""
    blob = ""
    for stem in ("Asset_S1_LSection_Plan", "Asset_S2_DeckSection_Substructure"):
        doc = ezdxf.readfile(str(pack[stem]))
        blob += " ".join(e.dxf.text for e in doc.modelspace().query("TEXT"))
    for value in ("102.625", "97.610", "101.950", "5.015"):
        assert value in blob, f"scheduled value {value} not annotated"


def test_amarwada_sheet_quotes_the_source_levels(pack):
    doc = ezdxf.readfile(str(pack["Asset_S4_SingleSpan_6m"]))
    blob = " ".join(e.dxf.text for e in doc.modelspace().query("TEXT"))
    for value in ("158.820", "158.145", "157.395", "152.450", "10900", "12000"):
        assert value in blob, f"source value {value} not annotated"


@pytest.mark.parametrize("stem", list(COVERAGE))
def test_no_degenerate_geometry(pack, stem):
    """A zero-length line plots as nothing but breaks CAD file health checks."""
    doc = ezdxf.readfile(str(pack[stem]))
    for e in doc.modelspace().query("LINE"):
        d = math.dist((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))
        assert d > 1e-6, f"{stem}: degenerate line at {e.dxf.start}"


@pytest.mark.parametrize("stem", list(COVERAGE))
def test_text_is_plottable(pack, stem):
    """Nothing below 1.2 mm survives a 1:1 A3 plot."""
    doc = ezdxf.readfile(str(pack[stem]))
    heights = [e.dxf.height for e in doc.modelspace().query("TEXT")]
    assert heights, f"{stem} has no annotation"
    assert min(heights) >= 1.2, f"{stem}: text {min(heights)} mm is illegible on A3"


def test_asset_pack_reports_failure_instead_of_partial_output(tmp_path, monkeypatch):
    """A partial pack must raise, never return a silently short list."""
    import bridgecad_draw.asset_pack as ap

    def boom(spec, path):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(ap, "_MANIFEST", [("9", "asset_sheet1_lsection", "X", "pmgsy_slab")])
    monkeypatch.setitem(
        __import__("sys").modules,
        "bridgecad_draw.asset_sheet1_lsection",
        type("M", (), {"generate": staticmethod(boom)}),
    )
    with pytest.raises(ap.AssetPackError):
        build_asset_pack(tmp_path)
