"""Robotic demonstration: a GRAVITY abutment with different earthside and
riverside batters must produce an asymmetric battered profile on Sheet 5.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "e2e" / "fixtures" / "simple_12m.json"


def _project(**sub_over):
    from . import contract

    data = contract._fixture_data("tests/e2e/fixtures/simple_12m.json")
    data["project"]["substructure"].update(sub_over)
    return contract._build_from_fixture(data)


def _section_polys(dxf_path):
    """Closed SUB-ABUT polylines in the abutment-section region (x>560)."""
    import ezdxf

    doc = ezdxf.readfile(str(dxf_path))
    out = []
    for e in doc.modelspace():
        if e.dxftype() != "LWPOLYLINE" or e.dxf.layer != "SUB-ABUT":
            continue
        pts = [(float(v[0]), float(v[1])) for v in e.get_points()]
        if pts and min(x for x, _ in pts) > 560 and max(y for _, y in pts) < 200:
            out.append(pts)
    return out


def test_gravity_abutment_draws_battered_profile(tmp_path):
    from bridgecad_draw.sheet5_pier_abutment_details import generate

    p = _project(
        abutment_type="GRAVITY",
        abutment_face_batter_1n=10,
        abutment_back_batter_1n=3,
    )
    dxf = generate(p, tmp_path / "s5.dxf")
    polys = _section_polys(dxf)
    # The battered stem is the only >8-vertex closed SUB-ABUT polyline there
    battered = [pts for pts in polys if len(pts) >= 10]
    assert battered, "no battered profile polyline found on Sheet 5"
    f_run, b_run = _batter_runs(dxf)
    assert b_run > f_run  # earthside batter steeper than riverside


def _batter_runs(dxf_path):
    """(face_run_mm, back_run_mm) measured off the drawn stem-profile vertices.

    The drawn polyline is the stem+footing sub-polygon:
    0=(x3,capB) 1=(x5,altbl) 2=(x6) 3=(x7) 4=(x7,y8) 5=(x10,y8)
    6=(x10,altbl) 7=(x12,altbl) 8=(x12 dup) 9=(x14,capB) 10=close
    """
    pts = next(q for q in _section_polys(dxf_path) if len(q) >= 10)
    face_run = pts[1][0] - pts[0][0]  # x5 - x3, gentle riverside face
    back_run = pts[9][0] - pts[7][0]  # x14 - x12, steep earthside face
    return abs(face_run), abs(back_run)


def test_batter_values_change_geometry(tmp_path):
    """Gentle (1:20) vs steep (1:4) batters must produce different measured
    batter runs on the sheet — proving the fields drive the drawing."""
    from bridgecad_draw.sheet5_pier_abutment_details import generate

    def runs(**kw):
        p = _project(abutment_type="GRAVITY", **kw)
        dxf = generate(p, tmp_path / f"s5_{len(list(tmp_path.iterdir()))}.dxf")
        return _batter_runs(dxf)

    f_g, b_g = runs(abutment_face_batter_1n=20, abutment_back_batter_1n=20)
    f_s, b_s = runs(abutment_face_batter_1n=4, abutment_back_batter_1n=4)
    assert f_s > f_g and b_s > b_g  # steeper batter → larger run


def test_different_face_and_back_batters_on_sheet(tmp_path):
    """The headline requirement: face and back batters differ on the drawing."""
    from bridgecad_draw.sheet5_pier_abutment_details import generate

    p = _project(
        abutment_type="GRAVITY",
        abutment_face_batter_1n=10,
        abutment_back_batter_1n=3,
    )
    dxf = generate(p, tmp_path / "s5.dxf")
    f_run, b_run = _batter_runs(dxf)
    assert b_run > f_run * 2  # 1:3 back batter is >2× the 1:10 face run


def test_cantilever_fixture_unchanged(tmp_path):
    """Non-GRAVITY abutments keep the rectangular stack (regression guard)."""
    from bridgecad_draw.sheet5_pier_abutment_details import generate

    p = _project()  # fixture default: CANTILEVER
    dxf = generate(p, tmp_path / "s5.dxf")
    polys = _section_polys(dxf)
    assert not [
        pts for pts in polys if len(pts) >= 10
    ], "CANTILEVER abutment should not draw the battered profile"
