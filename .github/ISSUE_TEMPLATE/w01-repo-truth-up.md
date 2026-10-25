---
name: "W01 · Repo truth-up"
about: "Phase 1 — one product, one entry point, honest README"
title: "W01 · Repo truth-up"
labels: "roadmap,phase-1,w01"
---

**Phase:** 1 · Foundation & truth-up
**Week:** 26 Oct – 1 Nov 2026

## Objective
Collapse two app generations and a broken README into one unambiguous product.

## Deliverables
- [ ] `ARCHITECTURE.md` — components, data flow, ownership
- [ ] `docs/adr/0001-one-product-one-entry-point.md` — legacy archived or fenced
- [ ] README: clone URL, `cd` path, and Issues link corrected
- [ ] Folder renamed `BridgeCAD Enterprise Suite` → `bridgecad-suite`
- [ ] `CODEOWNERS` + `main` branch protection enabled
- [ ] `SUITE_DIR` env updated in both workflows

## Definition of done
- [ ] Fresh clone on a clean machine runs with ONE documented command
- [ ] No README instruction is wrong on first try
- [ ] Issue tracker points at this repo, not `Bridge_GAD_Yogendra_Borse`
- [ ] A PR with a lint error cannot merge

## Verification
```bash
git clone <url> /tmp/bc && cd /tmp/bc
<the one documented command>
```

## Evidence
<!-- paste terminal output, PR links -->
