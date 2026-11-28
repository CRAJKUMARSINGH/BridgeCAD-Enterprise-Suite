# Standalone Tool and Verifier Inventory

Snapshot: 27 November 2026 at `6cbc5a9`.

A script that is not imported by the application is not automatically unwired. Most files in this report are intended to be executed directly by developers, CI, release engineers, or acceptance workflows. The purpose of this inventory is to distinguish those intentional entrypoints from genuinely disconnected code.

Current totals: **77 tracked scripts**, **zero untracked scripts**, five legacy scripts, and two active launch scripts. All are tracked on the current branch; the remaining Git action is merging the branch into `main`.

## 1. Tracked Scripts

| # | Script | Wiring classification | Recommended action |
|---:|---|---|---|
| 1 | `scripts/_gen_golden_packages.py` | Direct golden-package generator. | Keep as direct tool. |
| 2 | `scripts/advanced_user_robot.py` | Makefile `robotic` target. | Keep; wired through developer workflow. |
| 3 | `scripts/audit_dead_geometry.py` | Makefile and Suite CI. | Keep; wired quality gate. |
| 4 | `scripts/audit_dxf_conformance.py` | Direct DXF audit tool. | Keep as direct tool; update stale guide reference. |
| 5 | `scripts/audit_layers.py` | Draw CI workflow. | Keep; wired quality gate. |
| 6 | `scripts/basic_user_robot.py` | Makefile `robotic` target. | Keep; wired through developer workflow. |
| 7 | `scripts/browser_test.py` | Direct browser test tool. | Keep as direct tool. |
| 8 | `scripts/build_ctb.py` | Direct CTB build tool. | Keep as direct tool. |
| 9 | `scripts/bump_version_rc1.py` | Release/version tool. | Keep as direct release tool. |
| 10 | `scripts/capture_release_baseline.py` | Phase 0 release evidence tool; branch-only addition. | Merge with baseline workflow/report. |
| 11 | `scripts/check_boq_provenance.py` | Direct BOQ provenance check. | Keep as direct check. |
| 12 | `scripts/check_browser_drafting.py` | Active launch dependency; branch-only addition. | Merge with launch checker and browser tests. |
| 13 | `scripts/check_checklists.py` | Direct checklist check. | Keep as direct check. |
| 14 | `scripts/check_drafting_standard.py` | Direct drafting-standard check. | Keep as direct check. |
| 15 | `scripts/check_notes.py` | Direct drawing-note check. | Keep as direct check. |
| 16 | `scripts/check_pdfa.py` | Direct PDF/A check. | Keep as direct check. |
| 17 | `scripts/check_perf_budgets.py` | Direct performance-budget check. | Keep as direct check. |
| 18 | `scripts/check_software_launch.py` | Active documented release gate; branch-only addition. | Merge with all source/test dependencies. |
| 19 | `scripts/check_text_heights.py` | Direct text-height check. | Keep as direct check. |
| 20 | `scripts/check_traceability.py` | Direct traceability check. | Keep as direct check. |
| 21 | `scripts/check_version_consistency.py` | Suite CI. | Keep; wired quality gate. |
| 22 | `scripts/check_view_axes.py` | Makefile `lint`. | Keep; wired quality gate. |
| 23 | `scripts/clear_stale_locks.py` | Direct maintenance tool. | Keep as operational tool. |
| 24 | `scripts/create_repo_sample_catalogue.py` | Direct sample-catalogue generator. | Keep as direct tool. |
| 25 | `scripts/dump_dxf_facts.py` | Direct DXF diagnostic tool. | Keep as diagnostic tool. |
| 26 | `scripts/export_project_schema.py` | Interoperability CI schema check. | Keep; wired contract gate. |
| 27 | `scripts/export_workflow_catalogue.py` | Direct workflow-catalogue generator. | Keep as direct tool. |
| 28 | `scripts/fix_e2e_fixtures.py` | One-time/maintenance fixture migration tool. | Review for archival after fixtures stabilize. |
| 29 | `scripts/freeze_golden.py` | Direct golden-baseline tool. | Keep as test tool. |
| 30 | `scripts/gad_reference_overlay.py` | Direct reference-overlay generator. | Keep as reference tool. |
| 31 | `scripts/gen_api_stubs.py` | Docs-deploy CI. | Keep; generated stubs are build output. |
| 32 | `scripts/gen_changelog.py` | Direct release tool. | Keep as release tool. |
| 33 | `scripts/generate_all_28_fixtures.py` | Direct fixture generator. | Keep as generation tool. |
| 34 | `scripts/generate_all_pwd_gads.py` | PWD sweep CI and acceptance callers. | Keep; wired verification/generation tool. |
| 35 | `scripts/generate_examples.py` | Direct example-corpus generator. | Keep as generation tool. |
| 36 | `scripts/generate_random_drawings.py` | Direct random-corpus generator. | Keep as test-data tool. |
| 37 | `scripts/generate_remaining.py` | Direct example-corpus completion tool. | Keep as generation tool. |
| 38 | `scripts/generate_templates.py` | Direct template generator. | Keep as generation tool. |
| 39 | `scripts/generate_test_corpus.py` | Direct test-corpus generator. | Keep as test-data tool. |
| 40 | `scripts/intermediate_user_robot.py` | Makefile `robotic` target. | Keep; wired through developer workflow. |
| 41 | `scripts/legacy/_enhance_elegant_pdf.py` | Legacy direct script. | Retain as legacy or archive after caller review. |
| 42 | `scripts/legacy/_generate_11span_gad.py` | Legacy direct generator. | Retain as legacy/reference. |
| 43 | `scripts/legacy/test_bridge_pdf.py` | Legacy manually invoked test. | Retain as opt-in legacy test. |
| 44 | `scripts/legacy/test_robustness.py` | Legacy manually invoked test. | Retain as opt-in legacy test. |
| 45 | `scripts/legacy/test_ultimate_app.py` | Explicit CI invocation. | Keep while legacy app remains supported. |
| 46 | `scripts/lint_standards.py` | Direct standards lint tool. | Keep as direct check. |
| 47 | `scripts/m0_scaffold_packages.py` | Historical one-time package scaffolder. | Keep only if needed to reproduce M0 setup; otherwise archive. |
| 48 | `scripts/measure.sh` | Direct measurement shell tool. | Keep as direct tool. |
| 49 | `scripts/parity_detail_sheets.py` | Direct detail-sheet parity audit. | Keep as direct verification tool. |
| 50 | `scripts/pin_golden.py` | Direct golden-model pinning tool. | Keep as test tool. |
| 51 | `scripts/promote_sheet.py` | Draw CI status/promotion tool. | Keep; wired workflow tool. |
| 52 | `scripts/prove_draw_detection.py` | Makefile and Draw CI. | Keep; wired regression-proof tool. |
| 53 | `scripts/rc1_smoke.py` | Makefile `smoke` and Suite CI. | Keep; active release gate. |
| 54 | `scripts/refs_coverage.py` | Makefile and Draw CI. | Keep; active reference gate. |
| 55 | `scripts/refs_extract.py` | Makefile and Draw CI. | Keep; active reference tool. |
| 56 | `scripts/refs_lisp.py` | Direct LISP inventory/report tool. | Keep as reference tool. |
| 57 | `scripts/refs_verify.py` | Makefile reference targets. | Keep; active reference tool. |
| 58 | `scripts/regression_test_suite.py` | Direct regression runner. | Keep as direct test tool. |
| 59 | `scripts/release_gate.py` | Direct release gate. | Keep as release tool. |
| 60 | `scripts/render_asset_pack.py` | Direct asset-pack renderer. | Keep as generation tool. |
| 61 | `scripts/robot/gate.py` | Makefile gates/robot-full and merge-gate logic. | Keep; active governance gate. |
| 62 | `scripts/robot/personas.py` | Support module imported by robot runner. | Keep as supporting code, not standalone entrypoint. |
| 63 | `scripts/robot/run_robot.py` | Makefile and Robot CI. | Keep; active UI verification tool. |
| 64 | `scripts/robot/triage.py` | Makefile and Robot CI. | Keep; active defect-ingestion tool. |
| 65 | `scripts/robotic_sheet_detail_audit.py` | Sheet-detail CI. | Keep; active drawing audit tool. |
| 66 | `scripts/robotic_smoke.py` | Makefile, Suite CI, and green-stack. | Keep; active smoke tool. |
| 67 | `scripts/robotic_test_harness.py` | CI workflow. | Keep; active test harness. |
| 68 | `scripts/robotic_test_viaduct.py` | Direct end-to-end robotic verification. | Keep as direct verification tool. |
| 69 | `scripts/scaffold_plugin.py` | Direct plugin scaffolder. | Keep as developer tool. |
| 70 | `scripts/scaffold_sheet.py` | Direct sheet scaffolder. | Keep as developer tool. |
| 71 | `scripts/simple_pdf_test.py` | Direct PDF smoke test. | Keep or fold into the main smoke suite. |
| 72 | `scripts/sitecustomize.py` | Source-checkout startup hook used through `PYTHONPATH`/launchers. | Keep; intentionally not imported as a normal runtime module. |
| 73 | `scripts/sync_labels.py` | Makefile and Labels CI. | Keep; active repository-maintenance tool. |
| 74 | `scripts/test_deployed_app.py` | Direct deployed-app test. | Keep as deployment verification tool. |
| 75 | `scripts/test_netlify_readiness.py` | CI and launch verification. | Merge current branch changes with Netlify proxy work. |
| 76 | `scripts/verify_wiring.py` | Direct wiring verifier. | Keep as architecture/verification tool. |
| 77 | `scripts/wing_report.py` | Makefile and Draw CI. | Keep; active drawing-report tool. |

## 2. Incorporated Active Launch Scripts

These two scripts were previously untracked. They are now tracked on the branch and stronger than ordinary direct tools because they are part of the documented release workflow.

| Script | Current wiring | Remaining action |
|---|---|---|
| `scripts/check_browser_drafting.py` | Invoked by `scripts/check_software_launch.py`. | Merge with the launch checker and browser tests. |
| `scripts/check_software_launch.py` | Referenced by README, deployment docs, launch report, and Suite CI. | Merge with every source/test dependency required by the command. |

## 3. Package-root Verifiers

These files sit outside their importable package directories by design. `pyproject.toml` explicitly exempts hand-run verification/audit scripts from several style rules.

| # | Verifier | Wiring classification | Recommended action |
|---:|---|---|---|
| 1 | `packages/bridgecad-core/_audit_imports.py` | Direct import audit. | Keep as historical/direct verifier. |
| 2 | `packages/bridgecad-core/_audit_types.py` | Direct type audit. | Keep as historical/direct verifier. |
| 3 | `packages/bridgecad-core/day1_verify.py` | Direct Day 1 verifier; referenced by week-one sign-off. | Keep as milestone evidence. |
| 4 | `packages/bridgecad-core/day2_audit.py` | Direct Day 2 audit. | Keep as milestone evidence. |
| 5 | `packages/bridgecad-core/day2_check.py` | Direct Day 2 check. | Keep as milestone evidence. |
| 6 | `packages/bridgecad-core/day2_summary.py` | Direct Day 2 summary; referenced by week-one sign-off. | Keep as milestone evidence. |
| 7 | `packages/bridgecad-core/day3_verify.py` | Invoked by `python -m bridgecad verify`. | Keep; actively wired to CLI verification. |
| 8 | `packages/bridgecad-core/day4_verify.py` | Invoked by `python -m bridgecad verify`. | Keep; actively wired to CLI verification. |
| 9 | `packages/bridgecad-core/day5_verify.py` | Direct Day 5 verifier; referenced by week-one sign-off. | Keep as milestone evidence. |
| 10 | `packages/bridgecad-core/week1_final_signoff.py` | Direct week-one sign-off runner. | Keep as milestone evidence. |
| 11 | `packages/bridgecad-draw/m1w2_verify.py` | Direct M1 Week-2 acceptance verifier. | Keep as milestone evidence. |
| 12 | `packages/bridgecad-draw/smoke_test_m3.py` | Direct M3 smoke test. | Keep as milestone evidence or fold into current smoke suite. |

## 4. Other Standalone Code

| File | Classification | Recommended action |
|---|---|---|
| `artifacts/gad-acceptance/_gen_nine_span.py` | Direct acceptance generator; referenced by production generator comments and acceptance evidence. | Keep as a direct verification tool, not an application import. |
| `docs/build_manual.py` | Standalone manual generator; blocked by missing `docs/manual_template.md`. | Restore source/tooling or retire with the archival PDF. |
| `docs/api/conf.py` | Sphinx configuration, not runtime code. | Keep with API docs. |
| `frontend/demo_pdf_button.html` | Standalone demo page. | Link, integrate, or archive; see [02-runtime-wiring.md](02-runtime-wiring.md#9-standalone-pages-and-unlinked-assets). |
| `learn.html` | Standalone learning page. | Link or document static route; see [02-runtime-wiring.md](02-runtime-wiring.md#9-standalone-pages-and-unlinked-assets). |

## 5. Expected Non-runtime Test Material

The repository tracks 199 test files in total: 197 under `tests/` and two at the root. They are not production imports and should not be reported as orphan code.

| Test area | Tracked files |
|---|---:|
| Root test files | 2 |
| `tests/api/` | 2 |
| `tests/benchmarks/` | 2 |
| `tests/catalogue/` | 6 |
| `tests/compliance/` | 4 |
| `tests/core/` | 1 |
| `tests/draw/` | 66 |
| `tests/drawings/` | 3 |
| `tests/e2e/` | 54 |
| `tests/fixtures/` | 1 |
| `tests/frontend/` | 1 |
| `tests/integration/` | 5 |
| `tests/interop/` | 5 |
| `tests/plugins/` | 2 |
| `tests/properties/` | 4 |
| `tests/pwd/` | 4 |
| `tests/refs/` | 10 |
| `tests/robot/` | 6 |
| `tests/unit/` | 18 |
| `tests/verification/` | 3 |

## 6. Classification Rule for Future Scripts

Use these labels when a new script is added:

1. **Runtime library:** imported by application/API/CLI code; must be in the production dependency graph.
2. **Direct developer tool:** invoked by a person; document the command and expected output.
3. **CI/release gate:** referenced by a workflow or Makefile; missing caller updates are defects.
4. **Test/support module:** imported by tests or another tool; no production route is expected.
5. **Legacy:** retained for compatibility; must be visibly separated from active entrypoints.
6. **Historical scaffold/migration:** one-time setup or migration code; archive when no longer reproducible or needed.

A script belongs in the incorporation backlog only if it is untracked/ignored, required by an active caller, documented as the canonical entrypoint but missing from Git, or intended for continued use but disconnected from every workflow.
