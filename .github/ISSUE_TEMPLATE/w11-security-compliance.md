---
name: "W11 · Security, privacy, compliance"
about: "Phase 4 — SAST, SBOM, DSC signing, threat model"
title: "W11 · Security, privacy, compliance"
labels: "roadmap,phase-4,w11"
---

**Phase:** 4 · Platform hardening, security & performance
**Week:** 4 – 10 Jan 2027

## Objective
Defensible security posture and signed deliverables.

## Deliverables
- [ ] SAST (bandit/CodeQL) + dependency scanning + Trivy container scan
- [ ] CycloneDX SBOM per release
- [ ] Signed build artifacts
- [ ] DSC digital signature on issued PDFs (IT Act 2000)
- [ ] Threat model doc
- [ ] DPDP Act 2023 / GDPR data-handling note

## Definition of done
- [ ] Zero high/critical CVEs
- [ ] SBOM ships with every release
- [ ] A signed PDF verifies in Adobe Reader

## Verification
```bash
pip-audit --strict
trivy image bc-suite:latest
```

## Evidence
