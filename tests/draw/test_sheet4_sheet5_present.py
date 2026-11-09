"""Regression: sheets 4 and 5 must exist and must carry their details.

Pins the deployed-frontend contract so the Netlify bundle cannot silently drop
the abutment foundation or the wing wall (fire wall) panel again.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src" / "sheets"
GOLDEN = ROOT / "tests" / "draw" / "golden" / "pins" / "detail_default.json"
FIXTURES = ROOT / "tests" / "draw" / "fixtures"

SHEET_SCALE = 100  # 1:100 sheet scale, mirrors detailGeometry.js


def _mm(metres: float) -> float:
    return metres * 1000.0 / SHEET_SCALE


DETAIL_LABELS = [
    "FOUNDATION ELEVATION",
    "PILE CAP REINFORCEMENT DETAIL",
    "ABUTMENT A1",
    "WING WALL LEFT",
    "WING WALL RIGHT",
    "FIRE WALL",
    "DIRT WALL",
    "WEEP HOLES",
    "GRANULAR FILTER",
    "RETAINED EMBANKMENT",
    "BEARING SCHEDULE",
]

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _run_node(script: str) -> dict:
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    return json.loads(proc.stdout)


def test_sheet_modules_exist():
    for name in (
        "Sheet04Foundation.tsx",
        "Sheet05PierAbutment.tsx",
        "detailGeometry.js",
        "registry.tsx",
    ):
        assert (FRONTEND / name).is_file(), f"missing {name}"


def test_registry_lists_sheets_4_and_5():
    registry = (FRONTEND / "registry.tsx").read_text(encoding="utf-8")
    assert "sheet4_foundation" in registry
    assert "sheet5_pier_abutment" in registry


@needs_node
def test_required_labels_are_emitted():
    """Every required label must reach the drawing, not merely the source.

    The previous version scanned `detailGeometry.js` as text, where `FIRE WALL`
    also sits inside a docstring comment — so the test passed even if the label
    never became a primitive. Reading the built text stream removes that false
    positive.
    """
    text = _run_node(
        "import { buildSheet4, buildSheet5 } from './frontend/src/sheets/detailGeometry.js';"
        "const textOf = (s) => s.prims.filter((q) => q.k === 'text').map((q) => q.s).join(' | ');"
        "process.stdout.write(JSON.stringify({ s4: textOf(buildSheet4()), s5: textOf(buildSheet5()) }));"
    )
    blob = f"{text['s4']} | {text['s5']}"
    for label in DETAIL_LABELS:
        assert label in blob, f"detail label not emitted: {label}"


@needs_node
@pytest.mark.parametrize("rung,value", [("futl", 20.0), ("footl", 18.0), ("futrl", 16.0), ("alcl", 15.0), ("alcw", 14.0)])
def test_abtl_ladder_rungs_are_reachable(rung: str, value: float):
    """Item-5 guard: every rung of the ABTL ladder must be selectable and the rung
    that fired must be printed on the sheet.

    Resolving the ladder on already-normalised params made `abtl` the first rung on
    every call, so FUTL..ALCW could never fire. This drives each rung from raw
    input and reads the printed `SOURCE:` label.
    """
    params = {"carriageway": 7.5, rung: value}
    out = _run_node(
        "import { buildSheet5 } from './frontend/src/sheets/detailGeometry.js';"
        f"const s = buildSheet5({json.dumps(params)});"
        "const text = s.prims.filter((q) => q.k === 'text').map((q) => q.s).join(' | ');"
        "process.stdout.write(JSON.stringify({ src: s.meta.abtlSource, text }));"
    )
    assert out["src"] == rung.upper(), f"ladder rung {rung} did not fire: {out['src']}"
    assert f"SOURCE: {rung.upper()}" in out["text"], f"rung not printed: {out['text']}"


@needs_node
def test_wing_walls_spring_from_both_abutment_ends():
    """Item-1 guard: the two wing-wall polygons must spring from the *opposite*
    ends of the abutment face, on the soffit, with a horizontal face run.

    The pre-fix drawing anchored both walls to one corner, rotated 90° out of the
    abutment face and floating below it — a defect the contract audit could not
    see. This reads the drawn polygons, so it fails on that geometry.
    """
    got = _run_node(
        "import { buildSheet5 } from './frontend/src/sheets/detailGeometry.js';"
        "const s = buildSheet5();"
        "const walls = s.prims.filter((q) => q.k === 'poly' && q.layer === 'SUB-ABUT').map((q) => {"
        "  const xs = q.pts.filter((_, i) => i % 2 === 0);"
        "  const ys = q.pts.filter((_, i) => i % 2 === 1);"
        "  return { noseX: q.pts[0], topY: Math.max(...ys),"
        "           run: Math.max(...xs) - Math.min(...xs), drop: Math.max(...ys) - Math.min(...ys) }; });"
        "process.stdout.write(JSON.stringify({"
        "  walls, abtl: s.meta.params.abtl,"
        "  meta: s.meta.walls.map((w) => ({ faceRunM: w.faceRunM, returnM: w.returnM })) }));"
    )
    walls = got["walls"]
    assert len(walls) == 2, f"expected two wing-wall polygons, got {len(walls)}"

    # Anchored at opposite ends of the abutment face, not a shared corner.
    assert walls[0]["noseX"] != walls[1]["noseX"], f"wing walls share a nose: {walls}"
    span = abs(walls[1]["noseX"] - walls[0]["noseX"])
    assert abs(span - _mm(got["abtl"])) < 1.0, f"nose span {span:.1f} != abutment width {_mm(got['abtl']):.1f}"

    # Seated on the same soffit line (the abutment base), level with each other.
    assert abs(walls[0]["topY"] - walls[1]["topY"]) < 1e-6, "wing walls not seated on the same soffit"

    for drawn, wall in zip(walls, got["meta"]):
        assert abs(drawn["run"] - _mm(wall["faceRunM"])) < 1.0, (
            f"drawn face run {drawn['run']:.1f} != {_mm(wall['faceRunM']):.1f}"
        )
        # The wall drops by the return plus its own thickness (mm(0.4) = 4 mm).
        assert abs(drawn["drop"] - (_mm(wall["returnM"]) + _mm(0.4))) < 1.0, (
            f"drawn return {drawn['drop']:.1f} != {_mm(wall['returnM']) + _mm(0.4):.1f}"
        )


@needs_node
@pytest.mark.skipif(not (FRONTEND / "detailGeometry.js").is_file(), reason="core missing")
def test_random_audit_is_clean():
    proc = subprocess.run(
        ["python", "scripts/robotic_sheet_detail_audit.py", "--cases", "200", "--seed", "7"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout[-3000:] + proc.stderr[-2000:]


@needs_node
def test_default_counts_match_golden():
    """D-11: pinned default primitive counts, so a panel cannot vanish quietly."""
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    got = _run_node(
        "import { buildSheet4, buildSheet5 } from './frontend/src/sheets/detailGeometry.js';"
        "process.stdout.write(JSON.stringify({"
        "sheet4: buildSheet4().prims.length, sheet5: buildSheet5().prims.length }));"
    )
    tol = golden["tolerance"]
    assert abs(got["sheet4"] - golden["sheet4"]) <= tol, f"sheet4 {got['sheet4']} vs pin {golden['sheet4']}"
    assert abs(got["sheet5"] - golden["sheet5"]) <= tol, f"sheet5 {got['sheet5']} vs pin {golden['sheet5']}"


@needs_node
@pytest.mark.parametrize("name", ["detail_splay_15.json", "detail_splay_60.json"])
def test_splay_extremes_audit_clean(name: str):
    """D-11: both splay extremes must still pass the contract audit."""
    params = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    result = _run_node(
        "import { buildSheet4, buildSheet5, audit } from './frontend/src/sheets/detailGeometry.js';"
        f"const p = {json.dumps(params)};"
        "process.stdout.write(JSON.stringify({ s4: audit(buildSheet4(p)), s5: audit(buildSheet5(p)) }));"
    )
    assert result["s4"]["ok"], result["s4"]["issues"]
    assert result["s5"]["ok"], result["s5"]["issues"]


@needs_node
def test_dirt_wall_detail_panel_is_thin_and_drained():
    """prewallcivil.com/dirt-wall-in-bridge-abutment: Sheet 05 must detail the
    dirt wall — a DWTH-thin wall on the cap, drained by weep holes, holding a
    layered granular backfill behind a geotextile filter.

    Reads the built primitive stream, so it fails if the wall is drawn thick (a
    second abutment) or left un-drained.
    """
    got = _run_node(
        "import { buildSheet5 } from './frontend/src/sheets/detailGeometry.js';"
        "const s = buildSheet5();"
        "const widths = s.prims.filter((q) => q.k === 'rect' && q.layer === 'SUB-ABUT').map((q) => q.w);"
        "const weep = s.prims.filter((q) => q.k === 'circle' && q.layer === 'STRUC-DETAIL').length;"
        "const text = s.prims.filter((q) => q.k === 'text').map((q) => q.s).join(' | ');"
        "process.stdout.write(JSON.stringify({"
        "  panel: s.prims.some((q) => q.k === 'panel' && q.id === '5G'),"
        "  minWidth: Math.min(...widths), weep, text }));"
    )
    assert got["panel"], "the dirt-wall detail panel 5G is missing"
    assert abs(got["minWidth"] - _mm(0.3)) < 0.05, f"dirt wall is not DWTH 0.3 m thin: {got['minWidth']}"
    assert got["weep"] >= 2, "the dirt wall has no weep holes"
    for label in ("DIRT WALL", "WEEP HOLES", "GRANULAR FILTER", "RETAINED EMBANKMENT", "APPROACH SLAB"):
        assert label in got["text"], f"dirt-wall detail label not emitted: {label}"
