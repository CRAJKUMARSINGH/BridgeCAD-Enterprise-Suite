"""W08 · export-only formats — IFC 4.3 and DWG.

Neither format has a reader in this suite, so neither can be round-tripped
against itself. The honest gate is therefore:

    IFC  an external validator must accept the file, and re-reading it must
         report the geometry that was written (the "import" half);
    DWG  the conversion either happens, or says exactly which licensed
         component is missing — never a silent no-op.
"""

from __future__ import annotations

import logging

import pytest

pytestmark = pytest.mark.interop


def test_ifc_export_passes_the_express_rule_validator(tmp_path, make_model):
    """DoD: 'IFC passes a validator'."""
    ifcopenshell = pytest.importorskip("ifcopenshell")
    import ifcopenshell.validate
    from bridgecad_export.ifc_engine import IFC_SCHEMA, export_ifc, read_ifc_summary

    target = export_ifc(make_model("skew15_3x18m"), tmp_path / "bridge.ifc")
    assert target.stat().st_size > 0

    # The "import" half: read the geometry back out of the written file.
    summary = read_ifc_summary(target)
    assert summary["schema"] == IFC_SCHEMA
    assert summary["products"] > 0
    assert summary["counts"]["IfcSlab"] == 1
    assert summary["deck_length_m"] > 0
    assert summary["deck_width_m"] > 0

    collected: list[logging.LogRecord] = []

    class _Errors(logging.Handler):
        def __init__(self) -> None:
            super().__init__(level=logging.ERROR)

        def emit(self, record: logging.LogRecord) -> None:
            collected.append(record)

    logger = logging.getLogger("ifcopenshell.validate")
    handler = _Errors()
    logger.addHandler(handler)
    try:
        model = ifcopenshell.open(str(target))
        ifcopenshell.validate.validate(model, logger=logger, express_rules=True)
    finally:
        logger.removeHandler(handler)

    assert collected == [], [r.getMessage() for r in collected]


def test_dwg_export_converts_or_explains_what_is_missing(tmp_path, make_model):
    """Deliverable: 'DWG export (ODA) where licensing permits'."""
    pytest.importorskip("ezdxf")
    from bridgecad_draw.booklet import generate_package
    from bridgecad_export import dwg_available, export_dwg

    sheets = generate_package(make_model("simple_12m"), tmp_path / "dxf", prefix="w08")
    assert sheets, "no DXF was produced to convert"

    dwg = tmp_path / "bridge.dwg"
    if not dwg_available():
        with pytest.raises(RuntimeError) as excinfo:
            export_dwg(sheets[0], dwg)
        assert "ODA File Converter" in str(excinfo.value)
        pytest.skip("ODA File Converter is not installed — DWG is licensed separately")

    produced = export_dwg(sheets[0], dwg)
    assert produced.is_file() and produced.stat().st_size > 0
