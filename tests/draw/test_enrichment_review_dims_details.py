"""Enrichment patch EP-2026-11: review checks, native dims, enlarged details."""
from __future__ import annotations

import io
import json

import ezdxf
import pytest

from bridgecad_ai import drawing_review as dr
from bridgecad_draw import dim_style as ds
from bridgecad_draw import sheet5_enlarged_details as en
from bridgecad_draw import sheet5_pier_abutment_details as s5

from .contract import make_project

pytestmark = pytest.mark.draw


@pytest.fixture(scope="module")
def project():
    return make_project("blank")


@pytest.fixture(scope="module")
def sheet5(project, tmp_path_factory):
    return s5.generate(project, tmp_path_factory.mktemp("s5") / "s5.dxf")


# ── Native dimensions ────────────────────────────────────────────────────
def test_dimlfac_turns_paper_mm_into_site_units():
    assert ds.dimlfac_for(75, "m") == pytest.approx(0.075)
    assert ds.dimlfac_for(75, "mm") == pytest.approx(75.0)


def test_bad_units_rejected():
    with pytest.raises(ValueError):
        ds.DimStyleConfig(units="ft")  # type: ignore[arg-type]


def test_every_dimension_becomes_measured_and_styled(sheet5):
    doc = ezdxf.readfile(sheet5)
    before = len(doc.modelspace().query("DIMENSION"))
    n = ds.apply_native_dimensions(doc, ds.DimStyleConfig(units="m", decimals=3), 75)
    assert n == before > 0
    for d in doc.modelspace().query("DIMENSION"):
        assert d.dxf.text == "<>"
        assert d.dxf.dimstyle == "BRIDGE_DIM"
    st = doc.dimstyles.get("BRIDGE_DIM")
    assert st.dxf.dimdec == 3 and st.dxf.dimpost == "<> m"


def test_changing_units_rescales_displayed_value(sheet5):
    doc = ezdxf.readfile(sheet5)
    ds.apply_native_dimensions(doc, ds.DimStyleConfig(units="m"), 75)
    d = doc.modelspace().query("DIMENSION")[0]
    in_m = ds.displayed_value(d, doc)
    ds.configure_dimstyle(doc, ds.DimStyleConfig(units="mm"), 75)
    assert ds.displayed_value(d, doc) == pytest.approx(in_m * 1000)


# ── Enlarged details ─────────────────────────────────────────────────────
@pytest.mark.parametrize("part", ["pier", "abutment"])
def test_enlarged_sheet_is_larger_scale_than_sheet5(project, tmp_path, part):
    out = en.generate(project, tmp_path / f"{part}.dxf", part=part)
    doc = ezdxf.readfile(out)
    texts = [t.dxf.text for t in doc.modelspace().query("TEXT")]
    scales = {int(m) for t in texts for m in dr._SCALE_RE.findall(t)}
    assert len(scales) == 1, f"one consistent scale expected, got {scales}"
    assert scales.pop() < 75
    assert len(doc.modelspace().query("DIMENSION")) > 0


def test_enlarged_rejects_unknown_part(project, tmp_path):
    with pytest.raises(ValueError):
        en.generate(project, tmp_path / "x.dxf", part="deck")  # type: ignore[arg-type]


def test_pick_scale_prefers_largest_fitting_rung():
    assert en.pick_scale(50, 50) == 10
    assert en.pick_scale(10_000, 10_000) == 75


# ── Drawing review ───────────────────────────────────────────────────────
def test_review_flags_wrong_scale_and_missing_note(sheet5):
    items = dr.review(sheet5, {"scale": "1:100", "required_notes": ["NOTE THAT IS NOT THERE"]})
    by = {i.title: i.status for i in items}
    assert by["Sheet carries dimensions"] == "pass"
    assert by["Stated scale matches requirement"] == "fail"
    assert by["Note present: NOTE THAT IS NOT THERE"] == "fail"


def test_review_passes_correct_scale(sheet5):
    items = dr.review(sheet5, {"scale": "1:75"})
    assert {i.title: i.status for i in items}["Stated scale matches requirement"] == "pass"


def test_ai_missing_key_is_reported_not_raised(sheet5, monkeypatch):
    monkeypatch.delenv("LOVABLE_API_KEY", raising=False)
    items = dr.review(sheet5, {}, use_ai=True)
    assert items[-1].title == "AI review unavailable" and "401" in items[-1].detail


def test_ai_stream_is_parsed_into_items(sheet5):
    payload = json.dumps({"items": [{"title": "Bearing level missing", "detail": "x", "severity": "major"}]})
    stream = io.BytesIO(
        b'data: {"type":"response.output_text.delta","delta":' + json.dumps(payload).encode() + b"}\n\n"
        b'data: {"type":"response.completed"}\n\n'
    )

    class _Resp:
        def __enter__(self):
            return stream

        def __exit__(self, *a):
            return False

    facts = dr.extract_facts(sheet5)
    out = dr.ai_checks(facts, {}, [], api_key="k", opener=lambda r: _Resp())
    assert [(i.title, i.source) for i in out] == [("Bearing level missing", "ai")]
