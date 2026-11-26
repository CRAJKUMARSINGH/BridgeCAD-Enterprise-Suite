# Git Incorporation Inventory

Snapshot: 26 November 2026 at `6ddf860` on `codex/phase-0-launch-baseline`.

This report lists files that exist locally but are not fully incorporated into `main`. It does **not** imply that every listed file is disconnected at runtime.

## 1. Untracked Files

There are 20 non-ignored untracked files. Several are already imported, tested, or invoked locally.

| # | File | Local wiring | Classification | Recommended action |
|---:|---|---|---|---|
| 1 | `BASELINE.md` | Linked by `LAUNCH_HARDENING_REPORT.md`. | Point-in-time launch guidance. | Review and commit as historical baseline evidence. |
| 2 | `CREAT.MD` | Linked by `README.md`. | Rolling continuity guidance. | Update stale `CODE-JUNCTION` statements, then commit. |
| 3 | `LAUNCH_HARDENING_REPORT.md` | Documents launch scripts and verification. | Release/verification guidance. | Review and commit with launch evidence. |
| 4 | `artifacts/browser-results/live-drafting-2026-11-24_01-desktop-initial.png` | Browser evidence only. | Generated artifact. | Decide whether to version evidence or store it externally. |
| 5 | `artifacts/browser-results/live-drafting-downloads/Browser-QA-Design-elevation.svg` | Output of browser drafting verification. | Generated review artifact. | Keep with the matching run or archive externally. |
| 6 | `artifacts/browser-results/live-drafting-feature-pack-desktop.png` | Browser evidence only. | Generated artifact. | Keep with the matching run or archive externally. |
| 7 | `artifacts/browser-results/live-drafting-feature-pack-mobile.png` | Browser evidence only. | Generated artifact. | Keep with the matching run or archive externally. |
| 8 | `artifacts/browser-results/live-drafting-feature-pack-report.json` | Machine-readable browser evidence. | Generated artifact. | Commit only if repository policy versions this evidence. |
| 9 | `artifacts/browser-results/live-drafting-headless-initial.png` | Browser evidence only. | Generated artifact. | Keep with the matching run or archive externally. |
| 10 | `artifacts/browser-results/live-drafting-headless-invalid.png` | Adversarial browser evidence. | Generated artifact. | Keep with invalid-input test evidence. |
| 11 | `artifacts/browser-results/live-drafting-headless-mobile.png` | Browser evidence only. | Generated artifact. | Keep with the matching run or archive externally. |
| 12 | `artifacts/browser-results/live-drafting-headless-report.json` | Machine-readable browser evidence. | Generated artifact. | Commit only if repository policy versions this evidence. |
| 13 | `artifacts/browser-results/live-drafting-headless-valid.png` | Successful browser export evidence. | Generated artifact. | Keep with valid-input test evidence. |
| 14 | `frontend/src/sheets/DraftingStudio.tsx` | Imported by `frontend/src/main.tsx`; routed at `#drafting`. | Active code awaiting Git incorporation. | Commit with the complete drafting feature. |
| 15 | `frontend/src/sheets/draftingGeometry.ts` | Imported by `DraftingStudio.tsx`. | Active code awaiting Git incorporation. | Commit with `DraftingStudio.tsx`. |
| 16 | `frontend/src/sheets/draftingStudio.css` | Imported by `DraftingStudio.tsx`. | Active code awaiting Git incorporation. | Commit with `DraftingStudio.tsx`. |
| 17 | `frontend/tests/drafting.test.mjs` | Included by `node --test tests/*.test.mjs`. | Active test awaiting Git incorporation. | Commit with drafting code and launch script. |
| 18 | `packages/bridgecad-draw/bridgecad_draw/deck_joints.py` | Imported by `engines/ga_sheet.py`, `sheet1_plan.py`, and `sheet2_long_section.py`. | Active Python code awaiting Git incorporation. | Commit with drawing changes that import it. |
| 19 | `scripts/check_browser_drafting.py` | Invoked by `scripts/check_software_launch.py`. | Active verification tool awaiting Git incorporation. | Commit with launch checker and drafting tests. |
| 20 | `scripts/check_software_launch.py` | Referenced by README, deployment docs, launch report, and Suite CI. | Active release tool awaiting Git incorporation. | Commit with all code required by the launch check. |

### Untracked Summary

- **Runtime-wired locally:** items 14–20.
- **Guidance/reporting:** items 1–3.
- **Generated evidence:** items 4–13. These ten files were subsequently deleted as regenerable duplicates, and `.gitignore` now excludes future `artifacts/browser-results/live-drafting-*` captures.
- **Clean-clone risk:** a clone of the current commit cannot reproduce the live drafting feature or launch checker because these files are absent from Git.

## 2. Actionable Ignored Source File — Resolved in Working Tree

The pre-fix snapshot reported 36,710 ignored files; the exact total fluctuates as caches are created. Nearly all are caches, bytecode, dependencies, packaging output, or generated frontend output. After excluding those, one source file required action:

| File | Ignore rule | Runtime wiring | Risk | Recommended action |
|---|---|---|---|---|
| `netlify/lib/drawing-proxy.cjs` | Previously matched by `.gitignore:13` (`lib/`); now covered by narrow negative exceptions. | Required by `netlify/functions/predict.js`, `template.js`, `generate_sample_pdf.js`, and `export_package.js`. | Without the fix, a clean checkout or deployment from Git lacks a required production module. | Commit the now-visible helper with its four callers and run a clean-checkout Netlify function test. |

Ignored build copies under `packages/*/build/`, `packages/*/*.egg-info/`, and `frontend/dist/` are regenerated output, not missing source.

**Working-tree resolution:** `.gitignore` now contains narrow exceptions for `netlify/lib/` and `netlify/lib/**`. `git check-ignore` confirms the proxy helper is no longer ignored, and `git status` now lists it as untracked source ready to commit with its four callers.

## 3. Branch-only Committed Changes Relative to `main`

`git rev-list --left-right --count main...HEAD` reports `0 14`: the branch is 14 commits ahead and not behind local `main`.

The following 47 change records are committed on the branch but not present in local `main` in their current form. Rename records show both the old and new paths. Deleted old paths are included because their deletion is part of the unmerged branch state.

| # | Status | Path or rename | Classification | Recommended action |
|---:|---|---|---|---|
| 1 | M | `.agents/tasks/security-audit-2026-10-13/trufflehog_git.json` | Security baseline evidence. | Merge with Phase 0 after reviewing scan churn. |
| 2 | M | `.github/actions/setup-suite/action.yml` | CI workspace installer. | Merge with dependent workflow changes. |
| 3 | M | `.github/workflows/ci.yml` | CI workflow. | Merge after open shared checks are green. |
| 4 | A | `.github/workflows/phase0-baseline.yml` | Phase 0 verification workflow. | Merge as baseline gate. |
| 5 | M | `.github/workflows/suite-ci.yml` | Suite CI workflow. | Merge with setup action and launch scripts. |
| 6 | M | `.gitignore` | Repository hygiene. | Merge with packaging/artifact policy review. |
| 7 | A | `CHANGELOG.md` | Release guidance. | Merge with Phase 0 documentation. |
| 8 | A | `CODE_OF_CONDUCT.md` | Governance guidance. | Merge with community docs. |
| 9 | A | `CONTRIBUTING.md` | Contributor guidance. | Merge with test/documentation policy. |
| 10 | M | `Dockerfile` | Container contract. | Merge with legacy fencing and dependency policy. |
| 11 | M | `Makefile` | Developer entrypoints. | Merge with relocated scripts. |
| 12 | A | `SECURITY.md` | Security guidance. | Merge with governance docs. |
| 13 | D | `_generate_11span_gad.py` | Old root path removed. | No current file; merge deletion with replacement path. |
| 14 | R051 | `app_lean.py` → `apps/streamlit-ui/legacy/app_lean.py` | Legacy app relocation. | Merge relocation; retain as opt-in legacy. |
| 15 | R073 | `streamlit_app_ultimate.py` → `apps/streamlit-ui/legacy/streamlit_app_ultimate.py` | Legacy app relocation. | Merge relocation; retain as opt-in legacy. |
| 16 | A | `artifacts/TRIAGE_LOG.md` | Merge-gate guidance/register. | Merge with robot gate changes. |
| 17 | A | `audit/baseline.json` | Release baseline evidence. | Merge with release report. |
| 18 | M | `bridgecad/__init__.py` | Active facade. | Merge after package-resolution tests. |
| 19 | M | `bridgecad/__main__.py` | Active CLI. | Merge with relocated verifier paths. |
| 20 | A | `docs/adr/0002-group-workspace-entry-points.md` | Architecture guidance. | Merge with file moves. |
| 21 | A | `docs/adr/README.md` | ADR index. | Merge with ADR. |
| 22 | A | `docs/index.md` | MkDocs landing page. | Merge with `mkdocs.yml`. |
| 23 | M | `docs/schema/bridgeproject.schema.json` | Published schema artifact. | Merge with schema export check. |
| 24 | A | `docs/verification/RELEASE_REPORT.md` | Release guidance/evidence. | Merge with Phase 0 status. |
| 25 | M | `docs/verification/TRACEABILITY.md` | Compliance guidance. | Merge with QA/test changes. |
| 26 | A | `mkdocs.yml` | Documentation navigation. | Merge with docs site files. |
| 27 | M | `packages/bridgecad-bill/bridgecad_bill/formatters/excel_formatter.py` | Active BOQ code. | Merge with bill tests. |
| 28 | M | `packages/bridgecad-bill/bridgecad_bill/measurers.py` | Active BOQ code. | Merge with bill tests. |
| 29 | M | `packages/bridgecad-bill/bridgecad_bill/processor.py` | Active BOQ code. | Merge with bill tests. |
| 30 | M | `packages/bridgecad-core/bridgecad_core/validation.py` | Active validation code. | Merge with core tests. |
| 31 | M | `packages/bridgecad-io/bridgecad_io/excel_reader.py` | Active input code. | Merge with interoperability tests. |
| 32 | M | `packages/bridgecad-io/bridgecad_io/json_adapter.py` | Active input/output code. | Merge with interoperability tests. |
| 33 | A | `scripts/capture_release_baseline.py` | Release evidence tool. | Merge with baseline workflow/report. |
| 34 | R056 | `_enhance_elegant_pdf.py` → `scripts/legacy/_enhance_elegant_pdf.py` | Legacy script relocation. | Merge relocation; retain as legacy. |
| 35 | A | `scripts/legacy/_generate_11span_gad.py` | Legacy generator at new path. | Merge with legacy relocation. |
| 36 | R087 | `test_bridge_pdf.py` → `scripts/legacy/test_bridge_pdf.py` | Legacy test relocation. | Merge relocation; keep opt-in. |
| 37 | A | `scripts/legacy/test_robustness.py` | Legacy robustness test at new path. | Merge with legacy relocation. |
| 38 | R071 | `test_ultimate_app.py` → `scripts/legacy/test_ultimate_app.py` | Legacy test relocation. | Merge relocation; CI invokes it explicitly. |
| 39 | R078 | `rc1_smoke.py` → `scripts/rc1_smoke.py` | Active release tool relocation. | Merge with Makefile/CI caller updates. |
| 40 | M | `scripts/refs_extract.py` | Reference extraction tool. | Merge with reference CI checks. |
| 41 | R072 | `sitecustomize.py` → `scripts/sitecustomize.py` | Source-checkout startup hook. | Merge with launcher/PYTHONPATH updates. |
| 42 | D | `test_robustness.py` | Old root path removed. | No current file; merge deletion with replacement path. |
| 43 | M | `tests/draw/test_boq_provenance.py` | Drawing/BOQ test. | Merge with bill changes. |
| 44 | M | `tests/draw/test_hypothesis_parameters.py` | Property test. | Merge with dependency/collection changes. |
| 45 | M | `tests/interop/test_fuzz.py` | Interoperability test. | Merge with IO changes. |
| 46 | M | `tests/properties/test_properties.py` | Property test. | Merge with model/validation changes. |
| 47 | M | `tests/properties/test_units.py` | Unit property test. | Merge with model/validation changes. |

## 4. Unstaged Modifications

All 49 files below exist and are tracked, but their current contents differ from `HEAD`. They are already part of the working application; the gap is commit/incorporation, not initial wiring.

| # | File | Area | Classification |
|---:|---|---|---|
| 1 | `.github/workflows/suite-ci.yml` | CI | Launch/check workflow changes. |
| 2 | `README.md` | Guidance | Production and launch instructions. |
| 3 | `apps/api-gateway/bridgecad_api/main.py` | API | Active gateway changes. |
| 4 | `docs/DEPLOYMENT.md` | Guidance | Deployment and verification changes. |
| 5 | `docs/verification/RELEASE_REPORT.md` | Guidance | Latest release and cleanup record. |
| 6 | `frontend/package.json` | Frontend | Scripts/dependencies. |
| 7 | `frontend/src/WorkflowLanding.tsx` | Frontend | Active landing page. |
| 8 | `frontend/src/main.tsx` | Frontend | Active routing and drafting import. |
| 9 | `frontend/src/sheets/Sheet01Overview.tsx` | Frontend | Active sheet UI. |
| 10 | `frontend/src/sheets/SheetChrome.tsx` | Frontend | Active sheet UI. |
| 11 | `frontend/src/sheets/detailGeometry.d.ts` | Frontend | Geometry type declarations. |
| 12 | `frontend/src/sheets/detailGeometry.js` | Frontend | Geometry implementation. |
| 13 | `frontend/src/sheets/registry.tsx` | Frontend | Sheet registry. |
| 14 | `frontend/src/sheets/theme.ts` | Frontend | UI theme. |
| 15 | `frontend/src/styles.css` | Frontend | Global styling. |
| 16 | `frontend/tests/workbook-proxy.test.mjs` | Test | Workbook proxy privacy/error test. |
| 17 | `frontend/vite.config.ts` | Frontend | Build configuration. |
| 18 | `netlify/functions/export_package.js` | Serverless | Active package proxy. |
| 19 | `netlify/functions/generate_sample_pdf.js` | Serverless | Active sample PDF proxy. |
| 20 | `netlify/functions/predict.js` | Serverless | Active prediction proxy. |
| 21 | `netlify/functions/template.js` | Serverless | Active template proxy. |
| 22 | `packages/bridgecad-core/bridgecad_core/abutment_stack.py` | Python core | Active geometry. |
| 23 | `packages/bridgecad-core/bridgecad_core/geometry/abutment_profiles.py` | Python core | Active geometry. |
| 24 | `packages/bridgecad-draw/bridgecad_draw/asset_sheet1_lsection.py` | Drawing | Active asset sheet. |
| 25 | `packages/bridgecad-draw/bridgecad_draw/asset_sheet2_deck_abutment.py` | Drawing | Active asset sheet. |
| 26 | `packages/bridgecad-draw/bridgecad_draw/asset_sheet3_pier.py` | Drawing | Active asset sheet. |
| 27 | `packages/bridgecad-draw/bridgecad_draw/asset_sheet4_single_span.py` | Drawing | Active asset sheet. |
| 28 | `packages/bridgecad-draw/bridgecad_draw/booklet.py` | Drawing | Production sheet manifest/generator. |
| 29 | `packages/bridgecad-draw/bridgecad_draw/engines/_render.py` | Drawing | Renderer support. |
| 30 | `packages/bridgecad-draw/bridgecad_draw/engines/ga_sheet.py` | Drawing | Active GA renderer. |
| 31 | `packages/bridgecad-draw/bridgecad_draw/engines/pdf_engine.py` | Drawing | PDF renderer. |
| 32 | `packages/bridgecad-draw/bridgecad_draw/engines/png_engine.py` | Drawing | PNG renderer. |
| 33 | `packages/bridgecad-draw/bridgecad_draw/engines/svg_engine.py` | Drawing | SVG renderer. |
| 34 | `packages/bridgecad-draw/bridgecad_draw/sheet1_plan.py` | Drawing | Production sheet. |
| 35 | `packages/bridgecad-draw/bridgecad_draw/sheet2_long_section.py` | Drawing | Production sheet. |
| 36 | `packages/bridgecad-draw/bridgecad_draw/sheet5_enlarged_details.py` | Drawing | Production enlarged-detail sheet. |
| 37 | `packages/bridgecad-draw/bridgecad_draw/sheet5_pier_abutment_details.py` | Drawing | Production pier/abutment sheet. |
| 38 | `packages/bridgecad-io/bridgecad_io/excel_template.py` | Python IO | Workbook template code. |
| 39 | `scripts/test_netlify_readiness.py` | Verification | Netlify readiness checks. |
| 40 | `server/index.mjs` | Server | Static serving/API proxy. |
| 41 | `server/start.sh` | Deployment | API/frontend launcher. |
| 42 | `tests/draw/test_ep2026_12_wire.py` | Test | Drawing wiring regression. |
| 43 | `tests/draw/test_nine_span_cross_view.py` | Test | Nine-span geometry regression. |
| 44 | `tests/draw/test_sheet01_elevation.py` | Test | Sheet 1 regression. |
| 45 | `tests/draw/test_sheet2_long_fit.py` | Test | Sheet 2 regression. |
| 46 | `tests/integration/test_ga_sheet_download.py` | Test | API download integration. |
| 47 | `tests/integration/test_workbook_pdf_download.py` | Test | Workbook/PDF integration. |
| 48 | `tests/test_asset_pack.py` | Test | Asset-pack regression. |
| 49 | `tests/unit/test_abutment_stack.py` | Test | Abutment geometry regression. |

### Recommended Commit Groups

1. **Netlify proxy hardening:** four functions plus the ignored `netlify/lib/drawing-proxy.cjs`.
2. **Live drafting:** untracked drafting sources, `main.tsx`, tests, launch scripts, and browser evidence.
3. **Drawing corrections:** modified drawing modules, `deck_joints.py`, and focused drawing/integration tests.
4. **Launch/deployment:** server, start script, readiness checks, README, deployment docs, and launch reports.
5. **Phase 0 governance:** branch-only CI, packaging, ADR, baseline, and community documentation.
6. **Core/IO/bill changes:** package modifications and their property/interoperability tests.

Do not combine unrelated legacy relocation, active drawing fixes, and release governance into a single unreviewed commit.

## 5. Ignored Noise Excluded from the Actionable List

The ignored population is large but mostly regenerable:

- `.pytest_cache/`
- `.mypy_cache/`
- `.hypothesis/`
- `.ruff_cache/`
- `__pycache__/` and `.pyc`
- `node_modules/`
- `frontend/dist/`
- `packages/*/build/`
- `packages/*/*.egg-info/`

These should not be force-added merely because they exist locally. The one exception is the source helper `netlify/lib/drawing-proxy.cjs`, which is required by tracked production callers.
