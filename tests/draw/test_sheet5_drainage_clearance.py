"""Priority 2 — Support and drainage consistency across Sheet 5 views.

Extends the existing diameter-parity test with structural checks:
  (a) every depicted weep-hole outlet centre lies within the vertical extent
      of the wall it is drawn inside (not floating above or below the wall);
  (b) the spacing note text on the sheet agrees with the configured
      weep_hole_spacing_m value;
  (c) the longitudinal and transverse hole diameters are identical (existing
      coverage, restated here as an explicit invariant with its own fixture).

The existing test_dirt_wall_weep_diameter.py verifies that the two views
agree on the drawn radius; this file verifies positional correctness — that
each outlet is inside its wall.

Design decisions
----------------
Scale is recovered from the same horizontal dimensioned cap line used in the
existing test (the single horizontal LINE on ABUT-PROF whose Y values are
equal).  Wall extents are derived from the ABUT-PROF CIRCLE centres plus the
recovered radius: a circle that starts above or ends below the wall rectangle
is a drainage outlet placed outside the structure.

We check that every circle centre Y lies between the bottom of the wall
rectangle (the minimum Y of any ABUT-PROF polyline in the same horizontal
band) and the top of the wall (cap_top line Y), with 1 mm tolerance.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.draw

ezdxf = pytest.importorskip("ezdxf")

from . import contract  # noqa: E402
from bridgecad_draw import sheet5_pier_abutment_details as sheet5  # noqa: E402

FIXTURE = "tests/e2e/fixtures/simple_12m.json"


def _build(tmp_path, diameter_mm: float = 100, spacing_m: float = 1.5):
    data = contract._fixture_data(FIXTURE)
    project = contract._build_from_fixture(data)
    project.substructure.weep_hole_diameter_mm = diameter_mm
    project.substructure.weep_hole_spacing_m = spacing_m
    out = tmp_path / "sheet5_drain.dxf"
    sheet5.generate(project, out)
    doc = ezdxf.readfile(str(out))
    return doc, project


def _recover_scale(msp, abutment_length_m: float) -> float:
    cap_lines = [
        e for e in msp.query('LINE[layer=="ABUT-PROF"]')
        if abs(e.dxf.start.y - e.dxf.end.y) < 1e-6
    ]
    assert cap_lines, "Cannot recover scale — no horizontal ABUT-PROF line found."
    cap = cap_lines[0]
    drawn_mm = abs(cap.dxf.end.x - cap.dxf.start.x)
    return drawn_mm / abutment_length_m  # mm per metre


def _wall_y_bounds(msp, cx_band: float, band_tol: float = 50.0) -> tuple[float, float]:
    """Y extent of ABUT-PROF polylines whose X centre is within band_tol of cx_band."""
    ys_all: list[float] = []
    for e in msp.query('LWPOLYLINE[layer=="ABUT-PROF"]'):
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if not pts:
            continue
        poly_cx = (max(p[0] for p in pts) + min(p[0] for p in pts)) / 2.0
        if abs(poly_cx - cx_band) < band_tol:
            ys_all.extend(p[1] for p in pts)
    if not ys_all:
        return (float("-inf"), float("inf"))  # no bound → skip positional check
    return min(ys_all), max(ys_all)


# ── tests ─────────────────────────────────────────────────────────────────────

def test_every_outlet_centre_is_inside_wall(tmp_path):
    """Each ABUT-PROF CIRCLE centre Y must lie within the wall's Y extent.

    A circle placed above the wall top or below the wall base is a drainage
    outlet drawn outside the structure — a construction impossibility.
    """
    doc, project = _build(tmp_path, diameter_mm=100)
    msp = doc.modelspace()
    scale = _recover_scale(msp, float(project.substructure.abutment_length_m))
    tol_mm = 1.0  # 1 mm on paper

    holes = list(msp.query('CIRCLE[layer=="ABUT-PROF"]'))
    assert holes, "No ABUT-PROF circles found — outlets not drawn."

    for hole in holes:
        cx = hole.dxf.center.x
        cy = hole.dxf.center.y
        y_bot, y_top = _wall_y_bounds(msp, cx)
        if y_bot == float("-inf"):
            continue  # no polyline in this band — cannot check
        assert cy >= y_bot - tol_mm, (
            f"Outlet centre Y={cy:.2f} is {y_bot - cy:.2f} mm BELOW the wall "
            f"bottom Y={y_bot:.2f} — outlet is outside the wall."
        )
        assert cy <= y_top + tol_mm, (
            f"Outlet centre Y={cy:.2f} is {cy - y_top:.2f} mm ABOVE the wall "
            f"top Y={y_top:.2f} — outlet is outside the wall."
        )


def test_spacing_note_matches_configured_value(tmp_path):
    """The spacing note text on the sheet must reflect weep_hole_spacing_m."""
    for spacing_m in (1.0, 1.5, 2.0):
        doc, project = _build(tmp_path / f"sp{spacing_m}", spacing_m=spacing_m)
        msp = doc.modelspace()
        texts = [
            e.dxf.text for e in msp.query("TEXT")
            if "WEEP" in str(e.dxf.text).upper()
        ]
        assert texts, f"No weep-hole note found on the sheet (spacing={spacing_m})"
        # Note must contain the spacing value rendered to 1 decimal place
        note = " ".join(texts).upper()
        expected = f"{spacing_m:.1f}"
        assert expected in note, (
            f"Spacing note does not contain '{expected}' m c/c "
            f"for configured spacing {spacing_m} m.\nNote: {note}"
        )


def test_transverse_and_longitudinal_diameters_agree(tmp_path):
    """Both views must draw circles whose radius equals weep_hole_diameter_mm / 2.

    This restates the existing invariant as an explicit named check: when the
    two views use different hard-coded radii the longitudinal view is correct
    and the transverse view is wrong (the pre-patch bug).
    """
    for dia_mm in (50, 100, 150):
        doc, project = _build(tmp_path / f"dia{dia_mm}", diameter_mm=dia_mm)
        msp = doc.modelspace()
        scale = _recover_scale(msp, float(project.substructure.abutment_length_m))
        holes = list(msp.query('CIRCLE[layer=="ABUT-PROF"]'))
        assert len(holes) == 4, (
            f"dia={dia_mm}: expected 4 outlets (2 per view), got {len(holes)}"
        )
        # Partition into transverse (y > 200) and longitudinal (y < 200) view bands
        transverse = [h for h in holes if h.dxf.center.y > 200]
        longitudinal = [h for h in holes if h.dxf.center.y < 200]
        assert transverse and longitudinal, \
            "Cannot separate transverse and longitudinal view outlets by Y."
        expected_m = dia_mm / 1000.0
        for h in holes:
            drawn_m = 2 * h.dxf.radius / scale
            assert drawn_m == pytest.approx(expected_m, abs=1e-4), (
                f"dia={dia_mm}: outlet radius {drawn_m * 1000:.2f} mm "
                f"!= {dia_mm / 2:.1f} mm in view y={h.dxf.center.y:.0f}"
            )
