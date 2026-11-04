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

## 2026-11-03

### Session

- **Standing order recorded.** While a session is active, the chat log in this
  file is appended and refreshed **every 12 minutes**; the order is mirrored in
  [README.md](README.md) §Continuity so it is not lost when this file's own
  rolling window trims.
- **Venice-kit enforcement layer applied** (from `CODE-JUNCTION/Venice-patch`):
  `defect` / `needs-triage` labels in `scripts/sync_labels.py`;
  `.github/ISSUE_TEMPLATE/defect.yml`; contact links in
  `.github/ISSUE_TEMPLATE/config.yml`; the Triage block in
  `.github/PULL_REQUEST_TEMPLATE.md`; `.githooks/pre-push` plus the `hooks` /
  `hooks-check` Makefile targets; `.github/workflows/robot.yml`.
- **Doc fork retired.** An earlier pass had placed the two playbooks at the repo
  root; they now live **only** under `docs/`, registered in `DOCS_INDEX.md` and
  the `mkdocs.yml` nav. The root duplicates were removed and the two bare refs in
  `artifacts/TRIAGE_LOG.md` were rebased to `docs/…` — "retire, don't fork".
- **Persona suite retargeted to the real contract.** Rather than port the Venice
  kit verbatim, the engineered oracles were mapped onto the live symbols and
  landed as `tests/robot/` (marker `robot`): engine, API-contract, export and
  console oracles over the real `bridgecad_core` / gateway / `bridgecad_draw` /
  `bridgecad_export` surface. Wired via the `robot` marker in `pyproject.toml`,
  `--ignore=tests/robot` in the unit lane, and a new `oracles` job in
  `robot.yml`. `docs/TEST_PLAN.md` documents the lane and is registered in
  `DOCS_INDEX.md`, the `mkdocs.yml` nav, and `.github/ISSUE_TEMPLATE/config.yml`.
- **Rolling window applied on append.** The previous `2026-11-01` entry was older
  than 24 hours and was dropped here, per the standing rule above. Durable
  history remains in [CHANGELOG.md](CHANGELOG.md).

### Not taken

- **Kit ported verbatim: no.** The kit's illustrative symbols (`design_girder`,
  `/api/v1/design`, `/api/v1/export/*`) do not exist in the tree, so a verbatim
  port would redden CI. The retarget above keeps the intent — engineering
  oracles on the real contract — without oracles for a contract the tree lacks.
- **Committed + pushed** on instruction (`commit push`): `c522356`
  `feat(robot): add engine/API/export oracle lane; certify CODE-JUNCTION/1.txt
  applied` — 25 files, +1298/−169. `HEAD == origin/main`. Certification of
  `CODE-JUNCTION/1.txt`: **applied**, 8 of 10 items, 2 rejected with reason
  (`PATCH_NOTES.md` doc artifact; `pyproject.toml` mypy `files` cosmetic).
- Generated `outputs/` binaries and scratch (`reports/`, `CODE-JUNCTION/`,
  `ATTACHED ASSETS/`) left untracked by design.
- **Certified `CODE-JUNCTION/Venice-patch` (`V*/`): APPLIED (adapted).** The
  robotic harness + triage apparatus is fully represented in the tree; the
  phantom-path variants (`tools/`, the phantom suite dir, `requirements-dev.txt`)
  were retargeted, and three kit deltas were rejected with reason — the
  `docs/TRIAGE_LOG.md` move, the kit's marker names, and the Playwright file.
  Local step outstanding: `make hooks` (install `.git/hooks/pre-push`).
- **Certified `CODE-JUNCTION/BridgeCAD_Robotic_Test_Package`: APPLIED (already
  present) + validated green.** The kit's two code patches (`01` soft-skip
  `hypothesis`, `02` intermediate QA hardening with `--strict-qa`) were already
  in `scripts/advanced_user_robot.py` / `scripts/intermediate_user_robot.py`;
  the legacy guidance (Patches 3–5) is already covered by the C1.5 fix in
  `src/bridge_gad/`. Its unique debug playbook + residual-issue list were merged
  into the root `ROBOTIC-TEST-GUIDE.MD` (§7–§8) — retire, don't fork. Green
  proofs: `robotic_smoke.py --persona all --seed 42` exit 0 · `verify` Day 3 7/7
  + Day 4 8/8 ★ACCEPTED★ · `--hypothesis` lane rc 0 · `--strict-qa` → `qa=88.0`.
  `ruff format --check scripts/` clean. The one `verify_docs.py` failure is the
  pre-existing untracked-inbox link defect, absent from the committed tree.
- **Ran `CODE-JUNCTION/BridgeCAD_Robotic_Test_Package` (already upstream).**
  Hash audit: every package script is byte-identical to the live tree (harness
  differs only by CRLF), so there was nothing to apply. Full matrix green:
  smoke seeds 42/7/99/1234 → 3/3 PASS each; basic 3 iterations `ALL OK`;
  intermediate `--strict-qa` → `qa=88.0`; advanced `--hypothesis` → schema
  201 843 B + unit OK; `verify` ★ACCEPTED★; `gate.py --json` → `blocked=false,
  total_open=0`; ruff clean (215 files); `pytest tests/unit` → 115 passed. Sole
  red: `verify_docs.py` `test_defect_02`, all dead links inside the untracked
  `CODE-JUNCTION/` inbox (committed tree clean).
