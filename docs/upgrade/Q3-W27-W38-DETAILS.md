# Q3 — Weeks 27–38: Details, Geometry Correctness, BOQ

**Theme:** detail sheets that a fabricator can work from, geometry that survives
a skew and a camber, and quantities derived rather than multiplied.
**Entry requirement:** Q2 exit checklist complete.
**Exit gate:** sheets 5 and 6 complete, skew/camber correct across all sheets,
formwork and rebar derived from geometry.

---

## Week 27 — Sheet 5: pier detail, geometry

### Tasks
- [ ] Pier elevation from real `pier_type`: single/multi-column, hammerhead,
      wall. Shaft taper per type.
- [ ] Pier cross-section (plan cut) with shaft width × length, chamfers,
      reinforcement cover.
- [ ] Foundation connection: pile cap stub so the pier does not float at
      `pier_by` (current defect).
- [ ] Bearing shelf, pedestal, drip groove.
- [ ] `assert_support_connected(doc)` — pier bbox touches cap bbox.

### Acceptance
- No floating support on any golden case.

### Exit gate
Connectivity assertion green.

---

## Week 28 — Sheet 5: pier reinforcement

### Tasks
- [ ] Bar marks: vertical main bars, links, cover, lap lengths, on
      `STRUC-DETAIL` at 1:20 detail scale.
- [ ] Bar bending schedule table: mark, dia, shape, length, number, total —
      feeding the week-35 rebar derivation.
- [ ] `assert_bbs_matches_callouts(doc)` — every callout mark exists in the BBS.

### Acceptance
- Callout/BBS parity on 5 golden cases.

### Exit gate
Deliberately break a mark; test fails.

---

## Week 29 — Sheet 5: abutment and wing walls

### Tasks
- [ ] Abutment elevation and section from `abutment_type`: gravity, cantilever,
      counterfort, box. Ballast wall, dirt wall, return walls, approach slab
      with dowels.
- [ ] Wing wall at `wing_wall_angle_deg` and `wing_wall_splay_length_m` — the
      current fixed 4-point polygon ignores both.
- [ ] Backfill hatch `ANSI37` on `SUB-BACKFILL`.
- [ ] `assert_wing_angle(doc, angle)`.

### Acceptance
- Wing wall angle matches model within 0.5°.

### Exit gate
Wing angle assertion green.

---

## Week 30 — Sheet 6: bearings and joints

### Tasks
- [ ] One detail per bearing type in the schedule: elastomeric (layers,
      dimensions), pot-PTFE (pot, piston, PTFE, restraint), spherical.
- [ ] Fixed / guided / free restraint symbols per `fixed_or_guide_or_free`.
- [ ] Expansion joint details by `joint_type` with `gap_mm` and
      `movement_range_mm`, seal, nosing, anchorage.
- [ ] Schedule tables matching sheet 2's symbols.
- [ ] `assert_bearing_schedule_matches_sheet2(pkg)`.

### Acceptance
- Zero mismatch between sheet 2 symbols and sheet 6 schedule rows.

### Exit gate
**Q3-A gate reached.**

---

## Week 31 — Skew correctness, sheets 1 and 3

### Tasks
- [ ] Sheet 1: replace the deck parallelogram approximation with a true skew
      rotation about the centreline; pier and abutment footprints rotate with
      it (currently axis-aligned).
- [ ] Sheet 3: section plane normal to the deck edge, so a skewed bridge gets a
      normal section — not an orthogonal one.
- [ ] `assert_skew_consistent(pkg, angle)` across sheets 1, 2, 3, 4, 5.
- [ ] `skew_direction` honoured, not just magnitude.

### Acceptance
- Consistent skew on all sheets for the 5° and 15° fixtures.

### Exit gate
Skew consistency assertion green.

---

## Week 32 — Superelevation and cross-fall

### Tasks
- [ ] `gi.superelevation_pct` and `cross_fall_pct` drive sheet 3's deck
      rotation and the drainage slope arrows.
- [ ] Camber + superelevation combine correctly; assert the deck top is a
      single continuous profile, not two independent offsets.
- [ ] Transition zone: superelevation run-off length drawn on sheet 1.

### Acceptance
- Deck top profile monotonic per the model; assertion green.

### Exit gate
A 4% superelevation fixture renders a visibly rotated deck.

---

## Week 33 — Vertical alignment and gradient

### Tasks
- [ ] `gi.gradient_pct` and the vertical curve drive sheet 2's deck line —
      currently perfectly flat regardless of input.
- [ ] Crest/sag curve drawn with tangent points and K value.
- [ ] `assert_gradient_matches(doc, pct)`.

### Acceptance
- Deck line slope on sheet 2 equals `gradient_pct` within 0.1%.

### Exit gate
A 3% gradient fixture renders a sloped deck.

---

## Week 34 — Curved bridges (first pass)

### Tasks
- [ ] Where `curved_bridge_flag`, sheet 1 draws a true arc; supports radial.
- [ ] Sheet 3 section radial, not orthogonal.
- [ ] Out of scope: spiral transitions. Log as a Q4 item.

### Acceptance
- Curved fixture renders arcs; orthogonal fallback removed.

### Exit gate
**Q3-B gate reached.**

---

## Week 35 — Formwork derivation

**Goal:** retire the 3.0–6.0 multipliers in `bill/processor.py`.

### Tasks
- [ ] `bridgecad_core/quantities/formwork.py`: area = developed perimeter ×
      length, per component, from geometry. Soffit, sides, curved soffit
      counted separately.
- [ ] Replace `_FORMWORK_FACTORS` and the `cap_cum * 5.5` style expressions.
- [ ] Keep a comparison test: derived vs old multiplier within ±25%, logged.
- [ ] Update `_ESTIMATED_CODES` — formwork codes move to `_CALCULATED`.

### Acceptance
- Zero formwork multipliers remain.
- `1702.1`/`1702.2`/`1702.3` classify as `calculated` with a formula.

### Exit gate
`build_boq()` shows no formwork line as `estimated`.

---

## Week 36 — Rebar derivation

### Tasks
- [ ] `quantities/rebar.py`: kg from the week-28 BBS plus the core bar
      schedules for other components. Cutting length, laps, hooks, wastage 3%.
- [ ] Replace `_REBAR_FACTORS` (0.05–0.135 t/cum).
- [ ] Emit a bar schedule per component into the BOQ appendix.
- [ ] Missing BBS → `not_calculated` with reason, never a ratio.

### Acceptance
- Zero rebar multipliers.
- Derived tonnage within ±15% of the old ratio on all fixtures (sanity, not
  correctness).

### Exit gate
`1601.1` lines are `calculated` or `not_calculated`, never `estimated`.

---

## Week 37 — Earthwork and protection derivation

### Tasks
- [ ] Excavation from foundation volumes + working space + side slope.
- [ ] Backfill = excavation − structure volume below ground.
- [ ] Launching apron from scour depth and pier perimeter, not
      `total_len * 0.08`.
- [ ] `301.1`, `301.2`, `601.2`, `601.4` recalculated.

### Acceptance
- Backfill never negative; assert `backfill <= excavation`.

### Exit gate
Earthwork arithmetic assertion green on 28 fixtures.

---

## Week 38 — Q3 sign-off and retro

### Tasks
- [ ] Full BOQ provenance audit: no line `estimated` without a documented
      source; log every remaining one with a closing week.
- [ ] Engineer review of sheets 5 and 6.
- [ ] Retro: `METRICS.md`, `DEFECT-LEDGER.md`, `PROGRESS.md`.
- [ ] Write `Q4-W39-W52-RELEASE.md`.

### Acceptance
- All Q3 exit criteria met.

### Exit gate
**Q3 complete.**

---

## Q3 exit checklist

- [ ] Sheets 5 and 6 complete and reviewed
- [ ] Skew consistent across 5 sheets
- [ ] Superelevation, camber and gradient all input-driven
- [ ] Formwork and rebar derived, not multiplied
- [ ] Backfill ≤ excavation asserted
- [ ] Remaining `estimated` BOQ lines each have a closing week
