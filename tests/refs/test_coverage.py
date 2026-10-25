"""Wing-21 — is the corpus actually evidence, or is it four files?

A bridge that can be deleted without any test outcome changing is decoration.
Two tests: the coverage report must be fresh and unthin, and every case must
contribute a distinct constraint.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from bridgecad_refs.parse import agree

pytestmark = pytest.mark.refs

REF = Path(__file__).resolve().parents[2] / "references"
CASES = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((REF / "cases").glob("*.json"))]
COVERAGE = json.loads((REF / "coverage.json").read_text(encoding="utf-8"))


def test_coverage_report_is_fresh():
    import subprocess, sys
    before = (REF / "coverage.json").read_bytes()
    subprocess.run([sys.executable, "scripts/refs_coverage.py"], check=True, capture_output=True)
    assert (REF / "coverage.json").read_bytes() == before, "coverage.json is stale"


def test_no_formula_critical_parameter_is_thin():
    """ABTL, splay, nspan and span each need >= 3 distinct values, or the
    formula is fitted to one or two bridges and extrapolated everywhere else."""
    for param in ("nspan", "span_m", "abtl_m", "splay_deg"):
        assert not COVERAGE["coverage"][param]["thin"], (
            f"{param}: {COVERAGE['coverage'][param]['distinct']} distinct values — "
            f"formula validation rests on too few points"
        )


def test_known_gaps_are_stated():
    assert COVERAGE["known_gaps"], "coverage claims no gaps — unlikely"


def test_every_case_contributes_a_distinct_constraint():
    """Perturb each case's distinguishing parameter and assert its own stated
    values stop being satisfied. A case that survives perturbation of everything
    is a case the suite does not use."""
    for case in CASES:
        p = case["parameters"]
        distinguished = False
        for param, bump in (("splay_deg", Decimal("5")), ("abtl_m", Decimal("0.5"))):
            if param not in p:
                continue
            mutated = dict(p)
            mutated[param] = str(Decimal(p[param]) + bump)
            face = (Decimal(mutated["abtl_m"]) - Decimal(mutated["carriageway_m"])) / 2
            stated = case["stated_values"].get("wing_face_run_m")
            if stated and not agree(face, Decimal(stated["value"])):
                distinguished = True
        assert distinguished, (
            f"{case['id']}: perturbing splay or ABTL left every stated value satisfied"
        )


def test_cases_are_pairwise_distinct_on_what_matters():
    sigs = [(c["parameters"]["nspan"], c["parameters"]["span_m"],
             c["parameters"]["abtl_m"], c["parameters"]["splay_deg"]) for c in CASES]
    assert len(set(sigs)) == len(sigs), f"duplicate case signatures: {sigs}"


def test_at_least_one_case_exercises_each_splay_extreme():
    splays = sorted(Decimal(c["parameters"]["splay_deg"]) for c in CASES)
    assert splays[0] <= Decimal("30"), f"min splay {splays[0]} — no shallow case"
    assert splays[-1] >= Decimal("60"), f"max splay {splays[-1]} — no steep case"
