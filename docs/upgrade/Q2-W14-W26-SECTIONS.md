# Q2 — Weeks 14–26: Legibility and Section Rebuild

**Theme:** a drawing is read at A1 in the hand, and a long section is read by a
site engineer checking whether he can build it. Fix text and title blocks, then
rebuild sheets 2 and 4 element by element.
**Entry requirement:** Q1 exit checklist complete.
**Exit gate:** fixed paper text hierarchy, no blank mandatory title field, sheet
2 and sheet 4 structurally complete and asserted.

---

## Week 14 — Text hierarchy

**Goal:** six legal text heights, defined once, used everywhere.

### Tasks
- [ ] `bridgecad_draw/text.py`: `TextClass` enum — `NOTE(2.5)`, `LABEL(2.5)`,
      `DIM(2.5)`, `SUBHEAD(3.5)`, `HEAD(5.0)`, `TITLE(7.0)`. All in paper mm.
- [ ] `def h(cls, frame) -> float: return cls.paper_mm * frame.plot_scale`.
- [ ] Ban raw floats: every `text()` call site takes a `TextClass`-derived
      height. Add a ruff custom rule or a grep-based CI check
      `scripts/check_text_heights.py` that fails on `height=` followed by a
      numeric literal in `bridgecad_draw/sheet*.py`.
- [ ] Delete `th = max(2.5, sc_h * 0.4)` from sheets 1, 2, 3, 4, 5.
- [ ] `assert_text_heights(doc, allowed)` on all sheets, `allowed` = the six
      paper values × plot scale.

### Acceptance
- Zero numeric literals in `height=` across sheet modules.
- All golden sheets pass `assert_text_heights`.

### Exit gate
`python scripts/check_text_heights.py` exits 0.

---

## Week 15 — Title block mandatory fields

**Goal:** a drawing that leaves the office carries a name, a date and a
checker.

### Tasks
- [ ] Add a `TitleBlockData` pydantic model with `mandatory` field list:
      project, bridge, drawing_no, drawing_title, revision, date, designed_by,
      checked_by, approved_by, scale, sheet_no, total_sheets.
- [ ] `draw_title_block` raises on a blank mandatory field unless
      `allow_blank=True` (test-only escape).
- [ ] Wire `ProjectMaster` → `TitleBlockData` in a single
      `titleblocks.from_project(pm)` factory. Sheets stop reading `pm` directly.
- [ ] Sheet 4 and 5: pass all fields; sheet 3 likewise.
- [ ] `assert_title_block_complete(doc)`.

### Acceptance
- All 8 sheets carry 12/12 mandatory fields on 5 golden cases.

### Exit gate
A deliberately blanked `checked_by` in a golden fixture fails the build.

---

## Week 16 — Sheet numbering and drawing-number series

**Goal:** kill the 7-vs-8 inconsistency.

### Tasks
- [ ] `booklet._SHEET_MANIFEST` becomes the single source: `total_sheets` is
      `len(_SHEET_MANIFEST)`, never a literal `"8"` in a sheet module.
- [ ] Replace the `"2"`/`"8"` literals in all sheet modules.
- [ ] Drawing numbers: `f"{prefix}-{sheet_no:02d}"` from the manifest, not
      per-module `GAD-00N` defaults.
- [ ] Fix `booklet.generate_package` scale bug: currently
      `sc = sheet_scale if scale_denom == 100 else scale_denom` — so any
      override forces the BOQ sheet to 1:N. Change to per-sheet scale unless
      explicitly overridden by a dict.
- [ ] `assert_sheet_numbering(doc, expected_no, expected_total)`.
- [ ] Update `GUIDE.md` §5.2 and `README.md` from 7 sheets to 8.

### Acceptance
- No `total_sheets="8"` literal in `bridgecad_draw/sheet*.py`.
- Sheet 7 renders at 1:1 when a caller passes `scale_denom=200`.

### Exit gate
Numbering assertions green; docs match reality.

---

## Week 17 — Revision strip and issue status

### Tasks
- [ ] Call `draw_revision_strip` on every sheet with `pm.revision_history`.
- [ ] Add `ISSUE STATUS` cell: `PRELIMINARY` / `FOR APPROVAL` /
      `FOR CONSTRUCTION`, from `pm.project_phase`, rendered bold.
- [ ] Add the `"Generated — not reviewed for construction"` banner to the title
      block (not just the manifest) while `project_phase != FOR_CONSTRUCTION`.
- [ ] `assert_issue_status_present(doc)`.

### Acceptance
- Every sheet has a revision strip and a non-empty issue status.

### Exit gate
Banner disappears only when phase is `FOR_CONSTRUCTION`.

---

## Week 18 — Notes, legend and abbreviation blocks

### Tasks
- [ ] `bridgecad_draw/notes.py`: standard note sets by discipline (concrete,
      steel, drainage, protection) drawn from `standards/notes.yaml`, each note
      with an IRC/MORTH source tag.
- [ ] Legend block: symbol → meaning, generated from the layers actually used
      on that sheet (not the full registry).
- [ ] Abbreviations block from `standards/abbreviations.yaml`.
- [ ] Place on sheets 1–6 in a reserved frame region declared in
      `coordinates.SheetFrame.sidebar_mm`.
- [ ] Sheet 5's hardcoded `notes = [...]` list moves to `notes.yaml`.

### Acceptance
- Every sheet carries ≥ 4 sourced notes, a legend of used symbols, and the
  abbreviation block.
- `assert_notes_sourced(doc)` — every note line has a bracketed source.

### Exit gate
**Q2-A gate reached.** Read a golden sheet at A1: legible without zoom.

---

## Week 19 — Sheet 2: deck build-up

**Goal:** the deck is a structure, not two lines and a hatch.

### Tasks
- [ ] Draw, bottom to top: soffit line, deck slab (thickness from
      `ss.deck_thickness_mm`), haunch if `is_box`/`is_t`, wearing course
      (`ss.wearing_coat_thickness_mm`) on `SUPER-WEARING`, kerb on `SUPER-KERB`,
      footpath on `SUPER-FOOTPATH` where `> 0`, parapet/crash barrier profile on
      `SUPER-PARAPET`/`SUPER-CRASH` at full `parapet_height_mm`, drainage
      spouts on `SUPER-DRAINAGE` at `ss.drainage_spacing_m`.
- [ ] Camber profile on `SUPER-CAMBER` from `gi.camber_mm` / `camber_method`.
- [ ] Separate hatches: concrete `ANSI31`, bituminous `AR-SAND`, earth `ANSI37`.
- [ ] Assert every one of those layers is used on sheet 2.

### Acceptance
- `assert_layer_used` passes for 7 layers on 5 golden cases.
- Deck build-up total thickness equals the model's sum within 1 mm.

### Exit gate
Un-xfail the week-4 `SUPER-WEARING` / `SUPER-KERB` / `SUPER-PARAPET` tests.

---

## Week 20 — Sheet 2: bearings, pedestals, expansion joints

### Tasks
- [ ] Delete the `py_ped_h`/pedestal variable that is computed and never drawn.
- [ ] Draw pedestals on `SUB-BEARING` from `pier_pedestal_height_m`, bearings
      from `project.bearings_joints.bearing_schedule` at their real
      `size_x_mm × size_y_mm`, correct type symbol per `bearing_type`.
- [ ] Expansion joints at each abutment on `SUB-EXPJOINT` from
      `expansion_joint_schedule`, width from `gap_mm`.
- [ ] Bearing schedule table on sheet 6 must match the symbols drawn on sheet 2
      — assert one symbol per schedule row.
- [ ] `assert_bearing_count(doc, expected)` from the schedule.

### Acceptance
- Bearing symbol count equals schedule quantity total.
- Zero pedestals missing.

### Exit gate
Un-xfail `SUB-BEARING` test; bearing count assertion green.

---

## Week 21 — Sheet 2: foundations in elevation

**Goal:** fix the inverted cap and draw the real foundation.

### Tasks
- [ ] Correct the ordering: pile tip < cutoff < cap bottom < cap top, with
      cap top = cap bottom + `pile_cap_thickness_mm`. Cutoff sits *inside* the
      cap. Assert `assert_foundation_ordering(doc, support)`.
- [ ] Pile cap as a rectangle on `FOUND-CAP`, full `pile_cap_width_m`, with the
      discarded `pile_cap_h_mm` from week 7 now used.
- [ ] Pile group elevation: `piles_per_pier` shafts at `pile_spacing_m` on
      `FOUND-PILE`, correct `pile_diameter_mm`.
- [ ] Branch by `fd.type`: `WELL` → steining circles on `FOUND-WELL`;
      `OPEN` → stepped footing on `FOUND-OPEN`; `PILE` → the above.
- [ ] Delete the current loop that draws piles under abutments *and* piers
      identically.

### Acceptance
- Ordering assertion green on 5 golden cases.
- All three foundation branches render on their fixtures.

### Exit gate
A hand-checked golden sheet shows cap above cutoff, tip below.

---

## Week 22 — Sheet 2: strata, water, protection works

### Tasks
- [ ] Soil stratigraphy from `inputs/` borelog data on `FOUND-SOIL`: layer
      boundaries, `ANSI37` hatch, SPT-N labels.
- [ ] HFL / LWL / scour lines move to correct RLs from `hydraulic_data`, with
      the `DASHED`/`DASHED2` linetypes from the registry (currently
      hardcoded).
- [ ] Launching apron and stone pitching at each pier on `CIVIL-*` per
      `hydraulic_data.design_scour_depth_m`.
- [ ] Freeboard dimension becomes a true DIMENSION entity (week 12 rewrite).

### Acceptance
- `FOUND-SOIL` used whenever borelog input exists; absent (not faked) when not.
- Water lines at correct RLs, asserted within 1 mm.

### Exit gate
Scour/apron geometry present on the 3 river fixtures.

---

## Week 23 — Sheet 2: sign-off

### Tasks
- [ ] Section cut marker on sheet 1 (`A-A`) maps to sheet 2's view; assert the
      marker chainage equals sheet 2's origin chainage.
- [ ] Chainage axis graduations at 5 m intervals, labels every 20 m, `CH` prefix
      with correct km format.
- [ ] Engineer walk-through of sheet 2 on all 5 golden cases; log every comment
      in `DEFECT-LEDGER.md` as a new row with a closing week.
- [ ] Update `METRICS.md`.

### Acceptance
- Marker/origin correlation asserted.
- Reviewer comments logged, none unassigned.

### Exit gate
**Q2-B gate reached.** Sheet 2 is structurally complete.

---

## Week 24 — Sheet 4: foundation plan

### Tasks
- [ ] Pile cap plan per `foundation_details.type`, scaled from the real
      `pile_cap_width_m × pile_cap_length_m`, with `compute_pile_group_layout`
      positions — delete the `0.35r` decorative inner circle if it is not a
      real feature.
- [ ] Skew: rotate the cap and pile grid by `skew_angle_deg` (sheet 4 currently
      ignores skew entirely).
- [ ] Well branch: outer/inner steining circles, dredge hole, well curb, on the
      correct layers.
- [ ] Open branch: stepped footing plan with offsets.
- [ ] `assert_support_skewed(doc, angle)`.

### Acceptance
- Skewed fixtures show a skewed cap matching sheet 1's deck shear.

### Exit gate
Skew assertion green on the 15° fixture.

---

## Week 25 — Sheet 4: sections and schedule

### Tasks
- [ ] Elevation at true `v_exag` declared per week 8.
- [ ] Reinforcement callouts: main bar dia/spacing per face, on `STRUC-DETAIL`.
- [ ] Pile schedule table: every column sourced from `fd` or `hd`, no `or`
      fallback defaults — missing input renders `—` not `1500`.
- [ ] `assert_table_cells_sourced(doc)`.

### Acceptance
- No fallback constant appears in a table cell that the model could supply.

### Exit gate
Blank an input in a golden fixture; the cell shows `—`.

---

## Week 26 — Sheet 4: sign-off and Q2 retro

### Tasks
- [ ] Engineer walk-through, comments logged.
- [ ] Retro: `METRICS.md`, `DEFECT-LEDGER.md` (rows 12 and 14 closed),
      `PROGRESS.md`.
- [ ] Write `Q3-W27-W38-DETAILS.md` before week 27.

### Acceptance
- All Q2 exit criteria met.

### Exit gate
**Q2 complete.**

---

## Q2 exit checklist

- [ ] Zero numeric `height=` literals
- [ ] 12/12 mandatory title-block fields on every sheet
- [ ] Revision strip + issue status + sourced notes + legend on every sheet
- [ ] Sheet 2 carries 7 previously-unused layers
- [ ] Foundation ordering asserted
- [ ] Skew respected on sheet 4
- [ ] `DEFECT-LEDGER.md` rows 8, 9, 10, 11, 12, 14 closed
