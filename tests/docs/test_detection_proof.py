"""Layer 4 — prove every defect is detectable.

Shells out to the mutation harness so the proof is a test result, not a
command you have to remember to run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from .conftest import REPO_ROOT

pytestmark = pytest.mark.slow


def _prove(*extra: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "prove_detection.py"),
         "--json", "--jobs", "4", *extra],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=900,
    )
    assert proc.stdout.strip(), f"harness produced no output\n{proc.stderr}"
    return json.loads(proc.stdout)


def test_control_run_passes_on_a_clean_copy():
    """If this fails, every other assertion below is unreliable."""
    data = _prove("--only", "D01")
    assert data["control_passed"], (
        "the integrity suite does not pass on an unmutated copy — "
        "fix that before trusting the detection numbers"
    )


def test_every_defect_is_detectable():
    data = _prove()
    assert data["detected"] == data["total"], (
        f"{data['detected']}/{data['total']} detected. "
        f"Guards with holes: {data['undetected']}"
    )


@pytest.mark.parametrize("mutation_id", [
    "D01", "D02", "D03", "D04", "D05", "D06", "D07",
    "D08", "D09", "D10", "D11", "D12", "D13", "D14",
])
def test_critical_defects_individually(mutation_id: str):
    """One defect at a time, so a failure names the exact hole."""
    data = _prove("--only", mutation_id)
    row = data["results"][0]
    assert row["detected"], f"{mutation_id} ({row['defect']}) not detected by {row['guard']}"
