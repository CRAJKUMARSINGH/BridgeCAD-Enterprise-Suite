# Sheet Review Checklists

One checklist per sheet, one row per requirement. The rule that makes these
worth having:

**Every item carries either an automated assertion or an explicit reason it
cannot have one.** A checklist item with neither is a gap in the harness, and
`scripts/check_checklists.py` fails the build on it.

## Row format

| `#` | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|

- **Assertion** — for `AUTO` rows, the name of a function in
  `tests/draw/dxf_assert.py`, without the `assert_` prefix. For `SCRIPT` rows,
  the script path. For `MANUAL` rows, `MANUAL: <reason>`.
- **Mode** — `AUTO` (harness), `SCRIPT` (a named checker), `MANUAL` (engineer
  judgement on paper).
- **OK** — `☑` only when the requirement is actually met. Blank is not a pass.

## Rules

1. `AUTO` and `SCRIPT` rows must be green before a `MANUAL` review is booked.
   There is no point asking an engineer to eyeball a sheet that still fails its
   own assertions.
2. A `MANUAL` row is signed by the reviewer in the sign-off block, not by the
   author.
3. Adding a drawing element means adding a row. Deleting an element means
   deleting its row and noting why in the commit.
4. A sheet module may only use layers listed in its checklist. Extra layers are
   a defect; `check_checklists.py` compares the module's `LAYERS_USED` against
   the checklist's `LAYER:` rows.
5. Clause references are provisional until the week-45 audit is signed. Do not
   cite a clause here that is not in `TRACEABILITY.md`.

## Current state

All checklists are **baseline**. Rows are `☐` and stay that way until their
assertion is un-xfailed and green. The checklists are the week-46 deliverable;
they exist now so the assertions have somewhere to land.

## Sign-off

Each checklist ends with a reviewer block. A checklist without a signature
blocks the release gate for that sheet. See `docs/upgrade/SIGNOFF.md` for the
family-level statement the per-sheet blocks roll up into.
