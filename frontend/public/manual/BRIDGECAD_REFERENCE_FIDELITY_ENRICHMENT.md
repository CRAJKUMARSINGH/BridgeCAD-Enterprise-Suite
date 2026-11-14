# BridgeCAD: reference fidelity, drawing variables and export media

Date: 2026-11-13. Baseline: `5d5f99e`, plus the earlier applicable-instructions and manual/landing patches. This is a further incremental implementation patch, not a claim that the reference is perfectly reproduced.

## Direct answer

**No: complete, perfect reference reproduction with arbitrary variable changes is not established.** The generator can produce 15 catalogue configurations and selected tested variations. Export visibility, correct geometry, correct annotations, correct sheet composition and engineering approval are separate acceptance questions.

The newly uploaded GENERAL ARRANGEMENT DRAWINGS(2).pdf has the same SHA-256 as the previously supplied reference:

`38c224549a50cc72a20aaa01e07b33618789dc4d3881844363bda199dd44a23d`

It is the same 27-position booklet. No change in the reference explains the remaining fidelity gaps.

## What this patch actually fixes

### White-paper visibility

The shared matplotlib renderer used the default dark-modelspace rendering context. Auto white/black CAD strokes (ACI 7) were white, while the axis-off export showed the white figure beneath them. Sheets containing mostly default-color borders and text could become entirely white images even though their DXFs contained entities.

The renderer now explicitly selects `BackgroundPolicy.WHITE` and a white figure. ACI 7 is resolved for white paper, preserving visible linework and text. The earlier blank-output failure gate remains enabled.

The renderer also disables automatic figure resizing, so requested media dimensions survive the drawing-backend finalization step.

This repairs visibility; a visible BOQ/reinforcement table can still have missing, nominal or incorrect engineering content. Do not promote it to reference acceptance on the basis of a nonblank image.

### Real PNG media selection

The CLI now accepts:

```powershell
python scripts/generate_all_pwd_gads.py --type BR-I-2022-002 --render-paper A3 --render-orientation portrait --dry-run
python scripts/generate_all_pwd_gads.py --type BR-I-2022-002 --render-paper A3 --render-orientation portrait
```

`--render-paper` accepts A0, A1, A2, A3 and A4. `--render-orientation` accepts landscape and portrait. These control PNG physical canvas size and its pixel dimensions at the renderer DPI. Nondefault media writes to the transient `out/pwd_sweep` tree. `render-status.json` records the selected media and whether rendering ran, failed or was skipped.

**These flags do not recompose the DXF paper-space layout, change physical bridge geometry, set viewport scales, or reproduce the reference's multiple-view composition.** The landing-page scale/viewport section remains a planning tool. This distinction is visible beside the controls and in exported scenario metadata.

## Drawing and variable decision table

| User task | Choose | Variables to inspect | Acceptance |
|---|---|---|---|
| Overall bridge arrangement | Browser overview or matching Python family | Spans, unequal-span baseline, carriageway, footpaths, skew, RTL/datum | Chainages, dimensions, support axes and orientation |
| RCC/PSC girder drawing | Matching girder-family catalogue card | Girder depth/count/spacing, deck depth, span and width | Cross-section identity, quantities and clearances |
| Open/raft foundation detail | Matching foundation card; browser sheet 04 where applicable | Site SBC/scour, foundation levels and substructure dimensions | Correct foundation type and reference sections |
| Pile foundation | PILE card | Pile diameter, length, count and foundation datum | Actual pile layout and dimensions |
| Well foundation | WELL card | Well diameter, levels and relevant pier geometry | Well plan/section completeness |
| Pier/abutment/wing walls | Browser sheet 05 or matching Python detail | Pier dimensions, abutment/return heights, splay, ABTL and levels | Geometry, dimensions, callouts and material notes |
| Box cell 004 / arches 014,015 | Corresponding catalogue configuration | Only supported dials; preserve approximation warnings | Remains an approximation until defining primitives and reference data are accepted |

Choose drawing identity first. Keep derived levels/lengths read-only. Enter overrides only for the scenario you intend to change. The frontend shows applicable fields, units, baseline values and the schema's ranges/choices. These limits are not a substitute for design validation.

Important: `span_length_m` applies to every span. Leave it unchanged to preserve an unequal reference arrangement. `carriageway_width` is clear road width, not total deck width. Cross slope still needs a versioned mapping/sign convention before being wired from Slope-Logic-Manager.

## How to choose format and layout

| Choice | Current implemented behavior | Still required for full reference fidelity |
|---|---|---|
| DXF | Nine-sheet Python package; local browser detail exports where supported | Per-view semantic/dimension checks and reference composition |
| PNG | White-paper visibility fix; A0-A4 export media and orientation | Per-sheet legibility and full print-size review |
| PDF/SVG | Existing engines share the renderer; not independently requalified by this patch | Execute their entry points and inspect artifacts before claiming parity |
| DWG | Not established by this task | A verified supported conversion/export path |
| Paper/portrait/landscape | Real PNG media arguments | DXF layout/viewport adapter, title-block placement and margins |
| Proposed elevation scale | Provisional fit planning on the landing page | Wire validated scales into every affected viewport and caption |
| Reference sheet layout | Existing separate drawing views | Compose all required plan/elevation/sections/details/notes/tables/title-block panels |

For a particular drawing: identify the reference page and all required views, reserve information columns and margins, fit each view independently, and check text/lineweight/clipping at the final print size. A larger denominator makes a view smaller. Changing export media must not change model geometry.

## Landing page changes

- The existing family-specific variable controls remain available.
- Paper and orientation now appear in prepared commands as actual PNG media flags.
- Scenario JSON separates render media from the proposed CAD layout.
- The landing-page evidence distinguishes the old blank-render failure from the rerendered visible outputs.
- The downloadable manual points to this enrichment supplement.
- The existing browser workspace, two deck families and three registered views remain unchanged.

The frontend still cannot execute a local Python process. A deployed generation backend is needed for browser Run -> Verify -> Download. A paper dropdown does not create that backend connection. Keep unsupported generation and unimplemented exact-match states visible rather than implying success.

## Remaining enrichment, in order

1. Recompose sheets to match each reference page's views, annotations and tables.
2. Complete the multi-unit box-cell and arch/precast primitives for 004/014/015 using verified reference dimensions, coordinate schedules and engineering review. Do not apply the contradictory prototype formulas in the earlier upload without reconciliation.
3. Implement per-family semantic/reference oracles: model identity, dimensions, layers, quantities, datum, section markers and annotated view placement. Layer presence and minimum entity count are insufficient.
4. Extend real CAD paper-space layout selection and validate caption/scale consistency and clipping. The new PNG media flags are not that adapter.
5. Connect the existing backend behind the Netlify functions, then execute template/import/generate/status/download against staging.
6. Test minimum/nominal/maximum valid scenarios, multiple spans, skew, rejected inputs, repeated-output determinism and each supported output format.
7. Perform mobile/keyboard browser tests and independent engineering acceptance before a production release.

## Netlify and project application

Retain the root `netlify.toml`: it builds frontend/ and publishes frontend/dist. Netlify static hosting is separate from the Python/CAD backend. Configure FASTAPI_URL server-side, verify health and actual generation/export endpoints, and retain rollback/evidence. No Netlify account release is performed by this patch.

Apply after the earlier instruction and manual/landing packages. The supplied Windows script checks whether this patch is already applied and whether it can apply cleanly before editing. Conflicts stop the operation; do not overwrite local changes with the review copies. The patch was applied only to the available checkout, not E: and not pushed to the user's GitHub repository.

## Validation

- The reattached PDF hash matches the original reference exactly.
- 76 catalogue/regression tests passed (one external pytest-plugin deprecation warning).
- All 24 previously all-white PNGs were rerendered at 50 DPI; all 24 now contain visible content.
- Actual type 002 generation with A3/portrait completed successfully: nine nonblank PNGs, each 1753 x 2480 pixels at 150 DPI; media is recorded in render-status.json.
- TypeScript/Vite production build passed.
- Browser check passed: choosing A3 and Portrait emits --render-paper A3 --render-orientation portrait; scale is still explicitly a CAD-layout proposal.
- Complete per-reference semantic/visual acceptance, approximate-family completion, live backend generation and Netlify release are not verified.


A visible output is not a perfect drawing match. The reference acceptance verdict remains **NOT VERIFIED**.

See also [the full drawing-selection manual](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/docs/BRIDGECAD_USER_MANUAL.md) for the 15 configurations, per-family variables and worked examples.
