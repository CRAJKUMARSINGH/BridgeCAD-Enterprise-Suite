---
name: "W07 · Drawing standards & CAD output"
about: "Phase 3 — ISO 13567 layers, title blocks, deterministic DXF"
title: "W07 · Drawing standards & CAD output"
labels: "roadmap,phase-3,w07"
---

**Phase:** 3 · Interoperability & drawing standards
**Week:** 7 – 13 Dec 2026

## Objective
Output that a CAD draughtsman accepts without rebuilding it.

## Deliverables
- [x] ISO 13567 / IS 962 layer naming scheme
- [x] Line weights, text heights, sheet sizes, scale bars, north arrow
- [x] Standard title block + revision table
- [x] Deterministic DXF generation (byte-identical for identical input)
- [x] PDF/A-1b archival export, veraPDF-validated
- [x] Drawing diff regression tests

## Definition of done
- [x] DXF opens clean in AutoCAD, BricsCAD and LibreCAD — zero repair prompts
- [x] Layer audit script passes
- [x] PDF/A validation passes
- [x] Two renders of the same input produce identical bytes

## Verification
```bash
pytest -q tests/drawings --regression
verapdf --format text -f 1b out/plan.dxf.pdf
```

## Evidence
