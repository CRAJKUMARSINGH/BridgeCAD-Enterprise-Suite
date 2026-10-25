---
name: "W08 · Interoperability"
about: "Phase 3 — IFC, Excel BOQ, JSON schema, fuzzing"
title: "W08 · Interoperability"
labels: "roadmap,phase-3,w08"
---

**Phase:** 3 · Interoperability & drawing standards
**Week:** 14 – 20 Dec 2026

## Objective
Play well with the rest of a design office's toolchain.

## Deliverables
- [ ] IFC 4.3 export via ifcopenshell
- [ ] Excel BOQ with live formulas
- [ ] DWG export (ODA) where licensing permits
- [ ] Published JSON project schema
- [ ] Importer fuzzing with malformed files
- [ ] Round-trip loss budget per format

## Definition of done
- [ ] export → import → compare test for every format, within loss budget
- [ ] IFC passes a validator
- [ ] A truncated/corrupt import produces a clear error, not a traceback

## Verification
```bash
pytest -q tests/interop
```

## Evidence
