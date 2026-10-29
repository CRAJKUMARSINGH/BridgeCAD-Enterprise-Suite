# BridgeCAD Enterprise Suite — 10-Working-Day Release-Confidence Sprint

**Purpose:** establish a trustworthy, bounded release candidate for a small set of representative bridge cases. This is a pilot-readiness plan, not an engineering certification or a claim that generated drawings are construction-ready.

**Plan status:** proposed; no repository changes have been made.
**Repository snapshot reviewed:** public main at commit 24e68b0c6944ce44f60bd40636c28194ff260cf3 (2026-10-29). Reconfirm the branch head before execution.
**Capacity assumption:** one maintainer, about six focused hours per workday, with access to an independent engineering reviewer for the final manual review. A small team can parallelize review and CI work, but should not broaden the acceptance scope.

## Recommended outcome

Deliver one reproducible release-candidate proof pack containing:

- A clean-clone installation and test report.
- One canonical sheet manifest shared by generation, tests, and docs.
- Drawing, BOQ, QA, and export-manifest results for the selected pilot fixtures.
- Regression checks and reviewed drawing renders for the sheets included in the release candidate.
- An explicit status for each sheet: supported, scaffolded, or awaiting engineering review.

The existing project roadmap is 15 weeks long; use this sprint as a focused W01–W02 execution slice rather than creating a competing 52-week plan. See [MASTER_ROADMAP.md](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/MASTER_ROADMAP.md) and [ROADMAP_STATUS.md](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/docs/ROADMAP_STATUS.md).

## Scope decision to make on Day 1

The current booklet lists eight sheets, while the guide and drawing-test contract describe seven. Make one explicit decision and record it in an ADR or a short decision note. Recommended default: treat the booklet's eight outputs as the intended package, but mark any sheet that has not passed its own acceptance checks as scaffolded/unverified. If the product contract is intentionally seven sheets, omit the eighth from the release-candidate package rather than silently generating an undocumented extra sheet.

References: [booklet sheet list](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/packages/bridgecad-draw/bridgecad_draw/booklet.py), [drawing test contract](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/tests/draw/contract.py), [DXF contract tests](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/tests/draw/test_dxf_contract.py), [master guide](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/GUIDE.md).

## PR plan

### PR-0 — Reproducible baseline (Days 1–2)

**Goal:** distinguish actual product failures from setup problems before editing geometry.

Tasks:
- Install from the repository's documented development setup in a clean environment; use the declared dependency/lock configuration, not ad hoc package installs.
- Run the documented verifier, focused drawing tests, integration tests, and E2E command; record exact commands, commit SHA, durations, failures, and xfails.
- Confirm the fixture inventory and record the baseline results without editing expected outputs or golden files.
- Open a short defect ledger; classify each item from the attached agent notes as verified, not reproduced, already fixed, or out of scope.

Acceptance:
- A fresh clone can install dependencies and execute the selected checks using documented steps.
- The baseline report separates environment/setup failures from code/test failures.
- No golden, expected-value, or xfail is changed merely to make the baseline green.

### PR-1 — One sheet/output contract (Day 2)

**Goal:** remove ambiguity about what the release candidate actually emits.

Tasks:
- Record the seven-versus-eight-sheet decision.
- Make the sheet registry/spec the canonical inventory; align booklet generation, test parametrization, numbering/title blocks, and user-facing docs with it.
- Give every emitted sheet a status and a minimum acceptance contract. A scaffold must be visibly labelled and must not be counted as promoted output.

Acceptance:
- Every generated sheet maps to exactly one registry/spec entry and one builder.
- There are no undocumented generated sheets, missing test entries, or conflicting total-sheet labels.
- Tests fail if generation and the declared inventory drift apart.

### PR-2 — Verified high-risk geometry corrections (Days 3–5)

**Goal:** fix only defects that can be demonstrated on the current branch and materially affect the pilot output.

Tasks:
- Reproduce candidate issues from the agent notes against current source and the baseline fixtures before editing.
- Prioritize geometry that can change support/deck position, foundation placement, dimensions, skew representation, or BOQ values. Do not treat note-only findings as confirmed defects.
- For each fix, add a focused regression that fails before the change and passes after it; keep unrelated refactors separate.
- Preserve and extend the existing golden, baseline, and sign-off mechanisms rather than replacing them with a new parallel framework.

Acceptance:
- Every claimed fix has a minimal reproducible test and a stated engineering invariant.
- No changed golden is accepted without a written reason and review of the resulting geometry.
- No calculation or geometry defect is hidden by xfail, skip, relaxed thresholds, or a changed expected value.

### PR-3 — Pilot regression and drawing review (Days 6–8)

**Goal:** demonstrate that the chosen workflow remains coherent across representative cases.

Suggested pilot cases, subject to current fixture availability: simple_12m, skew15_3x18m, and well_0_600.

Tasks:
- Generate the full agreed sheet set for each pilot case.
- Run structural DXF checks for finite extents, non-empty geometry, legal layers, no degenerate entities, title-block fields, sheet numbering, and dimensions where required.
- Review plotted/rendered outputs at print scale; check cross-sheet levels/support positions and the status of all scaffolds.
- Run the existing complete E2E suite after the focused pilot checks.

Acceptance:
- Every promoted sheet passes its declared automated checks for all pilot cases.
- Every scaffolded sheet is clearly identified in the report and is not represented as verified.
- Drawings and outputs are reproducible under the documented environment; any intended nondeterminism is documented.
- All repository release-gate tests pass, or the release candidate remains blocked with the exact failures listed. A partial pilot pass is not reported as a full-suite pass.

### PR-4 — Release-candidate proof pack (Days 9–10)

**Goal:** make the result reviewable by someone who did not implement it.

Tasks:
- Update README/guide/roadmap status to match what was actually tested and emitted.
- Produce a concise run report with commit SHA, environment, commands, fixture IDs, sheet statuses, test totals, failures/xfails, and links to rendered outputs.
- Ensure each package export carries an accurate manifest and the existing “generated, not reviewed for construction” limitation unless an independent engineer has signed the relevant deliverables.
- Present the release candidate for independent engineering review; do not sign off on your own engineering output.

Acceptance:
- A reviewer can reproduce the run from the report and locate every output.
- Docs, generated package, and test inventory agree on the sheet count and status.
- No construction-ready, standards-certified, or independently validated claim is made without the corresponding evidence and reviewer sign-off.

## Day-by-day schedule

| Day | Focus | Exit evidence |
|---|---|---|
| 1 | Clean-clone setup and baseline commands | Environment/setup report; exact commit and command log |
| 2 | Baseline triage; sheet-count decision; PR-1 | Decision recorded; inventory/spec consistency tests |
| 3 | Reproduce and rank candidate geometry defects | Verified defect ledger with reproduction inputs |
| 4 | Fix highest-risk reproducible defect(s) | Regression tests fail before/fix passes after |
| 5 | Complete bounded geometry fixes and PR-2 | Focused suite green; no scope creep |
| 6 | Generate pilot fixtures and inspect structural metrics | Pilot output inventory and automated results |
| 7 | Render/print review; resolve pilot blockers | Review notes tied to fixture/sheet |
| 8 | Full existing E2E and regression run; PR-3 | Full-suite report; unresolved failures block release |
| 9 | Align docs, manifest, status, and run report | Candidate proof pack assembled |
| 10 | Independent review and release decision | Sign-off or explicit “not ready” decision |

## Release gate — all must be true

- Clean-clone dependency installation and documented checks work.
- The canonical sheet inventory matches generators, tests, title blocks, and docs.
- The selected pilot cases pass all release-gate checks for every promoted sheet.
- The complete existing E2E suite is green; failures are not converted into xfails or hidden by lower thresholds.
- Scaffolded or unsupported functionality is disclosed in the output and report.
- An independent engineering reviewer has reviewed any drawings described as engineering-validated. Without that review, the release remains a software pilot and retains the non-construction-ready warning.

## Explicitly out of scope for these 10 days

- New bridge families, new AI features, wholesale package restructuring, or a replacement drawing/test framework.
- Broad standards certification claims, construction-ready claims, or sign-off by the implementer.
- Implementing every proposed defect or every item in the 52-week notes without reproducing it against current main.
- IFC, new export formats, auth/RBAC, desktop packaging, and unrelated performance work unless a verified blocker prevents the pilot from running.

## Known execution caveat from the review snapshot

In the review shell, python -m bridgecad verify stopped because pydantic was unavailable, and pytest was not installed. This does not establish that the repository's tests pass or fail. PR-0 must rerun them in the repository's intended clean development environment and report the result honestly.

## Source files to recheck at kickoff

- [Master roadmap](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/MASTER_ROADMAP.md)
- [Booklet generator](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/packages/bridgecad-draw/bridgecad_draw/booklet.py)
- [Drawing test contract](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/tests/draw/contract.py)
- [DXF structural checks](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/tests/draw/dxf_assert.py)
- [E2E runner](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/tests/e2e/run_e2e.py)
- [Master guide](https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/blob/main/GUIDE.md)
