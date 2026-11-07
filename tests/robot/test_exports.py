"""File-integrity and determinism oracles for the real export surface.

Bound to ``bridgecad_draw.booklet.generate_package`` (which emits **8** sheets,
not the 7 the older docs claim), ``bridgecad_export.orchestrator.export_all``,
and the ``bridgecad_io`` workbook round-trip. A green UI over a corrupt or
nondeterministic drawing is still a FAIL.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.robot

ezdxf = pytest.importorskip("ezdxf")


@pytest.fixture(scope="module")
def package(project, tmp_path_factory):
    """Generate the DXF package once for the whole module."""
    from bridgecad_draw.booklet import generate_package

    out = tmp_path_factory.mktemp("gad")
    return generate_package(project, out, prefix="GAD")


def test_package_emits_every_sheet(package):
    assert len(package) == 9, f"expected 9 sheets, got {len(package)}"
    for sheet in package:
        assert sheet.exists()
        assert sheet.stat().st_size > 0


def test_partial_package_raises_instead_of_shipping(project, tmp_path, monkeypatch):
    """A single sheet failure must fail the package, never ship a partial set."""
    import bridgecad_draw.sheet5_pier_abutment_details as sheet5
    from bridgecad_draw.booklet import PackageGenerationError, generate_package

    def _boom(*_args, **_kwargs):
        raise RuntimeError("simulated sheet failure")

    monkeypatch.setattr(sheet5, "generate", _boom)

    with pytest.raises(PackageGenerationError) as excinfo:
        generate_package(project, tmp_path / "partial", prefix="GAD")

    assert 5 in excinfo.value.failures
    assert "RuntimeError" in excinfo.value.failures[5]


def test_every_sheet_is_a_valid_dxf(package):
    for sheet in package:
        doc = ezdxf.readfile(str(sheet))
        auditor = doc.audit()
        assert not auditor.errors, f"{sheet.name}: {[str(e) for e in auditor.errors]}"
        # Units must be declared — unitless DXF is un-auditable in the field.
        assert doc.header["$INSUNITS"] in (4, 6), f"{sheet.name} has $INSUNITS={doc.header['$INSUNITS']}"


def test_every_sheet_carries_real_geometry(package):
    for sheet in package:
        doc = ezdxf.readfile(str(sheet))
        entities = sum(1 for _ in doc.modelspace())
        assert entities >= 20, f"{sheet.name} has only {entities} entities (title block only?)"


def test_output_is_deterministic(project, tmp_path):
    """Same project, same bytes — an un-auditable DXF set is worse than none."""
    from bridgecad_draw.booklet import generate_package
    from bridgecad_draw.determinism import canonical_dxf_bytes

    first = generate_package(project, tmp_path / "a", prefix="GAD")
    second = generate_package(project, tmp_path / "b", prefix="GAD")

    assert [p.name for p in first] == [p.name for p in second]
    for a, b in zip(first, second, strict=True):
        assert canonical_dxf_bytes(ezdxf.readfile(str(a))) == canonical_dxf_bytes(
            ezdxf.readfile(str(b))
        ), f"{a.name} is not byte-stable across runs"


def test_export_bundle_has_manifest_and_drawings(project, tmp_path):
    from bridgecad_export.orchestrator import export_all

    bundle = export_all(project, tmp_path, prefix="GAD")
    assert bundle.exists()
    with zipfile.ZipFile(bundle) as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert any(n.startswith("drawings/") and n.endswith(".dxf") for n in names)
        assert any(n.startswith("bill/") for n in names)


def test_workbook_round_trip_preserves_geometry(project, tmp_path):
    """write_excel → read_excel must survive the trip the API depends on."""
    pytest.importorskip("openpyxl")
    from bridgecad_io import read_excel, write_excel

    path = write_excel(project, tmp_path / "roundtrip.xlsx")
    assert Path(path).exists()
    reloaded = read_excel(path)

    assert int(reloaded.geometry_input.span_count) == int(project.geometry_input.span_count)
    assert float(reloaded.geometry_input.total_length_m) == pytest.approx(
        float(project.geometry_input.total_length_m), rel=1e-6
    )
