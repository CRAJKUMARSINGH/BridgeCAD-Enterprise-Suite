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
