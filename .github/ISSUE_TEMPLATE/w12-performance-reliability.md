---
name: "W12 · Performance & reliability"
about: "Phase 4 — budgets, gated benchmarks, observability"
title: "W12 · Performance & reliability"
labels: "roadmap,phase-4,w12"
---

**Phase:** 4 · Platform hardening, security & performance
**Week:** 11 – 17 Jan 2027

## Objective
Speed that is measured, gated and honest about limits.

## Deliverables
- [ ] Published performance budgets (GAD gen, 100-sheet project, memory)
- [ ] `scripts/check_perf_budgets.py` gating CI
- [ ] Structured logging + error tracking
- [ ] Health/readiness endpoints
- [ ] Backup/restore drill
- [ ] Capacity limits documented

## Definition of done
- [ ] A regression beyond threshold fails the build
- [ ] Budgets stated for a named reference project, not "typical"
- [ ] Documented limits are honest, not aspirational

## Verification
```bash
pytest -q tests/benchmarks --benchmark-json=bench.json
python scripts/check_perf_budgets.py bench.json
```

## Evidence
