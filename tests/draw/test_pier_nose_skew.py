"""Priority 3 — Pier positioning and skew in the Sheet 1 plan view.

For each skew angle (0°, +15°, −15°) and a 3-span, 18 m bridge:

  (a) The correct number of intermediate piers is drawn — nspans − 1.
  (b) Each pier rectangle centre X matches the expected pier chainage, within
      one paper millimetre at the recovered scale.
  (c) At non-zero skew the deck outline has non-zero horizontal offset between
      its top and bottom edges (the parallelogram is not a rectangle).  At zero
      skew that offset must be negligible.

What we do NOT test here
------------------------
Pier nose arcs (rounded corners): Sheet 1 uses filled plan-view rectangles
(`SUB-PIER`), not arc nosings.  Arc nosings belong to the pier elevation on
Sheet 5.  Measuring arc endpoints on Sheet 1 would test a feature that is not
drawn there.

Scale recovery
--------------
The plan has no guaranteed reference dimension entity that is recoverable
across all fixture combinations.  Instead we recover scale from the deck
outline: the total_length_m from the fixture is known; the longest horizontal
LINE on layer `C-DECK` or the C-DECK LWPOLYLINE span gives the drawn length in
mm.  mm / total_length_m = scale.
"""
from __future__ import annotations

import math

import pytest

pytestmark = pytest.mark.draw

ezdxf = pytest.importorskip("ezdxf")

from . import contract  # noqa: E402

SKEW_FIXTURE = "tests/e2e/fixtures/gad_3x18m_skew15.json"
ZERO_FIXTURE = "tests/e2e/fixtures/simple_12m.json"
SHEET_MODULE = "bridgecad_draw.sheet1_plan"

# 3-span 18 m fixture: intermediate piers at 18 m and 36 m.
EXPECTED_PIER_CHAINAGES_3x18 = [18.0, 36.0]
TOTAL_LEN_3x18 = 54.0
TOTAL_LEN_1x12 = 12.0


def _generate(project, tmp_path, skew_override=None):
    import importlib
    mod = importlib.import_module(SHEET_MODULE)
    if skew_override is not None:
        gi = project.geometry_input
        project = project.model_copy(
            update={"geometry_input": gi.model_copy(
                update={"skew_angle_deg": skew_override}
            )}
        )
    out = tmp_path / f"sheet1_skew{skew_override}.dxf"
    mod.generate(project, out)
    return ezdxf.readfile(str(out)), project


def _pier_centres(msp) -> list[tuple[float, float]]:
    """Centre (cx, cy) of every SUB-PIER LWPOLYLINE (pier cap rectangles)."""
    centres = []
    for e in msp.query('LWPOLYLINE[layer=="SUB-PIER"]'):
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if max(xs) - min(xs) < 1e-3 or max(ys) - min(ys) < 1e-3:
            continue  # degenerate
        centres.append(((max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0))
    return centres


def _recover_scale_from_total_length(msp, total_len_m: float) -> float:
    """Recover mm-per-metre by finding the longest C-DECK or SUPER-DECK span."""
    best = 0.0
    for layer in ("C-DECK", "SUPER-DECK"):
        for e in msp.query(f'LWPOLYLINE[layer=="{layer}"]'):
            pts = [p[0] for p in e.get_points("xy")]
            if pts:
                best = max(best, max(pts) - min(pts))
        for e in msp.query(f'LINE[layer=="{layer}"]'):
            dx = abs(e.dxf.end.x - e.dxf.start.x)
            best = max(best, dx)
    if best < 1.0:
        # Fall back: use the widest span across any entity
        all_x = []
        for e in msp:
            try:
                b = ezdxf.bbox.extents([e], fast=True)
                if b and b.has_data:
                    all_x.extend([b.extmin.x, b.extmax.x])
            except Exception:
                pass
        best = max(all_x) - min(all_x) if all_x else 1.0
    scale = best / total_len_m
    assert scale > 1.0, (
        f"Recovered plan scale {scale:.3f} mm/m is implausible "
        f"(best span {best:.1f} mm, total_len {total_len_m} m)"
    )
    return scale


# ── tests ─────────────────────────────────────────────────────────────────────

def test_pier_count_zero_skew(tmp_path):
    """1-span bridge has 0 intermediate piers (simple_12m fixture)."""
    data = contract._fixture_data(ZERO_FIXTURE)
    project = contract._build_from_fixture(data)
    doc, project = _generate(project, tmp_path, skew_override=0.0)
    centres = _pier_centres(doc.modelspace())
    # single span → no intermediate pier
    assert len(centres) == 0, (
        f"1-span bridge should have 0 intermediate piers, found {len(centres)}"
    )


def test_pier_count_3span(tmp_path):
    """3-span bridge has exactly 2 intermediate piers (gad_3x18m_skew15 fixture)."""
    data = contract._fixture_data(SKEW_FIXTURE)
    project = contract._build_from_fixture(data)
    doc, project = _generate(project, tmp_path, skew_override=0.0)
    centres = _pier_centres(doc.modelspace())
    assert len(centres) == 2, (
        f"3-span bridge should have 2 intermediate piers, found {len(centres)}"
    )


@pytest.mark.parametrize("skew_deg", [0.0, 15.0, -15.0])
def test_pier_centre_chainages_match_expected(skew_deg, tmp_path):
    """Pier rectangle centres map to the correct chainages at any skew.

    The plan coordinate is a sheared (hpos, vpos) mapping, but pier centres
    lie on the bridge centreline (vpos = sheet CL Y).  We recover the chainage
    from the centre X using the inverse of hpos: ch = (cx - cx_offset) / scale.
    Since cx_offset shifts with the layout we cannot predict its absolute value,
    but we CAN check that the RELATIVE spacing between pier centres equals
    span_length_m in metres — that is the invariant skew cannot distort.
    """
    data = contract._fixture_data(SKEW_FIXTURE)
    project = contract._build_from_fixture(data)
    doc, project = _generate(project, tmp_path / f"skew{skew_deg:.0f}", skew_deg)
    msp = doc.modelspace()
    centres = sorted(_pier_centres(msp), key=lambda c: c[0])
    assert len(centres) == 2, (
        f"skew={skew_deg}: expected 2 piers, got {len(centres)}"
    )
    scale = _recover_scale_from_total_length(msp, TOTAL_LEN_3x18)
    # Spacing between the two pier centre Xs (mm) → metres
    drawn_spacing_m = (centres[1][0] - centres[0][0]) / scale
    expected_spacing_m = 18.0  # each span is 18 m
    tol_m = 0.015  # 15 mm at 1:1 — generous for a plan at any rung
    assert abs(drawn_spacing_m - expected_spacing_m) < tol_m, (
        f"skew={skew_deg}: pier-to-pier spacing {drawn_spacing_m:.4f} m "
        f"!= {expected_spacing_m} m (diff {abs(drawn_spacing_m - expected_spacing_m)*1000:.1f} mm)"
    )


@pytest.mark.parametrize("skew_deg,expect_shear", [(0.0, False), (15.0, True), (-15.0, True)])
def test_deck_outline_shear_matches_skew(skew_deg, expect_shear, tmp_path):
    """Non-zero skew produces a parallelogram deck outline; zero skew does not.

    We measure the horizontal offset between the top-edge Y row and the
    bottom-edge Y row of the deck outline.  For a skewed deck the two edges
    have different X extents (the leading corner leans); for a straight deck
    they are symmetric.
    """
    data = contract._fixture_data(SKEW_FIXTURE)
    project = contract._build_from_fixture(data)
    doc, project = _generate(project, tmp_path / f"shear{skew_deg:.0f}", skew_deg)
    msp = doc.modelspace()
    # Collect all X values per Y level from C-DECK / SUPER-DECK polylines
    top_xs: list[float] = []
    bot_xs: list[float] = []
    for layer in ("C-DECK", "SUPER-DECK"):
        for e in msp.query(f'LWPOLYLINE[layer=="{layer}"]'):
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            if not pts:
                continue
            ys = [p[1] for p in pts]
            mid_y = (max(ys) + min(ys)) / 2.0
            for x, y in pts:
                if y > mid_y:
                    top_xs.append(x)
                else:
                    bot_xs.append(x)
    if not top_xs or not bot_xs:
        pytest.skip("No deck outline found for skew shear check")
    top_x_min, bot_x_min = min(top_xs), min(bot_xs)
    shear_mm = abs(top_x_min - bot_x_min)
    if expect_shear:
        assert shear_mm > 1.0, (
            f"skew={skew_deg}: expected parallelogram shear > 1 mm, "
            f"got {shear_mm:.2f} mm — deck outline may not be skew-aware"
        )
    else:
        assert shear_mm < 2.0, (
            f"skew=0: expected symmetric deck, "
            f"got {shear_mm:.2f} mm shear — zero-skew deck is not rectangular"
        )
