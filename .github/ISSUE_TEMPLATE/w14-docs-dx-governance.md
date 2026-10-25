---
name: "W14 · Docs, DX, governance"
about: "Phase 5 — docs site, verification manual, ADRs, semver"
title: "W14 · Docs, DX, governance"
labels: "roadmap,phase-5,w14"
---

**Phase:** 5 · Release engineering, compliance & launch
**Week:** 25 – 31 Jan 2027

## Objective
A stranger can contribute and trust the docs.

## Deliverables
- [ ] MkDocs Material site, built and link-checked in CI
- [ ] Verification manual published
- [ ] CONTRIBUTING + issue/PR templates
- [ ] ADR index
- [ ] semver policy, changelog automation, deprecation policy
- [ ] Support SLA

## Definition of done
- [ ] New contributor ships a change in under a day using docs alone
- [ ] Docs build fails CI on broken links
- [ ] Verification manual is public, not buried in the repo

## Verification
```bash
mkdocs build --strict
```

## Evidence
