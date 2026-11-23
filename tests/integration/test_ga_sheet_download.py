"""Exercise workbook upload and verify the actual A1 GA response."""
from decimal import Decimal
from pathlib import Path

import pytest


@pytest.mark.parametrize(("family", "girder_type", "depth", "title"), [
    ("SOLID_SLAB", None, 0, "RCC SOLID SLAB"),
    ("RCC_TBEAM", "T_BEAM_RCC", 1800, "RCC T-BEAM"),
    ("PSC_IGIRDER", "I_GIRDER_PSC", 1800, "PSC I-GIRDER"),
    ("PSC_I_GIRDER_COMPOSITE", "I_GIRDER_PSC", 1800, "PSC I-GIRDER"),
])
def test_ga_pdf_download_and_reject_conflicting_soffit(tmp_path, family, girder_type, depth, title):
    pymupdf = pytest.importorskip("pymupdf")
    pytest.importorskip("reportlab")
    from fastapi.testclient import TestClient
    from bridgecad_api.main import app
    from bridgecad_io.excel_reader import read_excel
    from bridgecad_io.excel_writer import write_excel

    root = Path(__file__).resolve().parents[2]
    project = read_excel(root / "frontend/public/samples/sample_input.xlsx")
    payload = project.model_dump(round_trip=True)
    payload["geometry_input"].update(span_count=3, span_lengths_m=[Decimal("18.75")] * 3)
    payload["geometry_input"].update(footpath_left_m=Decimal("2.05"), footpath_right_m=Decimal("2.05"), kerb_width_left_m=Decimal("0.45"), kerb_width_right_m=Decimal("0.45"))
    payload["bridge_selection"]["span_count"] = 3
    slab_mm = 800 if not depth else 200
    payload["superstructure"].update(
        type=family, girder_type=girder_type, deck_thickness_mm=slab_mm,
        girder_depth_mm=depth or None, girders_per_deck_count=9 if depth else None,
        girder_spacing_m=Decimal("1.25") if depth else None,
    )
    structure = payload["superstructure"]
    payload["hydraulic_data"]["actual_soffit_level_m"] = (
        project.project_master.road_level_rl_m
        - Decimal(slab_mm + depth + (structure["wearing_coat_thickness_mm"] or 0)) / 1000
    )
    payload["hydraulic_data"].update(hfl_m=Decimal("106.5"), lwl_m=Decimal("105.5"),
                                    scour_level_m=Decimal("104.0"))
    project = type(project).model_validate(payload)
    client = TestClient(app)

    def upload():
        path = write_excel(project, tmp_path / "input.xlsx")
        return client.post("/draw/ga", files={"excel_file": (path.name, path.read_bytes())})

    response = upload()
    assert response.status_code == 200, response.text[:400]
    assert response.headers["content-type"] == "application/pdf"
    assert "GA-01-A1.pdf" in response.headers["content-disposition"]
    with pymupdf.open(stream=response.content, filetype="pdf") as pdf:
        assert len(pdf) == 1
        assert pdf[0].rect.width * 25.4 / 72 == pytest.approx(841, abs=.01)
        assert pdf[0].rect.height * 25.4 / 72 == pytest.approx(594, abs=.01)
        text = pdf[0].get_text()
        for marker in ("01  PLAN", "02  LONGITUDINAL ELEVATION", "03  TYPICAL CROSS-SECTION",
                       "56.250 m", title, "REVIEW DRAFT"):
            assert marker in text

        # Read vector geometry from the response, in paper millimetres.
        import re

        ga_scale = int(re.search(r"01  PLAN  /  1:(\d+)", text)[1])
        section_scale = int(re.search(r"03  TYPICAL CROSS-SECTION  /  1:(\d+)", text)[1])
        paper = lambda points: points * 25.4 / 72
        paths = pdf[0].get_drawings()
        axes = [
            (paper(a.x), paper(z.x), paper(a.y))
            for path in paths if abs(paper(path["width"] or 0) - .15) < .001
            for op, a, z in [item for item in path["items"] if item[0] == "l"]
        ]
        assert len(axes) == (27 if depth else 0)
        if depth:
            pitch = 1.25 * 1000 / ga_scale
            for i in range(3):
                expected_x = 100 + i * 18750 / ga_scale
                span_axes = sorted(y for x, z, y in axes if abs(x - expected_x) < .01
                                   and abs(z - x - 18750 / ga_scale) < .01)
                assert len(span_axes) == 9
                assert [y - span_axes[0] for y in span_axes] == pytest.approx(
                    [j * pitch for j in range(9)], abs=.01,
                )

        slab_bottom = 594 - 103 + slab_mm / section_scale
        soffit = slab_bottom + depth / section_scale
        rects = [item[1] for path in paths for item in path["items"] if item[0] == "re"]
        assert any(abs(paper(r.x0) - 46) < .01 and abs(paper(r.y1) - slab_bottom) < .01
                   and abs(paper(r.width) - 12500 / section_scale) < .01 for r in rects)
        girder_parts = [r for r in rects if paper(r.y0) >= slab_bottom - .01
                        and abs(paper(r.y1) - soffit) < .01]
        assert len(girder_parts) == (9 if depth else 0)
        if depth:
            girder_parts.sort(key=lambda r: r.x0)
            for j, r in enumerate(girder_parts):
                assert paper((r.x0 + r.x1) / 2) == pytest.approx(
                    46 + (1250 + 1250*j) / section_scale, abs=.01,
                )
                top_flanges = [f for f in rects
                               if abs(paper((f.x0 + f.x1 - r.x0 - r.x1) / 2)) < .01
                               and abs(paper(f.y0) - slab_bottom) < .01]
                assert len(top_flanges) == 1
                if girder_type == "I_GIRDER_PSC":
                    assert r.width == pytest.approx(top_flanges[0].width, abs=.01)
                else:
                    assert r.width < top_flanges[0].width

    project.hydraulic_data.actual_soffit_level_m -= Decimal("0.3")
    rejected = upload()
    assert rejected.status_code == 422
    assert "reconcile" in rejected.text
