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
- [ ] ISO 13567 / IS 962 layer naming scheme
- [ ] Line weights, text heights, sheet sizes, scale bars, north arrow
- [ ] Standard title block + revision table
- [ ] Deterministic DXF generation (byte-identical for identical input)
- [ ] PDF/A-1b archival export, veraPDF-validated
- [ ] Drawing diff regression tests

## Definition of done
- [ ] DXF opens clean in AutoCAD, BricsCAD and LibreCAD — zero repair prompts
- [ ] Layer audit script passes
- [ ] PDF/A validation passes
- [ ] Two renders of the same input produce identical bytes

## Verification
```bash
pytest -q tests/drawings --regression
verapdf --format text -f 1b out/plan.dxf.pdf
```

## Evidence
