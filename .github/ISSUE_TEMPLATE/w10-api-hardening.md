---
name: "W10 · API & platform hardening"
about: "Phase 4 — versioned API, auth, RBAC, load test"
title: "W10 · API & platform hardening"
labels: "roadmap,phase-4,w10"
---

**Phase:** 4 · Platform hardening, security & performance
**Week:** 28 Dec 2026 – 3 Jan 2027

## Objective
A service layer you can expose without embarrassment.

## Deliverables
- [ ] `/v1` prefix + published OpenAPI spec
- [ ] Auth (JWT/OAuth2), RBAC, rate limits, idempotency keys
- [ ] Consistent error contract
- [ ] Contract tests from the OpenAPI spec
- [ ] k6 load test against a published p95 budget
- [ ] Node/Express layer removed or explicitly scoped

## Definition of done
- [ ] No undocumented endpoints
- [ ] Load test meets p95 budget at target RPS
- [ ] Auth paths covered by tests

## Verification
```bash
pytest -q tests/api
k6 run tests/load/gad_gen.js
```

## Evidence
