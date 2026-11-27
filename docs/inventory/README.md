# Repository Wiring and Incorporation Inventory

Snapshot: 27 November 2026

Repository: `BridgeCAD-Enterprise-Suite`

Branch: `codex/phase-0-launch-baseline`

HEAD: `c428656`

Baseline state: committed tree synchronized with `origin/codex/phase-0-launch-baseline`, with an in-flight uncommitted change set (11 unstaged files and 2 untracked modules).

## Executive Finding

The only local incorporation backlog is a small, uncommitted change set: two new wired modules (`bridgecad_core/drawing_audit.py`, `bridgecad_export/worker_jobs.py`) plus the entry-point refactor and documentation refresh that go with them. Everything else — the live drafting feature, Netlify proxy helper, worker entrypoint, launch scripts, guidance files, and inventory reports — is tracked on the current branch.

The remaining incorporation backlog is the branch itself: local `main` is 21 commits behind, with 187 branch-only change records. The remaining engineering backlog is runtime policy and incomplete behavior, especially API authentication, gateway lifecycle setup, eight placeholder modules, and seven implemented modules with no production caller.

## Purpose

This inventory separates four conditions that are often confused:

1. **Git incorporation gap** — a change is committed on this branch but is not present in local `main`, or a local file is untracked, ignored, staged, or unstaged.
2. **Runtime wiring gap** — a tracked file is not reachable from an active application, API, CLI, or deployment entrypoint.
3. **Intentional non-runtime file** — a test, direct tool, fixture, reference asset, report, or generated artifact that is not expected to be imported by production code.
4. **Incomplete implementation** — a module is imported or advertised but contains only a placeholder or lacks required behavior.

A file can belong to more than one category. For example, the live drafting sources are runtime-wired and tracked, but their branch changes are still not incorporated into local `main`.

## Reports

| Report | Contents |
|---|---|
| [01-git-incorporation.md](01-git-incorporation.md) | Current Git state, the uncommitted change set, resolved historical untracked/ignored gaps, and all 187 branch-only change records. |
| [02-runtime-wiring.md](02-runtime-wiring.md) | Resolved clean-clone fixes, active entrypoints, legacy code, test-only scaffolds, eight placeholders, seven zero-production-reference modules, and partial wiring. |
| [03-guidance-reference.md](03-guidance-reference.md) | Guidance, handover material, reference corpora, learning assets, missing guidance targets, stale continuity statements, and inventory-navigation gaps. |
| [04-standalone-tools.md](04-standalone-tools.md) | All 77 tracked scripts, incorporated launch tools, package-root verifiers, and expected non-runtime test material. |

## Snapshot Counts

| Measure | Count | Interpretation |
|---|---:|---|
| Tracked files | 2,005 | Files known to Git at `c428656`. |
| Commits ahead of local `main` | 21 | Branch changes are not yet merged into local `main`. |
| Branch-only change records vs `main...HEAD` | 187 | Includes additions, modifications, deletions, and rename records. |
| Staged files | 0 | No index changes at baseline capture. |
| Unstaged modified files | 11 | Five inventory reports plus six source/manifest edits from the entry-point refactor. |
| Untracked, non-ignored files | 2 | Two new wired modules (`drawing_audit.py`, `worker_jobs.py`) awaiting initial Git incorporation. |
| Ignored files reported by Git | tens of thousands | Dominated by test, type-check, bytecode, dependency, and build caches. |
| Actionable ignored source/guidance files after filtering | 0 | The Netlify helper exception is committed; remaining ignored files are regenerable. |
| Tracked scripts under `scripts/` | 77 | Includes five legacy scripts and two active launch scripts. |
| Tracked test files | 199 | Intentional non-runtime verification material. |
| Tracked `EXAMPLES/` files | 802 | Generated exemplar corpus; not production imports. |
| Legacy `src/bridge_gad` files | 45 | Retained legacy surface, fenced from the Suite container contract. |
| Test-only `bridgecad_draw/sheets` scaffold files | 12 | Not used by the production booklet manifest. |
| Docstring-only capability placeholders | 8 | Advertised capabilities without implementation. |
| Implemented zero-production-reference modules | 7 | Four WIRE and three PLUGIN-PROMOTE decisions. |

These counts describe the working tree at `c428656` plus the uncommitted change set.

## Resolved Since the Previous Inventory

| Former issue | Current state |
|---|---|
| `netlify/lib/drawing-proxy.cjs` was hidden by the broad `lib/` ignore rule. | Narrow ignore exceptions are committed; the helper is tracked and required by four Netlify functions. |
| Docker Compose called a missing `bridgecad_infra.queue.run_worker`. | `queue.py` implements `run_worker` and three ARQ jobs; `make worker` is present. |
| Live drafting sources and launch scripts were untracked. | `DraftingStudio.tsx`, geometry, CSS, tests, `deck_joints.py`, and both launch scripts are tracked and wired. |
| Ten transient live-drafting browser captures created status noise. | They were deleted as regenerable duplicates; future matching captures are ignored. |
| Seven implemented modules had no explicit disposition. | Decisions are recorded in [02-runtime-wiring.md](02-runtime-wiring.md#7-implemented-but-not-connected-to-an-active-application-route): 4 WIRE, 3 PLUGIN-PROMOTE, 0 ARCHIVE. |

## Main Entrypoints Used for Reachability

| Surface | Entrypoint | Status |
|---|---|---|
| Root Netlify frontend | `frontend/index.html` → `frontend/src/main.tsx` | Active production frontend. |
| Root frontend routes | `#drafting`, `#workspace`, default workflow landing | Active hash-routed application. |
| Node server | `server/index.mjs` | Serves `frontend/dist` and proxies `/api/*`. |
| Netlify functions | `netlify/functions/*.js` | Active serverless API surface. |
| FastAPI gateway | `apps/api-gateway/bridgecad_api/main.py` | Active Python API; auth and lifespan gaps remain. |
| Python CLI facade | `bridgecad/__main__.py` | Active `bridgecad` command. |
| Streamlit console | `apps/streamlit-ui/app.py` | Active through `make ui` and README quick start. |
| React console | `apps/web-console/src/main.tsx` | Separate active product surface with its own build, CI, Docker image, and `make web` target. |
| Vercel static entrypoint | `public/index.html` | Active alternate entrypoint through `vercel.json`. |
| Docker Compose worker | `docker-compose.yml` → `bridgecad_infra.queue.run_worker` | Implemented and tracked; Redis-backed smoke remains pending in a compliant environment. |

`apps/web-console` and `public/index.html` are therefore **not** orphaned merely because they differ from the root Netlify entrypoint.

## Current Action Backlog

| Priority | Finding | Evidence | Recommended action |
|---|---|---|---|
| P1 | An uncommitted entry-point refactor is not yet in Git. | 2 untracked modules (`drawing_audit.py`, `worker_jobs.py`) and 6 refactor files across `core`, `draw`, `export`, and `infra`. | Review as one commit, `git add` the untracked and modified files together, and commit before merging the branch. |
| P1 | The Phase 0 branch is not incorporated into `main`. | 21 commits ahead; 187 branch-only records. | Review and merge in coherent groups after open CI/release gates are green. |
| P1 | Deployment configuration advertises API-key authentication that the gateway does not enforce. | `BRIDGECAD_API_KEYS` appears in deployment files; no gateway call to `verify_api_key`, `require_role`, or `ApiKey` was found. | Wire `bridgecad_infra.auth` into the gateway or correct the deployment contract before production. |
| P1 | Gateway DB/cache/storage lifecycle is unimplemented. | `main.py` lifespan contains only `yield  # M8: init DB / cache / storage here`. | Implement lifecycle integration or explicitly document unsupported infrastructure. |
| P1 | Guidance references are broken or stale. | Missing guides/manual sources, absent `README_RAJKUMAR.md`, and stale `CREAT.MD` queue statements. | Repair, replace, or retire each reference and add a documentation-link check. |
| P2 | Eight capability modules are placeholders. | Infra, export, QA, plugins, bill, and draw modules contain only milestone docstrings. | Implement, mark unsupported, or remove from public discovery. |
| P2 | Seven implemented modules have no production caller. | Four WIRE and three PLUGIN-PROMOTE decisions. | Wire the four core capabilities and promote the three optional adapters through discoverable plugins. |
| P2 | Legacy and duplicate drawing surfaces need an explicit policy. | 45 legacy files and 12 test-only scaffold files remain referenced. | Retain as opt-in compatibility/test code, migrate selected capabilities, or archive with a record. |
| P3 | The inventory reports are not in MkDocs navigation. | `mkdocs.yml` contains no `inventory/` entry. | Add an Inventory navigation section or document the reports as repository-local audit material. |
| P3 | The user-manual generator cannot regenerate its output. | `docs/build_manual.py` requires absent `docs/manual_template.md`; legacy GUI text references absent `build_manual.bat`. | Restore source template/tooling or mark the PDF as archival. |
| P3 | Standalone learning/demo surfaces are not linked from main navigation. | `learn.html` and `frontend/demo_pdf_button.html` have no root frontend navigation link. | Link deliberately, integrate, or archive with a documented route. |

## Recommended Incorporation Order

1. **Commit the in-flight change set first:** the two untracked modules plus the entry-point refactor (see [01-git-incorporation.md](01-git-incorporation.md#24-current-uncommitted-change-set-new-since-3110881)).
2. **Review the 187-record branch diff by subsystem:** CI/governance, documentation, frontend/Netlify, Python packages, tools, legacy `src/bridge_gad`, and tests.
3. **Close production behavior gaps:** API authentication and gateway lifespan initialization.
4. **Repair guidance:** missing targets, stale `CREAT.MD`, manual generation, and inventory navigation.
5. **Merge the Phase 0 branch after open CI/release gates are resolved.**
6. **Decide placeholder policy:** implement M3–M8 features or stop advertising them as available.
7. **Execute the seven zero-reference dispositions:** four WIRE and three PLUGIN-PROMOTE.
8. **Decide legacy/scaffold policy:** retain as opt-in compatibility/test code, migrate selected capabilities, or archive explicitly.
9. **Keep direct tools, tests, references, and generated exemplars out of the production import graph unless there is a concrete caller.**

## Scope and Confidence

- **High confidence:** Git state, import statements, route entrypoints, Makefile/CI references, placeholder file contents, and explicit documentation statements.
- **Static-analysis boundary:** “no production call site found” means no reference was found in the inspected application, CLI, deployment, frontend, and workspace configuration. It is not proof that no external consumer imports a public Python API.
- **Intentional exclusions:** routine tests, fixtures, generated drawings, example corpora, dependency locks, caches, bytecode, and build output are not defects merely because production code does not import them.
- **Working-tree disclosure:** this refresh rewrites only `docs/inventory/README.md` and reports 01–04, which remain uncommitted until separately reviewed. The reports also describe the wider uncommitted change set (2 untracked modules and 6 refactor files) recorded in [01-git-incorporation.md](01-git-incorporation.md#24-current-uncommitted-change-set-new-since-3110881).
