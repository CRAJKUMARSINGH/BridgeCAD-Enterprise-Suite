---
name: "W09 · Data model & versioning"
about: "Phase 3 — Pydantic schema, migrations, .bcad container"
title: "W09 · Data model & versioning"
labels: "roadmap,phase-3,w09"
---

**Phase:** 3 · Interoperability & drawing standards
**Week:** 21 – 27 Dec 2026

## Objective
Project files survive upgrades.

## Deliverables
- [ ] Pydantic v2 project model
- [ ] Schema version field + migration engine
- [ ] `.bcad` container spec published
- [ ] Autosave + crash recovery
- [ ] Forward and backward migration tests

## Definition of done
- [ ] A v1.0 file opens in the current version unchanged
- [ ] A deliberately corrupted file recovers gracefully
- [ ] Spec is public and versioned

## Verification
```bash
pytest -q tests/migrations tests/recovery
```

## Evidence
