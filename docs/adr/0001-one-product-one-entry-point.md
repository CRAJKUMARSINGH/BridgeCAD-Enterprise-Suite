# ADR-0001 · One product, one entry point

- **Status:** Proposed
- **Date:** 2026-10-26
- **Phase:** 1 / W01

## Context
The repo ships two application generations in one tree: the active
BridgeCAD Enterprise Suite (`packages/*`, `apps/*`) and the legacy
Ultimate Bridge GAD Generator (`streamlit_app_ultimate.py`, `ci.yml`).
A newcomer cannot tell which to run, and README instructions are wrong.

## Decision
<!-- Pick ONE and delete the rest -->

### Option A — archive to a branch (recommended)
`git branch legacy/ultimate-gad`, then remove the legacy tree from `main`.
Delete `.github/workflows/ci.yml`. Cheapest, cleanest.

### Option B — keep as a fenced subfolder
Move to `legacy/ultimate-gad/` with its own README, `ci.yml` scoped by path
filter, and an explicit "not maintained" banner.

### Option C — submodule
Split to its own repo, reference as a submodule. Most work, most isolation.

## Consequences
- **Good:** one clone, one command, one CI file, one thing to keep green.
- **Bad:** git history for the legacy path is noisier if option A.
- **Mitigation:** tag the pre-removal commit as `pre-suite-only`.

## Verification
Fresh clone on a clean machine runs with one documented command.
