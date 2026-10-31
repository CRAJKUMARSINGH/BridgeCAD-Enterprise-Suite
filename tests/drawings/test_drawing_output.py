"""W07 — drawing-output regression lane.

Verification command from the W07 issue::

    pytest -q tests/drawings --regression

Each test gates one W07 deliverable:

    deliverable                          gate
    -----------------------------------  --------------------------------------
    ISO 13567 / IS 962 layer naming      test_iso_13567_scheme_covers_every_...
                                         test_layer_audit_script_passes
    line weights on the ISO 128 series   test_every_layer_weight_is_on_the_...
    deterministic DXF                    test_dxf_is_byte_identical_across_...
    drawing-diff regression              test_a_parameter_change_changes_the...
    DXF opens without repair             test_written_dxf_reloads_without_repair
    PDF/A-1b archival export             test_pdf_a1b_export_passes_the_check...

The byte-equality claim is exact for the DXF path: the canonical serializer
replaces the volatile header stamps, GUIDs and the ezdxf ``999`` timestamp that
carry no geometry. The PDF path is not byte-stable (the renderer's content
stream differs in anti-aliasing), so its gate is the PDF/A-1b structural
contract, not a byte comparison.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from draw import contract

REPO = Path(__file__).resolve().parents[2]

SHEETS = (
    "sheet1_plan",
    "sheet2_long_section",
    "sheet3_cross_section",
    "sheet4_foundation",
    "sheet5_pier_abutment_details",
    "sheet6_bearings_joints",
    "sheet7_bill_of_quantities",
)

pytestmark = [pytest.mark.regression, pytest.mark.draw]


# ── ISO 13567-2 / IS 962 layer naming ────────────────────────────────────────
def test_iso_13567_scheme_covers_every_project_layer():
    from bridgecad_draw import layers as L

    project = {name for name in L.LAYER_REGISTRY if name != "0"}
    missing = sorted(project - set(L.ISO_13567_NAMES))
    assert missing == [], f"layers with no ISO 13567-2 name: {missing}"

    names = [L.ISO_13567_NAMES[name] for name in sorted(project)]
    assert len(set(names)) == len(names), "two layers claim the same ISO 13567-2 name"
    for name in names:
        assert L.ISO_13567_PATTERN.match(name), f"{name!r} leaves the ISO 13567-2 scheme"


def test_every_layer_weight_is_on_the_iso_128_series():
    from bridgecad_draw import layers as L

    off = {
        name: ld.lineweight
        for name, ld in L.LAYER_REGISTRY.items()
        if ld.lineweight not in L.ISO_128_LINEWEIGHTS
    }
    assert off == {}, f"weights off the ISO 128 series (1/100 mm): {off}"


def test_layer_audit_script_passes():
    """DoD: 'Layer audit script passes'. Same gate CI runs, invoked as CI runs it."""
    proc = subprocess.run(
        [sys.executable, "scripts/audit_layers.py", "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ── deterministic DXF ────────────────────────────────────────────────────────
@pytest.mark.parametrize("sheet", SHEETS)
def test_dxf_is_byte_identical_across_renders(sheet: str):
    """DoD: 'Two renders of the same input produce identical bytes'."""
    from bridgecad_draw.determinism import canonical_dxf_bytes

    first = canonical_dxf_bytes(contract.build_sheet(contract.make_project("simple_12m"), sheet))
    second = canonical_dxf_bytes(contract.build_sheet(contract.make_project("simple_12m"), sheet))
    assert first == second, f"{sheet}: the same input rendered to two different DXFs"


def test_a_parameter_change_changes_the_canonical_bytes():
    """The byte-equality gate must be a diff gate, not an always-equal."""
    from bridgecad_draw.determinism import canonical_dxf_bytes

    reference = contract.make_project("simple_12m")
    moved = contract.make_project("simple_12m")
    moved.geometry_input.span_length_m = 15.0

    before = canonical_dxf_bytes(contract.build_sheet(reference, "sheet1_plan"))
    after = canonical_dxf_bytes(contract.build_sheet(moved, "sheet1_plan"))
    assert before != after, "moving the span length did not change the drawing"


def test_volatile_dxf_values_are_normalised():
    from bridgecad_draw.determinism import normalize

    sample = (
        "$FINGERPRINTGUID\n{3F2504E0-4F89-11D3-9A0C-0305E82C3301}\n"
        "999\n1.4.4 @ 2026-10-31T12:00:00.000000+05:30\n"
    )
    cleaned = normalize(sample)
    assert "3F2504E0" not in cleaned
    assert "2026-10-31" not in cleaned


def test_written_dxf_reloads_without_repair(tmp_path: Path):
    """Structural stand-in for 'opens clean in AutoCAD/BricsCAD/LibreCAD'.

    ``ezdxf.readfile`` raises ``DXFStructureError`` and CAD shows a repair
    prompt for exactly the damage a reload would have to recover from.
    """
    import ezdxf

    from bridgecad_draw.determinism import write_deterministic

    doc = contract.build_sheet(contract.make_project("simple_12m"), "sheet1_plan")
    path = write_deterministic(doc, tmp_path / "sheet1_plan.dxf")

    reloaded = ezdxf.readfile(path)
    auditor = reloaded.audit()
    assert not auditor.errors, auditor.errors


# ── PDF/A-1b archival export ─────────────────────────────────────────────────
def test_pdf_a1b_export_passes_the_check_script(tmp_path: Path):
    pytest.importorskip("pymupdf")
    from bridgecad_draw.engines.pdf_engine import export_pdf_a, inspect_pdf_a, is_pdf_a1b

    doc = contract.build_sheet(contract.make_project("simple_12m"), "sheet1_plan")
    pdf = export_pdf_a(doc, tmp_path / "plan.dxf.pdf")
    assert pdf.is_file() and pdf.stat().st_size > 0

    facts = inspect_pdf_a(pdf)
    assert is_pdf_a1b(facts), facts

    proc = subprocess.run(
        [sys.executable, "scripts/check_pdfa.py", str(pdf)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
