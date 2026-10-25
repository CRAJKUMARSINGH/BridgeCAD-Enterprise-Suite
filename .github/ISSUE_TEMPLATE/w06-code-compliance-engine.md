---
name: "W06 · Code compliance engine"
about: "Phase 2 — clause mapping, load combinations, calc sheets"
title: "W06 · Code compliance engine"
labels: "roadmap,phase-2,w06"
---

**Phase:** 2 · Engineering correctness & V&V
**Week:** 30 Nov – 6 Dec 2026

## Objective
Every check carries its clause, demand, capacity and utilisation.

## Deliverables
- [ ] Compliance object model with clause references
- [ ] Load combination engine (IRC:6 / EN 1990)
- [ ] Calc sheet export citing clause numbers per check
- [ ] Utilisation ratio per check, with pass/fail
- [ ] `docs/verification/TRACEABILITY.md`: check → clause → test → benchmark

## Definition of done
- [ ] No gap in the traceability matrix
- [ ] Calc sheet is a document you would hand a checker
- [ ] Every supported code has a stated version/edition

## Verification
```bash
pytest -q tests/compliance
python -m bridgecad.cli.calc_sheet --demo > /tmp/sheet.md
```

## Evidence
