"""EP-2026-12: wire native dims, export review API, 5A/5B in booklet.

Tests added by this patch:
  - drawing_review importable at package root (G1)
  - native-dimension pass converts hard-typed Sheet-5 labels to "<>" (G2)
  - generate_package returns 11 paths including 5A and 5B (G3)
  - 5A and 5B sheets have DIMENSION entities with text "<>" after the native-dim pass (G2+G3)
"""
from __future__ import annotations

import ezdxf
import pytest

pytestmark = pytest.mark.draw


# ── G1: drawing_review exported from bridgecad_ai package root ──────────────

def test_drawing_review_importable_from_package_root():
    from bridgecad_ai import review, extract_facts, to_markdown, CheckItem, AIReviewError  # noqa: F401


def test_review_function_at_package_root_works(tmp_path):
    """Smoke test: review a minimal valid DXF through the package root export."""
    import ezdxf as _ezdxf
    from bridgecad_ai import review

    doc = _ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_text("Scale 1:75", dxfattribs={"layer": "TEXT-SPEC"})
    p = tmp_path / "smoke.dxf"
    doc.saveas(str(p))
    items = review(str(p), {"scale": "1:75"})
    by = {i.title: i.status for i in items}
    # No DIMENSION entities on this minimal sheet → R01 must fail
    assert by["Sheet carries dimensions"] == "fail"
    # Scale caption matches → R03 passes
    assert by["Stated scale matches requirement"] == "pass"


# ── G2: apply_native_dimensions is called by booklet._apply_native_dims ─────

def test_native_dim_pass_converts_sheet5_labels(tmp_path):
    """After generating Sheet 5 and running the native-dim pass, every
    DIMENSION entity must have text=="<>" (measured, not hard-typed)."""
    from .contract import make_project
    from bridgecad_draw import sheet5_pier_abutment_details as s5
    from bridgecad_draw.booklet import _apply_native_dims

    proj = make_project("blank")
    p = s5.generate(proj, tmp_path / "s5.dxf")
    # Before the pass: dimensions carry hard-typed labels
    doc_before = ezdxf.readfile(str(p))
    dims_before = list(doc_before.modelspace().query("DIMENSION"))
    assert len(dims_before) > 0, "Sheet 5 must produce DIMENSION entities"
    hard_before = sum(
        1 for d in dims_before if (d.dxf.get("text", "<>") or "<>") not in ("<>", "")
    )
    assert hard_before > 0, "Sheet 5 dims should start hard-typed (EP-2026-11 baseline)"

    # Apply the native-dim pass (the same call booklet makes)
    _apply_native_dims(p, 75)

    # After the pass: all dimensions must be measured
    doc_after = ezdxf.readfile(str(p))
    for d in doc_after.modelspace().query("DIMENSION"):
        assert d.dxf.text == "<>", f"DIMENSION text should be '<>' after pass, got {d.dxf.text!r}"
        assert d.dxf.dimstyle == "BRIDGE_DIM"


# ── G3: generate_package returns 11 paths, including 5A and 5B ──────────────

def test_booklet_generates_11_sheets(tmp_path):
    """generate_package must return 11 paths (9 original + 5A + 5B)."""
    from .contract import make_project
    from bridgecad_draw.booklet import generate_package

    proj = make_project("blank")
    paths = generate_package(proj, tmp_path / "pkg")
    assert len(paths) == 11, f"Expected 11 sheets, got {len(paths)}: {[p.name for p in paths]}"


def test_booklet_5A_stem_present(tmp_path):
    from .contract import make_project
    from bridgecad_draw.booklet import generate_package

    proj = make_project("blank")
    paths = generate_package(proj, tmp_path / "pkg5A")
    stems = {p.stem for p in paths}
    assert any("Sheet5A" in s for s in stems), f"Sheet5A not found in {stems}"
    assert any("Sheet5B" in s for s in stems), f"Sheet5B not found in {stems}"


def test_sheet5A_5B_are_dimensioned_after_native_dim_pass(tmp_path):
    """Sheets 5A and 5B must have DIMENSION entities with text '<>' after package generation."""
    import re

    from .contract import make_project
    from bridgecad_draw.booklet import generate_package

    proj = make_project("blank")
    paths = generate_package(proj, tmp_path / "pkg_dim")
    for p in paths:
        if "Sheet5A" in p.stem or "Sheet5B" in p.stem:
            doc = ezdxf.readfile(str(p))
            titles = [e.dxf.text for e in doc.modelspace().query('TEXT[layer=="TEXT-TITLE"]')]
            scale = next(int(match[1]) for title in titles if (match := re.search(r"SCALE 1:(\d+)", title)))
            dims = list(doc.modelspace().query("DIMENSION"))
            assert len(dims) > 0, f"{p.name} has no DIMENSION entities"
            for d in dims:
                assert d.dxf.text == "<>", (
                    f"{p.name}: DIMENSION text should be '<>' after native-dim pass, "
                    f"got {d.dxf.text!r}"
                )
                assert doc.dimstyles.get(d.dxf.dimstyle).dxf.dimlfac == pytest.approx(scale / 1000)
