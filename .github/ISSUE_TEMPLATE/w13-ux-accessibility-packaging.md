---
name: "W13 · UX, accessibility, packaging"
about: "Phase 5 — WCAG 2.2 AA, i18n, signed installer"
title: "W13 · UX, accessibility, packaging"
labels: "roadmap,phase-5,w13"
---

**Phase:** 5 · Release engineering, compliance & launch
**Week:** 18 – 24 Jan 2027

## Objective
Installable by a design office, usable by everyone.

## Deliverables
- [ ] WCAG 2.2 AA audit: contrast, keyboard nav, focus order
- [ ] i18n framework, English + Hindi, all strings externalised
- [ ] Actionable error messages ("span must be ≥ X because clause Y")
- [ ] Code-signed Windows installer (Inno Setup / MSI)
- [ ] Offline / desktop mode validated

## Definition of done
- [ ] Accessibility audit ≥ 90
- [ ] Installer installs on a clean Windows VM with no warnings
- [ ] Zero hardcoded UI strings

## Verification
```bash
python -m axe_selenium_python  # or Lighthouse CI
```

## Evidence
