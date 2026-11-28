# CREAT.MD — Continuity Chat Log

> **Standing instruction** (see [README](README.md#-standing-instructions--continuity-log-creatmd)).
> This shared log helps tools and engineers pick up recent work. Keep only the
> last 24 hours, put the newest entry first, and remove older entries whenever
> a new entry is written. Keep entries short.

## 25 November 2026 IST — Phase 0 baseline

- A new BridgeCAD directive is in `CODE-JUNCTION`. Work started on `codex/phase-0-launch-baseline`, with `rc1-audit-baseline` at `a488ea8`.
- Base collection passed with 1,532 tests. The strict documentation build and 15 CLI checks passed. Three reference drawing sets were generated and hashed. Repeat DXF hashes differed.
- Phase 0 awaits remote CI and merge. Preserve both guides and proceed in phase order.

## 25 November 2026 IST — BridgeCAD sync and launch checks

- Fast-forwarded BridgeCAD `main` to GitHub commit `4998d7d`. Resolved three conflicts and retained the pre-sync autostash.
- The launch guide in `CODE-JUNCTION` applies to BridgeCAD. Disregard Legal Luminaire references. Keep the guide until compliance is verified.
- Software launch passed with 27 frontend and 31 focused Python tests, plus a static browser export run. All 25 Netlify readiness checks passed.
- Engineering release remains open. The release gate reports a missing defect ledger and sign-off file. Two verified changes were committed locally. The remaining changes are unstaged.

## 24 November 2026 IST — Drawing follow-up

- **Continuity log.** Record all of today's instructions in `CREAT.MD`. Keep the newest entry first, retain only the last 24 hours, and remove older entries during each update.
- **Browser review and test runs.** Show the GAD elevation and bridge plan together on one browser screen. The earlier request also called for a side-by-side browser run. Demonstrate different founding levels for A1, A2, and the piers. Make the pier foundations and PCC pad outlines easy to see in both elevation and plan.
- **Founding levels.** Allow separate RCC footing underside RLs for A1, A2, and each pier. Blank inputs preserve the existing shared default for the two abutments and the existing shared default for all piers. In the GAD elevation, show Road RL, HFL and NGL, with a single footing-base RL label beside the deepest pier.
- **PCC pads.** Default to **300 mm thickness** with **150 mm projection beyond each RCC footing edge** on all four sides in plan. Draw the pad below the footing in elevation and show its outline in plan.
- **Approach slabs and dirt walls.** At both ends, extend the approach slab **3,500 mm from the outside face of the dirt wall**, make it **300 mm thick**, and match the **full deck slab width**. Keep the dirt-wall top flush with the concrete deck and approach slab tops for solid slab, RCC T-beam, and PSC girder bridges.
- **Spans and joints.** Accept comma-separated span lengths and `count × length` shorthand, including `x` and `X`, in the same input. Show discontinuities at pier centrelines in both plan and elevation for solid slab, RCC T-beam, and PSC girder bridges.
- **GAD accuracy and abutments.** Review the existing agent-written code closely. Correct incomplete or erroneous plan and elevation geometry, including multiple supports and the three selectable abutment profiles (cantilever, gravity, and full-height wall). Improve the clarity and finish of the drawing details.
- **Emergent comparison.** Use the [BridgeGA Studio preview](https://bridge-abutment--6w1pphk9.preview.emergentagent.com) as a benchmark for on-screen controls and live redraw. Verify the repo against the supplied reference before certifying parity. The reference includes LISP `abt1()` profiles, batters, wing-wall splay, dirt walls, toe/heel and weep holes, four dimensioned views, three presets, named designs saved to MongoDB, pan/zoom, layered R12 DXF and SVG export, and an eight-check IRC audit strip.
- **Git.** Synchronize the local and remote repository. Git synchronization and Emergent feature parity remain open for verification.

## 24 November 2026, 20:20 IST — Browser test recorded

- Left **GAD + plan** open with test footing-base RLs of A1 **104.250 m**, A2 **102.000 m**, P1 **99.500 m**, and P2 **96.750 m**. P2 carries the sole pier footing-base RL label. The PCC pads were highlighted in both views.
- Verified the combined view in the browser. All 14 frontend tests passed, and the production build succeeded.
