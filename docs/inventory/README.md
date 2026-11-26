# Repository Wiring and Incorporation Inventory

Snapshot: 26 November 2026

Repository: `BridgeCAD-Enterprise-Suite`

Branch: `codex/phase-0-launch-baseline`

HEAD: `6ddf860`

## Purpose

This inventory separates four different conditions that are often confused:

1. **Git incorporation gap** — a file exists locally but is untracked, ignored, uncommitted, or not merged into `main`.
2. **Runtime wiring gap** — a file is tracked but is not reachable from an active application, API, CLI, or deployment entrypoint.
3. **Intentional non-runtime file** — a test, direct tool, fixture, reference asset, report, or generated artifact that is not expected to be imported by production code.
4. **Incomplete implementation** — a module is imported or advertised but contains only a placeholder or lacks the symbol its caller expects.

A file can belong to more than one category. For example, the live drafting sources are already imported by the frontend, but they remain untracked and therefore absent from a clean clone.

## Reports

| Report | Contents |
|---|---|
| [01-git-incorporation.md](01-git-incorporation.md) | Every untracked file, the actionable ignored source file, all 47 branch-only change records, and all 49 unstaged modifications. |
| [02-runtime-wiring.md](02-runtime-wiring.md) | Legacy code, test-only sheet scaffolds, placeholder modules, public-only APIs, unlinked pages, and confirmed broken or partial wiring. |
| [03-guidance-reference.md](03-guidance-reference.md) | Reports, continuity material, documentation, reference corpora, learning assets, handover artifacts, and missing guidance references. |
| [04-standalone-tools.md](04-standalone-tools.md) | Every tracked script and package-root verifier, classified as Makefile/CI-wired, directly invoked, supporting code, legacy, or historical. |

## Snapshot Counts

| Measure | Count | Interpretation |
|---|---:|---|
| Tracked files | 1,989 | Files known to Git. |
| Commits ahead of local `main` | 14 | The current branch has not been merged into local `main`. |
| Branch-only change records vs `main...HEAD` | 47 | Includes additions, modifications, deletions, and rename records. |
| Unstaged modified files | 49 | Existing tracked files with local changes. |
| Untracked, non-ignored files | 20 | Local files not yet known to Git. |
| Ignored files reported by Git | 36,710 | Dominated by test, type-check, bytecode, dependency, and build caches. |
| Actionable ignored source files after excluding caches/build output | 1 | `netlify/lib/drawing-proxy.cjs`. |
| Legacy `src/bridge_gad` files | 45 | Retained legacy surface, fenced from the Suite container contract. |
| Test-only `bridgecad_draw/sheets` scaffold files | 12 | Not used by the production booklet manifest. |
| Docstring-only placeholder modules | 9 | Advertised capabilities without implementation. |
| Tracked test files | 199 | Intentional non-runtime verification material. |
| Tracked `EXAMPLES/` files | 802 | Generated exemplar corpus; not production imports. |

The counts above describe the repository before these five inventory reports were created.

### Post-snapshot Working-tree Updates

- `netlify/lib/drawing-proxy.cjs` is no longer ignored and is now visible as untracked source.
- `packages/bridgecad-infra/bridgecad_infra/queue.py` now implements `run_worker` and three ARQ jobs.
- `Makefile` now exposes `make worker`.
- The seven zero-production-reference modules now have explicit WIRE / PLUGIN-PROMOTE decisions in [02-runtime-wiring.md](02-runtime-wiring.md#6-implemented-but-not-connected-to-an-active-application-route).
- Ten untracked live-drafting browser captures were deleted as regenerable duplicates; future captures under `artifacts/browser-results/live-drafting-*` are ignored.

## Main Entrypoints Used for Reachability

| Surface | Entrypoint | Status |
|---|---|---|
| Root Netlify frontend | `frontend/index.html` → `frontend/src/main.tsx` | Active production frontend. |
| Root frontend routes | `#drafting`, `#workspace`, default workflow landing | Active hash-routed application. |
| Node server | `server/index.mjs` | Serves `frontend/dist` and proxies `/api/*`. |
| Netlify functions | `netlify/functions/*.js` | Active serverless API surface. |
| FastAPI gateway | `apps/api-gateway/bridgecad_api/main.py` | Active Python API. |
| Python CLI facade | `bridgecad/__main__.py` | Active `bridgecad` command. |
| Streamlit console | `apps/streamlit-ui/app.py` | Active through `make ui` and README quick start. |
| React console | `apps/web-console/src/main.tsx` | Separate active product surface with its own build, CI, Docker image, and `make web` target. |
| Vercel static entrypoint | `public/index.html` | Active alternate entrypoint through `vercel.json`. |
| Docker Compose worker | `docker-compose.yml` → `bridgecad_infra.queue.run_worker` | Active in the working tree; `run_worker` and `make worker` are implemented. |

`apps/web-console` and `public/index.html` are therefore **not** orphaned merely because they differ from the root Netlify entrypoint.

## Highest-Priority Findings

| Priority | Finding | Evidence | Recommended action |
|---|---|---|---|
| P0 | A required production Netlify helper was ignored. | `netlify/lib/drawing-proxy.cjs` is required by four functions; the broad `lib/` rule previously hid it. | **Resolved in the working tree:** narrow ignore exceptions added. Commit the helper with its callers and verify a clean-checkout Netlify build. |
| P0 | Docker Compose called a missing worker function. | `docker-compose.yml:95` imports `run_worker`; `queue.py` was previously a docstring-only stub. | **Resolved in the working tree:** worker implementation and `make worker` added. Run against Redis in CI/Compose, then commit. |
| P1 | Live drafting code is wired locally but absent from Git. | `main.tsx` imports `DraftingStudio`; geometry, CSS, tests, `deck_joints.py`, and launch scripts are also locally connected but untracked. | Commit the complete feature set together, then run the launch check from a clean checkout. |
| P1 | A large amount of active work is not incorporated. | 14 commits ahead of `main`, 47 branch-only change records, 49 unstaged modifications, and 20 untracked files. | Review and land in coherent groups; do not treat all of these as runtime orphans. |
| P1 | Deployment documentation promises API-key auth that the gateway does not call. | `docs/DEPLOYMENT.md` lists `BRIDGECAD_API_KEYS`; no `verify_api_key`, `require_role`, or `ApiKey` use was found in the gateway. | Wire authentication before production or correct the deployment contract. |
| P1 | Several guidance links point to absent files. | Active Streamlit copy references `GUIDE.md`, `docs/USER-MANUAL.md`, and `docs/PWD_ENRICHMENT_GUIDE.md`; triage guidance references two absent documents. | Restore, replace, or remove each reference and add a documentation-link check. |
| P2 | Nine modules are placeholders despite being exported or facade-loaded. | Infra, export, QA, plugins, bill, and draw modules contain only milestone docstrings. | Implement, explicitly mark unsupported, or remove from public discovery. |
| P2 | Legacy code is retained but outside the main Suite contract. | `Dockerfile` explicitly fences `src/bridge_gad`; ADR-0002 preserves legacy entrypoints. | Keep as legacy until feature parity is decided; do not silently merge it into the active facade. |
| P2 | The enhancement queue is empty, but the continuity log still describes queued guides. | `RELEASE_REPORT.md` records three deleted guides; `CREAT.MD` still says guides are in `CODE-JUNCTION`. | Update the rolling continuity log to match the release report. |
| P3 | The user-manual generator cannot regenerate its output. | `docs/build_manual.py` requires absent `docs/manual_template.md`; legacy GUI text references absent `build_manual.bat`. | Restore the source template/tooling or mark the PDF as an archival artifact. |

## Recommended Incorporation Order

1. **Land the resolved clean-clone fixes:** commit `netlify/lib/drawing-proxy.cjs`, the queue implementation, and the `make worker` target; verify from clean checkout/Compose.
2. **Land live drafting as one feature:** drafting component, geometry, CSS, Python joint module, tests, launch scripts, and launch evidence.
3. **Reconcile documentation with deployed behavior:** API auth, missing guides, manual generation, and stale `CREAT.MD` queue statements.
4. **Merge the Phase 0 branch after its open CI/release gates are resolved.**
5. **Decide placeholder policy:** implement M4–M8 features or stop advertising them as available.
6. **Decide legacy policy:** retain as opt-in compatibility code, migrate selected capabilities, or archive with an explicit record.
7. **Keep direct tools, tests, references, and generated exemplars out of the production import graph unless there is a concrete caller.**

## Scope and Confidence

- **High confidence:** Git state, import statements, route entrypoints, Makefile/CI references, placeholder file contents, and explicit documentation statements.
- **Static-analysis boundary:** “no production call site found” means no reference was found in the inspected application, CLI, deployment, frontend, and workspace configuration. It is not a proof that no external consumer imports a public Python API.
- **Intentional exclusions:** routine tests, fixtures, generated drawings, example corpora, dependency locks, caches, bytecode, and build output are not treated as defects simply because production code does not import them.
- **Working-tree changes:** the original inventory was documentation-only. Subsequent work implemented the worker, fixed the Netlify ignore rule, and removed transient browser captures; see the post-snapshot notes.
