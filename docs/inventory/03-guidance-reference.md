# Guidance, Handover, and Reference Inventory

Snapshot: 26 November 2026 at `6ddf860`.

This report inventories documentation, continuity material, enhancement guidance, reference corpora, learning assets, sample inputs, and handover evidence. It also records guidance that is referenced but absent, because those broken references are part of the incorporation problem.

## 1. Root Guidance and Reports

| File | Git state | Purpose | Wiring/status | Recommended action |
|---|---|---|---|---|
| `README.md` | Tracked; unstaged changes | Primary repository guidance and launch instructions. | Linked by GitHub and documentation; operationally wired. | Commit current launch changes after review. |
| `BASELINE.md` | Untracked | Original checkout and pre-launch verification baseline. | Linked by `LAUNCH_HARDENING_REPORT.md`. | Commit as point-in-time evidence. |
| `CREAT.MD` | Untracked | Rolling 24-hour continuity log. | Linked by README standing instructions. | Update stale queue statements, then commit. |
| `LAUNCH_HARDENING_REPORT.md` | Untracked | Launch changes, verification, and release status. | Linked by baseline/deployment guidance. | Commit with launch scripts and evidence. |
| `CHANGELOG.md` | Branch-only addition | Keep-a-Changelog release history. | Referenced by project metadata. | Merge with Phase 0 documentation. |
| `CODE_OF_CONDUCT.md` | Branch-only addition | Community conduct policy. | Standard repository governance file. | Merge with governance docs. |
| `CONTRIBUTING.md` | Branch-only addition | Contribution, testing, and data-protection rules. | Linked by security policy. | Merge with governance docs. |
| `SECURITY.md` | Branch-only addition | Private vulnerability reporting guidance. | Linked by contribution guidance. | Merge with governance docs. |

### Continuity Conflict to Resolve

`CREAT.MD` contains 25 November entries saying enhancement guides are in `CODE-JUNCTION`. `docs/verification/RELEASE_REPORT.md` records that the queue was reviewed and emptied on 26 November. The release report is newer and explicit, so the continuity log is stale on this point.

Recommended action: keep `CREAT.MD` as the rolling handoff file, but replace the obsolete queue statements with the cleanup outcome and current open gates.

## 2. Documentation Site and Architecture Guidance

| File | Purpose | Navigation/wiring | Recommended action |
|---|---|---|---|
| `docs/index.md` | MkDocs landing page. | `mkdocs.yml` Home entry. | Keep and merge with Phase 0. |
| `docs/DEPLOYMENT.md` | Backend deployment, environment variables, verification, and rollback. | MkDocs Deployment entry; README link. | Reconcile API-key auth claims with actual gateway wiring. |
| `docs/LISP_FIDELITY_AND_DIRT_WALL.md` | AutoLISP provenance, fidelity limits, acceptance gaps, and patch notes. | MkDocs AutoLISP provenance entry; README link. | Keep as engineering guidance; refresh historical patch references. |
| `docs/interop.md` | JSON/CSV/Excel/IFC/DWG interoperability contract. | MkDocs Interoperability entry. | Keep; ensure public-only IFC/DWG APIs are documented as library or route options. |
| `docs/verification/TRACEABILITY.md` | Compliance-check-to-test/benchmark matrix. | MkDocs Verification traceability entry. | Keep as definition-of-done guidance. |
| `docs/verification/RELEASE_REPORT.md` | Phase 0 baseline, acceptance status, queue review, and cleanup outcome. | MkDocs Release verification entry. | Keep current; merge later working-tree updates. |
| `docs/adr/README.md` | ADR index and authoring guidance. | MkDocs Architecture decisions index. | Keep. |
| `docs/adr/0002-group-workspace-entry-points.md` | Accepted decision to group apps, scripts, tests, and startup hooks. | MkDocs ADR entry; explains legacy moves. | Keep with relocation changes. |
| `mkdocs.yml` | Documentation navigation. | Controls MkDocs site. | Keep; add restored guidance if appropriate. |
| `docs/schema/bridgeproject.schema.json` | Published project schema. | Checked by schema-export tooling. | Treat as generated contract artifact, not prose guidance. |
| `audit/baseline.json` | Repository/test/reference baseline metrics and hashes. | Referenced by release report. | Keep as release evidence. |
| `artifacts/TRIAGE_LOG.md` | S1/S2 defect register and merge-gate rules. | Read by `scripts/robot/gate.py`. | Keep operational; repair missing guide links. |
| `docs/api/conf.py` | Sphinx API-reference configuration. | Used with generated API stubs. | Keep as docs tooling. |
| `docs/api/index.rst` | Sphinx package-reference toctree. | CI generates package stub pages. | Keep; generated pages are build output. |
| `docs/api/requirements.txt` | Sphinx documentation dependencies. | API-docs build input. | Keep. |
| `docs/requirements-docs.txt` | MkDocs dependencies. | Documentation build input. | Keep. |
| `docs/build_manual.py` | Standalone user-manual generator. | Not referenced by Makefile/CI; currently blocked by missing template. | Restore template/tooling or mark archival. |
| `docs/Bridge_GAD_User_Manual.pdf` | Existing legacy user manual. | Referenced by legacy GUI. | Keep as archival output until reproducible source is restored. |

## 3. `CODE-JUNCTION/` Enhancement Queue

Current state: the directory is intentionally preserved but **empty**.

`README.md` defines the queue policy: new enhancement guides and patches wait there; once applied, tested, and merged, their guide/patch files are deleted.

`docs/verification/RELEASE_REPORT.md` records the review and deletion of these three files on 26 November 2026:

| Historical queue file | Disposition | Current inventory status |
|---|---|---|
| `# BridgeCAD Enterprise Suite — Code.txt` | Deleted after Phase 0/acceptance requirements were consolidated into the release report. | Does not currently exist. |
| `# CREAT.MD — Continuity Chat Log.MD` | Deleted after applicable BridgeCAD requirements were consolidated; unrelated legal/court material was excluded. | Does not currently exist. |
| `Bcad venus 26.txt` | Deleted after applicable drafting fixes were reviewed; incomplete revisions and unverified engineering inputs were not adopted. | Does not currently exist. |

Recommended action: do not recreate these files as if they were pending. Use the release report as the disposition record. Add new guidance to `CODE-JUNCTION/` only under the standing queue policy.

## 4. Preserved AutoLISP and Reference Corpus

These files are reference material, not production runtime modules. They support extraction, comparison, provenance, and acceptance work.

### Preserved source archives

| File | Role | Recommended action |
|---|---|---|
| `ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp` | Preserved named AutoLISP routine archive. | Keep protected; do not treat as a certified executable port. |
| `ATTACHED ASSETS/yogipwd_lisp_solid_slab_gad_original.txt` | Preserved explanatory/source text. | Keep protected with provenance. |
| `references/lisp/fixture_min.lsp` | Minimal LISP fixture for inventory tests. | Keep as test reference. |

### Raw reference drawings

| File | Role |
|---|---|
| `references/raw/gad-borse-sheet5.pdf` | Raw Sheet 5 reference. |
| `references/raw/gad-set-b-sheet5.pdf` | Raw Sheet 5 reference. |
| `references/raw/gad-set-c-sheet5.pdf` | Raw Sheet 5 reference. |
| `references/raw/gad-set-d-sheet5.pdf` | Raw Sheet 5 reference with additional text content. |

### Extracted facts

| File | Role |
|---|---|
| `references/extracted/gad-borse-sheet5.json` | Extracted facts from Borse reference. |
| `references/extracted/gad-set-b-sheet5.json` | Extracted facts from Set B reference. |
| `references/extracted/gad-set-c-sheet5.json` | Extracted facts from Set C reference. |
| `references/extracted/gad-set-d-sheet5.json` | Extracted facts from Set D reference. |

### Expected values and case definitions

| File | Role |
|---|---|
| `references/expected/ref_bridge_a_sheet5_pier_abutment_details.json` | Expected Sheet 5 facts for case A. |
| `references/expected/ref_bridge_b_sheet5_pier_abutment_details.json` | Expected Sheet 5 facts for case B. |
| `references/expected/ref_bridge_c_sheet5_pier_abutment_details.json` | Expected Sheet 5 facts for case C. |
| `references/expected/ref_bridge_d_sheet5_pier_abutment_details.json` | Expected Sheet 5 facts for case D. |
| `references/cases/ref_bridge_a.json` | Reference case A definition. |
| `references/cases/ref_bridge_b.json` | Reference case B definition. |
| `references/cases/ref_bridge_c.json` | Reference case C definition. |
| `references/cases/ref_bridge_d.json` | Reference case D definition. |

### Corpus indexes and conflict records

| File | Role |
|---|---|
| `references/index.json` | Reference corpus index. |
| `references/coverage.json` | Reference coverage report. |
| `references/conflicts.jsonl` | Reference/implementation conflict register. |
| `packages/bridgecad-refs/bridgecad_refs/gad_text.py` | Implemented legacy text codec, intentionally not wired to production pending semantic adaptation. |

Recommended action: keep the corpus versioned and regenerate extracted/coverage/conflict data through the reference tools. Do not delete raw references merely because they are not runtime imports.

## 5. Learning Centre and Manual Assets

| File | Current wiring | Recommended action |
|---|---|---|
| `learn.html` | Standalone learning page; no root frontend link found. | Add a navigation link or document the static route. |
| `learn-media/bridgecad-quickstart.mp4` | Used by `learn.html`. | Keep with the page. |
| `learn-media/captions.vtt` | Used by `learn.html`. | Keep with the page. |
| `learn-media/poster.png` | Used by `learn.html`. | Keep with the page. |
| `docs/Bridge_GAD_User_Manual.pdf` | Used by legacy GUI/manual links. | Keep as archival manual until source template is restored. |
| `frontend/public/bridge-catalogue-11.pdf` | Static frontend asset linked by the PDF demo. | Keep as product sample asset. |
| `frontend/public/samples/sample_input.xlsx` | Static frontend sample workbook. | Keep as synthetic sample input. |

## 6. Sample Inputs and Drawing References

### Root `inputs/` samples

These files are sample/reference data, not runtime imports. Confirm that they are synthetic or approved for redistribution.

| File | Recommended action |
|---|---|
| `inputs/23_span_bridge_input.xlsx` | Keep as approved/synthetic sample or move to test fixtures. |
| `inputs/TEST_12m_var001.xlsx` | Keep as test sample. |
| `inputs/bridge_parameters.json` | Keep as documented sample. |
| `inputs/bridge_parameters.txt` | No code/config reference found; confirm purpose or remove. |
| `inputs/bridge_parameters_comprehensive.xlsx` | Keep as approved/synthetic sample or move to test fixtures. |
| `inputs/bridge_parameters_simple.xlsx` | Keep as approved/synthetic sample or move to test fixtures. |
| `inputs/large_bridge.xlsx` | Keep as approved/synthetic sample or move to test fixtures. |
| `inputs/lisp_input.xlsx` | Keep with LISP reference work. |
| `inputs/lisp_params.xlsx` | Keep with LISP reference work. |
| `inputs/real_lisp.xlsx` | Review privacy/provenance before retaining the word “real” in a public sample name. |
| `inputs/sample_input.xlsx` | Keep as documented sample. |
| `inputs/spans.xlsx` | Keep as test/sample input. |
| `inputs/spans_only.xlsx` | Keep as test/sample input. |

### Vercel public samples

`public/samples/` contains 12 tracked sample/template files:

- `bridge_23span.xlsx`
- `bridge_comprehensive.xlsx`
- `bridge_large.xlsx`
- `bridge_parameters.json`
- `bridge_parameters.txt`
- `bridge_simple_12m.xlsx`
- `sample_input.xlsx`
- `template_arch_24m.xlsx`
- `template_box_culvert_8m.xlsx`
- `template_continuous_3x12m.xlsx`
- `template_girder_4x18m.xlsx`
- `template_simple_12m.xlsx`

These are static assets served by the alternate Vercel surface. They are not production Python imports, but they are intentional product samples.

### Source drawing references

| File | Role |
|---|---|
| `sample-gad-drawings/ASSET_Asset_S1_LSection_Plan.dxf` | Reconstructed asset-pack Sheet 1. |
| `sample-gad-drawings/ASSET_Asset_S2_DeckSection_Substructure.dxf` | Reconstructed asset-pack Sheet 2. |
| `sample-gad-drawings/ASSET_Asset_S3_Pier_RetainingWall.dxf` | Reconstructed asset-pack Sheet 3. |
| `sample-gad-drawings/ASSET_Asset_S4_SingleSpan_6m.dxf` | Reconstructed asset-pack Sheet 4. |
| `sample-gad-drawings/ilide.info-01-gad-at-ch-2-300-7x9-0-pr_d96902819f4721e17604fcc2ca8a5da0.pdf` | Source reference PDF for asset sheets 1–3. |
| `sample-gad-drawings/ilide.info-gad-final-3-340-1-pr_d326d376c529af47cbe4d40708752e42.pdf` | Source reference PDF for the single-span asset. |

## 7. Handover and Verification Artifacts

### `artifacts/continue/`

| File | Current status | Recommended action |
|---|---|---|
| `artifacts/continue/T1-tracked.diff` | Historical tracked diff snapshot. | Keep as historical evidence or archive after confirming no active process reads it. |
| `artifacts/continue/T1d-tracked.diff` | Historical tracked diff snapshot. | Keep as historical evidence or archive. |
| `artifacts/continue/T8-prove-detection-after.json` | Detection-proof results referenced by acceptance evidence. | Keep with the matching verification record. |
| `artifacts/continue/T9-final-tracked.diff` | Historical final diff snapshot. | Keep as historical evidence or archive. |
| `artifacts/continue/full-after.xml` | Large one-line historical test output. | Keep only if required as evidence; otherwise archive externally. |

No active runtime import of these files was found. Their value is historical traceability, not application wiring.

### Browser and acceptance evidence

- Tracked browser evidence: `artifacts/browser-results/bills.json`, `defect-blank-template-parse.json`, and `qa-report.html`, plus associated generated files.
- Former untracked browser evidence: the ten live-drafting files listed in [01-git-incorporation.md](01-git-incorporation.md) were deleted as regenerable duplicates. Future captures matching `artifacts/browser-results/live-drafting-*` are ignored.
- Acceptance tooling: `artifacts/gad-acceptance/_gen_nine_span.py`.
- Acceptance metadata: `collision-report.json`, `content-report.json`, `reference_requirements.json`, `variant-validation.json`, per-run `summary.json`, `params.resolved.json`, `quality.json`, `render-status.json`, `required-content.json`, and layout audits.
- Acceptance output: generated DXF/PDF packages and failure reports under commit-keyed run directories.

Recommended action: retain a minimal, reproducible evidence set. Do not treat generated DXFs/PDFs as source files, and do not commit every transient run unless repository policy requires it.

### Generated exemplar corpus

`EXAMPLES/` contains 802 tracked files:

- 270 files under `EXAMPLES/PWD_Booklet/`.
- 28 project directories with 19 generated files each.

These are exemplars/test corpus, not runtime imports. They are intentionally excluded from the per-file actionable list. Regenerate them through the example/catalogue scripts rather than manually editing generated output.

`outputs/11span_110m_rcc_slab/` similarly contains 19 generated drawing files. Treat it as output/evidence, not application source.

## 8. Referenced but Absent Guidance

The following references were found, but the target files do not exist in the current working tree.

| Missing target | Referenced by | Impact | Recommended action |
|---|---|---|---|
| `GUIDE.md` | Streamlit UI, import-linter comments, API comments, multiple code docstrings. | Users and maintainers are sent to a missing master guide. | Restore the guide or replace each reference with current documentation. |
| `docs/USER-MANUAL.md` | Active Streamlit UI and `.gitignore` comments. | Broken user-manual link. | Restore, rename to the existing manual, or update links. |
| `docs/PWD_ENRICHMENT_GUIDE.md` | Active Streamlit UI. | Broken PWD guidance link. | Restore or remove the link. |
| `docs/TRIAGE_AND_DEBUG.md` | `artifacts/TRIAGE_LOG.md`. | Triage rules cite a missing procedure. | Restore the procedure or inline the required steps. |
| `docs/PATCH_GUIDE.md` | `artifacts/TRIAGE_LOG.md`. | Patch classes cite missing sections. | Restore the guide or update the register. |
| `docs/manual_template.md` | `docs/build_manual.py`. | Manual generator exits before producing output. | Restore the source template or retire the generator. |
| `build_manual.bat` | Legacy GUI error text. | Legacy instructions point to a missing launcher. | Restore the launcher or update the GUI instructions. |
| `CODE-JUNCTION/2026-01-irc-standards-enrichment/GUIDE.md` | `scripts/audit_dxf_conformance.py` docstring. | Historical queue reference remains after queue cleanup. | Replace with a permanent documentation reference or mark historical. |
| `lisp-fidelity.patch` | `docs/LISP_FIDELITY_AND_DIRT_WALL.md`. | Patch-application instructions cannot be followed as written. | Mark the patch section historical or restore the patch in an archive. |
| `TEST-RESULTS.txt` | `docs/LISP_FIDELITY_AND_DIRT_WALL.md`. | Verification instructions reference absent evidence. | Link the current release report/test records instead. |
| `FAILED-RUN` | LISP documentation and acceptance tooling. | LISP document treats it as an existing artifact location. | Clarify that it is generated on failure, not a checked-in guide. |

## 9. Guidance Triage Summary

| Disposition | Files/materials |
|---|---|
| Keep operational | README, deployment, interoperability, traceability, release report, ADRs, triage log, MkDocs config. |
| Keep governance | Changelog, code of conduct, contributing, security. |
| Update before commit | `CREAT.MD`, deployment auth wording, missing-guide links, historical patch/manual references. |
| Keep as point-in-time evidence | `BASELINE.md`, `LAUNCH_HARDENING_REPORT.md`, audit baseline, continue snapshots, browser/acceptance reports. |
| Keep protected as reference | AutoLISP archives, raw reference PDFs, source drawing PDFs, expected facts, conflict records. |
| Keep as direct tooling | Manual generator only after its missing source is restored; acceptance generator remains a direct tool. |
| Do not treat as pending enhancement | The three deleted `CODE-JUNCTION/` files; the queue is empty. |
| Review for archival cleanup | Large historical XML/diff snapshots and generated run output, subject to evidence-retention policy. |
