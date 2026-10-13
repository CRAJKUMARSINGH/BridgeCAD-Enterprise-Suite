# BridgeCAD Enterprise Suite — implementation plan

**Repository:** `CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse`  
**Baseline reviewed:** `main` at `a04e9de41db38d2109a3431df8c47da31fda1923`  
**Product focus:** BridgeCAD Enterprise Suite  
**Deliverable type:** Plan only; no repository files are changed by this ZIP.

## Goal

Turn the Suite into a dependable engineering workflow from workbook input to
reviewable drawing, QA findings, BOQ, and export bundle. “Done” means that the
same validated project data drives every output, failures are visible rather
than silently approximated, and CI tests the Suite users actually run.

Do not describe generated GADs, compliance scores, or BOQs as approved for
construction. They remain engineering aids until a qualified engineer has
reviewed and approved the outputs.

## Verified starting gaps

1. **The latest root CI run is blocked by its PII scan.** The scan uses
   recursive `grep` after editable installation, so it finds install-generated
   `src/bridge_gad.egg-info/PKG-INFO` metadata and exits before the remaining
   smoke, lint, and test steps. Change the scan to inspect tracked source files
   (for example, `git grep`) and retain a failing check for actual committed
   contact data.
2. **The active Suite’s CI workflow is nested.** Its workflow is at
   `BridgeCAD Enterprise Suite/.github/workflows/ci.yml`; GitHub Actions
   discovers workflows only from the repository-root `.github/workflows/`.
   The root workflow currently exercises the older top-level application, not
   the Suite’s package, fixture, or React test matrix.
3. **Suite package metadata points at a missing README.**
   `BridgeCAD Enterprise Suite/pyproject.toml` names
   `BridgeCAD Enterprise Suite/README.md` as its readme, while that file is not
   present in the reviewed tree. Correct the path relative to the project
   directory and add a Suite-specific README before building distributions.
4. **Drawing completeness is the highest product risk.** The
   `sample-gad-drawings/2 OCT PROGRAM.MD` note describes Sheet 1 as the most
   complete sheet and Sheets 2–7 as scaffolds. It also calls for fixture
   parsing, BOQ, workbook round-trip, plugin wiring, and end-to-end export
   verification.
5. **BOQ status has drifted between the program note and code.** The program
   note describes quantity extraction as a stub; the current
   `packages/bridgecad-bill/bridgecad_bill/processor.py` contains quantity
   calculations, but includes heuristic multipliers. Reconcile the two
   descriptions, identify which values come from validated model calculations,
   and expose assumptions instead of presenting estimates as measured takeoff.
6. **The repository contains two application generations.** The root README
   describes the older “Ultimate Bridge GAD Generator,” while the updated app
   is the Suite. Make the active product, supported entry point, and status
   explicit so users do not follow stale run/deploy instructions.
7. **The API gateway has a file-handling hardening opportunity.**
   `apps/api-gateway/bridgecad_api/main.py` uses `tempfile.mktemp()` for a
   generated ZIP and does not clean that response file after download. Replace
   it with an atomically created temporary file, validate user-controlled
   output names and scale, and remove the file after the response completes.

The two large `.txt` files in `sample-gad-drawings/` contain repeated and
historical generated material as well as useful requirements. Treat the
October 2 program note as the current status snapshot, but verify engineering
requirements against the supplied drawing PDFs and applicable standards before
implementing them.

## Recommended sequence

### Phase 0 — Establish one trustworthy build (P0)

**Scope**

- Fix the root PII check so generated package metadata is not mistaken for
  tracked source; keep the check strict for tracked files.
- Activate the Suite’s CI from the repository-root workflow directory. Keep
  the older app’s checks separate and clearly named rather than silently
  replacing them.
- Correct the Suite `pyproject.toml` readme path and add
  `BridgeCAD Enterprise Suite/README.md` with install, test, API, UI, and
  current-limitations instructions.
- Add a top-level orientation section naming BridgeCAD Enterprise Suite as the
  active application and identifying the legacy entry points.
- Make lint, type-check, unit, fixture, API, and web-build results visible.
  Do not mark mandatory checks as successful with `|| true`.

**Acceptance gate**

- A pull request touching the Suite runs Suite checks from the root workflow.
- The legacy app and Suite have separately named CI jobs.
- The PII scan passes on generated build metadata but fails on an intentionally
  added tracked-source match.
- A clean checkout can build the Suite metadata and follow its README without
  a missing-file error.

**Estimated effort:** 0.5–1.5 engineering days.

### Phase 1 — Make project data and fixture parsing deterministic (P1)

**Scope**

- Treat the 28 JSON fixtures as a regression corpus; preserve their provenance
  and add expected project summaries for representative bridge types.
- Normalize enum deserialization deliberately: accept canonical enum values
  and documented names/aliases, case-insensitively where safe. Avoid broad
  fuzzy matching that can turn an invalid structural input into a plausible
  but wrong value.
- Improve validation errors to identify the workbook/fixture field, accepted
  value, unit, and relevant standard clause when known.
- Add unit and range checks for span lengths, widths, levels, skew, and support
  configuration. Make absent required data distinct from valid zero values.
- Add round-trip tests for JSON and Excel adapters using canonical model
  equality, not just successful parsing.

**Acceptance gate**

- All 28 fixtures parse, or any intentionally unsupported fixture is explicitly
  listed with a reason and a tracked issue.
- Name/value enum tests cover every non-identical enum name/value pattern.
- Invalid or ambiguous enum inputs fail with actionable errors.
- Excel → model → Excel → model preserves all supported fields in the
  round-trip test.

**Estimated effort:** 2–4 engineering days, subject to the fixture error count.

### Phase 2 — Complete and verify the seven-sheet drawing pipeline (P1)

**Scope**

- Implement the missing engineering geometry for Sheets 2–7 from approved
  drawing requirements; do not count a title block or placeholder text as a
  completed sheet.
- Keep one coordinate/unit convention across plan, longitudinal section,
  cross-section, foundation, substructure, bearings/joints, and BOQ sheets.
- Define drawing contracts for sheet size, scale, title block, revision,
  dimensions, layers, symbols, levels, and required schedules.
- Add regression cases for at least: single span, multi-span continuous bridge,
  skew bridge, pile foundation, well foundation, culvert, and one PSC bridge.
- Validate generated DXF structure, extents, non-empty geometry, required
  layers, dimensions, labels, and output paths. Compare representative sheets
  visually against reviewed reference PDFs.
- Make incomplete or unsupported features produce explicit QA warnings in the
  export manifest.

**Acceptance gate**

- Every supported fixture produces exactly the documented sheet set.
- Each sheet passes structural checks and has finite, non-degenerate geometry
  inside its drawing extents.
- The single-span and skew cases have dedicated regression tests.
- A bridge engineer reviews at least one representative output for each
  supported bridge family before release.

**Estimated effort:** 1–2 weeks; this is the largest correctness workstream.

### Phase 3 — Replace implicit BOQ estimates with traceable quantities (P1)

**Scope**

- Create an explicit quantity schedule that records item code, quantity, unit,
  formula/source field, assumptions, and confidence/status.
- Derive quantities from validated geometry and calculation outputs. Do not use
  unexplained constants (for example, fixed concrete-to-formwork multipliers)
  as if they were measured project quantities.
- If source fields are absent or a method is unsupported, return “not
  calculated” with a reason. Do not silently substitute a plausible default.
- Separate quantity takeoff from rate lookup. Record rate source, schedule
  year, state override, and whether a rate is missing.
- Compare the generated BOQ against manually checked reference quantities for
  representative fixtures; have an engineer approve tolerances by item class.

**Acceptance gate**

- Every non-zero BOQ line has traceable inputs and a documented calculation.
- Missing inputs are visible and cannot silently yield a certified-looking
  total.
- Reference BOQs meet engineer-approved, item-specific tolerances.
- Changing the state/rate schedule changes rates without changing physical
  quantities.

**Estimated effort:** 4–8 engineering days plus review of reference BOQs.

### Phase 4 — Finish the workbook and user journey (P2)

**Scope**

- Establish one versioned workbook schema shared by the template generator,
  reader, writer, API, Streamlit UI, and React console.
- Implement or explicitly defer workbook formulas, dropdowns, conditional
  validation, instructions, and locked calculated cells.
- Make input status visible before drawing or BOQ generation: valid, warning,
  blocked, unsupported.
- Make the web console encode request parameters, constrain prefixes/scales,
  explain upload failures, and distinguish estimates from checked quantities.
- Add API upload limits, filename/prefix validation, safe temporary-file
  lifecycle, and structured error responses.

**Acceptance gate**

- A first-time user can download a template, enter a valid project, validate,
  generate drawings/BOQ, and download the export bundle without manual
  filesystem steps.
- Invalid file types, oversized uploads, invalid scale, and unsafe prefixes
  fail before expensive work begins.
- The output ZIP contains the manifest, expected drawings, BOQ, QA report, and
  provenance for the rates/standards used.

**Estimated effort:** 4–7 engineering days.

### Phase 5 — Release readiness and maintenance (P2)

**Scope**

- Publish a single install/deploy guide for supported modes and environment
  variables; document migrations and supported Python/Node versions.
- Decide which bridge plugins are supported now and test plugin dispatch for
  each advertised type.
- Add deterministic fixture generation, dependency update/security review, and
  a release checklist.
- Keep generated DXF/PDF/XLSX/ZIP artifacts out of source history unless they
  are intentional golden fixtures with documented provenance.
- Track open limitations and standards versions in the app and exported
  manifest.

**Acceptance gate**

- Clean CI and clean install from a fresh checkout.
- Supported plugin matrix matches the UI and documentation.
- Release artifacts are reproducible and include version, standards, rate
  schedule, input file hash, and QA findings.

**Estimated effort:** 3–5 engineering days after the correctness gates pass.

## Suggested first sprint

1. Complete Phase 0 and make the Suite checks run from root CI.
2. Run the 28-fixture suite and publish a machine-readable failure summary.
3. Select five golden cases: simple single span, continuous multi-span, skew,
   well foundation, and PSC.
4. For each golden case, agree the expected model summary, sheet checklist, and
   independently checked BOQ with a bridge engineer.
5. Start Phase 2 and Phase 3 only against those approved expectations.

## Release rule

Do not call the repository “perfect” or release drawings as construction-ready
until Phase 0–3 gates pass and an engineer has reviewed representative outputs.
Keep the legacy app available only with clear labeling until migration or
retirement is intentional.