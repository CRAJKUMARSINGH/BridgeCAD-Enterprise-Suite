# BridgeCAD release verification

Updated 27 November 2026 IST

## Due versus done

| Work | Done / due | Completion | Evidence |
|---|---:|---:|---|
| `CODE-JUNCTION` file dispositions | 3 / 3 | 100% | All three reviewed files were removed and the directory was checked recursively. |
| Focused asset-pack tests | 34 / 34 | 100% | Local drawing regression tests passed. |
| Sheet 04/05 contract tests | 27 / 27 | 100% | The layer visibility fix passed the full contract suite locally. |
| Seeded sheet audit | 3,000 / 3,000 | 100% | The audit rendered 6,000 sheets with zero failures. |
| Sheet audit mutation drills | 6 / 6 | 100% | The audit detected all six injected drawing errors. |
| Legacy regression tests | 6 / 6 | 100% | The legacy drawing generator now uses the supported `ezdxf.document.Drawing` annotation. |
| Legacy workbook smoke cases | 11 / 11 | 100% | The robotic harness passed ingestion, calculation, drawing, and validation locally. |
| Netlify readiness checks | 25 / 25 | 100% | All checks passed locally with gateway dependencies installed. |
| Originally failing Phase 0 CI jobs restored | 5 / 6 | 83.3% | GitHub confirmed suite lint, suite mypy, sheet details, and both legacy jobs passed at `48fa296`. |
| Suite unit jobs restored after lint passed | 2 / 2 | 100% | GitHub confirmed the Python 3.11 and 3.12 jobs passed at `4da0643` after adding test dependencies. |
| Release phases merged | 0 / 7 | 0% | Phase 0 remains open as draft PR #1. The green CI and merge gate still applies. |
| Release acceptance criteria recorded as passed | 1 / 17 | 5.9% | AC-2 passed in the local baseline. One criterion failed, one is partial, and 14 are pending. |

On 27 November, [Phase 0 draft PR #1](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/pull/1)
at `48fa296` had 25 passing checks, three failed jobs, and eight skipped or neutral
checks. Both unit jobs ran after lint passed and exposed missing gateway and CLI test
dependencies. The Python 3.11 unit job reached 79.73% coverage against the 75% floor.
Both unit jobs passed on the follow-up commit `4da0643`.
The architecture checker still reports imports from core validation into drawing
audits and from the infrastructure worker into drawing, bill, and export packages.
Those imports also break the transitive dependency contracts. Release certification
remains open.

## Phase 0 baseline

| Check | Command or evidence | Result |
|---|---|---|
| Audit baseline | Tag `rc1-audit-baseline` at `a488ea8` | 1,976 tracked files and 103,332 Python lines |
| Tagged test inventory | `python -m pytest -p no:hypothesispytest --collect-only -q` in the tagged archive | 1,587 tests collected |
| Clean base collection | `python -m pytest --collect-only -q` in a clean Python 3.11 environment with no dev extras | Pass. 1,532 tests collected, seven optional modules skipped |
| Unit baseline | `coverage run --branch -m pytest -p no:hypothesispytest -q tests/unit` in the tagged archive | 190 tests passed. Combined line and branch coverage from this lane was 72.67%, below the 75% floor |
| CLI after the file moves | `python -m bridgecad verify` | Pass. All 15 checks passed |
| Documentation | `python -m mkdocs build --strict` | Pass locally |
| Release-candidate smoke | `python scripts/rc1_smoke.py` in the Phase 0 snapshot with a temporary SQLite database | 34 of 34 checks passed, including 28 E2E fixtures |
| Triage merge gate | `python scripts/robot/gate.py --json` after restoring the historical triage log from Git | Pass. The restored records contain no open blocking entries |
| CI lint | Ruff 0.6.0 over `packages/`, `apps/` and `scripts/` | Fails. The tagged baseline has 133 findings. The Phase 0 snapshot has 504, including findings in entry points moved into those directories |
| CI unit and integration selection | CI test selection with fail-fast enabled and the Hypothesis collection plugin disabled for this run | 222 passed before the first failure. `Asset_S4_SingleSpan_6m` extends past the A3 frame. The same assertion failed on the tagged baseline |
| CI workspace setup | Resolve all editable member packages and the root project in one pip invocation | Clean-environment resolver dry run passed. The first PR run failed during ordered installation because `bridgecad-export` requires the local `bridgecad-qa` package |
| Published schema | `python scripts/export_project_schema.py --check` | Passed locally after regenerating the checked-in schema from the existing model. GitHub's interoperability job had stopped at the stale-schema check |
| Reference drawings | `python scripts/capture_release_baseline.py` with the tagged archive and `--repeat-drawings` | Three fixtures generated 11 DXFs each. The two runs differed in each fixture's hash manifest |
| Remote phase gate | [Phase 0 draft PR](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/pull/1) | Base collection and documentation passed on GitHub after the installer fix. Broader CI and merge remain open |

The source revision, timings, and SHA-256 values are in `audit/baseline.json`.

## Acceptance status

| Criterion | Status |
|---|---|
| AC-1 Cross-platform install and test | Pending. Python 3.11 on Windows was verified for the checks above |
| AC-2 Base collection | Passed locally on Python 3.11 |
| AC-3 QA registry coverage and advertised count | Pending |
| AC-4 Drawing exception handling | Pending |
| AC-5 Public entry points across types and formats | Pending |
| AC-6 Issued BOQ integrity | Pending |
| AC-7 Byte-identical DXF | Failed at the baseline. All three fixture manifests differed on repeat generation |
| AC-8 Clause traceability and provisional markers | Pending |
| AC-9 Strict typing and lint | Pending. The CI lint command reports findings in both the tagged baseline and the Phase 0 snapshot |
| AC-10 Coverage | Pending. The measured unit lane was below the repository floor |
| AC-11 Security scanning and SBOM | Pending |
| AC-12 Container service and image checks | Pending |
| AC-13 Accessibility and keyboard walkthrough | Pending |
| AC-14 Bundle and runtime budgets | Pending |
| AC-15 Governance, documentation and ADRs | Partial. Local docs build passed. Publication and the remaining ADRs are pending |
| AC-16 Generated artifact and LFS policy | Pending |
| AC-17 Independent engineering sign-off | Pending. No reviewer or date has been recorded |

Agent-generated engineering values are not a substitute for engineer review.

## CODE-JUNCTION review, 26 November 2026 IST

| File | Suitability | Disposition |
|---|---|---|
| `# BridgeCAD Enterprise Suite — Code.txt` | BridgeCAD release directive. Phases 0–6 cover baseline, reporting, BOQ, consolidation, engineering standards, feature selection, and release. Sections 7–9 define acceptance criteria, deliverables, and working rules. | Phase 0 baseline and verification work are in draft PR #1. The current PR still has failing shared checks. Phase 1 awaits a green, merged Phase 0. Engineering acceptance requires independent sign-off. |
| `# CREAT.MD — Continuity Chat Log.MD` | The user confirmed that its general instructions apply to BridgeCAD. Local demo, privacy, regression tests, rollback documentation, protected assets, and the rolling log have BridgeCAD equivalents. Legal deadlines, case examples, and court drafting do not have equivalents here. | Browser-only review, export guard tests and proxy privacy work have existing implementations. The working tree still contains unstaged portions of that work. The complete CI and release claims remain open. |
| `Bcad venus 26.txt` | A 1,196-line handover for a proposed five-span solid-slab example. Its drawing and test observations are relevant. It includes six revisions of embedded replacement lists, several incomplete modules, and unverified project inputs. | Applied dynamic sheet footers. Corrected a separately reproduced A3 note overflow affecting the existing single-span asset. Preserved the source handover. |

### Embedded manifests

The replacement lists were parsed as data. The counts below come from sequential
simulation in memory against the current checkout before edits. Renderer
instructions and separately printed modules were outside this literal-pair test.

| Revision | Single-match pairs | Other results | Disposition |
|---|---:|---|---|
| 1 | 21 | Guide says 20 patches | Adapted the three footer replacements. Other drawing changes require separate geometry tests and review. |
| 2 | 14 | All extracted pairs matched after simulated revision 1 | Review cap/body alignment and plan footprints against a common coordinate model. Articulation, bearing type, soil strata and cover require project inputs. |
| 3 | 0 | Three missing-file pairs, one no-op pair | The expected renderer and usable reinforcement implementation are missing. |
| 4 | 0 | Three missing-file pairs | The reinforcement module is absent. The B2 count in the replacement differs from the accompanying prose. |
| 5 | 5 | Three missing-file pairs, one missing anchor | Superseded by revision 6 in the handover. Registers a hydraulic sheet whose implementation was not supplied. |
| 6 | 5 | Two missing-file pairs, one missing anchor | Depends on both the original renderer and revision 5 source states. Keep hydraulic and founding inputs provisional. |

Both embedded installers write each passing pair immediately. A later failed
anchor leaves earlier edits on disk. The embedded tests also include assertions
that only inspect spec values or look for a label. Those tests cannot establish
whether the printed geometry is correctly located or sized.

### Drawing findings and disposition

| Finding | Repository evidence and disposition |
|---|---|
| B-01 and B-15, deck crossfall and wearing width | Sheet 2 prints a camber label. Confirm the polygon geometry and intended wearing limits from the governing cross-section before adapting the combined replacement. |
| B-02 through B-06, pier details | Sheet 3 derives dimensions and geometry in multiple views. Compare the generated elevation, section, and plan against the same measured step widths, heights, seat width and plan envelope. Retain the source 7 × 9 m values in the archival example. |
| B-07, PCC levelling | Sheet 2 places the PCC block and label at or above the footing-base datum in the cited branch. Apply a consistent below-footing rule only after the reference section and bearing datum are reconciled across views. |
| B-08, weep-hole symbols | Applied using the existing scale-aware circle helper. The patch's `Panel.sample()` call expects a paper-space radius in millimetres, so feeding it a radius in model metres would shrink the marker. The DXF test checks all four marker radii against a non-default diameter. |
| B-09, deck spout symbols | Retain as open. The supplied replacement reuses the weep-hole size for the deck spout, passes it in the wrong units and leaves the placement logic unchanged. |
| B-10 and B-18, title and notes | Check actual text bounds against the title-block region before adopting the proposed shared offset or guard. The confirmed single-span overflow was separate: note columns began at x = 402 and 552 mm on a 420 mm sheet. The notes now occupy x = 252–410 mm below the plan. |
| B-11, expansion gap | Sheet 2 uses a constant fallback when the spec omits the field. Replace that pattern with declared data when the joint schedule is settled. |
| B-12, HFL | The archival PMGSY source spec deliberately leaves HFL unset. Keep that source status and avoid asserting clearance for an unverified flood level. |
| B-13 and B-14, steel and articulation | Withhold the proposed bar schedule, curtailment, bearing selection and movement-joint locations. The revisions give conflicting reinforcement quantities and lack signed design inputs. |
| B-16 and B-17, abutment geometry | Check the cap, shaft, dirt and return walls against a common support geometry and reference plan before changing the dimensions. |
| B-19, pier annotations | The reported panel collision needs a generated DXF geometry or bounds test. Moving a caption in isolation would leave the dimension chain unverified. |
| B-20, strata | The different rock datums are proposals. Require a traceable borehole profile and a verified founding basis before changing the source or printing a rock depth. |
| B-21, setting-out and completeness | A profile, datum and setting-out table would be useful with declared project inputs. The supplied prototype inserts a constant ground RL and assumes HFL is numeric although the default spec permits it to be absent. |
| B-22, footer totals | Applied to Sheets 01–03 using the same `SheetIdentity.total_sheets` already passed to the title block. Tests generate all three DXFs with a five-sheet identity. |
| B-23, fixed captions | The bundle mixes default-specific document text and labels that can become stale with overrides. Review the generated labels individually before changing the reference captions. |
| B-24, silent omissions | Typed or recorded layout errors are suitable, but the bundle does not supply the proposed warning propagation. Keep this open with the drawing error-handling work. |

### Engineering hold points

- The first renderer checks the absolute value of the soffit-to-HFL difference.
  That can treat a submerged soffit as having clearance. Use signed clearance
  with the verified design flood level and afflux.
- Revision 6 turns off the provisional HFL flag while its runoff coefficient,
  travel time and rainfall intensity remain assumptions. The supplied IRC
  reference also needs an edition-specific check. IRC:5-2024 places vertical
  clearance in §106.8, and its table includes bands omitted in the handover.
  [Indian Roads Congress, IRC:5-2024, pp. 27–28](https://law.resource.org/pub/in/bis/irc/irc.gov.in.103.2022.pdf#page=41)
- The founding narrative describes the older level as 0.08 m above the
  requirement, even though its own values give 95.610 m below the stated
  95.690 m threshold by 0.080 m. This is an arithmetic comparison of the
  supplied values. The threshold itself remains unverified.
- The handover does not establish project-approved reinforcement, lap
  lengths, hydraulic and scour basis, afflux, protection works, or independent
  engineering sign-off. The proposed drawing set remains open.

### Local verification

| Check | Result |
|---|---|
| `pytest -p no:hypothesispytest -q tests/test_asset_pack.py` | 34 passed, including the A3 bounds regression, all three non-default footer checks, and the weep-hole radius check. |
| `mkdocs build --strict` | Passed with this review included. |
| SHA-256 comparison of the three input files | All three hashes match the initial inventory. |
| Draft PR #1 at `6ddf860` | That CI snapshot showed five failed jobs. The current PR snapshot is recorded above. |

### Cleanup outcome

The recursive inventory found three files and no subfolders before cleanup.
The three reviewed files were deleted from the queue on 26 November 2026.
The `CODE-JUNCTION/` directory remains in place and is empty. The deletions
record the decision to close the queue. Release and engineering verification
status is recorded above.

| File | Disposition | Reason |
|---|---|---|
| `# BridgeCAD Enterprise Suite — Code.txt` | Deleted | Phase 0 had yet to merge. The phase structure and acceptance status are recorded above. |
| `# CREAT.MD — Continuity Chat Log.MD` | Deleted from the queue on 26 November 2026 after consolidation | The BridgeCAD requirements are recorded below and linked from the README. The legal deadlines, briefs and court exports do not apply to BridgeCAD. |
| `Bcad venus 26.txt` | Deleted | Applicable drafting fixes were verified locally. Revisions 3–6 were incomplete, and the proposed engineering figures lacked verified inputs. The disposition of each revision and finding is recorded above. |

### Consolidated BridgeCAD launch instructions

These are the BridgeCAD requirements carried forward from the mixed continuity
note. The phase and acceptance decisions above record the status at cleanup.
Keep the release and engineering acceptance gates active.

| Area | Requirement | Evidence or remaining work |
|---|---|---|
| Protected paths and continuity | Preserve asset and reference directories and the `CODE-JUNCTION/` directory. Keep the root `CREAT.MD` short, newest first, and within a rolling 24-hour window. | Standing instructions in the README. |
| Baseline and verification | Record the clean installation, type checks, frontend and backend tests, and production build. Identify critical drawing, validation and export paths. Keep the baseline, production status, remaining backlog, and results available in the release records. | Phase 0 evidence is above. Broader CI remains open. |
| Privacy and test data | Use synthetic data for demos and tests. Preserve input privacy and verify handling of workbook uploads and generated files. | Local demo and proxy tests exist. Full launch verification remains open. |
| Draft and export gates | Keep a single software launch command and CI job. Verify that invalid or incomplete inputs block export, with at least eight adversarial checks. Exercise the browser-only demo through both blocked and successful review exports. Keep independent engineering approval visible on issue workflows. | Local launch and adversarial test evidence exists. Phase and release gates remain open. |
| Navigation and deployment | Group navigation clearly, provide useful empty, loading and error states, and guide first-time users to a labelled sample. Verify export reliability and document deployment and rollback. | Deployment and rollback are documented. Full UI and staging acceptance remain open. |
| Delivery | Use small conventional commits, record test counts and blockers in the release report, and verify remaining items before certifying completion. | Phase 0 is tracked in draft PR #1. |
