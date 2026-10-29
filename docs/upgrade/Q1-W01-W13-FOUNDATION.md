# Q1 — Weeks 1–13: Foundation

**Theme:** stop guessing, start measuring, then enforce one coordinate system and
real dimensions.
**Exit gate:** no sheet calls `draw_border`; every dimension is an entity with a
correct `dimlfac`; harness green on 5 golden cases.

**Rule for the whole quarter:** every week starts by writing an assertion that
fails, and ends with it passing. A week that adds drawing features without an
assertion is not done.

---

## Week 1 — Freeze and baseline

**Goal:** capture exactly how bad it is, so later weeks can prove improvement.

### Tasks
- [ ] Branch `upgrade/q1-foundation`. Tag `baseline-pre-upgrade`.
- [ ] Freeze: add `docs/upgrade/FROZEN.md` listing the §8 freeze list. Add a
      `CODEOWNERS` entry so engine/AI/react PRs need explicit approval.
- [ ] Write `scripts/dump_dxf_facts.py`: takes a DXF, emits JSON of entity
      count by type, count by layer, bbox, text heights present, dimension
      entity count, layer names used.
- [ ] Generate all 8 sheets for all 28 fixtures into `build/baseline/`.
      Commit the JSON facts only (gitignore the DXFs).
- [ ] Write `docs/upgrade/METRICS.md` from the facts. Fill the baseline column
      in MASTER-PLAN §5.
- [ ] Write `docs/upgrade/DEFECT-LEDGER.md` with all 14 MASTER-PLAN §1 defects
      as rows: id, symptom, file, line, closing week, status.

### Acceptance
- `build/baseline/facts/` holds 224 JSON files (28 × 8).
- `METRICS.md` baseline column complete.
- `DEFECT-LEDGER.md` has 14 rows, none blank.

### Exit gate
`python scripts/dump_dxf_facts.py --selftest` runs clean.

---

## Week 2 — Golden cases

**Goal:** pick 5 fixtures that span the bridge families, and freeze their model
inputs. These are the only cases that matter for visual and structural review.

### Tasks
- [ ] Select and copy to `tests/draw/golden/`:
      `simple_12m` (slab), `continuous_3x12m` (continuous slab),
      `girder_4x18m` (PSC girder), `box_culvert_8m` (box),
      `GAD 3×18 m skew 15°` (skew).
- [ ] For each, write `expected_facts.json` from the week-1 baseline.
- [ ] Write `tests/draw/test_golden_frozen.py`: assert each golden fixture's
      model inputs hash to a pinned SHA-256. Changing an input requires a
      deliberate hash bump.

### Acceptance
- 5 golden directories, each with fixture + `expected_facts.json`.
- Input hashes pinned.

### Exit gate
Editing any golden fixture input without bumping the hash fails the test.

---

## Week 3 — Assertion harness core

**Goal:** a reusable library that asserts the properties industry drawings have
and these do not.

### Tasks
- [ ] Write `tests/draw/dxf_assert.py` with:
  - `load(path) -> Drawing` via ezdxf
  - `entities_by_layer(doc)`, `entity_types(doc)`
  - `bbox(doc)`, `assert_inside_frame(doc, frame)` 
  - `assert_layer_used(doc, layer)`, `assert_layer_absent(doc, layer)`
  - `text_heights(doc) -> set[float]`
  - `assert_text_heights(doc, allowed: set[float], tol=0.01)`
  - `dimensions(doc)`, `assert_dimension_count(doc, minimum)`
  - `assert_dimension_scale(doc, expected_lfac)`
  - `assert_no_duplicate_geometry(doc)` — same layer + same point pair
  - `assert_no_zero_length_lines(doc)`
  - `assert_drawn_extent(doc, min_mm, max_mm)` — real-world extent check
- [ ] Every assertion returns a structured failure with entity handles, not a
      bare `AssertionError`.

### Acceptance
- 14 assertion helpers, unit-tested against hand-built fixtures in
  `tests/draw/fixtures/` (one passing, one failing each).

### Exit gate
`pytest tests/draw/test_dxf_assert.py` — 28 tests, all pass.

---

## Week 4 — Harness against golden cases, baseline defects recorded

**Goal:** turn the 14 defects into executable expectations that currently fail.

### Tasks
- [ ] Write `tests/draw/test_golden_current.py` asserting, per golden case:
      - every sheet declares a scale in the title block
      - every sheet's bbox sits inside its declared frame
      - dimension entity count ≥ 10 per sheet (sheet 7 exempt)
      - text heights drawn from `{2.5, 3.5, 5.0, 7.0}` × plot scale
      - `SUB-BEARING` used on sheet 2
      - `FOUND-CAP` used on sheet 2
      - `SUPER-WEARING`, `SUPER-KERB`, `SUPER-PARAPET` used on sheet 3
      - pier `x` on sheet 2 equals pier `x` on sheet 1 within 1 mm
      - no duplicate geometry
      - pile cap top below pile cutoff on sheet 4
- [ ] Mark each with `pytest.mark.xfail(reason=..., strict=True)` and the
      ledger id. `strict=True` means the test fails once fixed until unmarked —
      which is the point.
- [ ] Wire `tests/draw/run_dxf_assertions.py` to emit a pass/xfail/fail table.

### Acceptance
- ≥ 40 xfailed assertions, all attributed to a ledger row.

### Exit gate
`python tests/draw/run_dxf_assertions.py` reports `0 failed`, `≥ 40 xfail`.

**Q1-A gate reached.** No refactoring has happened yet; the repo is measurably
bad and every later week has a scoreboard.

---

## Week 5 — Delete `draw_border` from sheet 1

**Goal:** first real contract migration, on the simplest sheet, alone.

### Tasks
- [ ] In `sheet1_plan.py`, replace `draw_border(msp, "A1")` +
      `draw_title_block(...)` with `frame_w, frame_h = draw_sheet_frame(msp, "sheet1_plan", ...)`.
- [ ] Delete the module's `_SHEET_W`, `_SHEET_H`, `_MARGIN`, `_TB_H`,
      `_PLAN_X0`, `_PLAN_Y0`, `_PLAN_W`, `_PLAN_H` constants; derive the drawing
      region from the returned frame.
- [ ] Replace the local `hpos()`/`vpos()` closures with `CoordMapper` built from
      `coordinates.FRAMES["sheet1_plan"]`.
- [ ] Remove the `(Not to Scale …)` label.
- [ ] Un-xfail: sheet-1 frame assertions, sheet-1 scale assertion.

### Acceptance
- No `draw_border` call remains in `sheet1_plan.py`.
- Sheet 1 bbox inside frame on all 5 golden cases.
- Entity count on sheet 1 within ±15% of baseline (no geometry lost).

### Exit gate
All 28 fixtures still emit 8 sheets; sheet 1 assertions pass.

---

## Week 6 — True scale on sheet 1, or declared NTS

**Goal:** resolve the arithmetic honestly. A 220 m bridge cannot be 1:100 on A1.

### Tasks
- [ ] Compute required paper extent at the declared scale. If it fits the
      drawing region, keep the scale and centre the view.
- [ ] If it does not fit, choose the next *standard* scale from
      `coordinates.PLOT_SCALES` that fits, write it into `FRAMES`, and stamp it.
- [ ] If even 1:1000 does not fit, mark the sheet `SCALE: NTS` in the title
      block and add a graphic scale bar. Assert `NTS` implies a scale bar exists.
- [ ] Add `assert_scale_honest(doc, frame)` to the harness: measured model
      extent ÷ frame extent equals the declared denominator within 2%, or the
      title block reads `NTS`.

### Acceptance
- All 5 golden cases pass `assert_scale_honest`.

### Exit gate
No golden sheet simultaneously claims a ratio and violates it.

---

## Week 7 — Sheet 2 frame migration

Same procedure as week 5 on `sheet2_long_section.py`.

### Tasks
- [ ] `draw_sheet_frame(msp, "sheet2_long_section", ...)`; delete local layout
      constants.
- [ ] Replace `hx()`/`vy()` with a `CoordMapper`; **delete the unused
      `CoordMapper(...)` construction that currently does nothing.**
- [ ] Fix the three dead statements while in the file:
      - `float(fd.pile_cap_thickness_mm or 1500)/1000.0*sc_v*v_exag` → assign
        `pile_cap_h_mm`
      - `(cols - 1) * float(fd.pile_spacing_m or 2.4) * sc_h` → `group_w_mm`
      - the two bare `toc_rls[i] if ... else ...` lines → delete
- [ ] Un-xfail sheet-2 frame assertions.

### Acceptance
- No `draw_border`, no `hx`/`vy` closures, no dead statements in the module.
- Frame assertions pass on 5 golden cases.

### Exit gate
Sheet 2 entity count within ±10% of baseline.

---

## Week 8 — Declare vertical exaggeration properly

**Goal:** exaggeration is legitimate; hiding it is not.

### Tasks
- [ ] Move `v_exag` out of the function signature into
      `coordinates.SheetFrame.vertical_exaggeration` (default 1.0).
- [ ] Set sheet 2 to 1.0 where it fits, else 2.0 — decided by the same
      fit arithmetic as week 6, not hardcoded.
- [ ] When `v_exag != 1.0`, the title block must read
      `H 1:100  V 1:50 (V.E. 2×)` and the sheet must carry two scale bars.
- [ ] `assert_exaggeration_declared(doc, frame)`.

### Acceptance
- `v_exag` appears nowhere as a literal in sheet modules.
- All golden sheets with `v_exag != 1.0` pass the assertion.

### Exit gate
Grep for `v_exag` returns only `coordinates.py` and the harness.

---

## Week 9 — Sheets 3, 4, 5 frame migration

### Tasks
- [ ] Same procedure, one commit per sheet.
- [ ] Sheet 4: remove the hardcoded `sc = 20.0`, the `-100.0` Y offset in
      `evy()`, and the `sc * 1.5` vertical fudge — all become `CoordMapper`.
- [ ] Sheet 5: remove `sc = 12.0`.
- [ ] Sheet 4: pass the missing title-block arguments (`scale_str`, date,
      designed/checked/approved, client, consultant).

### Acceptance
- No `draw_border` call anywhere in `bridgecad_draw/`.
- Sheets 3, 4, 5 inside frame on all golden cases.

### Exit gate
`grep -rn "draw_border" packages/bridgecad-draw/bridgecad_draw/` → empty except
the definition in `titleblocks.py`.

---

## Week 10 — Cross-sheet coordinate correlation

**Goal:** the same pier is at the same place on every sheet. This is the
assertion that makes the whole contract worth having.

### Tasks
- [ ] Give every sheet a declared origin in chainage/level space via
      `FRAMES[...].origin_chainage_m` / `origin_level_m`.
- [ ] Sheet 1 origin becomes the reference; sheets 2 and 5 derive from it.
- [ ] Write `assert_cross_sheet_alignment(pkg)`: pier centreline `x` on sheet 1
      equals pier `x` on sheet 2 equals pier `x` on sheet 5, within 1 mm after
      origin translation. Same for abutment chainages.
- [ ] Un-xfail the cross-sheet test from week 4.

### Acceptance
- Alignment passes on 5 golden cases.

### Exit gate
**Q1-B gate reached.** Coordinate contract is enforced by test, not by
convention. Update `DEFECT-LEDGER.md` rows 3 and 4 to `closed`.

---

## Week 11 — DIMSTYLE infrastructure

**Goal:** dimensions that are entities and read real metres.

### Tasks
- [ ] `bridgecad_draw/dimstyles.py`: create `BRG-DIM-25`, `BRG-DIM-35`,
      `BRG-DIM-50` per the standard set, with `dimtxt` from paper height ×
      plot scale, `dimasz` 2.5× text, `dimexe`/`dimexo` per IRC SP:55,
      `dimclrt` BYLAYER, `dimdec` 0 for mm / 3 for m, `dimlfac = 1000` so model
      mm reads as metres.
- [ ] `setup_dimstyles(doc, frame)` called from `new_sheet`.
- [ ] `assert_dimension_scale(doc, 1000)` on every sheet.

### Acceptance
- `dimlfac` = 1000 on every dimstyle. No dimension drawn before styles exist.

### Exit gate
A hand-run dimension on a scratch DXF reads `12.500` for a 12.5 m span.

---

## Week 12 — Replace `dim_linear_h` / `dim_linear_v`

### Tasks
- [ ] Rewrite both in `primitives.py` to emit `msp.add_linear_dim(...)` with
      `.render()`, correct `dimstyle`, and `override` for the case at hand.
- [ ] Keep the old exploded versions as `dim_linear_h_exploded` for one release.
- [ ] Convert sheet 1 span dims, overall width, overall length.
- [ ] Delete the duplicate `CW=11.500 m` text beside sheet 3's native dim.
- [ ] Un-xfail dimension-count assertions on sheet 1.

### Acceptance
- Sheet 1 has ≥ 12 DIMENSION entities, 0 exploded dims.
- Rendered text reads metres, not paper mm.

### Exit gate
`assert_dimension_scale` passes on sheet 1 for 5 golden cases.

---

## Week 13 — Dimension rollout, sheets 2 and 3

### Tasks
- [ ] Convert sheet 2: span chainages, freeboard, pier offsets, all RL tags
      that are true dimensions.
- [ ] Convert sheet 3: overall width, carriageway, deck depth, girder depth,
      kerb, footpath — all native.
- [ ] `assert_dimension_count` ≥ 10 on sheets 1–6.
- [ ] Quarter retro: update `METRICS.md`, `DEFECT-LEDGER.md`, `PROGRESS.md`.

### Acceptance
- 0 exploded dimensions in sheets 1, 2, 3.
- All dimension assertions green on 5 golden cases.

### Exit gate
**Q1-C gate reached.** Write `Q2-W14-W26-SECTIONS.md` before week 14 starts.

---

## Q1 exit checklist

- [ ] No sheet calls `draw_border`
- [ ] No hardcoded scale literal in any sheet module
- [ ] Every sheet passes frame and origin assertions
- [ ] Cross-sheet pier alignment asserted and green
- [ ] ≥ 60 native DIMENSION entities per golden package, all `dimlfac` 1000
- [ ] `METRICS.md`: sheets declaring a true scale ≥ 6 / 8
- [ ] `DEFECT-LEDGER.md` rows 3, 4, 5, 7 closed
- [ ] 28 fixtures still emit 8 sheets
