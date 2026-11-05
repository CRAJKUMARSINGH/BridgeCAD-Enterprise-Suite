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

DETAIL_LABELS = [
    "FOUNDATION ELEVATION",
    "PILE CAP REINFORCEMENT DETAIL",
    "ABUTMENT A1",
    "WING WALL LEFT",
    "WING WALL RIGHT",
    "FIRE WALL",
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


def test_labels_present_in_core():
    core = (FRONTEND / "detailGeometry.js").read_text(encoding="utf-8")
    for label in DETAIL_LABELS:
        assert label in core, f"detail label dropped: {label}"


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
