"""Browser downloads must return actual drawings from the sample workbook."""

from importlib import import_module
from io import BytesIO
from pathlib import Path
import re
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKBOOK = ROOT / "frontend/public/samples/sample_input.xlsx"


@pytest.mark.parametrize("module", ["bridgecad_api.main", "bridge_gad.api"])
def test_sample_workbook_predict_downloads_complete_pdf(monkeypatch, module):
    pymupdf = pytest.importorskip("pymupdf")
    pytest.importorskip("ezdxf")
    pytest.importorskip("matplotlib")
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    monkeypatch.syspath_prepend(str(ROOT / "src"))
    app = import_module(module).app
    from bridgecad_draw.booklet import SHEET_COUNT

    with TestClient(app) as client:
        response = client.post(
            "/predict",
            params={"output_format": "pdf"},
            files={"excel_file": (WORKBOOK.name, WORKBOOK.read_bytes())},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    with pymupdf.open(stream=response.content, filetype="pdf") as pdf:
        assert len(pdf) == SHEET_COUNT
        for index, page in enumerate(pdf, start=1):
            pixels = page.get_pixmap(matrix=pymupdf.Matrix(.15, .15), colorspace=pymupdf.csGRAY)
            assert sum(value < 200 for value in pixels.samples) > 50, f"Blank sheet {index}"


def test_gateway_predict_downloads_zip_with_plan_and_elevation_dimensions(tmp_path):
    import ezdxf
    from fastapi.testclient import TestClient
    from bridgecad_api.main import app
    from bridgecad_draw.booklet import SHEET_COUNT
    from bridgecad_io.excel_reader import read_excel

    with TestClient(app) as client:
        response = client.post("/predict", files={"excel_file": (WORKBOOK.name, WORKBOOK.read_bytes())})
    assert response.status_code == 200, response.text[:400]
    assert response.headers["content-type"] == "application/zip"
    assert "GAD_drawings.zip" in response.headers["content-disposition"]

    project = read_excel(WORKBOOK)
    with ZipFile(BytesIO(response.content)) as archive:
        assert len(archive.namelist()) == SHEET_COUNT
        assert all(name.endswith(".dxf") for name in archive.namelist())
        for name in ("GAD_Sheet1_Plan.dxf", "GAD_Sheet2_LongSection.dxf"):
            (tmp_path / name).write_bytes(archive.read(name))

    plan = ezdxf.readfile(tmp_path / "GAD_Sheet1_Plan.dxf").modelspace()
    elevation = ezdxf.readfile(tmp_path / "GAD_Sheet2_LongSection.dxf").modelspace()
    expected_length = f"Total L = {float(project.geometry_input.total_length_m):.3f} m"
    assert any(dim.dxf.text == expected_length for dim in plan.query("DIMENSION"))
    dimensions = {dim.dxf.text: dim for dim in elevation.query("DIMENSION")}
    assert "T.O.DECK" in dimensions
    v_scale = next(float(match[1]) for entity in elevation.query("TEXT")
                   if (match := re.search(r"V Scale 1:(\d+(?:\.\d+)?)", entity.dxf.text)))
    deck_mm = project.superstructure.deck_thickness_mm
    assert dimensions[f"DECK={deck_mm}mm"].get_measurement() * v_scale == pytest.approx(deck_mm, abs=.01)


def test_gateway_predict_downloads_a_nonblank_plan_png():
    from PIL import Image
    from fastapi.testclient import TestClient
    from bridgecad_api.main import app

    with TestClient(app) as client:
        response = client.post("/predict?output_format=png", files={"excel_file": (WORKBOOK.name, WORKBOOK.read_bytes())})
    assert response.status_code == 200, response.text[:400]
    assert response.headers["content-type"] == "image/png"
    assert "bridge_gad_plan.png" in response.headers["content-disposition"]
    with Image.open(BytesIO(response.content)) as plan:
        assert plan.format == "PNG"
        assert plan.width > plan.height
        assert plan.convert("L").getextrema()[0] < 100


def test_gateway_predict_rejects_unreadable_workbooks_and_unknown_formats():
    from fastapi.testclient import TestClient
    from bridgecad_api.main import app

    with TestClient(app) as client:
        files = {"excel_file": ("broken.xlsx", b"invalid workbook")}
        assert client.post("/predict", files=files).status_code == 422
        assert client.post("/predict?output_format=svg", files=files).status_code == 422
