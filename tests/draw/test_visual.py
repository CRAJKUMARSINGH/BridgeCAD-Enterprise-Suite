"""Wing-07 — determinism and PNG baselines.

Two distinct properties:
  1. Determinism — same input, same geometry, every run. Without this, every
     other test in the suite is flaky and no baseline means anything.
  2. Visual regression — the picture has not changed beyond a tolerance.
"""
from __future__ import annotations

import pytest

from . import contract, dxf_assert

pytestmark = [pytest.mark.draw, pytest.mark.visual]

BASELINE = contract.REPO / "tests" / "draw" / "baselines"
TOLERANCE = 6          # Hamming distance on a 64-bit dHash, out of 64


def _dhash(png: bytes, size: int = 8) -> int:
    """Difference hash. No imagehash dependency."""
    import io
    from PIL import Image

    img = Image.open(io.BytesIO(png)).convert("L").resize((size + 1, size))
    px = list(img.getdata())
    bits = 0
    for row in range(size):
        for col in range(size):
            left = px[row * (size + 1) + col]
            right = px[row * (size + 1) + col + 1]
            bits = (bits << 1) | int(left > right)
    return bits


def _render_png(doc) -> bytes:
    import io
    import matplotlib
    matplotlib.use("Agg")
    from ezdxf.addons.drawing import matplotlib as ezmpl
    buf = io.BytesIO()
    ezmpl.qsave(doc.modelspace(), buf, bg="#ffffff")
    return buf.getvalue()


@pytest.mark.parametrize("sheet", ["sheet1_plan", "sheet5_pier_abutment_details"])
def test_rendering_is_deterministic(sheet: str):
    project = contract.make_project("simple_12m")
    first = dxf_assert.fingerprint(contract.build_sheet(project, sheet))
    second = dxf_assert.fingerprint(contract.build_sheet(project, sheet))
    assert first == second, f"{sheet} is non-deterministic — every baseline is meaningless"


def test_a_parameter_change_changes_the_fingerprint():
    """Guard against a fingerprint so coarse it never moves."""
    a = contract.make_project("simple_12m")
    b = contract.make_project("simple_12m")
    b.geometry_input.span_length_m = 15.0

    fa = dxf_assert.fingerprint(contract.build_sheet(a, "sheet1_plan"))
    fb = dxf_assert.fingerprint(contract.build_sheet(b, "sheet1_plan"))
    assert fa != fb, "changing the span length did not change the geometry"


@pytest.mark.parametrize("sheet", ["sheet1_plan", "sheet5_pier_abutment_details"])
def test_visual_baseline(sheet: str):
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, sheet)
    actual = _dhash(_render_png(doc))

    ref_file = BASELINE / f"simple_12m__{sheet}.hash"
    if not ref_file.exists():
        ref_file.parent.mkdir(parents=True, exist_ok=True)
        ref_file.write_text(str(actual), encoding="utf-8")
        pytest.skip(f"baseline created for {sheet} — re-run to compare")

    expected = int(ref_file.read_text(encoding="utf-8").strip())
    distance = bin(actual ^ expected).count("1")
    assert distance <= TOLERANCE, (
        f"{sheet}: visual drift {distance}/{64} (tolerance {TOLERANCE}). "
        f"Run `make wing-rebaseline` if the change is intended."
    )
