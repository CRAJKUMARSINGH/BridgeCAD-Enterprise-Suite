---
name: "W03 · Test harness + CI baseline"
about: "Phase 1 — pytest, coverage ratchet, blocking checks"
title: "W03 · Test harness + CI baseline"
labels: "roadmap,phase-1,w03"
---

**Phase:** 1 · Foundation & truth-up
**Week:** 9 – 15 Nov 2026

## Objective
A green gate that a PR physically cannot bypass.

## Deliverables
- [ ] `tests/` structure + `conftest.py` with shared fixtures
- [ ] ~100 tests on pure functions (unit conversion, section properties, bar schedule, rounding)
- [ ] `--cov-fail-under` set to current level, recorded in `MASTER_ROADMAP.md` scoreboard
- [ ] `suite-ci.yml` wired; `ci / required` is the only required status check
- [ ] Coverage XML uploaded as artifact

## Definition of done
- [ ] CI green on `main` and under 10 minutes
- [ ] Deliberately failing test blocks merge
- [ ] Coverage floor documented and non-negotiable downward

## Verification
```bash
pytest -q --cov --cov-fail-under=45
gh pr checks
```

## Evidence
