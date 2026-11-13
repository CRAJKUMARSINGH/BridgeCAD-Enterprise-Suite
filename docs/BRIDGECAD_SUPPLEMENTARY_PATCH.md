# BridgeCAD Enterprise Suite: supplementary verification and workflow patch

Date: 2026-11-13. Tested commit: `5d5f99e68b3efcc36fdfaf295d2e76d986d1fa69`.

## Verdict

The inspected repository can generate nine-sheet DXF packages for all 15 catalogue types. This is not proof that every reference drawing is reproduced perfectly. Types 004, 014 and 015 are explicitly declared approximations in `packages/bridgecad-catalogue/bridgecad_catalogue/registry.py`. The inspected generated type 002 plan is a separate-view sheet, while PDF page 6 combines elevation, plan, sections, abutment details, notes, tables and title block. Matching sheet composition remains unfinished/unverified.

## Executed checks

| Check | Result | Limit |
|---|---|---|
| Inspect generator source and `--help` | Successful | Writes baseline corpus or transient override tree |
| `SKIP_PNG=1 python scripts/generate_all_pwd_gads.py` | Exit 0; 15/15 packages, 9 DXFs each | Completed batch skips PNG rendering |
| Read and audit all 135 generated DXFs with ezdxf | 0 audit errors, 0 fixes; minimum 73 entities | Structural validity, not semantic/reference correctness |
| `python -m pytest tests/catalogue -q` | 31 passed, one plugin deprecation warning | Not the complete project test suite |
| Type 006 `--sweep pier_height_m=6:12:3 --dry-run` | 3 variants resolve, exit 0 | Resolution only |
| Same sweep with `SKIP_PNG=1` and actual generation | 3/3 packages, exit 0 | Geometry comparison below |
| Type 006 `--set skew_deg=35 --dry-run` | Rejected; exit 1 | Expected rejection outside 0–30 range |
| Full default DXF + PNG batch | Exit 0, 15/15 packages; 135 PNGs decoded | **24 PNGs are entirely white**, affecting BOQ and reinforcement sheets |
| Reference composition | Visual inspection: type 002 output plan differs from PDF page 6 composition | No exhaustive calibrated comparison or engineering sign-off |
| Site browser QA | Variable update and fit warning; checklist persistence/reset; reference PDF viewer | Real generator backend and Netlify E2E not connected |

Do not pass the GitHub URL as a positional generator argument. Run inside the checked-out repository; the inspected CLI accepts `--type`, `--set`, `--sweep`, `--force`, and `--dry-run`.

## Reference inventory

The supplied booklet has 27 PDF pages. PDF 1 is cover, 2 acknowledgement, 3 index, 4 glossary. Printed drawing pages 02–24 correspond to PDF pages 5–27. Dimensions must be read per sheet; reduced levels and dimensions can use different units.

| Drawing BR-I / 2022 | Configuration | Printed page | PDF position |
|---|---|---|---|
| 001 | Open foundation, PCC pier, solid slab | 02 | 5 |
| 002 | Open foundation, RCC pier, solid slab | 03 | 6 |
| 003 | Raft, RCC pier, solid slab | 04 | 7 |
| 004 | Raft, RCC box cell | 05 | 8 |
| 005 A/B | RCC portal, open foundation | 06–07 | 9–10 |
| 006 | Open, RCC pier and cap, solid slab | 08 | 11 |
| 007 A/B | Open, RCC three girder | 09–10 | 12–13 |
| 008 A/B | Pile, RCC three girder | 11–12 | 14–15 |
| 009 A/B | Open, PSC four girder | 13–14 | 16–17 |
| 010 A/B | Pile, PSC four girder | 15–16 | 18–19 |
| 011 A/B | Open / well, PSC box | 17–18 | 20–21 |
| 012 A/B | Pile, PSC box | 19–20 | 22–23 |
| 013 A/B | Well, PSC box | 21–22 | 24–25 |
| 014 | Open, RCC arch / slab, pedestrian | 23 | 26 |
| 015 | Open, RCC arch, vehicular | 24 | 27 |

Keep the P.W.D. in-house-use restriction with the reference. Do not put the reference PDF into a public repository or public Netlify deployment.

### Observed rendering defect

A pixel-content check on the completed default run found **24 all-white PNGs out of 135**. Type 002 Sheet 9 was also visually inspected and is blank. All 15 BOQ PNGs and nine reinforcement PNGs are white. DXF structural audit and entity thresholds did not catch this. Investigate `engines/_render.py`, text/table rendering, content extents and visibility; the root cause is not yet established. A successful decode is not a nonblank-content check. Gate requested renders on visible content and expected semantic content, with fixtures for BOQ and reinforcement.

Three actual pier-height variants (6, 9 and 12 m) also yielded different Sheet 5 LINE-coordinate hashes: `2105a900ae32efec`, `fe1bfef223512d9e`, `addaebf3f8fe08d6`. This demonstrates changing selected geometry, not proof of correct dimensions or all variable combinations.

## Patch priorities grounded in current code

1. **P0: truth in capability reporting.** README and GUIDE scaffold/eight-sheet claims conflict with the current nine-sheet booklet path. Document each entry point separately. `docs/PWD_ENRICHMENT_GUIDE.md` uses “perfectly” / “Exact” while also listing approximation gaps; replace those verdicts with independently evidenced checks. A passed entity count is not a PDF match.
2. **P0: stop false-positive rendering success.** `_render_pngs` catches exceptions and returns `None`; `generate_one` ignores the result. Retain render errors in a manifest and classify the run as failed or degraded when PNG is requested but unavailable. `_write_index` must not claim PNG packages when `SKIP_PNG=1`. Add a rendering-failure fixture that verifies this behavior.
3. **P0: fail on unintended partial sweeps.** The CLI continues after a resolver rejection. If some jobs remain, it can return success for only the accepted jobs. Record requested/resolved/rejected/generated counts and return nonzero on rejected variants unless an explicit partial-success mode is selected. This behavior was identified by source inspection; a mixed-validity regression fixture is still required.
4. **P0: close approximation gaps by family.** Preserve registry warnings for 004 multi-unit box cell, 014 coordinate-schedule arch, and 015 precast block/socket arch. Inspect the implemented geometry before following old enrichment prescriptions, because the registry and legacy docs describe different stages. Define feature-level acceptance against PDF pages 8, 26 and 27.
5. **P1: reference-driven paper composition.** Create per-family layout recipes with reference page, views, paper size, margins, right-side notes/table/title-block region, viewport scale and minimum text height. Compose from the same model as the DXFs. Exporting nine isolated views does not reproduce a composite reference sheet.
6. **P1: parameter schema parity.** Generate UI controls, CLI docs and manual tables from `bridgecad_catalogue.schema.VARIABLES`; preserve resolver warnings and existing Excel contract. Do not create another incompatible set of hardcoded engineering defaults.
7. **P1: semantic and visual acceptance.** Map each reference view to output; compare physical extents, units, dimension values, layers, section markers, annotations and foundation/superstructure identity. Calibrate rendered images by view scale and alignment; do not use raw pixel equality alone.
8. **P1: actual backend connection.** Connect the existing frontend to authenticated generation jobs, status, errors and artifact download endpoints. The companion Site intentionally disables CAD Generate until this is implemented.

## How to choose variables

Choose a reference family from foundation, pier and superstructure identity first. Load its canonical catalogue card and display locked identity values separately from editable and derived fields. These are code-declared limits at the tested commit, not independent validation of IRC clauses or engineering suitability.

| Variable | Unit | Inspected code contract | Affects |
|---|---|---|---|
| span_count | count | 1–12; UI should require integer | Span arrangement and derived pier count |
| span_length_m | m | 6–50, step 0.5; applies to every span | Length, chainages, dimensions |
| carriageway_width | m | 3.5, 7.5, 11.0 | Road cross section / dependent geometry |
| footpath_width | m | 0–2, step 0.25 | Overall deck arrangement |
| skew_deg | degrees | 0–30, step 5 | Skew-dependent plan geometry; prove behavior in tests |
| pier_height_m | m | 3–25 | Shaft and level-related geometry |
| pier_shaft_width_m | m | 0.8–3, step 0.1 | Pier dimensions |
| deck_thickness_mm | mm | 200–900, step 25 | Depth and derived levels |
| girder_depth_mm | mm | 600–3000, step 50 | Girder families |
| girder_spacing_m | m | 1.5–3.5, step 0.1 | Girder layout |
| freeboard_m | m | 0.6–4, step 0.05 | Hydraulic clearance constraints |
| pile_diameter_mm | mm | 1000, 1200, 1500 | Pile families |
| pile_length_m | m | 6–45, step 0.5 | Pile foundation |
| well_diameter_m | m | 4–8, step 0.5 | Well foundation |

Derived fields include total_length_m, soffit_level, road_level, foundation_level, pier_count and span_lengths. Do not edit them as independent inputs. Foundation/superstructure/abutment/bearing identities are protected fields; do not expose `--force` as an ordinary user control. Scope fields to applicable families. Cross slope requires an explicit schema and sign convention before wiring Slope-Logic-Manager.

Example commands, run in an isolated checkout:

```powershell
python scripts/generate_all_pwd_gads.py --type BR-I-2022-006 --dry-run
python scripts/generate_all_pwd_gads.py --type BR-I-2022-006 --set skew_deg=25
python scripts/generate_all_pwd_gads.py --type BR-I-2022-006 --sweep pier_height_m=6:12:3
```

Canonical defaults write `EXAMPLES_PWD`; overrides and sweeps write `out/pwd_sweep`. Retain `params.resolved.json` and its trace. Back up existing outputs before baseline generation. Record `$LASTEXITCODE` immediately after every command.

## How to choose format and layout

1. Identify the matching reference page and all required views.
2. Read its actual page dimensions and orientation. The booklet's first page is A2 landscape; the Site includes a per-page dimensions inventory.
3. Reserve margins, title block, notes, design/material tables and view captions before choosing view scales.
4. Fit elevation and plan to available viewport width; independently scale sections and details. Reference examples use scales such as 1:100, 1:250 and 1:300; the correct value is per view, not per entire project.
5. Check dimension text height, hatching, lineweight, legends, section callouts and clipping at the intended print size.
6. Verify changing paper size or title block does not change physical geometry.
7. The inspected booklet path emits DXF and optionally PNG. Do not advertise reference-composed PDF or DWG as verified exports until the relevant path has executed and passed review.

## Landing page and Netlify implementation

Use drawing family cards with reference page, implemented/approximation flags, schema, available output formats and known gaps. Primary routes: Choose Drawing, Open Sample, Import existing workbook, Guided Manual, App Test Bench, Reference Comparison and Verification Results. Disable unsupported generation. The created companion Site supplies configuration, command preparation, app launch URLs, local evidence records, comparison and checklists; it does not execute the CAD backend.

Netlify hosts frontend static assets. Keep Python/CAD generation on a separately deployed service. Use a verified API base URL (frontend build-time variable or same-origin proxy), allowlisted CORS, health checks, job IDs, limits, authenticated downloads and persistent artifact storage. Never put secrets in `VITE_` variables. Test deploy previews against staging, including mobile and keyboard access, generation failure paths and artifact downloads. Record rollback version. No actual Netlify release was executed in this task.

## Reusable app checklist

- [ ] Record app, commit, environment, fixture, expected artifacts and command.
- [ ] Inspect generator imports, arguments, output paths and side effects.
- [ ] Run nominal input, boundaries, multiple spans, skew and invalid cases.
- [ ] Record individual exit codes and retain logs.
- [ ] Open DXFs; inspect semantic layers, entities, units and dimensions.
- [ ] Render outputs; inspect text, clipping, lineweights and annotations.
- [ ] Map each output view to reference and record measured differences.
- [ ] File minimal reproduction, patch, rerun and retain evidence.

## Slope-Logic-Manager to Dwg-Param-Mapper checklist

- [ ] Record both app versions and schema version.
- [ ] Specify chainage origin, axes, slope sign, percent/ratio and units.
- [ ] Map slope, chainage and reduced-level fields explicitly.
- [ ] Reject missing values, invalid ranges and unit mismatches.
- [ ] Independently calculate expected RL differences for 2% and 2.5% cases.
- [ ] Test reversed direction, round-trip precision and unchanged identity.
- [ ] Retain input, mapped output, expected values and evidence.

## Final Bridge-Design-Suite wiring checklist

- [ ] One canonical registry and validated parameter model.
- [ ] Preserve drawing identity, layout, warnings and provenance in handoffs.
- [ ] Reject unsupported output and approximation claims presented as exact.
- [ ] Test job status, retry, failure and artifact download.
- [ ] Complete browser journey through real backend.
- [ ] Compare every reference view and close acceptance gaps.
- [ ] Obtain independent engineering review before construction use.

## Apply to the existing Windows checkout

A targeted documentation patch accompanies this guide. It adds this supplement and links it from GUIDE.md and DOCS_INDEX.md. It does not claim to repair engineering primitives. Review and apply from the repository root:

```powershell
cd E:\Rajkumar\BridgeCAD-Enterprise-Suite
git switch -c docs/pwd-verification-supplement
git apply --check path\to\bridgecad-docs.patch
git apply path\to\bridgecad-docs.patch
git diff --check
git diff -- GUIDE.md DOCS_INDEX.md docs/BRIDGECAD_SUPPLEMENTARY_PATCH.md
```

If a link or supplement already exists, merge the content rather than applying twice. First review affected `.md` files, then `.txt` files. At the inspected commit, the `docs` text files found are dependency requirement lists (`docs/requirements-docs.txt`, `docs/api/requirements.txt`); there is no reason to rewrite them as manuals. Preserve their package syntax. Local documentation edits here do not write to E: and have not been pushed to the user's GitHub repository.
