# Continual improvement programme — detail sheets 04 / 05

**Scope:** `frontend/src/sheets/**`, `scripts/robotic_sheet_detail_audit.py`, `tests/draw/test_sheet4_sheet5_present.py`, `bridgecad_draw/sheets/sheet4_foundation.py`, `sheet5_pier_abutment_details.py`, and the themes that render them.

**Goal:** the detail sheets get *better* every cycle and never silently disappear from a deploy again. Improvement is ratcheted, not hoped for.

---

## 1. Non-negotiables

These hold on every commit. A PR that breaks one is rejected regardless of feature value.

| ID | Invariant | Enforced by |
|---|---|---|
| N1 | Sheets 04 and 05 are reachable from the deployed bundle | `test_registry_lists_sheets_4_and_5` |
| N2 | Both wing walls exist, left and right, with positive face run and return | `E_WALL_COUNT`, `E_WALL_SIDE`, `E_FACE_RUN`, `E_RETURN` |
| N3 | `length >= face_run` for every wall | `E_HYPOTENUSE` |
| N4 | The ABTL ladder rung is printed beside the length | `E_ABTL_SOURCE` |
| N5 | Every required layer and label is emitted | `E_LAYER_MISSING`, `E_LABEL_MISSING` |
| N6 | No NaN, no zero-size rect, no sheet breaking the border | `E_NAN_PRIM`, `E_ZERO_RECT`, `E_EXTENTS` |
| N7 | No sheet component styles itself through a shared class | `test_no_shared_class` (add in week 1) |
| N8 | Randomised audit is clean at the current case budget | `test_random_audit_is_clean` |

N1–N6 are machine-checked today. N7 needs the guard test below; add it first.

```python
# tests/draw/test_no_shared_class.py
from pathlib import Path
SHEETS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "sheets"
FORBIDDEN = ("drawing-sheet", "sheet-bg", "sheet-border", "sheet-inner-border")

def test_no_shared_class():
    for name in ("Sheet04Foundation.tsx", "Sheet05PierAbutment.tsx", "SheetChrome.tsx"):
        body = (SHEETS / name).read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in body, f"{name} reintroduced shared class {token}"
```

---

## 2. Cadence

| When | Activity | Artefact |
|---|---|---|
| Every commit | N1–N8 gate, `tsc --noEmit`, build | CI green |
| Every PR | Debt ledger touched if scope shifts, `docs/PATCH_RESTORE_SHEET4_5.md` if install steps change | review checklist |
| Weekly | One mutation added to the harness; one debt item burned or re-scoped | diff + ledger edit |
| Fortnightly | Parity run against the Python sheets on the 28 E2E fixtures | parity report |
| Monthly | Budget review (§4), accessibility sweep, print check on A1 | signed review note |
| Per release | Failure drill (§10), canary (§11), signoff (§13) | drill log |

No cycle may close with the debt ledger longer than it opened unless the growth is justified in writing.

---

## 3. Extension protocols

### 3.1 New sheet (e.g. 06 bearings, 07 drainage)

1. Add `SHEET_06` constants to `detailGeometry.js`; keep the panel layout inside the border with at least 12 mm margin.
2. Emit layer-tagged primitives only — no coordinates in the `.tsx`.
3. Register `REQUIRED_LABELS[6]` and `REQUIRED_LAYERS[6]` before writing the builder, so the audit drives the design.
4. Add `Sheet06.tsx` using `SheetFrame`/`Prims` with `theme`.
5. Add registry entry, nav is automatic.
6. Add one fixed fixture and one seeded range to the harness.
7. Golden case: pin the default-parameter primitive count in `tests/draw/`.

### 3.2 New layer

1. Add to `LAYERS` **and** `TOKEN` in `theme.ts` — both, or the layer renders black.
2. Add to `REQUIRED_LAYERS` for the sheet that needs it.
3. If it is dashed, add to `LINETYPE`.
4. Name it from the IRC set already used in `bridgecad_draw/layers.py`; do not invent a prefix.

### 3.3 New theme

Themes are additive, never mutations. A theme must supply all 15 tokens; missing tokens are a compile error because the type is exhaustive. Reviewers check contrast at 100% zoom and print legibility.

### 3.4 New parameter

1. `normalizeParams` clamp with a stated band and a comment naming the governing clause.
2. `DETAIL_DEFAULTS` entry.
3. `DETAIL_FIELDS` entry in `main.tsx` with step.
4. Oracle or invariant if the value drives geometry.
5. Fixture at both clamp ends.

---

## 4. Budgets

Recorded per release in `docs/verification/BENCHMARKS.md`. Regression beyond a budget needs an ADR.

| Metric | Ceiling |
|---|---|
| Randomised cases in CI | 3000 (raise only) |
| Mutation score on `detailGeometry.js` | ≥ 0.90 |
| Fixed fixtures in `tests/draw/` | ≥ 12 (raise only) |
| `buildSheet4` + `buildSheet5` wall time, default params | ≤ 8 ms |
| Bundle contribution of `sheets/**` | ≤ 60 kB gzipped |
| Render commits per keystroke | ≤ 1 (debounce 120 ms if exceeded) |
| Audit codes without a fixture | 0 |
| Debt items older than 90 days | ≤ 3 |

---

## 5. Parity discipline

The Python sheets are the source of truth for the CAD package; the JS sheets are the deploy mirror. Parity is checked both ways, fortnightly, on the 28 fixtures in `tests/e2e/fixtures/`.

- **Geometry parity:** face run, length, return, splay, pile count, cap dimensions must match the Python output within 1e-6 m.
- **Content parity:** required label set and layer set must match.
- **Divergence:** file as debt with `parity` label and a date. A divergence older than 30 days blocks release.

```bash
python scripts/robotic_sheet_detail_audit.py --cases 3000 --seed "$(date +%Y%m%d)"
python scripts/parity_detail_sheets.py --fixtures tests/e2e/fixtures --tolerance 1e-6
```

`parity_detail_sheets.py` is debt **D-02** until it exists; write it before the second parity cycle.

---

## 6. Debt ledger

One row per item, in `docs/upgrade/DEFECT-LEDGER.md`, section "Detail sheets". Nothing here is allowed to be folklore.

| ID | Item | Impact | Exit criterion |
|---|---|---|---|
| D-01 | `toDxf` emits a minimal AC1015 skeleton | may fail strict CAD validators | one export opens in a real viewer and round-trips |
| D-02 | No automated parity against Python sheets | silent drift | `parity_detail_sheets.py` green on 28 fixtures |
| D-03 | PDF is print-to-file only, no vector path | weaker deliverable | client-side vector PDF with embedded fonts |
| D-04 | Bearing schedule values hardcoded in `buildSheet5` | schedule can contradict the model | rows read from `bearings_joints` |
| D-05 | No well-foundation panel on sheet 5 | well bridges under-drawn | well variant rendered with `FOUND-WELL` |
| D-06 | Layer set is a subset of the 53 IRC layers | package mismatch | layers reconciled with `layers.py` |
| D-07 | No scale bar or north arrow | drafting completeness | both drawn on every sheet |
| D-08 | Zoom has no drag-pan | awkward at 200% | pointer drag pans the stage |
| D-09 | No inter-panel overlap check | panels can collide at extremes | `E_OVERLAP` with bbox test |
| D-10 | Print theme switch is timeout-based | flaky on slow devices | `beforeprint` hook |
| D-11 | No fixture at splay 15 and 60 | clamp ends untested | two fixed fixtures |
| D-12 | `CHANGELOG.md` not updated for this work | history gap | entry under Unreleased |

Rules: no new audit code without a fixture; no debt row without an exit criterion; three consecutive 90-day-old items triggers a debt-only sprint.

---

## 7. Failure drills

Monthly, on a scratch branch, break one thing and confirm the gate catches it:

| Drill | Must fail |
|---|---|
| Delete `WING WALL RIGHT` label | `E_LABEL_MISSING`, `test_labels_present_in_core` |
| Remove `splay` clamp | `E_SPLAY_RANGE` |
| Drop the right-hand wall from `walls` | `E_WALL_COUNT` |
| Remove the registry entry | `test_registry_lists_sheets_4_and_5` |
| Add `className="drawing-sheet"` to `Sheet05` | `test_no_shared_class` |
| Return `prims: []` | `E_EMPTY`, `E_THIN_SHEET` |

A drill that passes silently is itself a defect: fix the gate, log it, and re-run.

---

## 8. Review gates

PRs touching `frontend/src/sheets/**` need:

- [ ] N1–N8 green
- [ ] No new audit code without a fixture
- [ ] No hardcoded colour in a component
- [ ] `theme.ts` token used for every new ink
- [ ] Clamp band commented with the governing clause
- [ ] Both splay extremes exercised
- [ ] Print check at A1 in the paper theme
- [ ] Debt ledger row added or burned
- [ ] `CHANGELOG.md` under Unreleased

Definition of done includes a screenshot of the affected sheet at 100% in both themes.

---

## 9. Accessibility and print

- Sheet text renders at 2.1–4.2 user units; nothing below 2.0 except table body text at 2.1.
- Paper theme contrast ≥ 7:1 for text, ≥ 3:1 for structure strokes.
- Every `<svg>` carries `role="img"` and an `aria-label` naming the sheet and its panels.
- Print hides chrome (§ print block) and must fit A1 landscape on one page; two pages is a defect.
- No information conveyed by colour alone: levels and dimensions are always labelled.

---

## 10. Canary and rollback

Deploy preview first, then production.

1. Preview deploy: open Sheet 05, both themes, both splay extremes, run one local DXF export.
2. Production: verify the audit chip reads `audit clean` and the sheet register lists 01 / 04 / 05.
3. Rollback: `git revert` the merge commit; the sheets are additive so revert is clean. If revert is not possible, `netlify` → Deploys → previous deploy → Publish.

Never promote a deploy whose audit chip reads a non-zero count.

---

## 11. Documentation of record

| Document | Owner | Update trigger |
|---|---|---|
| `docs/PATCH_RESTORE_SHEET4_5.md` | sheet owner | install or netlify steps change |
| `docs/CONTINUAL_IMPROVEMENT_SHEET_DETAILS.md` | sheet owner | budgets, cadence, or protocols change |
| `docs/upgrade/DEFECT-LEDGER.md` | maintainer | every cycle |
| `CHANGELOG.md` | maintainer | every PR |
| ADR in `docs/adr/` | author | any budget or protocol deviation |

ADR template:

```markdown
# NNNN — <decision>

- Status: proposed | accepted | superseded by NNNN
- Context: <what forced the decision>
- Decision: <what we do>
- Consequences: <budgets moved, debt created, gates affected>
```

---

## 12. Retrospective prompts (quarterly)

1. Which audit codes fired in production-adjacent runs, and what did they teach?
2. Which invariants are load-bearing and which are ceremony?
3. Where does the JS mirror drift from Python, and is the mirror still worth keeping?
4. Is the sheet still readable by a bridge engineer at 1:100 on paper?
5. What did a reviewer have to explain twice?

Answers feed the next cycle's debt list, not a slide deck.

---

## Adoption order (first four weeks)

1. **Week 1** — add `test_no_shared_class`, wire CI, seed the ledger with D-01…D-12, raise CI cases to 3000.
2. **Week 2** — write `parity_detail_sheets.py`, run the first parity pass, file divergences.
3. **Week 3** — burn D-11 and D-10 (cheap, high value), add the `E_OVERLAP` fixture.
4. **Week 4** — first failure drill, first monthly budget review, first ADR if any budget moved.

Programme health is simple: the ledger shortens, the fixture count rises, and the audit chip stays clean in production.
