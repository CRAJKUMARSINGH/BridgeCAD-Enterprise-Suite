---
name: "W15 · v1.0 release & certification"
about: "Phase 5 — signed release, external validation, sign-off"
title: "W15 · v1.0 release & certification"
labels: "roadmap,phase-5,w15"
---

**Phase:** 5 · Release engineering, compliance & launch
**Week:** 1 – 7 Feb 2027

## Objective
Ship v1.0.0 and prove it on real bridges.

## Deliverables
- [ ] Signed `v1.0.0` tag + SLSA provenance
- [ ] Release notes + migration guide + rollback plan
- [ ] Installers, SBOM, checksums published
- [ ] Three external bridge projects run end-to-end
- [ ] Independent engineer reviews the outputs
- [ ] Case study + published benchmark table
- [ ] Retrospective

## Definition of done
- [ ] Written sign-off from an independent engineer
- [ ] All scoreboard targets met
- [ ] Rollback plan tested

## Verification
```bash
gh release view v1.0.0
slsa-verifier verify-artifact ...
```

## Evidence
