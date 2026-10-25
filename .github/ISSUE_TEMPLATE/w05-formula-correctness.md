---
name: "W05 · Formula correctness"
about: "Phase 2 — property tests, unit guards, rounding rules"
title: "W05 · Formula correctness"
labels: "roadmap,phase-2,w05"
---

**Phase:** 2 · Engineering correctness & V&V
**Week:** 23 – 29 Nov 2026

## Objective
No formula silently returns a plausible wrong number.

## Deliverables
- [ ] Hypothesis property tests for every formula module
- [ ] SI/FPS unit-system guards with explicit conversion errors
- [ ] Significant-figure and rounding rules encoded as policy, not ad hoc
- [ ] Input domain validation (span/depth limits, min reinforcement)
- [ ] Inventory doc: every formula → test → benchmark

## Definition of done
- [ ] Zero known silent-failure paths
- [ ] A kN/mm input cannot be read as kip/inch without an error
- [ ] Property tests cover monotonicity, bounds and degenerate inputs

## Verification
```bash
pytest -q tests/property -p no:randomly
```

## Evidence
