# Documentation index

Every doc in this repo, what it is, and whether to trust it.

## Authoritative

| File | What | Owner | Status |
|---|---|---|---|
| **[GUIDE.md](GUIDE.md)** | Master guide. Wins all conflicts. | maintainer | ✅ current |
| [README.md](README.md) | Front door, quick start | maintainer | ✅ current |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, data flow, invariants, ownership | maintainer | ✅ current |
| [CHANGELOG.md](CHANGELOG.md) | Versioned changes | maintainer | ✅ current |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute | maintainer | ✅ current |

## Guides

| File | What |
|---|---|
| [docs/getting-started.md](docs/getting-started.md) | Start here: prerequisites, four install paths, first bridge end to end, verification gates, common pitfalls |
| [docs/excel-contract.md](docs/excel-contract.md) | The 15-sheet workbook schema |
| [docs/interop.md](docs/interop.md) | Per-format round-trip loss budget, import fuzzing, published JSON schema |
| [docs/standards.md](docs/standards.md) | IRC/MORTH coverage, rule authoring |
| [docs/drafting-standard.md](docs/drafting-standard.md) | Drawing-sheet drafting standard (text heights, layer weights) |
| [docs/plugin-authoring.md](docs/plugin-authoring.md) | Adding a bridge type |
| [docs/deployment.md](docs/deployment.md) | Shipping it |
| [docs/troubleshooting.md](docs/troubleshooting.md) | When it breaks |
| [docs/api-reference.md](docs/api-reference.md) | Public API surface, package by package |
| [docs/BRIDGE_GAD_STANDARDS_ALIGNMENT.md](docs/BRIDGE_GAD_STANDARDS_ALIGNMENT.md) | IRC/MORTH clause → code alignment matrix |
| [docs/USER-MANUAL.md](docs/USER-MANUAL.md) | **Current user manual** — task-oriented: install, 15 tabs, CLI groups, workbook fields, errors |
| [docs/Bridge_GAD_User_Manual.md](docs/Bridge_GAD_User_Manual.md) | ⚠️ Legacy manual for the old `.exe` product — superseded by USER-MANUAL.md |
| [docs/manual_template.md](docs/manual_template.md) | Source template for the generated manual |
| [docs/how-to-use-video.md](docs/how-to-use-video.md) | "How to use" walkthrough — video-form storyboard + player |
| [docs/TRIAGE_AND_DEBUG.md](docs/TRIAGE_AND_DEBUG.md) | Post-test debug protocol — minimize, bisect, classify, record |
| [docs/PATCH_GUIDE.md](docs/PATCH_GUIDE.md) | Patch patterns by defect class, cross-referenced from the triage log |
| [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Robotic oracle lane — engine, API, export and console oracles |
| [docs/CONTINUAL_IMPROVEMENT_SHEET_DETAILS.md](docs/CONTINUAL_IMPROVEMENT_SHEET_DETAILS.md) | Continual improvement programme for detail sheets 04 / 05 — invariants, budgets, parity, debt ledger |
| [docs/abutment-geometry.md](docs/abutment-geometry.md) | Resolved abutment datum stack — cap, dirt wall, approach slab, wearing coat |
| [docs/lisp-baseline.md](docs/lisp-baseline.md) | LISP baseline audit — where the suite disagrees with the original AutoLISP |

## Governance

| File | What |
|---|---|
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Conduct |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |
| [LICENSE](LICENSE) | MIT |

## Planning and history — read once, then leave alone

| File | What | Note |
|---|---|---|
| [SKELETON.md](SKELETON.md) | M0 scaffold tree | path note now fixed |
| [archive/01_ACTION_PLAN_M0_to_M10.md](archive/01_ACTION_PLAN_M0_to_M10.md) | Milestone plan | M0–M10 complete |
| [archive/00_REPORT_Trust_Assessment_and_Synthesis.md](archive/00_REPORT_Trust_Assessment_and_Synthesis.md) | Source synthesis | historical |
| [archive/GAPS_OPPORTUNITIES_FIXES.md](archive/GAPS_OPPORTUNITIES_FIXES.md) | Audit + patch report | historical |
| [archive/app-robustness-testing.md](archive/app-robustness-testing.md) | Robustness notes | historical |
| [archive/september-update.md](archive/september-update.md) | September update | historical |
| [archive/CREAT.MD](archive/CREAT.MD) | Milestone chat summary | historical |
| [MASTER_ROADMAP.md](MASTER_ROADMAP.md) | 15-week plan to v1.0.0 | anchor doc |
| [M1_WEEK_1_PLAN.md](M1_WEEK_1_PLAN.md) | M1 Week 1 sprint — executed, verified | record |
| [archive/TEST_DEPLOYMENT_SUMMARY.md](archive/TEST_DEPLOYMENT_SUMMARY.md) | Legacy deployment status report | historical |
| [docs/ROADMAP_STATUS.md](docs/ROADMAP_STATUS.md) | Weekly progress from roadmap issues | auto-generated |

## Legacy generation — superseded by the Suite

| File | What | Note |
|---|---|---|
| [OUTPUT_GENERATION_GUIDE.md](OUTPUT_GENERATION_GUIDE.md) | Legacy output driver | targets `src/bridge_gad/` |
| [PDF_OUTPUT_FEATURES.md](PDF_OUTPUT_FEATURES.md) | Legacy PDF features | legacy |

## The two rules

1. **One fact, one place.** Entry points, versions and paths live in `GUIDE.md`
   only. Other docs link to it.
2. **Retire, don't fork.** Superseded docs are deleted or moved to `archive/`.
   Never `X.md` beside `X_NEW.md`.

## Adding a doc

Put it in `docs/`, add a row here, and link it from `GUIDE.md` §14. A doc that
is not in this index does not exist.


## PWD verification supplement — 2026-11-13

See [the executed PWD checks, reference inventory, parameter/layout guidance and patch priorities](docs/BRIDGECAD_SUPPLEMENTARY_PATCH.md). At commit `5d5f99e`, all 15 types generated nine-sheet DXF packages, but the completed full rendering run produced 24 all-white PNGs. Successful generation is not reference fidelity or engineering approval.

- [Uploaded v.md instruction ledger](docs/V_INSTRUCTIONS_APPLIED.md): applied safeguards, already present fixes, pending engineering/reference work and validation results.


## Drawing selection and landing-page workflow

See [the practical manual and reference-fidelity enrichment](docs/BRIDGECAD_REFERENCE_FIDELITY_ENRICHMENT.md) for interface capabilities, drawing selection, family-specific variables, paper/layout planning, worked CLI examples and Netlify/browser release gates; it also records the white-paper PNG visibility fix, real A0–A4 paper/orientation selection and the remaining exact-match gates. The root Netlify frontend now opens a guided landing page; the existing renderer remains at `#workspace`.


## Additional implementation and audit notes

- [BRIDGECAD_ATTACHED_ASSETS_LISP_PATCH.md](docs/BRIDGECAD_ATTACHED_ASSETS_LISP_PATCH.md)
- [BRIDGECAD_USER_MANUAL.md](docs/BRIDGECAD_USER_MANUAL.md)
- [PWD_ENRICHMENT_GUIDE.md](docs/PWD_ENRICHMENT_GUIDE.md)
