"""Regression: the four workspace features borrowed from the CAD Bridge Studio
prototype — clause-cited IRC/MoRTH checks, CAD layer visibility, superstructure
type / standard presets, and the priced Bill of Quantities.

Each feature is a pure, import-free module under ``frontend/src/sheets`` so it
can be loaded straight by Node and asserted here, plus a source-level guard that
the workspace actually wires it in. A feature that exists only in a module but
never reaches ``main.tsx`` is not a feature.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src" / "sheets"

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _run_node(script: str) -> object:
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]
    return json.loads(proc.stdout)


def test_feature_modules_exist():
    for name in ("compliance.js", "layerGroups.js", "presets.js", "boq.js"):
        assert (FRONTEND / name).is_file(), f"missing {name}"


# ── Feature 1: clause-cited IRC / MoRTH checks ────────────────────────────────


@needs_node
def test_compliance_report_cites_every_clause():
    """Every check must carry a standard-edition-clause citation and a verdict,
    and the summary counts must agree with the checks themselves."""
    got = _run_node(
        "import { buildComplianceReport, CHECK_IDS } from './frontend/src/sheets/compliance.js';"
        "const r = buildComplianceReport({ spanLength: 12, width: 12 }, { carriageway: 7.5, abtl: 13, splay: 45 });"
        "process.stdout.write(JSON.stringify({"
        "  ids: r.checks.map((c) => c.id), declared: CHECK_IDS,"
        "  citations: r.checks.map((c) => c.citation),"
        "  verdicts: r.checks.map((c) => c.verdict),"
        "  nChecks: r.nChecks, nPassed: r.nPassed, nFailed: r.nFailed, ok: r.ok }));"
    )
    assert got["ids"] == got["declared"], "checks must be the declared CHECK_IDS in order"
    assert got["nChecks"] == len(got["ids"])
    assert got["nPassed"] + got["nFailed"] == got["nChecks"]
    assert got["ok"] == (got["nFailed"] == 0)
    for citation in got["citations"]:
        assert citation and any(token in citation for token in ("IRC:", "MoRTH", "BridgeCAD")), citation
    for verdict in got["verdicts"]:
        assert verdict in ("PASS", "FAIL")


@needs_node
def test_compliance_utilisation_sign_convention():
    """`utilisation = demand / capacity`, so a provided value inside the limit
    gives utilisation <= 1 and passes; a value outside it exceeds 1 and fails.
    A minimum-thickness check with a generous value must pass, and an
    undersized value must fail."""
    got = _run_node(
        "import { buildComplianceReport } from './frontend/src/sheets/compliance.js';"
        "const generous = buildComplianceReport({ spanLength: 12, width: 12 }, { deckThickMm: 400 });"
        "const thin = buildComplianceReport({ spanLength: 12, width: 12 }, { deckThickMm: 150 });"
        "const pick = (r) => r.checks.find((c) => c.id === 'CC-102');"
        "process.stdout.write(JSON.stringify({ generous: pick(generous), thin: pick(thin) }));"
    )
    assert got["generous"]["pass"] is True
    assert got["generous"]["utilisation"] <= 1
    assert got["thin"]["pass"] is False
    assert got["thin"]["utilisation"] > 1


# ── Feature 2: CAD layer visibility ───────────────────────────────────────────


@needs_node
def test_layer_groups_cover_every_drawn_layer():
    """Every IRC layer the geometry engine can emit must belong to exactly one
    visibility group — an uncovered layer could never be switched off."""
    got = _run_node(
        "import { LAYERS } from './frontend/src/sheets/detailGeometry.js';"
        "import { LAYER_GROUPS, LAYER_TO_GROUP, groupForLayer } from './frontend/src/sheets/layerGroups.js';"
        "const drawn = Object.keys(LAYERS);"
        "const uncovered = drawn.filter((l) => !(l in LAYER_TO_GROUP));"
        "const counts = {};"
        "for (const g of LAYER_GROUPS) for (const l of g.layers) counts[l] = (counts[l] || 0) + 1;"
        "const duplicated = Object.keys(counts).filter((l) => counts[l] > 1);"
        "process.stdout.write(JSON.stringify({ drawn, uncovered, duplicated,"
        "  fallback: groupForLayer('NO-SUCH-LAYER') }));"
    )
    assert got["uncovered"] == [], f"layers with no visibility group: {got['uncovered']}"
    assert got["duplicated"] == [], f"layers in more than one group: {got['duplicated']}"
    assert got["fallback"] == "STRUCTURE", "an unknown layer must fall back to the structure group"


@needs_node
def test_hidden_layers_for_resolves_group_members():
    got = _run_node(
        "import { hiddenLayersFor } from './frontend/src/sheets/layerGroups.js';"
        "process.stdout.write(JSON.stringify({"
        "  none: [...hiddenLayersFor([])],"
        "  dimText: [...hiddenLayersFor(['DIM', 'TEXT'])],"
        "  levels: [...hiddenLayersFor(['LEVELS'])] }));"
    )
    assert got["none"] == []
    assert set(got["dimText"]) == {"DIM", "TEXT", "TEXT-HEADER"}
    assert got["levels"] == ["TEXT-LEVEL"]


def test_sheet_renderers_accept_hidden_layers():
    """The filter must be plumbed from the context into the primitive renderer,
    without reintroducing a shared sheet class (the N7 guard)."""
    chrome = (FRONTEND / "SheetChrome.tsx").read_text(encoding="utf-8")
    registry = (FRONTEND / "registry.tsx").read_text(encoding="utf-8")
    main = (ROOT / "frontend" / "src" / "main.tsx").read_text(encoding="utf-8")
    assert "hiddenLayers" in chrome and "filter" in chrome
    assert "hiddenLayers" in registry
    assert "hiddenLayersFor" in main
    for token in ("drawing-sheet", "sheet-bg", "sheet-border", "sheet-inner-border"):
        assert token not in chrome


# ── Feature 3: superstructure type + standard presets ─────────────────────────


@needs_node
def test_superstructure_type_moves_only_the_thickness_family():
    got = _run_node(
        "import { SUPERSTRUCTURE_TYPES, typeById, applySuperstructureType } from './frontend/src/sheets/presets.js';"
        "const base = { deckThickMm: 650, girderDepthMm: 0, girders: 2, abtl: 13, splay: 45, pileDiaMm: 600 };"
        "const t = applySuperstructureType(base, 'tbeam');"
        "process.stdout.write(JSON.stringify({ types: SUPERSTRUCTURE_TYPES.map((x) => x.id), applied: t,"
        "  same: t.abtl === base.abtl && t.pileDiaMm === base.pileDiaMm,"
        "  fallback: typeById('nope').id }));"
    )
    assert got["types"] == ["slab", "tbeam"]
    assert got["applied"]["girderDepthMm"] > 0 and got["applied"]["deckThickMm"] == 250
    assert got["same"] is True, "opening / level params must survive a type switch"
    assert got["fallback"] == "slab", "an unknown type must fall back to the slab"


@needs_node
def test_standard_presets_bundle_project_and_detail():
    got = _run_node(
        "import { STANDARD_PRESETS, presetBundle, DEFAULT_PRESET_ID } from './frontend/src/sheets/presets.js';"
        "const ids = STANDARD_PRESETS.map((p) => p.id);"
        "const b = presetBundle(DEFAULT_PRESET_ID);"
        "process.stdout.write(JSON.stringify({ ids, hasDefault: ids.includes(DEFAULT_PRESET_ID),"
        "  bundle: b, missing: presetBundle('nope') ?? null }));"
    )
    assert got["hasDefault"] is True
    bundle = got["bundle"]
    assert bundle is not None
    for key in ("project", "detail", "typeId"):
        assert key in bundle
    assert bundle["project"]["spanLength"] > 0 and bundle["detail"]["carriageway"] > 0
    assert got["missing"] is None


# ── Feature 4: priced Bill of Quantities ──────────────────────────────────────


@needs_node
def test_boq_is_priced_and_totals_reconcile():
    got = _run_node(
        "import { buildBoq } from './frontend/src/sheets/boq.js';"
        "const b = buildBoq({ spans: 3, spanLength: 12, width: 12 }, { carriageway: 7.5, abtl: 13, pileDiaMm: 600, pileLenM: 6, rows: 2, cols: 2 });"
        "const items = b.sections.flatMap((s) => s.items);"
        "process.stdout.write(JSON.stringify({"
        "  sections: b.sections.map((s) => s.code), nItems: b.nItems, subtotal: b.subtotal,"
        "  contingency: b.contingencyAmount, grand: b.grandTotal,"
        "  codes: items.map((i) => i.code),"
        "  amountMismatch: items.filter((i) => Math.abs(i.amount - Math.round(i.qty * i.rate * 100) / 100) > 0.05).map((i) => i.code),"
        "  missingRef: items.filter((i) => !i.ref).map((i) => i.code),"
        "  sectionSum: b.sections.reduce((s, x) => s + x.total, 0) }));"
    )
    assert got["nItems"] == len(got["codes"]) and got["nItems"] > 0
    assert "1701.4" in got["codes"], "superstructure concrete must be scheduled"
    assert "1801.1" in got["codes"], "600 mm bored piles must be scheduled"
    assert got["amountMismatch"] == [], f"amount != qty × rate for {got['amountMismatch']}"
    assert got["missingRef"] == [], f"MoRTH reference missing on {got['missingRef']}"
    assert abs(got["subtotal"] - got["sectionSum"]) < 0.5
    assert abs(got["grand"] - (got["subtotal"] + got["contingency"])) < 0.5
    assert got["grand"] > got["subtotal"] > 0


@needs_node
def test_boq_never_emits_zero_quantity_lines():
    """A take-off never invents or zeroes a line: every scheduled line carries a
    positive quantity and amount. Both abutments stand on pile groups, so a
    single-span deck still schedules piles even with no pier."""
    got = _run_node(
        "import { buildBoq } from './frontend/src/sheets/boq.js';"
        "const b = buildBoq({ spans: 1, spanLength: 12, width: 12 }, { carriageway: 7.5, abtl: 13 });"
        "const items = b.sections.flatMap((s) => s.items);"
        "process.stdout.write(JSON.stringify({"
        "  zeroQty: items.filter((i) => !(i.qty > 0)).map((i) => i.code),"
        "  zeroAmt: items.filter((i) => !(i.amount > 0)).map((i) => i.code),"
        "  codes: items.map((i) => i.code) }));"
    )
    assert got["zeroQty"] == [], f"zero-quantity lines scheduled: {got['zeroQty']}"
    assert got["zeroAmt"] == [], f"zero-amount lines scheduled: {got['zeroAmt']}"
    assert "1801.1" in got["codes"], "both abutments sit on piles, even without a pier"


@needs_node
def test_format_inr_uses_indian_grouping():
    got = _run_node(
        "import { formatINR } from './frontend/src/sheets/boq.js';"
        "process.stdout.write(JSON.stringify([formatINR(12345678.9), formatINR(1234.5), formatINR(900), formatINR(Number.NaN)]));"
    )
    assert got[0] == "1,23,45,678.90"
    assert got[1] == "1,234.50"
    assert got[2] == "900.00"
    assert got[3] == "–"


# ── workspace wiring ──────────────────────────────────────────────────────────


def test_workspace_wires_all_four_features_and_has_no_dead_nav():
    main = (ROOT / "frontend" / "src" / "main.tsx").read_text(encoding="utf-8")
    for symbol in ("buildComplianceReport", "LAYER_GROUPS", "STANDARD_PRESETS", "buildBoq", "SUPERSTRUCTURE_TYPES"):
        assert symbol in main, f"{symbol} is not wired into the workspace"
    # The sidebar nav and the dock must share one destination set, so no nav
    # entry can sit inert (the old "Standards review" / "Export package" bug).
    assert "layer-strip" in main and "dock-tabs" in main
    assert main.count("setDock(") >= 2, "both the nav and the dock must drive the active panel"
