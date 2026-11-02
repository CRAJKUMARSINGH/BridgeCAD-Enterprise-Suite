"""W08 · importer fuzzing — a damaged file must fail clearly, not traceback.

Third DoD clause: *"A truncated/corrupt import produces a clear error, not a
traceback."* Every importer is fed input it cannot possibly accept, and each
must answer with a typed error from ``bridgecad_io.exceptions`` carrying the
offending file, rather than leaking a ``zipfile``, ``json`` or Pydantic
internal exception.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

REPO = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.interop


# ── JSON ─────────────────────────────────────────────────────────────────────
def test_truncated_project_json_raises_a_clear_error(tmp_path):
    from bridgecad_io.exceptions import JsonParseError
    from bridgecad_io.json_adapter import load_project

    whole = (REPO / "tests" / "e2e" / "fixtures" / "simple_12m.json").read_text(encoding="utf-8")
    truncated = tmp_path / "truncated.json"
    truncated.write_text(whole[: len(whole) // 2], encoding="utf-8")

    with pytest.raises(JsonParseError) as excinfo:
        load_project(truncated)
    assert "Malformed JSON" in str(excinfo.value)


@given(payload=st.text(max_size=512))
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_no_json_payload_leaks_a_raw_traceback(tmp_path, payload):
    """Arbitrary text is never a valid project, so it must always be typed."""
    from bridgecad_io.exceptions import JsonParseError
    from bridgecad_io.json_adapter import load_project

    target = tmp_path / "fuzz.json"
    target.write_text(payload, encoding="utf-8")
    with pytest.raises(JsonParseError):
        load_project(target)


# ── CSV ──────────────────────────────────────────────────────────────────────
def test_csv_row_without_the_value_column_raises_a_clear_error(tmp_path):
    from bridgecad_io.csv_adapter import from_csv
    from bridgecad_io.exceptions import CsvParseError

    out = tmp_path / "csv"
    out.mkdir()
    (out / "project_master.csv").write_text("path,other\nproject_title,x\n", encoding="utf-8")

    with pytest.raises(CsvParseError) as excinfo:
        from_csv(out)
    assert "project_master.csv" in str(excinfo.value)


def test_csv_value_that_is_not_json_raises_a_clear_error(tmp_path):
    from bridgecad_io.csv_adapter import from_csv
    from bridgecad_io.exceptions import CsvParseError

    out = tmp_path / "csv"
    out.mkdir()
    (out / "project_master.csv").write_text("path,value\nproject_title,{not json\n", encoding="utf-8")

    with pytest.raises(CsvParseError):
        from_csv(out)


def test_empty_csv_directory_raises_a_clear_error(tmp_path):
    from bridgecad_io.csv_adapter import from_csv
    from bridgecad_io.exceptions import CsvParseError

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(CsvParseError) as excinfo:
        from_csv(empty)
    assert "No sub-model CSV files" in str(excinfo.value)


def test_missing_csv_directory_raises_a_clear_error(tmp_path):
    from bridgecad_io.csv_adapter import from_csv
    from bridgecad_io.exceptions import CsvParseError

    with pytest.raises(CsvParseError):
        from_csv(tmp_path / "does-not-exist")


# ── Excel ────────────────────────────────────────────────────────────────────
def test_truncated_workbook_raises_a_clear_error(tmp_path, make_model):
    """A half-written .xlsx is the failure mode a dropped upload produces."""
    pytest.importorskip("openpyxl")
    from bridgecad_io import read_excel, write_excel
    from bridgecad_io.exceptions import ExcelParseError

    whole = write_excel(make_model("simple_12m"), tmp_path / "whole.xlsx").read_bytes()
    truncated = tmp_path / "truncated.xlsx"
    truncated.write_bytes(whole[: len(whole) // 2])

    with pytest.raises(ExcelParseError) as excinfo:
        read_excel(truncated)
    assert str(truncated) in str(excinfo.value), "the error must name the file"


def test_renamed_text_file_raises_a_clear_error(tmp_path):
    pytest.importorskip("openpyxl")
    from bridgecad_io import read_excel
    from bridgecad_io.exceptions import ExcelParseError

    renamed = tmp_path / "notes.xlsx"
    renamed.write_text("this is not a workbook\n", encoding="utf-8")

    with pytest.raises(ExcelParseError):
        read_excel(renamed)


@given(payload=st.binary(max_size=512))
@settings(
    max_examples=60,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_no_workbook_payload_leaks_a_raw_traceback(tmp_path, payload):
    pytest.importorskip("openpyxl")
    from bridgecad_io import read_excel
    from bridgecad_io.exceptions import ExcelParseError

    target = tmp_path / "fuzz.xlsx"
    target.write_bytes(payload)
    with pytest.raises(ExcelParseError):
        read_excel(target)
