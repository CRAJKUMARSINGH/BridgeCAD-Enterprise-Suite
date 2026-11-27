# Git Incorporation Inventory

Snapshot: 27 November 2026 at `c428656` on `codex/phase-0-launch-baseline`.

This report separates local Git hygiene from branch incorporation. A branch-only change is not necessarily an orphan or a runtime defect; it is committed work that has not yet been merged into local `main`.

## 1. Current Local Git State

| Measure | Result | Interpretation |
|---|---:|---|
| Tracked files | 2,005 | Known to Git. |
| Staged files | 0 | No pending index changes. |
| Unstaged modified files | 11 | Five inventory reports plus six source/manifest edits from the entry-point refactor (section 2.4). |
| Untracked, non-ignored files | 2 | Two new wired source modules awaiting `git add` (section 2.4). |
| Actionable ignored source/guidance files | 0 | Remaining ignored files are caches, bytecode, dependencies, or generated output. |
| Commits ahead of local `main` | 21 | Branch work remains to be merged. |
| Commits behind local `main` | 0 | Local `main` has no divergent commits. |
| Branch-only change records | 187 | Complete list in section 3. |

The committed tree is synchronized with `origin/codex/phase-0-launch-baseline`. The 11 unstaged and 2 untracked items are an in-flight, uncommitted change set: a documentation refresh plus an entry-point refactor (see section 2.4).

## 2. Resolved Historical Local Gaps

### 2.1 Former Untracked Files

The earlier `6ddf860` snapshot had 20 non-ignored untracked files. They are retained here only as a historical audit trail; **none of those 20 remains untracked**.

| # | Former file | Current disposition |
|---:|---|---|
| 1 | `BASELINE.md` | Tracked branch-only guidance; merge with Phase 0 evidence. |
| 2 | `CREAT.MD` | Tracked branch-only continuity guidance; stale queue statements still need correction. |
| 3 | `LAUNCH_HARDENING_REPORT.md` | Tracked branch-only launch evidence. |
| 4 | `artifacts/browser-results/live-drafting-2026-11-24_01-desktop-initial.png` | Deleted as regenerable evidence. |
| 5 | `artifacts/browser-results/live-drafting-downloads/Browser-QA-Design-elevation.svg` | Deleted as regenerable evidence. |
| 6 | `artifacts/browser-results/live-drafting-feature-pack-desktop.png` | Deleted as regenerable evidence. |
| 7 | `artifacts/browser-results/live-drafting-feature-pack-mobile.png` | Deleted as regenerable evidence. |
| 8 | `artifacts/browser-results/live-drafting-feature-pack-report.json` | Deleted as regenerable evidence. |
| 9 | `artifacts/browser-results/live-drafting-headless-initial.png` | Deleted as regenerable evidence. |
| 10 | `artifacts/browser-results/live-drafting-headless-invalid.png` | Deleted as regenerable evidence. |
| 11 | `artifacts/browser-results/live-drafting-headless-mobile.png` | Deleted as regenerable evidence. |
| 12 | `artifacts/browser-results/live-drafting-headless-report.json` | Deleted as regenerable evidence. |
| 13 | `artifacts/browser-results/live-drafting-headless-valid.png` | Deleted as regenerable evidence. |
| 14 | `frontend/src/sheets/DraftingStudio.tsx` | Tracked, runtime-wired at `#drafting`, branch-only. |
| 15 | `frontend/src/sheets/draftingGeometry.ts` | Tracked and imported by `DraftingStudio.tsx`, branch-only. |
| 16 | `frontend/src/sheets/draftingStudio.css` | Tracked and imported by `DraftingStudio.tsx`, branch-only. |
| 17 | `frontend/tests/drafting.test.mjs` | Tracked branch-only frontend regression test. |
| 18 | `packages/bridgecad-draw/bridgecad_draw/deck_joints.py` | Tracked and imported by active drawing modules, branch-only. |
| 19 | `scripts/check_browser_drafting.py` | Tracked and invoked by the launch checker, branch-only. |
| 20 | `scripts/check_software_launch.py` | Tracked and referenced by README, deployment docs, launch report, and CI, branch-only. |

Future captures matching `artifacts/browser-results/live-drafting-*` are ignored to avoid recurring status noise.

### 2.2 Former Ignored Production Helper

`netlify/lib/drawing-proxy.cjs` was previously hidden by the broad `lib/` ignore rule. Narrow exceptions for `netlify/lib/` and `netlify/lib/**` are committed, and the helper is tracked.

It remains required by:

- `netlify/functions/predict.js`
- `netlify/functions/template.js`
- `netlify/functions/generate_sample_pdf.js`
- `netlify/functions/export_package.js`

**Current status:** resolved. The remaining incorporation action is to merge the branch containing the helper and its callers.

### 2.3 Former Unstaged Modifications

The earlier snapshot had 49 unstaged tracked-file modifications. All were committed in `3110881` and later commits; their current branch state is represented in the 187-record inventory below.

### 2.4 Current Uncommitted Change Set (New Since `3110881`)

The working tree is no longer clean. Two groups of uncommitted changes exist and should be incorporated together.

**Untracked, non-ignored files (2) — both are wired:**

| File | Evidence of wiring | Recommended action |
|---|---|---|
| `packages/bridgecad-core/bridgecad_core/drawing_audit.py` | Defines the `DrawingAudit` protocol, `register_layout_auditor()`, `layout_audit_requested()`, and `collect_layout_audit()`. Imported by `bridgecad/__init__.py`, `bridgecad_draw/layout_audit.py`, and `bridgecad_core/validation.py`. | `git add` and commit with the refactor below. |
| `packages/bridgecad-export/bridgecad_export/worker_jobs.py` | Implements `generate_drawing`, `generate_bill`, and `export_package`. Registered as `bridgecad.worker_jobs` entry points in `packages/bridgecad-export/pyproject.toml`; resolved by `bridgecad_infra/queue.py`. | `git add` and commit with the refactor below. |

**Unstaged modified files (11):**

| Group | File(s) | Role in the change set |
|---|---|---|
| Inventory refresh | `docs/inventory/README.md`, `01`–`04` | Documentation-only refresh tracked by this report. |
| Entry-point refactor | `bridgecad/__init__.py`, `packages/bridgecad-core/bridgecad_core/validation.py`, `packages/bridgecad-draw/bridgecad_draw/layout_audit.py`, `packages/bridgecad-draw/pyproject.toml`, `packages/bridgecad-export/pyproject.toml`, `packages/bridgecad-infra/bridgecad_infra/queue.py` | Moves the draw/export coupling behind `bridgecad.layout_audit` and `bridgecad.worker_jobs` entry points so `core` and `infra` no longer import `draw`/`export` directly. |

**Recommended action:** review the refactor as one coherent commit (the two new modules cannot function without the manifest entry points and the modified import sites), then `git add` the untracked and modified files together and commit.

## 3. Complete Branch-only Change Inventory

`git rev-list --left-right --count main...HEAD` reports `0 21`.

`git diff --name-status main...HEAD` reports 187 records. Status meanings:

- `A` — added on the branch.
- `M` — modified on the branch.
- `D` — deleted on the branch.
- `Rnnn` — renamed with Git similarity score `nnn`; both paths are shown.

These records are already committed and pushed on the feature branch. The recommended action is branch review and merge, not initial file incorporation.

### 3.1 Repository, CI, Governance, Facade, and Legacy Relocations — Records 1–25

| # | Status | Path or rename | Classification | Recommended action |
|---:|---|---|---|---|
| 1 | M | `.agents/tasks/security-audit-2026-10-13/trufflehog_git.json` | Security baseline evidence. | Review scan churn and merge with the baseline evidence. |
| 2 | M | `.github/actions/setup-suite/action.yml` | CI workspace installer. | Merge with dependent workflow changes. |
| 3 | M | `.github/workflows/ci.yml` | CI workflow. | Merge after shared checks are green. |
| 4 | A | `.github/workflows/phase0-baseline.yml` | Phase 0 verification workflow. | Merge as the baseline gate. |
| 5 | M | `.github/workflows/suite-ci.yml` | Suite CI workflow. | Merge with the setup action and launch scripts. |
| 6 | M | `.gitignore` | Repository hygiene. | Merge with packaging and artifact-policy review. |
| 7 | A | `BASELINE.md` | Point-in-time launch guidance. | Merge as historical baseline evidence. |
| 8 | A | `CHANGELOG.md` | Release history. | Merge with Phase 0 documentation. |
| 9 | A | `CODE_OF_CONDUCT.md` | Governance guidance. | Merge with community documentation. |
| 10 | A | `CONTRIBUTING.md` | Contributor guidance. | Merge with test and documentation policy. |
| 11 | A | `CREAT.MD` | Rolling continuity guidance. | Correct stale queue statements, then merge. |
| 12 | M | `Dockerfile` | Container contract. | Merge with legacy fencing and dependency policy. |
| 13 | A | `LAUNCH_HARDENING_REPORT.md` | Launch/release evidence. | Merge with launch scripts and verification records. |
| 14 | M | `Makefile` | Developer entrypoints. | Merge with worker target and relocated scripts. |
| 15 | M | `README.md` | Primary guidance. | Merge current launch and repository instructions. |
| 16 | A | `SECURITY.md` | Security guidance. | Merge with governance documentation. |
| 17 | D | `_generate_11span_gad.py` | Removed root legacy path. | Apply deletion with its replacement relocation. |
| 18 | M | `apps/api-gateway/bridgecad_api/main.py` | Active Python API. | Merge with the branch; close auth/lifespan gaps before production. |
| 19 | M | `apps/streamlit-ui/app.py` | Active Streamlit console. | Merge with facade/entry-point changes. |
| 20 | R051 | `app_lean.py` → `apps/streamlit-ui/legacy/app_lean.py` | Legacy app relocation. | Merge with ADR-0002; retain as opt-in legacy. |
| 21 | R073 | `streamlit_app_ultimate.py` → `apps/streamlit-ui/legacy/streamlit_app_ultimate.py` | Legacy app relocation. | Merge with ADR-0002; migrate only verified capabilities. |
| 22 | A | `artifacts/TRIAGE_LOG.md` | Defect register and merge-gate guidance. | Merge with gate tooling; repair missing guide references. |
| 23 | A | `audit/baseline.json` | Release baseline evidence. | Merge with the release report. |
| 24 | M | `bridgecad/__init__.py` | Active package facade. | Merge after package-resolution checks; includes the layout-audit bootstrap. |
| 25 | M | `bridgecad/__main__.py` | Active CLI entrypoint. | Merge with relocated verifier paths. |

### 3.2 Documentation, Schema, Inventory, and Verification — Records 26–37

| # | Status | Path | Classification | Recommended action |
|---:|---|---|---|---|
| 26 | M | `docs/DEPLOYMENT.md` | Deployment guidance. | Reconcile API-key claims with actual gateway enforcement, then merge. |
| 27 | A | `docs/adr/0002-group-workspace-entry-points.md` | Architecture decision. | Merge with file relocations. |
| 28 | A | `docs/adr/README.md` | ADR index. | Merge with ADR-0002. |
| 29 | A | `docs/index.md` | MkDocs landing page. | Merge with `mkdocs.yml`. |
| 30 | A | `docs/inventory/01-git-incorporation.md` | Git inventory. | Merge the refreshed report. |
| 31 | A | `docs/inventory/02-runtime-wiring.md` | Runtime inventory. | Merge the refreshed report. |
| 32 | A | `docs/inventory/03-guidance-reference.md` | Guidance inventory. | Merge the refreshed report. |
| 33 | A | `docs/inventory/04-standalone-tools.md` | Tool inventory. | Merge the refreshed report. |
| 34 | A | `docs/inventory/README.md` | Inventory index. | Merge the refreshed index and decide MkDocs navigation. |
| 35 | M | `docs/schema/bridgeproject.schema.json` | Published project schema. | Merge with schema-export checks. |
| 36 | A | `docs/verification/RELEASE_REPORT.md` | Release/verification evidence. | Merge with Phase 0 status. |
| 37 | M | `docs/verification/TRACEABILITY.md` | Compliance guidance. | Merge with QA and test changes. |

### 3.3 Frontend, Documentation Site, Netlify, Server, and Startup — Records 38–60 and 133–134

| # | Status | Path | Classification | Recommended action |
|---:|---|---|---|---|
| 38 | M | `frontend/package.json` | Frontend scripts/dependencies. | Merge with frontend tests and build configuration. |
| 39 | M | `frontend/src/WorkflowLanding.tsx` | Active landing page. | Merge with routing changes. |
| 40 | M | `frontend/src/main.tsx` | Active route entrypoint. | Merge with drafting and workspace routes. |
| 41 | A | `frontend/src/sheets/DraftingStudio.tsx` | Active drafting UI. | Merge with geometry, CSS, tests, and launch tooling. |
| 42 | M | `frontend/src/sheets/Sheet01Overview.tsx` | Active sheet UI. | Merge with sheet presentation changes. |
| 43 | M | `frontend/src/sheets/SheetChrome.tsx` | Active sheet chrome. | Merge with sheet presentation changes. |
| 44 | M | `frontend/src/sheets/detailGeometry.d.ts` | Geometry type declarations. | Merge with geometry implementation. |
| 45 | M | `frontend/src/sheets/detailGeometry.js` | Geometry implementation. | Merge with sheet and test changes. |
| 46 | A | `frontend/src/sheets/draftingGeometry.ts` | Drafting geometry. | Merge with `DraftingStudio.tsx`. |
| 47 | A | `frontend/src/sheets/draftingStudio.css` | Drafting styling. | Merge with `DraftingStudio.tsx`. |
| 48 | M | `frontend/src/sheets/layerGroups.js` | Sheet layer grouping. | Merge with sheet rendering changes. |
| 49 | M | `frontend/src/sheets/registry.tsx` | Sheet registry. | Merge with active sheet changes. |
| 50 | M | `frontend/src/sheets/theme.ts` | UI theme. | Merge with frontend styling changes. |
| 51 | M | `frontend/src/styles.css` | Global styling. | Merge with frontend layout changes. |
| 52 | A | `frontend/tests/drafting.test.mjs` | Drafting regression test. | Merge with the drafting feature. |
| 53 | M | `frontend/tests/workbook-proxy.test.mjs` | Workbook proxy regression test. | Merge with Netlify proxy changes. |
| 54 | M | `frontend/vite.config.ts` | Frontend build configuration. | Merge with frontend build changes. |
| 55 | A | `mkdocs.yml` | Documentation navigation. | Merge with docs; add inventory navigation or document its local-only status. |
| 56 | M | `netlify/functions/export_package.js` | Active package proxy. | Merge with proxy helper and tests. |
| 57 | M | `netlify/functions/generate_sample_pdf.js` | Active sample-PDF proxy. | Merge with proxy helper and tests. |
| 58 | M | `netlify/functions/predict.js` | Active prediction proxy. | Merge with proxy helper and tests. |
| 59 | M | `netlify/functions/template.js` | Active template proxy. | Merge with proxy helper and tests. |
| 60 | A | `netlify/lib/drawing-proxy.cjs` | Required serverless helper. | Merge with all four callers; clean-clone risk is resolved by inclusion. |
| 133 | M | `server/index.mjs` | Static server/API proxy. | Merge with launch/deployment changes. |
| 134 | M | `server/start.sh` | API/frontend launcher. | Merge with server and deployment changes. |

### 3.4 Python Production Packages — Records 61–115

| # | Status | Path | Classification | Recommended action |
|---:|---|---|---|---|
| 61 | M | `packages/bridgecad-ai/bridgecad_ai/drawing_review.py` | Active AI drawing review. | Merge with AI/Streamlit tests. |
| 62 | M | `packages/bridgecad-bill/bridgecad_bill/formatters/excel_formatter.py` | Active BOQ formatter. | Merge with bill tests. |
| 63 | M | `packages/bridgecad-bill/bridgecad_bill/measurers.py` | Active BOQ measurement code. | Merge with bill tests. |
| 64 | M | `packages/bridgecad-bill/bridgecad_bill/processor.py` | Active BOQ orchestration. | Merge with bill and drawing tests. |
| 65 | M | `packages/bridgecad-catalogue/bridgecad_catalogue/registry.py` | Catalogue registry. | Merge with catalogue tests. |
| 66 | M | `packages/bridgecad-catalogue/bridgecad_catalogue/resolve.py` | Catalogue resolver. | Merge with catalogue tests. |
| 67 | M | `packages/bridgecad-catalogue/bridgecad_catalogue/schema.py` | Catalogue schema. | Merge with catalogue tests. |
| 68 | M | `packages/bridgecad-core/bridgecad_core/abutment_stack.py` | Active geometry. | Merge with core and drawing tests. |
| 69 | M | `packages/bridgecad-core/bridgecad_core/geometry/abutment_profiles.py` | Active geometry profiles. | Merge with core and drawing tests. |
| 70 | M | `packages/bridgecad-core/bridgecad_core/geometry/long_section.py` | Active long-section geometry. | Merge with core and drawing tests. |
| 71 | M | `packages/bridgecad-core/bridgecad_core/geometry/superstructure_profiles.py` | Active superstructure profiles. | Merge with core and drawing tests. |
| 72 | M | `packages/bridgecad-core/bridgecad_core/geometry/support_levels.py` | Active support-level geometry. | Merge with core and drawing tests. |
| 73 | M | `packages/bridgecad-core/bridgecad_core/validation.py` | Active validation. | Merge after the drawing-audit decoupling (section 2.4). |
| 74 | M | `packages/bridgecad-core/bridgecad_core/validation_registry.py` | Validation check registry. | Merge with core validation changes. |
| 75 | M | `packages/bridgecad-draw/bridgecad_draw/_sheetkit.py` | Drawing sheet toolkit. | Merge with drawing tests. |
| 76 | M | `packages/bridgecad-draw/bridgecad_draw/asset_pack.py` | Asset-pack builder. | Merge with asset-pack tests. |
| 77 | M | `packages/bridgecad-draw/bridgecad_draw/asset_sheet1_lsection.py` | Active asset sheet. | Merge with asset-pack tests. |
| 78 | M | `packages/bridgecad-draw/bridgecad_draw/asset_sheet2_deck_abutment.py` | Active asset sheet. | Merge with asset-pack tests. |
| 79 | M | `packages/bridgecad-draw/bridgecad_draw/asset_sheet3_pier.py` | Active asset sheet. | Merge with asset-pack tests. |
| 80 | M | `packages/bridgecad-draw/bridgecad_draw/asset_sheet4_single_span.py` | Active asset sheet. | Merge with asset-pack tests. |
| 81 | M | `packages/bridgecad-draw/bridgecad_draw/asset_specs.py` | Asset-pack specifications. | Merge with asset-pack tests. |
| 82 | M | `packages/bridgecad-draw/bridgecad_draw/booklet.py` | Production sheet manifest/generator. | Merge with production sheet changes. |
| 83 | A | `packages/bridgecad-draw/bridgecad_draw/deck_joints.py` | Active drawing geometry. | Merge with the modules that import it. |
| 84 | M | `packages/bridgecad-draw/bridgecad_draw/dim_style.py` | Dimension-style definitions. | Merge with drawing tests. |
| 85 | M | `packages/bridgecad-draw/bridgecad_draw/engines/_render.py` | Renderer support. | Merge with engine changes. |
| 86 | M | `packages/bridgecad-draw/bridgecad_draw/engines/ga_sheet.py` | Active GA renderer. | Merge with drawing tests. |
| 87 | M | `packages/bridgecad-draw/bridgecad_draw/engines/pdf_engine.py` | PDF renderer. | Merge with export/integration tests. |
| 88 | M | `packages/bridgecad-draw/bridgecad_draw/engines/png_engine.py` | PNG renderer. | Merge with export/integration tests. |
| 89 | M | `packages/bridgecad-draw/bridgecad_draw/engines/svg_engine.py` | SVG renderer. | Merge with export/integration tests. |
| 90 | M | `packages/bridgecad-draw/bridgecad_draw/fit.py` | Scale-ladder/fit helpers. | Merge with drawing and layout-audit changes. |
| 91 | M | `packages/bridgecad-draw/bridgecad_draw/geometry/_errors.py` | Geometry error types. | Merge with drawing tests. |
| 92 | M | `packages/bridgecad-draw/bridgecad_draw/geometry/arch_schedule.py` | Arch-schedule geometry. | Merge with drawing tests. |
| 93 | M | `packages/bridgecad-draw/bridgecad_draw/geometry/box_cell.py` | Box-cell geometry. | Merge with drawing tests. |
| 94 | M | `packages/bridgecad-draw/bridgecad_draw/layers.py` | Layer registry. | Merge with layout-audit changes. |
| 95 | M | `packages/bridgecad-draw/bridgecad_draw/layout_audit.py` | Layout audit. | Merge with the core `drawing_audit` decoupling (section 2.4). |
| 96 | M | `packages/bridgecad-draw/bridgecad_draw/primitives.py` | Drawing primitives. | Merge with drawing tests. |
| 97 | M | `packages/bridgecad-draw/bridgecad_draw/sheet1_plan.py` | Production sheet. | Merge with drawing tests. |
| 98 | M | `packages/bridgecad-draw/bridgecad_draw/sheet2_long_section.py` | Production sheet. | Merge with drawing tests. |
| 99 | M | `packages/bridgecad-draw/bridgecad_draw/sheet3_cross_section.py` | Production sheet. | Merge with drawing tests. |
| 100 | M | `packages/bridgecad-draw/bridgecad_draw/sheet4_foundation.py` | Production sheet. | Merge with drawing tests. |
| 101 | M | `packages/bridgecad-draw/bridgecad_draw/sheet5_enlarged_details.py` | Production detail sheet. | Merge with drawing tests. |
| 102 | M | `packages/bridgecad-draw/bridgecad_draw/sheet5_pier_abutment_details.py` | Production detail sheet. | Merge with drawing tests. |
| 103 | M | `packages/bridgecad-draw/bridgecad_draw/sheet8_side_elevations.py` | Production sheet. | Merge with drawing tests. |
| 104 | M | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet5A_pier_enlarged.py` | Test-only scaffold sheet. | Merge with scaffold policy decision (02-runtime-wiring.md). |
| 105 | M | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet5B_abutment_enlarged.py` | Test-only scaffold sheet. | Merge with scaffold policy decision (02-runtime-wiring.md). |
| 106 | M | `packages/bridgecad-draw/bridgecad_draw/sheets/superstructure_section.py` | Test-only scaffold sheet. | Merge with scaffold policy decision (02-runtime-wiring.md). |
| 107 | M | `packages/bridgecad-infra/bridgecad_infra/queue.py` | Implemented ARQ worker. | Merge after the `worker_jobs` entry-point refactor (section 2.4); complete Redis smoke in a compliant environment. |
| 108 | M | `packages/bridgecad-io/bridgecad_io/excel_reader.py` | Active input code. | Merge with interoperability tests. |
| 109 | M | `packages/bridgecad-io/bridgecad_io/excel_template.py` | Workbook template code. | Merge with interoperability tests. |
| 110 | M | `packages/bridgecad-io/bridgecad_io/json_adapter.py` | Active JSON I/O. | Merge with interoperability tests. |
| 111 | M | `packages/bridgecad-qa/bridgecad_qa/quality_manifest.py` | QA quality manifest. | Merge with QA tests. |
| 112 | M | `packages/bridgecad-qa/bridgecad_qa/required_content.py` | Required-content checks. | Merge with QA tests. |
| 113 | M | `packages/bridgecad-refs/bridgecad_refs/gad_text.py` | Intentionally unwired text codec. | Merge; keep unwired (02-runtime-wiring.md §8). |
| 114 | M | `packages/bridgecad-refs/bridgecad_refs/lisp_baseline.py` | LISP baseline support. | Merge with reference tooling/tests. |
| 115 | M | `pyproject.toml` | Workspace/dependency configuration. | Merge with packaging and dependency policy. |

### 3.5 Tools, Legacy Relocations, and Removed Root Test — Records 116–132 and 173

| # | Status | Path or rename | Classification | Recommended action |
|---:|---|---|---|---|
| 116 | M | `scripts/audit_dxf_conformance.py` | Direct DXF audit tool. | Merge; update the stale guide reference. |
| 117 | A | `scripts/capture_release_baseline.py` | Release evidence tool. | Merge with baseline workflow/report. |
| 118 | A | `scripts/check_browser_drafting.py` | Active launch dependency. | Merge with launch checker and browser tests. |
| 119 | A | `scripts/check_software_launch.py` | Active release gate. | Merge with all source/test dependencies. |
| 120 | M | `scripts/export_workflow_catalogue.py` | Workflow-catalogue generator. | Merge with catalogue changes. |
| 121 | M | `scripts/gad_reference_overlay.py` | Reference-overlay generator. | Merge with reference tooling. |
| 122 | M | `scripts/generate_all_pwd_gads.py` | PWD sweep generator. | Merge with acceptance/PWD tooling. |
| 123 | R056 | `_enhance_elegant_pdf.py` → `scripts/legacy/_enhance_elegant_pdf.py` | Legacy script relocation. | Merge relocation; retain as legacy or archive explicitly. |
| 124 | A | `scripts/legacy/_generate_11span_gad.py` | Legacy generator at new path. | Merge with legacy relocation. |
| 125 | R087 | `test_bridge_pdf.py` → `scripts/legacy/test_bridge_pdf.py` | Legacy test relocation. | Merge relocation; keep opt-in. |
| 126 | A | `scripts/legacy/test_robustness.py` | Legacy robustness test at new path. | Merge with legacy relocation. |
| 127 | R071 | `test_ultimate_app.py` → `scripts/legacy/test_ultimate_app.py` | CI-invoked legacy test relocation. | Merge relocation; keep while legacy app is supported. |
| 128 | R078 | `rc1_smoke.py` → `scripts/rc1_smoke.py` | Active release tool relocation. | Merge with Makefile/CI caller updates. |
| 129 | M | `scripts/refs_extract.py` | Reference extraction tool. | Merge with reference CI checks. |
| 130 | M | `scripts/render_asset_pack.py` | Asset-pack renderer. | Merge with asset-pack changes. |
| 131 | R072 | `sitecustomize.py` → `scripts/sitecustomize.py` | Source-checkout startup hook relocation. | Merge with launcher/PYTHONPATH updates. |
| 132 | M | `scripts/test_netlify_readiness.py` | Netlify verification tool. | Merge with proxy/helper changes. |
| 173 | D | `test_robustness.py` | Removed root legacy test path. | Apply deletion with replacement relocation. |

### 3.6 Legacy Package Modifications: `src/bridge_gad` — Records 135–172

All 38 records below are modifications to the fenced legacy package. The Suite image contract excludes this tree (see `Dockerfile` and [02-runtime-wiring.md](02-runtime-wiring.md#4-legacy-package-srcbridge_gad)); the changes are bulk formatting/lint or compatibility edits that should be merged with the legacy-fencing policy.

| # | Status | Path | Recommended action |
|---:|---|---|---|
| 135 | M | `src/bridge_gad/__init__.py` | Merge with legacy-fencing policy. |
| 136 | M | `src/bridge_gad/advanced_features.py` | Merge with legacy-fencing policy. |
| 137 | M | `src/bridge_gad/ai_optimizer.py` | Merge with legacy-fencing policy. |
| 138 | M | `src/bridge_gad/api.py` | Merge with legacy-fencing policy. |
| 139 | M | `src/bridge_gad/bridge_canvas_features.py` | Merge with legacy-fencing policy. |
| 140 | M | `src/bridge_gad/bridge_generator.py` | Merge with legacy-fencing policy. |
| 141 | M | `src/bridge_gad/bridge_types.py` | Merge with legacy-fencing policy. |
| 142 | M | `src/bridge_gad/calc_engine.py` | Merge with legacy-fencing policy. |
| 143 | M | `src/bridge_gad/cli.py` | Merge with legacy-fencing policy. |
| 144 | M | `src/bridge_gad/config.py` | Merge with legacy-fencing policy. |
| 145 | M | `src/bridge_gad/core.py` | Merge with legacy-fencing policy. |
| 146 | M | `src/bridge_gad/drawing.py` | Merge with legacy-fencing policy. |
| 147 | M | `src/bridge_gad/drawing_generator.py` | Merge with legacy-fencing policy. |
| 148 | M | `src/bridge_gad/dxf_to_pdf.py` | Merge with legacy-fencing policy. |
| 149 | M | `src/bridge_gad/enhanced_io_utils.py` | Merge with legacy-fencing policy. |
| 150 | M | `src/bridge_gad/enhanced_lisp_functions.py` | Merge with legacy-fencing policy. |
| 151 | M | `src/bridge_gad/generate_all_drawings.py` | Merge with legacy-fencing policy. |
| 152 | M | `src/bridge_gad/geometry.py` | Merge with legacy-fencing policy. |
| 153 | M | `src/bridge_gad/gui.py` | Merge with legacy-fencing policy. |
| 154 | M | `src/bridge_gad/lisp_mirror.py` | Merge with legacy-fencing policy. |
| 155 | M | `src/bridge_gad/logger.py` | Merge with legacy-fencing policy. |
| 156 | M | `src/bridge_gad/logger_config.py` | Merge with legacy-fencing policy. |
| 157 | M | `src/bridge_gad/multi_sheet_generator.py` | Merge with legacy-fencing policy. |
| 158 | M | `src/bridge_gad/optimize.py` | Merge with legacy-fencing policy. |
| 159 | M | `src/bridge_gad/output_formats.py` | Merge with legacy-fencing policy. |
| 160 | M | `src/bridge_gad/parameters.py` | Merge with legacy-fencing policy. |
| 161 | M | `src/bridge_gad/plugin_generator.py` | Merge with legacy-fencing policy. |
| 162 | M | `src/bridge_gad/plugin_installer.py` | Merge with legacy-fencing policy. |
| 163 | M | `src/bridge_gad/plugin_runner.py` | Merge with legacy-fencing policy. |
| 164 | M | `src/bridge_gad/plugins/__init__.py` | Merge with legacy-fencing policy. |
| 165 | M | `src/bridge_gad/plugins/box_culvert.py` | Merge with legacy-fencing policy. |
| 166 | M | `src/bridge_gad/plugins/psc_girder.py` | Merge with legacy-fencing policy. |
| 167 | M | `src/bridge_gad/plugins/slab_bridge.py` | Merge with legacy-fencing policy. |
| 168 | M | `src/bridge_gad/standards.py` | Merge with legacy-fencing policy. |
| 169 | M | `src/bridge_gad/templates.py` | Merge with legacy-fencing policy. |
| 170 | M | `src/bridge_gad/ultimate_exporter.py` | Merge with legacy-fencing policy. |
| 171 | M | `src/bridge_gad/updater.py` | Merge with legacy-fencing policy. |
| 172 | M | `src/bridge_gad/worker.py` | Merge with legacy-fencing policy. |

### 3.7 Tests — Records 174–187

| # | Status | Path | Classification | Recommended action |
|---:|---|---|---|---|
| 174 | M | `tests/draw/test_boq_provenance.py` | Drawing/BOQ regression. | Merge with bill changes. |
| 175 | M | `tests/draw/test_ep2026_12_wire.py` | Drawing wiring regression. | Merge with drawing changes. |
| 176 | M | `tests/draw/test_hypothesis_parameters.py` | Property test. | Merge with dependency/collection changes. |
| 177 | M | `tests/draw/test_nine_span_cross_view.py` | Nine-span geometry regression. | Merge with drawing changes. |
| 178 | M | `tests/draw/test_sheet01_elevation.py` | Sheet 1 regression. | Merge with drawing changes. |
| 179 | M | `tests/draw/test_sheet2_long_fit.py` | Sheet 2 regression. | Merge with drawing changes. |
| 180 | M | `tests/integration/test_full_pipeline.py` | End-to-end pipeline integration. | Merge with package/entry-point changes. |
| 181 | M | `tests/integration/test_ga_sheet_download.py` | API download integration. | Merge with gateway/renderer changes. |
| 182 | M | `tests/integration/test_workbook_pdf_download.py` | Workbook/PDF integration. | Merge with gateway/export changes. |
| 183 | M | `tests/interop/test_fuzz.py` | Interoperability fuzz test. | Merge with IO changes. |
| 184 | M | `tests/properties/test_properties.py` | Model/validation property test. | Merge with core changes. |
| 185 | M | `tests/properties/test_units.py` | Unit property test. | Merge with core changes. |
| 186 | M | `tests/test_asset_pack.py` | Asset-pack regression. | Merge with asset-sheet changes. |
| 187 | M | `tests/unit/test_abutment_stack.py` | Abutment geometry regression. | Merge with core/drawing changes. |

## 4. Ignored Noise Excluded from the Actionable List

Git reports tens of thousands of ignored files. The largest groups are:

| Ignored area | Dominant content | Reason excluded |
|---|---|---|
| `.pytest_cache/` | Test cache | Regenerable. |
| `.mypy_cache/` | Type-check cache | Regenerable. |
| `frontend/` ignored output | `node_modules/`, `dist/` | Dependencies/build output. |
| `.hypothesis/` | Property-test database | Regenerable. |
| `packages/`, `tests/`, `scripts/`, `apps/`, `src/` ignored output | Build, packaging, bytecode, metadata | Regenerable. |
| `.ruff_cache/` and root bytecode | Lint cache and `__pycache__` | Regenerable. |

After excluding caches, dependencies, bytecode, build output, packaging output, and generated frontend/browser output, **zero actionable ignored source or guidance files remain**.

Do not force-add ignored output merely because it exists locally.

## 5. Recommended Merge Groups

1. **Uncommitted change set (do first):** the two untracked modules plus the six refactor files in section 2.4.
2. **Repository/CI/governance:** records 1–17, 19, 22–25.
3. **Documentation and verification:** records 26–37 and 55.
4. **Frontend, Netlify, server, and startup:** records 38–60 and 133–134.
5. **Python production packages:** records 61–115.
6. **Tools and legacy relocations:** records 116–132 and 173.
7. **Legacy `src/bridge_gad`:** records 135–172.
8. **Tests:** records 174–187.

Keep the branch review coherent by subsystem. The prior clean-clone defects are already fixed in committed branch content; the remaining Git action is to commit the in-flight change set and merge the branch into `main` after the open CI, security, and release gates are satisfied.
