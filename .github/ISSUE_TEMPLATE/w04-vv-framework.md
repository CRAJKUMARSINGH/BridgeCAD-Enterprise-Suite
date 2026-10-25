---
name: "W04 · V&V framework"
about: "Phase 2 — benchmarks, tolerances, verification manual"
title: "W04 · V&V framework"
labels: "roadmap,phase-2,w04"
---

**Phase:** 2 · Engineering correctness & V&V
**Week:** 16 – 22 Nov 2026

## Objective
Make correctness defensible in front of a reviewing engineer.

## Deliverables
- [ ] `docs/verification/README.md` — methodology
- [ ] `docs/verification/TOLERANCE_POLICY.md` published
- [ ] 25+ benchmark cases: hand calcs, textbook problems, code worked examples
- [ ] Expected outputs stored as golden files
- [ ] Every benchmark mapped to a source module
- [ ] Cross-checks against an independent tool where available

## Definition of done
- [ ] Benchmarks run in CI and fail the build on drift
- [ ] Each case cites its source document and clause/example number
- [ ] Tolerance policy states exact / 0.1% / 1% tiers and why

## Verification
```bash
pytest -q tests/verification
```

## Evidence
