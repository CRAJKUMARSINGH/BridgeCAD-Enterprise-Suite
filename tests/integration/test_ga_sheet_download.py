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
    from bridgecad_core.types import SpanConfiguration
    from bridgecad_io.excel_reader import read_excel
    from bridgecad_io.excel_writer import write_excel

    root = Path(__file__).resolve().parents[2]
    project = read_excel(root / "frontend/public/samples/sample_input.xlsx")
    payload = project.model_dump(round_trip=True)
    payload["geometry_input"].update(span_count=3, span_lengths_m=[Decimal("18.75")] * 3)
    payload["geometry_input"].update(footpath_left_m=Decimal("2.05"), footpath_right_m=Decimal("2.05"), kerb_width_left_m=Decimal("0.45"), kerb_width_right_m=Decimal("0.45"))
    payload["bridge_selection"].update(span_count=3, span_configuration=SpanConfiguration.CONTINUOUS)
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

    def upload(**query):
        path = write_excel(project, tmp_path / "input.xlsx")
        return client.post("/draw/ga", params=query, files={"excel_file": (path.name, path.read_bytes())})

    response = upload()
    assert response.status_code == 200, response.text[:400]
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["cache-control"] == "no-store"
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
        p1, p2 = [100 + station*1000/ga_scale for station in (18.75, 37.5)]
        assert _pier_joint_x(paths, paper) == pytest.approx([p1, p1, p2, p2], abs=.01)
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
                assert paper(top_flanges[0].width) * section_scale == pytest.approx(500, abs=.2)
                if girder_type == "I_GIRDER_PSC":
                    assert r.width == pytest.approx(top_flanges[0].width, abs=.01)
                else:
                    assert r.width < top_flanges[0].width

    for kind, label in (("CANTILEVER", "Cantilever"), ("GRAVITY", "Gravity"),
                        ("FULL_HEIGHT_WALL", "Full-height wall")):
        selected = upload(abutment_type=kind)
        assert selected.status_code == 200, selected.text[:400]
        with pymupdf.open(stream=selected.content, filetype="pdf") as pdf:
            assert f"A1 / A2: {label}" in pdf[0].get_text()
            outlines = [path for path in pdf[0].get_drawings()
                        if path["fill"] == pytest.approx((196/255, 214/255, 223/255), abs=.002)]
            assert len(outlines) == 4  # two plan footprints and two elevation profiles
            for footprint, elevation in zip(outlines[:2], outlines[2:]):
                assert footprint["rect"].x0 == pytest.approx(elevation["rect"].x0, abs=.05)
                assert footprint["rect"].x1 == pytest.approx(elevation["rect"].x1, abs=.05)
            if kind == "GRAVITY":
                assert all(len(profile["items"]) >= 12 for profile in outlines[2:])
                assert "Footing 1.0 m thick" in pdf[0].get_text()
            elif kind == "FULL_HEIGHT_WALL":
                assert all(path["items"][0][0] == "re" for path in outlines[2:])
            else:
                left, right = outlines[2:]
                def vertices(path):
                    return {(round(point.x, 3), round(point.y, 3)) for op, *points in path["items"]
                            if op == "l" for point in points}

                left_points, right_points = vertices(left), vertices(right)
                assert len(left_points) == len(right_points) == 8
                mirror_sum = left["rect"].x0 + right["rect"].x1
                for x, y in left_points:
                    assert any(abs(x + xx - mirror_sum) < .01 and abs(y - yy) < .01 for xx, yy in right_points)

    if not depth:
        path = write_excel(project, tmp_path / "a1.xlsx")
        via_predict = client.post("/predict?output_format=ga_pdf&abutment_type=GRAVITY",
                                  files={"excel_file": (path.name, path.read_bytes())})
        assert via_predict.status_code == 200, via_predict.text[:400]
        with pymupdf.open(stream=via_predict.content, filetype="pdf") as pdf:
            assert "A1 / A2: Gravity" in pdf[0].get_text()

        from bridgecad_core.models import ExpansionJointScheduleRow
        from bridgecad_core.types import ExpansionJointType

        def joint_lines(response):
            assert response.status_code == 200, response.text[:400]
            with pymupdf.open(stream=response.content, filetype="pdf") as pdf:
                return _pier_joint_x(pdf[0].get_drawings(), paper)

        project.bridge_selection.span_configuration = SpanConfiguration.SIMPLY_SUPPORTED
        assert joint_lines(upload()) == pytest.approx([p1, p1, p2, p2], abs=.01)
        project.bridge_selection.span_configuration = SpanConfiguration.CONTINUOUS
        project.bearings_joints.expansion_joint_schedule = [ExpansionJointScheduleRow(
            location="P2 centreline", joint_type=ExpansionJointType.COMPRESSION_SEAL, gap_mm=50,
        )]
        half_gap = 25 / ga_scale
        assert joint_lines(upload()) == pytest.approx(
            [p1, p1, p2-half_gap, p2-half_gap, p2+half_gap, p2+half_gap], abs=.01,
        )
    assert upload(abutment_type="COUNTERFORT").status_code == 422

    project.hydraulic_data.actual_soffit_level_m -= Decimal("0.3")
    rejected = upload()
    assert rejected.status_code == 422
    assert "reconcile" in rejected.text

    if depth:
        project.hydraulic_data.actual_soffit_level_m += Decimal("0.3")
        project.superstructure.girder_spacing_m = Decimal("1.6")
        rejected = upload()
        assert rejected.status_code == 422
        assert "Girder centres must fit" in rejected.text


def _pier_joint_x(paths, paper):
    return sorted(paper(a.x) for path in paths
                  if path["color"] == pytest.approx((150/255, 61/255, 45/255), abs=.002)
                  for op, a, z in path["items"] if op == "l" and a.x == z.x)
