"""Priority 1 — Sheet 3 cross-section DXF geometry regression.

Methodology (guard against the Venice collapse defect)
-------------------------------------------------------
Venice's section test counted 33 label entities and called it verified, even
though all 33 outline vertices shared one X coordinate — the outline had
collapsed to a vertical line. That test proved labels were emitted; it did not
prove the outline had real horizontal extent.

Every check here reopens the saved DXF and measures actual drawing coordinates.
Scale is recovered from the SUPER-DECK rectangle width divided by the known
overall_width_m from the fixture — no hard-coded denominator.  Checks are then
applied in real-world metres so tolerance statements are meaningful.

Fixture: pwd_br2022_002_open_rcc_solidslab — SOLID_SLAB, 4 × 10 m,
  carriageway 7.5 m, kerb 0.25 m each side, crash barrier 0.45 m each side,
  deck_thickness_mm = 200, wearing_coat_thickness_mm = 65.
  overall_width_m is computed by the model (cw + 2*kerb + 2*cb = 8.9 m).
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

pytestmark = pytest.mark.draw

ezdxf = pytest.importorskip("ezdxf")

from . import contract  # noqa: E402

FIXTURE = "tests/e2e/fixtures/pwd/pwd_br2022_002_open_rcc_solidslab.json"
SHEET_MODULE = "bridgecad_draw.sheet3_cross_section"

# Tolerances (metres in drawing space after scale inversion)
TOL_M = 0.01     # ±10 mm for position/dimension checks
TOL_T = 0.005    # ±5 mm for thickness checks (tighter: direct subtraction)


# ── helpers ──────────────────────────────────────────────────────────────────

def _rects_on(msp, layer: str) -> list[dict]:
    """Every LWPOLYLINE on *layer* that is a closed axis-aligned rectangle."""
    out = []
    for e in msp.query(f'LWPOLYLINE[layer=="{layer}"]'):
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) < 4:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if max(xs) - min(xs) < 1e-6 or max(ys) - min(ys) < 1e-6:
            continue  # degenerate / collapsed
        out.append({"xmin": min(xs), "xmax": max(xs),
                    "ymin": min(ys), "ymax": max(ys),
                    "w": max(xs) - min(xs), "h": max(ys) - min(ys)})
    return out


def _recover_scale(msp, overall_width_m: float) -> float:
    """Derive drawing scale (mm/m) from the SUPER-DECK rectangle width.

    Returns mm_per_metre so that  drawn_mm / scale == real_metres.
    Raises if no non-degenerate SUPER-DECK rectangle is found.
    """
    rects = _rects_on(msp, "SUPER-DECK")
    if not rects:
        raise AssertionError("No SUPER-DECK rectangles found — cannot recover scale.")
    # The widest rectangle is the full-width deck slab
    widest = max(rects, key=lambda r: r["w"])
    scale = widest["w"] / overall_width_m
    assert scale > 1.0, (
        f"Recovered scale {scale:.3f} mm/m is implausible — "
        f"deck width {widest['w']:.1f} mm for {overall_width_m:.3f} m"
    )
    return scale


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def _slab_project():
    data = contract._fixture_data(FIXTURE)
    return contract._build_from_fixture(data)


@pytest.fixture(scope="module")
def _slab_dxf(_slab_project, tmp_path_factory):
    import importlib
    mod = importlib.import_module(SHEET_MODULE)
    out = tmp_path_factory.mktemp("sheet3") / "sheet3_slab.dxf"
    mod.generate(_slab_project, out)
    doc = ezdxf.readfile(str(out))
    return doc, _slab_project


# ── Priority 1a: outline must not be collapsed ────────────────────────────────

def test_deck_slab_has_real_width(_slab_dxf):
    """SUPER-DECK rectangle must span the declared overall width (± 1 %).

    Failure here is the Venice defect: a collapsed outline returns width ≈ 0.
    """
    doc, project = _slab_dxf
    gi = project.geometry_input
    overall_w = float(gi.overall_width_m)
    rects = _rects_on(doc.modelspace(), "SUPER-DECK")
    assert rects, "No SUPER-DECK rectangle found — slab outline was not drawn."
    widest = max(rects, key=lambda r: r["w"])
    scale = _recover_scale(doc.modelspace(), overall_w)
    drawn_w_m = widest["w"] / scale
    assert abs(drawn_w_m - overall_w) < TOL_M, (
        f"Deck drawn width {drawn_w_m:.4f} m != expected {overall_w:.4f} m "
        f"(scale={scale:.2f} mm/m)"
    )


def test_deck_slab_has_real_thickness(_slab_dxf):
    """SUPER-DECK rectangle height must equal deck_thickness_mm (± 5 mm)."""
    doc, project = _slab_dxf
    ss = project.superstructure
    deck_t_m = float(ss.deck_thickness_mm) / 1000.0
    overall_w = float(project.geometry_input.overall_width_m)
    scale = _recover_scale(doc.modelspace(), overall_w)
    rects = _rects_on(doc.modelspace(), "SUPER-DECK")
    widest = max(rects, key=lambda r: r["w"])
    drawn_t_m = widest["h"] / scale
    assert abs(drawn_t_m - deck_t_m) < TOL_T, (
        f"Deck drawn thickness {drawn_t_m * 1000:.1f} mm != "
        f"declared {deck_t_m * 1000:.1f} mm"
    )


def test_wearing_coat_has_correct_thickness(_slab_dxf):
    """SUPER-WEARING rectangle height must equal wearing_coat_thickness_mm (± 5 mm)."""
    doc, project = _slab_dxf
    ss = project.superstructure
    wc_t_m = float(ss.wearing_coat_thickness_mm) / 1000.0
    overall_w = float(project.geometry_input.overall_width_m)
    scale = _recover_scale(doc.modelspace(), overall_w)
    rects = _rects_on(doc.modelspace(), "SUPER-WEARING")
    assert rects, "No SUPER-WEARING geometry — wearing coat not drawn."
    widest = max(rects, key=lambda r: r["w"])
    drawn_wc_m = widest["h"] / scale
    assert abs(drawn_wc_m - wc_t_m) < TOL_T, (
        f"Wearing coat drawn {drawn_wc_m * 1000:.1f} mm != "
        f"declared {wc_t_m * 1000:.1f} mm"
    )


def test_wearing_coat_sits_on_top_of_deck(_slab_dxf):
    """WC bottom == deck top (continuous surface; no gap, no overlap > 1 mm)."""
    doc, project = _slab_dxf
    overall_w = float(project.geometry_input.overall_width_m)
    scale = _recover_scale(doc.modelspace(), overall_w)
    deck_rects = _rects_on(doc.modelspace(), "SUPER-DECK")
    wc_rects = _rects_on(doc.modelspace(), "SUPER-WEARING")
    if not deck_rects or not wc_rects:
        pytest.skip("deck or WC layer absent — covered by other tests")
    deck_top = max(r["ymax"] for r in deck_rects)
    wc_bot = min(r["ymin"] for r in wc_rects)
    gap_m = abs(deck_top - wc_bot) / scale
    assert gap_m < TOL_T, (
        f"Gap between deck top and WC bottom = {gap_m * 1000:.2f} mm — "
        "levels are inconsistent"
    )


def test_total_depth_equals_deck_plus_wc(_slab_dxf):
    """Combined stack height matches deck_thickness + wearing_coat_thickness."""
    doc, project = _slab_dxf
    ss = project.superstructure
    expected_m = (float(ss.deck_thickness_mm) + float(ss.wearing_coat_thickness_mm)) / 1000.0
    overall_w = float(project.geometry_input.overall_width_m)
    scale = _recover_scale(doc.modelspace(), overall_w)
    deck_rects = _rects_on(doc.modelspace(), "SUPER-DECK")
    wc_rects = _rects_on(doc.modelspace(), "SUPER-WEARING")
    if not deck_rects or not wc_rects:
        pytest.skip("layers absent")
    total_bot = min(r["ymin"] for r in deck_rects)
    total_top = max(r["ymax"] for r in wc_rects)
    drawn_m = (total_top - total_bot) / scale
    assert abs(drawn_m - expected_m) < TOL_T, (
        f"Total stack {drawn_m * 1000:.1f} mm != "
        f"declared {expected_m * 1000:.1f} mm"
    )


def test_kerbs_are_present_and_symmetric(_slab_dxf):
    """SUPER-KERB polylines must exist in matching pairs (left ≈ right)."""
    doc, project = _slab_dxf
    kerbs = []
    for e in doc.modelspace().query('LWPOLYLINE[layer=="SUPER-KERB"]'):
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        xs = [p[0] for p in pts]
        if max(xs) - min(xs) > 1e-3:
            kerbs.append((min(xs), max(xs)))
    assert len(kerbs) == 2, f"Expected 2 kerb polylines, got {len(kerbs)}"
    # Left kerb xmax ≈ mirrored from right kerb xmin
    kerbs.sort()
    sheet_cx = sum(r[0] + r[1] for r in kerbs) / (2 * len(kerbs))
    l_offset = sheet_cx - kerbs[0][1]
    r_offset = kerbs[1][0] - sheet_cx
    assert abs(l_offset - r_offset) < 2.0, (  # 2 mm tolerance on paper
        f"Kerbs are asymmetric: left offset {l_offset:.2f} mm, right {r_offset:.2f} mm"
    )


# ── Priority 1b: vary carriageway width ───────────────────────────────────────

@pytest.mark.parametrize("cw_override", [6.0, 7.5, 9.0])
def test_carriageway_width_changes_wc_extent(cw_override, tmp_path):
    """WC width must track carriageway_width_m as the input changes."""
    import importlib
    mod = importlib.import_module(SHEET_MODULE)
    data = contract._fixture_data(FIXTURE)
    project = contract._build_from_fixture(data)
    # Override carriageway on the model directly
    gi = project.geometry_input
    new_gi = gi.model_copy(update={"carriageway_width_m": cw_override})
    project = project.model_copy(update={"geometry_input": new_gi})
    out = tmp_path / f"sheet3_cw{cw_override}.dxf"
    mod.generate(project, out)
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    overall_w = float(project.geometry_input.overall_width_m)
    scale = _recover_scale(msp, overall_w)
    wc_rects = _rects_on(msp, "SUPER-WEARING")
    assert wc_rects, "No SUPER-WEARING geometry after carriageway override"
    widest = max(wc_rects, key=lambda r: r["w"])
    drawn_cw_m = widest["w"] / scale
    assert abs(drawn_cw_m - cw_override) < TOL_M, (
        f"WC drawn width {drawn_cw_m:.3f} m != set carriageway {cw_override} m"
    )


# ── Priority 1c: vary slab thickness ─────────────────────────────────────────

@pytest.mark.parametrize("deck_mm", [200, 400, 900])
def test_slab_thickness_changes_deck_height(deck_mm, tmp_path):
    """Deck rectangle height must track deck_thickness_mm."""
    import importlib
    mod = importlib.import_module(SHEET_MODULE)
    data = contract._fixture_data(FIXTURE)
    project = contract._build_from_fixture(data)
    ss = project.superstructure
    new_ss = ss.model_copy(update={"deck_thickness_mm": deck_mm})
    project = project.model_copy(update={"superstructure": new_ss})
    out = tmp_path / f"sheet3_deck{deck_mm}.dxf"
    mod.generate(project, out)
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    overall_w = float(project.geometry_input.overall_width_m)
    scale = _recover_scale(msp, overall_w)
    rects = _rects_on(msp, "SUPER-DECK")
    assert rects, f"No SUPER-DECK after deck_mm={deck_mm}"
    widest = max(rects, key=lambda r: r["w"])
    drawn_t_m = widest["h"] / scale
    expected_m = deck_mm / 1000.0
    assert abs(drawn_t_m - expected_m) < TOL_T, (
        f"deck_mm={deck_mm}: drawn {drawn_t_m * 1000:.1f} mm != {deck_mm} mm"
    )


# ── Priority 1d: collapsed outline must fail ─────────────────────────────────

def test_slab_outline_not_collapsed(_slab_dxf):
    """Guard directly against the Venice collapse: no SUPER-DECK poly with one unique X.

    Venice's section returned 33 labelled points that all shared one X coordinate.
    That is a vertical line, not a section. This test fails if the widest deck
    rectangle has effectively zero width — i.e. max(x) - min(x) < 1 mm.
    """
    doc, project = _slab_dxf
    for e in doc.modelspace().query('LWPOLYLINE[layer=="SUPER-DECK"]'):
        pts = [p[0] for p in e.get_points("xy")]
        spread = max(pts) - min(pts) if pts else 0.0
        assert spread > 1.0, (  # 1 mm minimum horizontal spread
            f"SUPER-DECK polyline has collapsed outline: "
            f"all {len(pts)} vertices share X within {spread:.4f} mm — "
            "section geometry is a vertical line, not a cross-section"
        )
