# CREAT.md — rolling 24-hour continuity log

**Standing rule** (also recorded in [README.md](README.md)): this file keeps only
the **last 24 hours** of work. Appending a new entry deletes anything older, so
the log stays a continuity hand-off between agents and engineers rather than a
second changelog. Durable history lives in [CHANGELOG.md](CHANGELOG.md).

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

---

## 2026-10-27

### Workspace

- Removed the redundant nested clone (a stale copy at an identical commit with
  none of the root's uncommitted work). Editor-level deletion was used because
  shell directory deletion is silently reverted in this environment. Root is now
  the single source of truth.

### Enrichment applied from `CODE-JUNCTION/`

- **KIMI-2610 (safe set).** RFC 7807 `application/problem+json` error bodies and
  upload limits (50 MB cap, `.xlsx` allowlist) wired across the API endpoints;
  the coordinate contract and structural DXF checks landed. The BOQ-provenance
  and QA-rule scaffolds were skipped — they duplicate existing Wing-13/14 modules.
- **GENSPARK-2610 (security + version).**
  - `src/bridge_gad/calc_engine.py`: the repository's only live `eval()` was on
    the workbook-formula path. Replaced with an AST whitelist walker that admits
    arithmetic, known names and pure math calls only. Verified against seven
    hostile payloads (`__import__("os")`, `SPAN1.__class__`, `open("x")`, lambda,
    ternary, list literal, `;`-chaining) — all rejected.
  - `src/bridge_gad/api.py`: CORS origins now come from `API_CORS_ORIGINS`; a
    wildcard or an empty list is refused at startup when `ENV=production`.
  - `packages/bridgecad-io/bridgecad_io/__init__.py`: version `0.2.0-m2` →
    `0.1.0-rc1`, so `rc1_smoke.py` RC1-01 passes for all nine packages.
- **Types.** All nine `mypy` `arg-type` errors in `bridgecad_core` fixed with
  None-guarded `float()` reads. `mypy` is clean.
- **Golden pins.** `scripts/pin_golden.py` lands the missing half of the golden
  machinery: the hand-picked golden cases pin selected values, this pins the
  **whole** model as canonical JSON with a sha256 drift diff. Five pins under
  `tests/draw/golden/pins/`. Verify mode is 5/5; a tampered pin fails loudly.
- **Architecture.** `import_linter_contract.ini` encodes the GUIDE.md §3
  invariants and `suite-ci.yml` gained the import-linter job. All three contracts
  are kept; a probe violation turns the gate red.

### This session — `CODE-JUNCTION/00 FOR ALL APPS`

- Scope taken: Phase 2 (continuity logging), Phase 9 (design trends),
  Phases 11/13 (README polish, operator README).
- `SARASWATI.test.tsx` and `SARASWATI.jpg` were **not** applied. The image is
  already at `apps/web-console/public/saraswati.jpg`; the test duplicates
  `apps/web-console/src/components/SaraswatiMascot.test.tsx` (which is a strict
  superset) and its imports resolve to paths that do not exist here.
- Phase 9 design layer, applied to `apps/web-console`:
  - `src/index.css` — `glass-panel`, `glass-panel-dark`, `neu-tile`, `neu-btn`,
    `lift`, `rise-in` plus a `prefers-reduced-motion` guard.
  - `src/components/Layout.tsx` — glass sidebar, gradient canvas, nav lift/glow
    micro-interactions, pulsing status dot.
  - `src/pages/Dashboard.tsx` — glass panels, lifting feature cards, neumorphic
    stat tiles.
  - `src/components/FileDropzone.tsx`, `src/pages/Projects.tsx` — drag scale and
    entrance feedback.
- Verification: `npm run typecheck` clean · `npm test` 3/3 · `npm run build` OK
  (958 modules, CSS 20.81 kB / 4.30 kB gzip).

### Not taken (explicitly out of scope this pass)

- Phase 10 marketing set (`subscriptionService.ts`, `PricingPage.tsx`,
  `WelcomeModal.tsx`, `UpgradeBanner.tsx`).
- Phases 4–8 and 12: bug review, `AUDIT-REPORT-v1.0.md`, refactor, Web-Vitals
  tuning, simulated-user QA (125 / 75 / 51), deploy configuration.
