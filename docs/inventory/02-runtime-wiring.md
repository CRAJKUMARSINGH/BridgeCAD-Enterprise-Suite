# Runtime Wiring Inventory

Snapshot: 26 November 2026 at `6ddf860`.

This report focuses on tracked or local source files that are not reachable from the main application, are only partially wired, or are advertised without a working implementation. Git-only incorporation gaps are listed separately in [01-git-incorporation.md](01-git-incorporation.md).

## 1. Confirmed Broken or High-Risk Wiring

| Priority | File(s) | Current state | Impact | Recommended action |
|---|---|---|---|---|
| P0 | `netlify/lib/drawing-proxy.cjs` | **Resolved in the working tree:** required by four tracked Netlify functions and now re-included by a narrow `.gitignore` exception. | The helper is visible to Git and ready to commit; a clean-checkout deployment is safe only after that commit lands. | Commit the helper with its four callers and rerun the Netlify readiness test from a clean checkout. |
| P0 | `packages/bridgecad-infra/bridgecad_infra/queue.py` | **Resolved in the working tree:** implements `run_worker`, Redis configuration, and drawing/BOQ/export job handlers. `Makefile` now has a `worker` target. | The configured Compose command and local worker entrypoint now resolve. | Run against Redis in CI/Compose and commit with the Makefile target. |
| P1 | `packages/bridgecad-infra/bridgecad_infra/auth.py` | Implemented and exported, but no gateway call site was found. | Deployment docs list API-key variables that do not enforce authentication. | Wire auth dependencies/middleware or correct the deployment contract. |
| P1 | `apps/api-gateway/bridgecad_api/main.py` | Lifespan contains only `yield  # M8: init DB / cache / storage here`. | DB/cache/storage lifecycle is not initialized by the API. | Implement lifespan integration or explicitly document unsupported infrastructure. |
| P2 | Nine placeholder modules listed in section 5 | Imported/advertised but functionless. | Public API and facade can imply unsupported capabilities. | Implement, mark unsupported, or remove from discovery. |

### Post-inventory Fix Verification

- `git check-ignore` now reports `netlify/lib/drawing-proxy.cjs` as not ignored, and Git lists it as untracked source.
- `ruff check` and `ruff format --check` pass for the new queue implementation.
- Import checks confirm three registered ARQ jobs and successful Redis settings parsing from Compose's `CACHE_URL`.
- The Netlify workbook-proxy regression test passes.
- A live drawing/BOQ job smoke test is blocked by the local interpreter's mismatched Pydantic installation (`pydantic 2.5.3` with `pydantic_core 2.14.6`), before worker job code executes. The repository declares `pydantic>=2.6`; rerun the smoke test in a compliant environment.

## 2. Active Entrypoints and False Positives

The following are connected to active surfaces and should not be labeled orphaned:

| File/surface | Evidence of wiring |
|---|---|
| `frontend/src/main.tsx` | Root Netlify entrypoint; routes to workflow landing, workspace, and drafting. |
| `frontend/src/sheets/DraftingStudio.tsx` | Imported and routed by `main.tsx`, although currently untracked. |
| `frontend/src/sheets/draftingGeometry.ts` | Imported by `DraftingStudio.tsx`. |
| `frontend/src/sheets/draftingStudio.css` | Imported by `DraftingStudio.tsx`. |
| `packages/bridgecad-draw/bridgecad_draw/deck_joints.py` | Imported by three active drawing modules, although currently untracked. |
| `apps/web-console/src/main.tsx` | Separate Vite application with its own CI job, Docker image, and `make web`. |
| `public/index.html` | Alternate Vercel entrypoint; `vercel.json` rewrites requests to `/index.html`. |
| `apps/streamlit-ui/app.py` | Active `make ui` target and README quick-start path. |
| `frontend/src/sheets/Sheet04Foundation.tsx` | Imported by `frontend/src/sheets/registry.tsx`. |
| `frontend/src/sheets/Sheet05PierAbutment.tsx` | Imported by `frontend/src/sheets/registry.tsx`. |
| `packages/bridgecad-infra/bridgecad_infra/repositories.py` | `ProjectIndexRepo` is used by API project-index routes. |
| `packages/bridgecad-infra/bridgecad_infra/db.py` | Used by `scripts/rc1_smoke.py`. |
| `packages/bridgecad-export/bridgecad_export/bbs.py` | Used by the active export orchestrator. |
| `packages/bridgecad-export/bridgecad_export/revisions.py` | Used by bundler/transmittal and revision tests. |
| `packages/bridgecad-ai/bridgecad_ai/drawing_review.py` | Active Streamlit tab and module CLI. |
| `packages/bridgecad-ai/bridgecad_ai/estimator.py` | Used by robotic verification tooling. |
| `packages/bridgecad-ai/bridgecad_ai/optimizer.py` | Used by RC smoke and robotic verification tooling. |
| `packages/bridgecad-ai/bridgecad_ai/param_suggester.py` | Used by robotic verification tooling. |
| `packages/bridgecad-refs/bridgecad_refs/parse.py` | Used by reference extraction and reference tests. |
| `packages/bridgecad-refs/bridgecad_refs/lisp_baseline.py` | Used by reference tooling and tests. |

## 3. Legacy Package: `src/bridge_gad`

The root `Dockerfile` explicitly states that the Suite image contract is the `bridgecad` facade and that `src/bridge_gad` is fenced legacy code. The package remains reachable through legacy Streamlit apps, legacy scripts, and tests, but not through the main Suite facade.

**Classification:** retained legacy implementation, not a candidate for blind import into production.

**Recommended action:** decide feature parity and migration scope file by file; retain as opt-in compatibility code or archive with an explicit migration record.

| # | File | Legacy role |
|---:|---|---|
| 1 | `src/bridge_gad/__init__.py` | Legacy package exports/version. |
| 2 | `src/bridge_gad/__main__.py` | Legacy module entrypoint. |
| 3 | `src/bridge_gad/advanced_features.py` | Legacy feature collection. |
| 4 | `src/bridge_gad/ai_optimizer.py` | Legacy AI optimization. |
| 5 | `src/bridge_gad/api.py` | Legacy API surface. |
| 6 | `src/bridge_gad/bridge_canvas_features.py` | Legacy drawing/canvas features. |
| 7 | `src/bridge_gad/bridge_generator.py` | Legacy bridge generator. |
| 8 | `src/bridge_gad/bridge_types.py` | Legacy type definitions. |
| 9 | `src/bridge_gad/calc_engine.py` | Legacy calculation engine. |
| 10 | `src/bridge_gad/cli.py` | Legacy command-line interface. |
| 11 | `src/bridge_gad/config.py` | Legacy configuration. |
| 12 | `src/bridge_gad/core.py` | Legacy core models/helpers. |
| 13 | `src/bridge_gad/drawing.py` | Legacy drawing code. |
| 14 | `src/bridge_gad/drawing_generator.py` | Legacy drawing generator. |
| 15 | `src/bridge_gad/dxf_to_pdf.py` | Legacy conversion tool. |
| 16 | `src/bridge_gad/enhanced_io_utils.py` | Legacy enhanced IO. |
| 17 | `src/bridge_gad/enhanced_lisp_functions.py` | Legacy LISP-related helpers. |
| 18 | `src/bridge_gad/generate_all_drawings.py` | Legacy batch generator/CLI. |
| 19 | `src/bridge_gad/geometry.py` | Legacy geometry calculations. |
| 20 | `src/bridge_gad/gui.py` | Legacy GUI. |
| 21 | `src/bridge_gad/io_utils.py` | Legacy IO helpers. |
| 22 | `src/bridge_gad/lisp_mirror.py` | Simplified legacy LISP mirror. |
| 23 | `src/bridge_gad/logger.py` | Legacy logging helper. |
| 24 | `src/bridge_gad/logger_config.py` | Legacy logging configuration. |
| 25 | `src/bridge_gad/multi_sheet_generator.py` | Legacy multi-sheet generator. |
| 26 | `src/bridge_gad/optimize.py` | Legacy optimization. |
| 27 | `src/bridge_gad/output_formats.py` | Legacy output-format adapter. |
| 28 | `src/bridge_gad/parameters.py` | Legacy parameters. |
| 29 | `src/bridge_gad/plugin_generator.py` | Legacy plugin generator. |
| 30 | `src/bridge_gad/plugin_installer.py` | Legacy plugin installer. |
| 31 | `src/bridge_gad/plugin_manifest.json` | Legacy plugin manifest. |
| 32 | `src/bridge_gad/plugin_registry.py` | Legacy plugin registry. |
| 33 | `src/bridge_gad/plugin_runner.py` | Legacy plugin runner. |
| 34 | `src/bridge_gad/plugins/__init__.py` | Legacy plugin package. |
| 35 | `src/bridge_gad/plugins/box_culvert.py` | Legacy box-culvert plugin. |
| 36 | `src/bridge_gad/plugins/psc_girder.py` | Legacy PSC-girder plugin. |
| 37 | `src/bridge_gad/plugins/slab_bridge.py` | Legacy slab-bridge plugin. |
| 38 | `src/bridge_gad/py.typed` | Legacy typing marker. |
| 39 | `src/bridge_gad/routing.py` | Legacy routing. |
| 40 | `src/bridge_gad/standards.py` | Legacy standards data/helpers. |
| 41 | `src/bridge_gad/telemetry.py` | Legacy telemetry. |
| 42 | `src/bridge_gad/templates.py` | Legacy templates. |
| 43 | `src/bridge_gad/ultimate_exporter.py` | Legacy exporter. |
| 44 | `src/bridge_gad/updater.py` | Legacy self-updater. |
| 45 | `src/bridge_gad/worker.py` | Legacy worker. |

### Legacy Applications

| File | Current status | Recommended action |
|---|---|---|
| `apps/streamlit-ui/legacy/app_lean.py` | Relocated by ADR-0002; opt-in legacy launch path. | Retain until parity review; do not route the main UI through it implicitly. |
| `apps/streamlit-ui/legacy/streamlit_app_ultimate.py` | Relocated by ADR-0002; large legacy workflow. | Retain until parity review; migrate only verified capabilities. |

### Legacy Scripts

| File | Current status | Recommended action |
|---|---|---|
| `scripts/legacy/_enhance_elegant_pdf.py` | Legacy PDF enhancement script. | Keep as legacy or archive after confirming no active caller. |
| `scripts/legacy/_generate_11span_gad.py` | Legacy eleven-span generator. | Keep as legacy/reference; do not confuse with active acceptance tooling. |
| `scripts/legacy/test_bridge_pdf.py` | Manually invoked legacy test. | Keep opt-in or archive with the legacy app. |
| `scripts/legacy/test_robustness.py` | Manually invoked legacy test. | Keep opt-in or archive with the legacy app. |
| `scripts/legacy/test_ultimate_app.py` | Explicitly invoked by CI. | Keep while the legacy app remains supported. |

## 4. Test-only Drawing Scaffold

Production `packages/bridgecad-draw/bridgecad_draw/booklet.py` imports root-level modules such as `bridgecad_draw.sheet1_plan`. It does **not** import the parallel `bridgecad_draw.sheets` package. The scaffold is exercised by tests such as `tests/draw/test_superstructure_section.py` and `tests/draw/contract.py`.

**Classification:** test/development scaffold, not the production sheet manifest.

**Recommended action:** compare each scaffold implementation with its production counterpart, then promote useful code or remove the duplicate after tests are migrated.

| # | File | Scaffold status |
|---:|---|---|
| 1 | `packages/bridgecad-draw/bridgecad_draw/sheets/__init__.py` | Scaffold package marker. |
| 2 | `packages/bridgecad-draw/bridgecad_draw/sheets/_common.py` | Shared scaffold canvas/helpers. |
| 3 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet1_plan.py` | Parallel plan implementation. |
| 4 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet2_long_section.py` | Parallel long-section implementation. |
| 5 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet3_cross_section.py` | Parallel cross-section implementation. |
| 6 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet4_foundation.py` | Parallel foundation implementation. |
| 7 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet5A_pier_enlarged.py` | In-memory enlarged-pier shim. |
| 8 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet5B_abutment_enlarged.py` | In-memory enlarged-abutment shim. |
| 9 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet5_pier_abutment_details.py` | Parallel pier/abutment implementation. |
| 10 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet6_bearings_joints.py` | Parallel bearings/joints implementation. |
| 11 | `packages/bridgecad-draw/bridgecad_draw/sheets/sheet7_bill_of_quantities.py` | Parallel BOQ sheet implementation. |
| 12 | `packages/bridgecad-draw/bridgecad_draw/sheets/superstructure_section.py` | Conditional superstructure renderer used by scaffold/tests. |

## 5. Placeholder Modules

At the snapshot, each file below contained only a milestone docstring. Some are eagerly imported by `bridgecad.__init__` or exported by package `__init__.py`; import success does not mean the capability exists. `queue.py` has since been implemented; the other eight remain placeholders.

| File | Advertised capability | Wiring problem | Recommended action |
|---|---|---|---|
| `packages/bridgecad-infra/bridgecad_infra/metrics.py` | Prometheus counters/histograms. | No implementation or caller. | Implement or remove from M8 claims. |
| `packages/bridgecad-infra/bridgecad_infra/queue.py` | ARQ async job runner. | **Resolved in the working tree:** `run_worker` and three job handlers are implemented; see section 1. | Run against Redis in CI/Compose, then commit. |
| `packages/bridgecad-infra/bridgecad_infra/storage.py` | Local/S3 dual storage adapter. | No implementation or production lifecycle call. | Implement or disable storage claims. |
| `packages/bridgecad-export/bridgecad_export/versioner.py` | Version stamping in outputs/metadata. | Facade-loaded but functionless. | Implement or remove from public discovery. |
| `packages/bridgecad-qa/bridgecad_qa/recommendations.py` | Auto-fix recommendation engine. | Facade-loaded but functionless. | Implement or remove from public discovery. |
| `packages/bridgecad-plugins/bridgecad_plugins/installer.py` | Plugin install/uninstall CLI. | Facade-loaded but functionless. | Implement or remove install guidance. |
| `packages/bridgecad-bill/bridgecad_bill/formatters/html_formatter.py` | HTML bill formatter. | No implementation; active orchestrator uses Excel/CSV/PDF. | Implement if HTML bills are required. |
| `packages/bridgecad-bill/bridgecad_bill/statements.py` | RA/final bill statements. | Facade-loaded but functionless. | Implement or mark unsupported. |
| `packages/bridgecad-draw/bridgecad_draw/engines/three_engine.py` | three.js JSON 3D scene engine. | No implementation or caller. | Implement or remove from M3 claims. |

## 6. Implemented but Not Connected to an Active Application Route

These files contain real code but have no production caller in the inspected application, CLI, API, or deployment entrypoints. Test coverage and package re-exports are noted separately because they are not production wiring.

| File | Evidence | Disposition | Acceptance condition |
|---|---|---|---|
| `packages/bridgecad-infra/bridgecad_infra/auth.py` | Exported by `bridgecad_infra`; deployment docs require `BRIDGECAD_API_KEYS`, but the gateway never calls it. | **WIRE** | Add gateway authentication dependencies/middleware and tests for missing, invalid, and under-privileged keys before production. |
| `packages/bridgecad-infra/bridgecad_infra/cache.py` | Exported by `bridgecad_infra`; no application call site found. | **WIRE** | Use the existing QA/BOQ/drawing caches at the relevant API/service boundaries, with invalidation and hit/miss tests. |
| `packages/bridgecad-infra/bridgecad_infra/logging_setup.py` | Exported by `bridgecad_infra`; no service startup configuration call found. | **WIRE** | Configure logging once in API and worker startup; preserve the standard-library fallback and test structured output. |
| `packages/bridgecad-ai/bridgecad_ai/comparator.py` | Exported and facade-loaded; no production or test caller found. The legacy UI has a separate comparator. | **PLUGIN-PROMOTE** | Package as an optional AI comparison plugin/CLI with a manifest, fixtures, and metric tests; do not add a core UI dependency by default. |
| `packages/bridgecad-export/bridgecad_export/dwg_engine.py` | Exported and covered by interoperability tests; requires a separately licensed ODA converter. | **PLUGIN-PROMOTE** | Expose through an optional licensed export adapter/plugin with capability discovery and a DXF fallback. |
| `packages/bridgecad-export/bridgecad_export/ifc_engine.py` | Exported and covered by interoperability tests; requires optional `ifcopenshell`. | **PLUGIN-PROMOTE** | Expose through an optional openBIM export adapter/plugin while preserving the `[ifc]` extra and round-trip tests. |
| `packages/bridgecad-export/bridgecad_export/transmittal.py` | Tested by `tests/draw/test_revisions.py`; no active issue/export route found. | **WIRE** | Include the transmittal in the issue/export flow and bundled output, with unknown-revision and hash-drift tests. |

**Disposition totals:** 4 WIRE, 3 PLUGIN-PROMOTE, 0 ARCHIVE.

`PLUGIN-PROMOTE` means retaining the implementation and tests while exposing it through an optional, discoverable adapter rather than making it a mandatory core UI/API dependency.

## 7. Intentionally Unwired Reference Codec

| File | Explicit status | Recommended action |
|---|---|---|
| `packages/bridgecad-refs/bridgecad_refs/gad_text.py` | `docs/LISP_FIDELITY_AND_DIRT_WALL.md` states the codec is intentionally not wired to the production generator until final-span and absolute-RL semantics are resolved. | Keep unwired until an adapter and acceptance tests exist; do not treat it as an accidental omission. |

## 8. Standalone Pages and Unlinked Assets

| File | Current state | Recommended action |
|---|---|---|
| `frontend/demo_pdf_button.html` | Standalone demo page; not referenced by `frontend/index.html` or Vite config. It calls real API paths but is not in main navigation. | Link it deliberately, fold it into the app, or archive as a demo. |
| `learn.html` | Standalone learning centre; no link found in the root frontend entrypoint. | Add navigation or move to a documented static route. |
| `learn-media/bridgecad-quickstart.mp4` | Used by `learn.html`. | Keep with the learning page; not a runtime import. |
| `learn-media/captions.vtt` | Used by `learn.html`. | Keep with the learning page. |
| `learn-media/poster.png` | Used by `learn.html`. | Keep with the learning page. |
| `inputs/bridge_parameters.txt` | No code/config reference found. | Confirm whether it is a sample; move to a documented samples area or remove. |
| `artifacts/gad-acceptance/_gen_nine_span.py` | Standalone acceptance generator referenced by production scripts/comments; not imported by the application. | Keep as a direct verification tool; see [04-standalone-tools.md](04-standalone-tools.md). |
| `docs/build_manual.py` | Standalone generator; required `docs/manual_template.md` is absent. | Restore source template/tooling or mark output archival; see [03-guidance-reference.md](03-guidance-reference.md). |

## 9. Expected Non-runtime Files

The following are intentionally outside the production import graph:

- 199 tracked files under `tests/`.
- 802 tracked exemplar files under `EXAMPLES/`.
- Reference PDFs, extracted facts, expected values, and conflict data under `references/`.
- Generated acceptance output under `artifacts/gad-acceptance/`.
- Browser screenshots, ZIPs, reports, and replay/test output under `artifacts/browser-results/` and `artifacts/continue/`.
- Direct scripts under `scripts/` and package-root verifiers.
- Documentation, manuals, schemas, and governance files.

Their absence from production imports is normal. They become inventory concerns only when they are untracked, ignored despite being required, stale, broken, or advertised as active functionality.
