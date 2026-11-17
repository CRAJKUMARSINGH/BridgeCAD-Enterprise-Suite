"""Booklet oracle — does each PWD type *draw* what the booklet says it is?

The generator's own gate is an entity floor (``MIN_ENTITIES = 20``); a sheet
with 20 entities "passes" whether it is the right drawing or not, so 15/15 PASS
says nothing about whether the drawing matches the booklet.  This lane replaces
that floor with per-type expectations (``booklet_oracle.json``) taken from the
Maharashtra PWD booklet:

* identity — the resolved spans, total length, skew, foundation and
  superstructure family must equal the booklet values, and the superstructure
  must resolve to the booklet's ``SuperstructureType`` member (not a silent
  ``SOLID_SLAB`` fallback);
* the PLAN and FOUNDATION sheets must carry — and must not carry — the layers
  the model implies (a pile type draws ``FOUND-PILE``; a bearingless box cell
  draws no ``SUB-BEARING``; a single-span arch has no ``SUB-PIER``).

Types 004 / 014 / 015 used to be carried without their family primitive
(multi-unit box cell, arch coordinate schedule, precast-block arch).  004 now
carries its lattice primitive and is not flagged.  014 / 015 draw their own arch
primitives too, but are still flagged ``approximation`` because their structural
depth is carried in the arch rise, not the deck slab, so the girder/slab
span/depth governor does not apply to them.  The ``approximation`` flag means
"span/depth governor not applied" here; the family primitive is still enforced
by the ``must_contain`` layer checks below.

Run:  pytest tests/pwd/test_booklet_oracle.py -q
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.e2e]

REPO = Path(__file__).resolve().parents[2]
ORACLE = json.loads((Path(__file__).parent / "booklet_oracle.json").read_text(encoding="utf-8"))
EXPECTED: dict[str, dict] = ORACLE["types"]


def _load_generator():
    """Import ``scripts/generate_all_pwd_gads.py`` as a module (it is not a package)."""
    spec = importlib.util.spec_from_file_location(
        "_pwd_gad_generator", REPO / "scripts" / "generate_all_pwd_gads.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def drawn(tmp_path_factory) -> dict[str, dict]:
    """Resolve, build and draw every booklet type once, and record its layers.

    Only the two sheets this oracle inspects are generated — the plan (sheet 1)
    and the foundation details (sheet 4) — so the lane stays a fast check of the
    drawing rather than a second copy of the full corpus run.
    """
    import ezdxf

    from bridgecad_catalogue import registry, resolve as R
    from bridgecad_draw import sheet1_plan, sheet4_foundation

    gen = _load_generator()
    root = tmp_path_factory.mktemp("pwd_booklet_oracle")
    out: dict[str, dict] = {}
    for card in registry.load():
        tid = card["id"]
        params = R.resolve(card, {})
        params["id"] = tid
        project = gen._build_project(params)
        target = root / tid
        target.mkdir(parents=True, exist_ok=True)
        sheets = {
            "plan": sheet1_plan.generate(project, target / "Sheet1_Plan.dxf", scale_denom=None),
            "foundation": sheet4_foundation.generate(
                project, target / "Sheet4_Foundation.dxf", scale_denom=50
            ),
        }
        out[tid] = {
            "project": project,
            "params": params,
            "layers": {
                name: {e.dxf.layer for e in ezdxf.readfile(str(path)).modelspace()}
                for name, path in sheets.items()
            },
        }
    return out


def test_oracle_covers_every_booklet_type():
    from bridgecad_catalogue import registry

    assert set(EXPECTED) == {c["id"] for c in registry.load()}, (
        "booklet_oracle.json and the catalogue disagree about which types exist"
    )


@pytest.mark.parametrize("tid", sorted(EXPECTED))
def test_type_matches_booklet(tid, drawn):
    """Identity: the model the sheets were drawn from must be the booklet's."""
    exp = EXPECTED[tid]
    project = drawn[tid]["project"]
    gi = project.geometry_input

    assert [float(s) for s in gi.span_lengths_m] == pytest.approx(exp["spans"], abs=0.001)
    assert float(gi.total_length_m) == pytest.approx(exp["total_length_m"], abs=0.01)
    assert float(gi.skew_angle_deg or 0) == pytest.approx(exp["skew_deg"], abs=0.001)
    assert project.foundation_details.type.name == exp["foundation_type"]
    assert project.superstructure.type.name == exp["superstructure_member"], (
        f"{tid}: booklet family {exp['superstructure_type']} resolved to "
        f"{project.superstructure.type.name}, not {exp['superstructure_member']}"
    )

    model_cw = exp.get("model_carriageway_width", exp["carriageway_width"])
    assert float(gi.carriageway_width_m) == pytest.approx(model_cw, abs=0.001)


@pytest.mark.parametrize("tid", sorted(EXPECTED))
def test_plan_sheet_shows_the_booklet_layers(tid, drawn):
    exp = EXPECTED[tid]
    layers = drawn[tid]["layers"]["plan"]

    missing = [lyr for lyr in exp["plan"]["must_contain"] if lyr not in layers]
    assert not missing, f"{tid} plan: expected layer(s) absent — {missing}"

    forbidden = sorted(set(exp["plan"]["must_not_contain"]) & layers)
    assert not forbidden, f"{tid} plan: layer(s) the booklet's type must not carry — {forbidden}"


@pytest.mark.parametrize("tid", sorted(EXPECTED))
def test_foundation_sheet_shows_the_booklet_layers(tid, drawn):
    exp = EXPECTED[tid]
    layers = drawn[tid]["layers"]["foundation"]

    missing = [lyr for lyr in exp["foundation"]["must_contain"] if lyr not in layers]
    assert not missing, f"{tid} foundation: expected layer(s) absent — {missing}"

    forbidden = sorted(set(exp["foundation"]["must_not_contain"]) & layers)
    assert not forbidden, (
        f"{tid} foundation: layer(s) the booklet's type must not carry — {forbidden}"
    )


@pytest.mark.parametrize("tid", sorted(EXPECTED))
def test_no_type_is_drawn_without_its_primitive(tid, drawn):
    """A type drawn without the full engine path must say so, not pass silently.

    Where the booklet expects the girder/slab span/depth governor to apply, the
    ``approximation`` flag must be absent — the guard against a family quietly
    dropping back onto the generic fallback.  An arch carries its span in thrust,
    so its governor is inapplicable and it must be flagged *and* carry a fidelity
    note and a warning; its primitive is still checked by the layer tests above.
    """
    exp = EXPECTED[tid]
    params = drawn[tid]["params"]
    if not exp["approximation"]:
        assert not params.get("approximation"), (
            f"{tid}: flagged as an approximation but the booklet expects a full primitive"
        )
        return
    assert params.get("approximation") is True, f"{tid}: approximation flag missing"
    assert params.get("fidelity_note"), f"{tid}: approximation carried with no fidelity note"
    assert any("approximation" in w for w in params.warnings), (
        f"{tid}: approximation not reported as a warning — the gap would be hidden"
    )
