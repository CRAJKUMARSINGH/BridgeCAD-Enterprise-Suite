"""Regression tests for formerly-unwired I/O, engine and CLI entry points."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "public" / "samples" / "bridge_23span.xlsx"


@pytest.fixture(scope="module")
def project():
    from bridgecad_io import read_excel

    return read_excel(SAMPLE)


def test_generate_template_public_wrapper(tmp_path):
    from bridgecad_io import generate_template

    assert generate_template(tmp_path / "t.xlsx").exists()


def test_json_round_trip(project, tmp_path):
    from bridgecad_io import from_json, to_json

    to_json(project, tmp_path / "p.json")
    assert from_json(tmp_path / "p.json").model_dump() == project.model_dump()


def test_json_with_computed_fields_loads(project, tmp_path):
    from bridgecad_io.json_adapter import load_project

    raw = project.model_dump(mode="json")  # includes computed fields
    (tmp_path / "raw.json").write_text(json.dumps(raw), encoding="utf-8")
    assert load_project(tmp_path / "raw.json").model_dump() == project.model_dump()


def test_csv_round_trip(project, tmp_path):
    from bridgecad_io import from_csv, to_csv

    files = to_csv(project, tmp_path / "csv")
    assert len(files) == 17  # 15 sections + 2 schedules
    assert from_csv(tmp_path / "csv").model_dump() == project.model_dump()


def test_write_excel_preserves_geometry(project, tmp_path):
    from bridgecad_io import read_excel, write_excel

    back = read_excel(write_excel(project, tmp_path / "w.xlsx"))
    a, b = project.geometry_input, back.geometry_input
    assert [float(x) for x in b.span_lengths_m] == [float(x) for x in a.span_lengths_m]
    assert float(b.carriageway_width_m) == float(a.carriageway_width_m)
    assert float(b.total_length_m) == float(a.total_length_m)


def test_pdf_booklet_engine(project, tmp_path):
    from bridgecad_draw.booklet import generate_package
    from bridgecad_draw.engines.pdf_engine import generate_pdf_booklet

    sheets = generate_package(project, tmp_path / "dxf")
    pdf = generate_pdf_booklet(sheets[:2], tmp_path / "b.pdf")
    assert pdf.read_bytes()[:4] == b"%PDF"


def test_cli_module_entry_point():
    import importlib

    assert importlib.import_module("bridgecad_cli.__main__").app is not None
