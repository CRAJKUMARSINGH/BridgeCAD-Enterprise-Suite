# Q4 — Weeks 39–52: Proof, Traceability, Release

**Theme:** make the output defensible. Visual regression so it cannot silently
drift, a clause matrix so every line can be justified, and a release gate that
lets you stop saying "not reviewed".
**Entry requirement:** Q3 exit checklist complete.
**Exit gate:** `construction-ready` claim unlocked behind an automated gate.

---

## Week 39 — Plot configuration

**Goal:** a DXF is not a drawing until it plots the same way twice.

### Tasks
- [ ] `bridgecad_draw/plot.py`: page setup per sheet — A1, landscape, monochrome
      `.ctb`, plot scale from `coordinates.FRAMES`, plot origin at frame origin,
      `PLOTSTYLE` named `BRG-MONO`.
- [ ] Paper-space layout per sheet: one layout named after the sheet, one
      viewport at the declared scale, locked. Model space keeps 1:1.
- [ ] Ship `standards/plot/BRG-MONO.ctb` with lineweight mapping: 0.70 border,
      0.50 outline, 0.35 section, 0.25 hidden, 0.18 dim, 0.13 text.
- [ ] `assert_layout_exists(doc, sheet)`, `assert_viewport_scale(doc, sheet)`.

### Acceptance
- 8 layouts, 8 locked viewports, correct scale on 5 golden cases.

### Exit gate
`ezdxf` batch plot of a golden package produces 8 PDFs at declared scale.

---

## Week 40 — PDF and plot verification

### Tasks
- [ ] PDF output via `ezdxf.addons.drawing` matplotlib backend with the CTB
      applied; A1 media box asserted.
- [ ] Measure the PDF: known 12.5 m span must measure 125 mm at 1:100 within
      1 mm. Assert on all 5 golden cases.
- [ ] Fail the build if any sheet's PDF page size ≠ A1 or the measured span is
      out of tolerance.

### Acceptance
- Measured-span assertion green; this is the definitive proof the scale work of
  weeks 5–10 actually holds through the plot path.

### Exit gate
A printed golden sheet is measurable with a scale rule.

---

## Week 41 — Visual regression baseline

### Tasks
- [ ] Render each golden sheet to PNG at 150 dpi.
- [ ] Commit baselines to `tests/visual/baseline/` (8 × 5 = 40 files).
- [ ] `tests/visual/compare.py`: pixel diff with 0.3% tolerance and a 3 px
      dilation to absorb antialiasing.
- [ ] Diff output as a side-by-side + heatmap artifact in CI.
- [ ] Wire into `suite-ci.yml` as a non-blocking job initially.

### Acceptance
- Re-running unchanged code diffs to zero.

### Exit gate
A one-pixel lineweight change is detected.

---

## Week 42 — Visual review, family 1–2

### Tasks
- [ ] Engineer reviews slab (`simple_12m`, `continuous_3x12m`) and PSC girder
      (`girder_4x18m`) sheets at A1 on paper.
- [ ] Every mark logged in `DEFECT-LEDGER.md` with severity
      `blocker`/`major`/`minor`, and a closing week.
- [ ] Fix all `blocker` marks in-week; `major` scheduled; `minor` accepted with
      a rationale.

### Acceptance
- Zero open `blocker` marks per family.

### Exit gate
Two families signed off in writing.

---

## Week 43 — Visual review, family 3–5

### Tasks
- [ ] Same for box culvert (`box_culvert_8m`), skew 15°, and one river case.
- [ ] Make the visual job blocking in CI once all five are signed.

### Acceptance
- All 5 families signed off; visual job blocking.

### Exit gate
**Q4-A gate reached.** Drift is now caught automatically.

---

## Week 44 — Traceability matrix

### Tasks
- [ ] `TRACEABILITY.md`: every drawn element → model field → IRC/MORTH clause
      with year. Example row:
      `Bearing pedestal | substructure.pier_pedestal_height_m | IRC:83-2018 Cl. 5.2`.
- [ ] Add `src_ref` to every `text()`/draw call that carries a standard-derived
      value; a build check fails on an uncited element class.
- [ ] Target ≥ 90% coverage of element classes.

### Acceptance
- Matrix covers every layer in `LAYER_REGISTRY` that is actually drawn.

### Exit gate
`scripts/check_traceability.py` exits 0.

---

## Week 45 — Clause audit

### Tasks
- [ ] Re-read each cited clause against the standard; correct the clause number
      or the geometry where they disagree.
- [ ] Log every correction as a defect row (these are the expensive ones — do
      not skip).
- [ ] Pay particular attention to: IRC:5 clearance and freeboard, IRC:6 barrier
      profiles, IRC:83 bearing seating, IRC:SP:55 text heights and layer
      naming, IRC:SP:114 seismic detailing zones.

### Acceptance
- Zero citations that fail re-read.

### Exit gate
Audit sheet signed.

---

## Week 46 — Drawing checklist per sheet

### Tasks
- [ ] One `docs/checklists/sheetN.md` per sheet: required views, dims, levels,
      notes, legend, title fields, scale, sign-off boxes.
- [ ] Checklist items map 1:1 to harness assertions; a checklist item without an
      assertion is a gap.
- [ ] Human sign-off block at the foot of each checklist.

### Acceptance
- Every checklist item has an assertion ID.

### Exit gate
**Q4-B gate reached.**

---

## Week 47 — QA rule completion

### Tasks
- [ ] `bridgecad-qa`: 120 stubs remain of 150. Implement all `critical` (25) and
      `warning` (75) rules.
- [ ] `info` rules may stay stubbed only with a reason.
- [ ] Grade must be reproducible: same project → same score.

### Acceptance
- 100 of 150 rules implemented; grade deterministic.

### Exit gate
A seeded defect fixture drops the grade by the expected amount.

---

## Week 48 — Release gate definition

### Tasks
- [ ] `scripts/release_gate.py`: refuses unless all hold —
      CI green on both workflows, 90 harness assertions green,
      visual regression green, 5 families signed, traceability ≥ 90%,
      zero open blockers, BOQ provenance audit clean.
- [ ] Gate writes `build/release-gate.json` with every check and its result.

### Acceptance
- Gate fails on `main` today and names every unmet condition.

### Exit gate
Gate output is the release checklist, generated not remembered.

---

## Week 49 — Manifest and UI flag flip

### Tasks
- [ ] `bridgecad_export`: manifest `review_status` becomes
      `construction_ready` only when `release-gate.json` is present and green;
      otherwise `generated_not_reviewed`.
- [ ] CLI prints the status and the gate path on every export.
- [ ] API `/exports` returns it in the response; React and Streamlit show it at
      download.
- [ ] `GUIDE.md` §11 release rule rewritten to point at the gate.

### Acceptance
- A hand-run export on a gated build reads `construction_ready`.

### Exit gate
Flag cannot be set by hand.

---

## Week 50 — Documentation and training

### Tasks
- [ ] `docs/drafting-standard.md`: the house standard — scales permitted, text
      heights, layers, dimstyles, plot styles, title block, checklist links.
- [ ] Rewrite `GUIDE.md` §5 with the new workflows.
- [ ] 90-minute recorded walkthrough for a new drafter.
- [ ] `CONTRIBUTING.md`: a sheet change requires an assertion and a checklist
      update.

### Acceptance
- A new drafter can produce a compliant sheet from the docs alone.

### Exit gate
External read-through by someone who has not seen the repo.

---

## Week 51 — Release candidate

### Tasks
- [ ] Version `v1.0.0-rc1`; `CHANGELOG.md` from the defect ledger (closed rows
      only, grouped by quarter).
- [ ] Full gate run, artifact set built, signed.
- [ ] Two-week soak: every fixture regenerated daily, gate re-run, drift logged.

### Acceptance
- Gate green 14 consecutive days.

### Exit gate
Zero gate failures in soak.

---

## Week 52 — Release and handover

### Tasks
- [ ] Tag `v1.0.0`. Publish release notes with the traceability matrix and the
      signed family sheets.
- [ ] `PROGRESS.md` closed; `METRICS.md` final column filled.
- [ ] Post-release backlog: curved-bridge spirals, 3D, SVG/PNG, plugin matrix,
      AI optimiser — in that order.
- [ ] Unfreeze everything from `FROZEN.md`.

### Acceptance
- Release published; `construction_ready` reachable.

### Exit gate
**Q4 complete. Plan closed.**

---

## Q4 exit checklist

- [ ] 8 layouts, 8 locked viewports, 8 correct PDFs
- [ ] Measured-span proof green
- [ ] 40 visual baselines committed and blocking
- [ ] 5 families signed in writing
- [ ] Traceability ≥ 90% with zero failed citations
- [ ] 100 of 150 QA rules implemented
- [ ] `release_gate.py` green 14 days
- [ ] Manifest flag flip automated
- [ ] Backlog written and prioritised
