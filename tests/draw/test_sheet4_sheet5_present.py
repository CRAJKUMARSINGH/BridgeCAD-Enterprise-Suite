"""Regression: sheets 4 and 5 must exist and must carry their details.

Pins the deployed-frontend contract so the Netlify bundle cannot silently drop
the abutment foundation or the wing wall (fire wall) panel again.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src" / "sheets"

DETAIL_LABELS = [
    "FOUNDATION ELEVATION",
    "PILE CAP REINFORCEMENT DETAIL",
    "ABUTMENT A1",
    "WING WALL LEFT",
    "WING WALL RIGHT",
    "FIRE WALL",
    "BEARING SCHEDULE",
]


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
