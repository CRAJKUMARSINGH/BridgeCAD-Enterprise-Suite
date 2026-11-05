# CREAT.md — rolling 24-hour continuity log

**Standing rule** (also recorded in [README.md](README.md)): this file keeps only
the **last 24 hours** of work. Appending a new entry deletes anything older, so
the log stays a continuity hand-off between agents and engineers rather than a
second changelog. Durable history lives in [CHANGELOG.md](CHANGELOG.md).

**Standing order — chat-log cadence.** For the duration of an active session, the
session chat log in this file is appended and refreshed **every 12 minutes**. The
order is stated here *and* in [README.md](README.md) §Continuity so neither copy
is the single point of loss.

Introduced by the `CODE-JUNCTION/00 FOR ALL APPS` brief (Phase 2).

---

## Standing rules

- **Rolling window.** Keep the last 24 hours only; delete the stale portion on
  every append.
- **Exempt from duplicate-file removal.** `Attached_Folder/`, `Test_Files/`, and
  any "how to use" guide are never deleted as redundant.
- **Commit identity.** Set it locally before committing:

  ```bash
  git config user.name  "RAJKUMAR SINGH CHAUHAN"
  git config user.email "<maintainer address — see the team password manager>"
  ```

  The address is deliberately **not** written here or in any root doc:
  `tests/docs/test_doc_integrity.py::test_no_pii_in_tracked_docs` rejects a
  personal email in `README.md`, `GUIDE.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, `DOCS_INDEX.md`, and `CHANGELOG.md`.
- **Build stays green.** Every step must leave `make lint`, `make test`, and the
  React console's `typecheck` / `test` / `build` passing.
- **Chat-log cadence.** While a session is active, append/refresh the session
  entry **every 12 minutes**; a session hands off before any gap exceeds one
  cadence.

---

## 2026-11-05

### Session

- **Venice-patch applied in chronology** (`CODE-JUNCTION/Venice-patch`):
  `Venice 6 steps.txt` → `Venice continual.txt` → `Venice santa.txt`, each audited
  against the live tree first. All items landed; one documented deviation.
  - **Phase 1 (6 steps).** `frontend/src/sheets/theme.ts` (INK/PAPER + `inkFor`),
    `SheetContext` in `registry.tsx`; Sheets 04/05 moved off the Sheet-01-owned
    `.drawing-sheet` / `.sheet-bg` / `.sheet-border` classes onto a new
    `.bcsheet` root (inline attrs, zero cascade reliance,
    `vector-effect: non-scaling-stroke`); `main.tsx` nav/zoom/theme/print;
    `sheets.css` theme + stage blocks.
  - **Phase 2 (continual).** New `docs/CONTINUAL_IMPROVEMENT_SHEET_DETAILS.md`
    (invariants N1–N8, parity discipline, budgets, ledger D-01…D-12), registered
    in `DOCS_INDEX.md` + `mkdocs.yml`; guard `tests/draw/test_no_shared_class.py`;
    debt rows mirrored into `docs/upgrade/DEFECT-LEDGER.md`; `CHANGELOG.md`
    `[Unreleased]` refreshed.
  - **Phase 3 (santa, G1–G8).** Panel markers + `E_OVERLAP` bbox check + audit
    fix map (**G1**); `scripts/parity_detail_sheets.py` JS↔Python oracle (**G2**);
    `.github/workflows/sheet-detail.yml` retargeted to `./.github/actions/
    setup-suite` (**G3**); `detailGeometry.d.ts` + `DetailParams` typing (**G4**);
    `beforeprint`/`afterprint` + `@page A1 landscape` (**G5**); splay-extreme
    fixtures + `tests/draw/golden/pins/detail_default.json` 156/567 ±2 + three
    tests (**G6**); scale bar + north arrow (**G7**); `docs/sheets/
    _SPEC_TEMPLATE.md` (**G8**).
  - **Deviation:** brief's panel bands `4C`/`5F` genuinely intersect neighbours →
    shrank `4C` width 220→200 and `5F` height 70→55 (smallest bbox change that
    still bounds the content) so `E_OVERLAP` stays a meaningful gate.
- **Verified (all green).** `npm run build --prefix frontend` exit 0 (index
  184.10 kB / gzip 59.92 kB) · `pytest tests/draw/test_sheet4_sheet5_present.py
  tests/draw/test_no_shared_class.py -q` → **8 passed** · `ruff check` on both
  scripts → *All checks passed* · `parity_detail_sheets.py --fixtures
  tests/e2e/fixtures` → `fixtures=28 divergences=0` ·
  `robotic_sheet_detail_audit.py --mutate all --cases 200` → **mutation 4/4** ·
  `scripts/verify_docs.py` → **3 passed / 0 failed / 3 skipped**.
- **Browser run + certified.** Vite dev server at `http://localhost:5173/` (index
  200; every edited module transforms 200). `robotic_sheet_detail_audit.py --cases
  2000` → 0 failures (4000 renders); `--mutate all` → 4/4. `ruff format --check`
  cleaned 2 files; `pytest … tests/docs -m "not slow"` → 49 passed.
- **Committed + pushed on instruction.** Pathspec (25 files, +994/−151) →
  **`449f57f`**; `git push origin main` → `69d54d2..449f57f`;
  `HEAD == origin/main`. `outputs/` binaries + scratch excluded by design.
- **Re-verified on the pushed tree — no change to ship.** On `5d97ecb`: dev server
  index + all edited modules 200; build exit 0; ruff clean (217 files); pytest
  49 passed; parity 28/0; audit 4000 renders 0 failures; mutation 4/4;
  `verify_docs` 3/0/3. Only `outputs/` binaries and untracked scratch differ.
- **Vite `.d.ts` overlay fixed.** A stray request for
  `src/sheets/detailGeometry.d.ts` made esbuild parse the type-only declarations
  as JS and broadcast a transform error to the HMR overlay. The runtime never
  imports the `.d.ts` (imports resolve to the `.js`). Added a 6-line
  `skipTypeDeclarations` plugin in `frontend/vite.config.ts` serving any `.d.ts`
  as `export {};`. Restarted the server; the file now returns 200 and all gates
  stay green.

### Not taken

- The santa brief's `docs/sheets/_SPEC_TEMPLATE.md` was left in the `docs/sheets/`
  subdir rather than promoted to top-level `docs/`: the doc-integrity gates glob
  `docs/*.md` only, so registering a template in the nav would orphan it — no
  registration tax is the correct trade.
- Feeder-ahead/cleanup debt rows **D-01, D-03, D-04, D-05, D-06, D-08, D-12**
  remain open in the Phase-2 ledger; not in scope for G1–G8.

## 2026-11-04

### Session

- **Netlify deploy 400 fixed + shipped.** Three deploys failed identically at the
  deploy stage: `HTTP 400 ... uploadDeployFunction ... unable to decode manifest
  file: json: cannot unmarshal string into Go struct field functionManifest.version
  of type int`. **Root cause:** Netlify decodes any `.json` in the functions dir
  whose basename matches a function name as that function's `functionManifest`;
  `netlify/functions/package.js` collided with root `package.json` (string
  `"version": "1.0.0"`). **Fix:** renamed the function to `export_package.js`,
  moved `[functions] directory` out of `[build]`, added the `/api/package`
  redirect, pinned Node 20 via `.nvmrc`. Green: `test_netlify_readiness.py`
  → **26/26 · READY**. Committed + pushed (pathspec, excludes `outputs/*` and
  scratch) → **`69d54d2`**; `HEAD == origin/main`. **Action for user:** redeploy
  on Netlify with *Clear cache and deploy site*.
- **Robotic matrix re-run green** (from the `BridgeCAD_Robotic_Test_Package`
  run): smoke seeds 42/7/99/1234 → 3/3 each; basic `--iterations 3` `ALL OK`;
  intermediate `--strict-qa` → `qa=88.0`; advanced `--hypothesis` OK; `verify`
  ★ACCEPTED★; ruff clean (215 files); `pytest tests/unit` → 115 passed.
- **Windows git-lock note.** `.git/index.lock` was repeatedly re-created by a
  background git process; `Remove-Item`/`Rename-Item` failed while it was held —
  resolved by retrying once the holder exited.
- **Venice abutment patch applied (adapted) — sheets 04/05 restored.** From
  `CODE-JUNCTION/Venice-patch/Cad.txt`: `frontend/src/sheets/*` (detail geometry,
  foundation + pier/abutment/wing-wall renderers, registry, chrome, css),
  `main.tsx` sheet register 01/04/05 with local DXF export, `allowJs: true`,
  `scripts/robotic_sheet_detail_audit.py`, `tests/draw/test_sheet4_sheet5_present.py`.
  The abutment fix floors `abtl` at `carriageway + 2` so `face_run` cannot reach
  ≤ 0 and collapse a wing wall. Three kit defects fixed on retarget (Windows argv
  limit, unquoted import specifier, centre-vs-corner rect extents). Dropped the
  patch-notes doc (doc-integrity gate). Green: audit 2000 cases → **0 failures**,
  `pytest …test_sheet4_sheet5_present.py` **4 passed**, `tsc --noEmit` + `vite
  build` clean, ruff clean. **Not committed** (standing rule).

<!-- Rolling window: entries older than 24 h are dropped on append. -->
