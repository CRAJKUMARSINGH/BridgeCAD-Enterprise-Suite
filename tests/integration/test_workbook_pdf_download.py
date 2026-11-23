"""The Netlify PDF request must return a readable booklet from the sample workbook."""

from pathlib import Path

import pytest


def test_sample_workbook_predict_downloads_complete_pdf(monkeypatch):
    pymupdf = pytest.importorskip("pymupdf")
    pytest.importorskip("ezdxf")
    pytest.importorskip("matplotlib")
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root / "src"))
    from bridge_gad.api import app
    from bridgecad_draw.booklet import SHEET_COUNT

    workbook = root / "frontend/public/samples/sample_input.xlsx"
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            params={"output_format": "pdf"},
            files={"excel_file": (workbook.name, workbook.read_bytes())},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    with pymupdf.open(stream=response.content, filetype="pdf") as pdf:
        assert len(pdf) == SHEET_COUNT
        for index, page in enumerate(pdf, start=1):
            pixels = page.get_pixmap(matrix=pymupdf.Matrix(.15, .15), colorspace=pymupdf.csGRAY)
            assert sum(value < 200 for value in pixels.samples) > 50, f"Blank sheet {index}"
