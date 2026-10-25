# BridgeCAD Enterprise Suite — Master Roadmap

> **Goal:** v1.0.0 that a reviewing engineer will sign off on.
> **Window:** 26 Oct 2026 → 7 Feb 2027 · 15 weeks · one shippable milestone per week
> **Status doc:** [`docs/ROADMAP_STATUS.md`](docs/ROADMAP_STATUS.md) (regenerated on every issue change)

---

## Operating rules

1. **One week = one demo-able artifact on `main`.** Not a branch. Not "mostly done."
2. **Every week ends in a PR** carrying its own DoD checklist. Unticked box ⇒ the week is not done; extend it rather than starting the next.
3. **Feature freeze weeks 1–12.** No new bridge types, no new AI features. Verification before capability.
4. **Ratchet only.** Coverage, type strictness, performance budgets go up and never come down.
5. **Friday = demo + retro.** Ten minutes, written, in the week's issue.

## Definition of "industry standard" (scored at week 15)

| # | Dimension | Bar |
|---|-----------|-----|
| 1 | Correctness | Documented V&V, tolerances published, clause-level traceability |
| 2 | Interoperability | DXF/DWG/IFC/Excel/PDF-A round-trip verified |
| 3 | Drawing standards | ISO 13567 / IS 962 layers, title blocks, revision control |
| 4 | Auditability | Calc sheets, revision history, signed deliverables |
| 5 | Software hygiene | Reproducible build, typed, tested, versioned API, packaged |

Dimensions 1 and 5 are the current gap.

---

## Phase 1 · Foundation & truth-up

### W01 · Repo truth-up — 26 Oct – 1 Nov
- [ ] `ARCHITECTURE.md` written
- [ ] `ADR-0001` one product, one entry point (legacy archived or fenced)
- [ ] README clone path, `cd` path and Issues link corrected
- [ ] Folder renamed `bridgecad-suite`
- [ ] `CODEOWNERS` + `main` branch protection

**DoD:** fresh clone on a clean machine runs with one documented command.

### W02 · Dependency discipline — 2 – 8 Nov
- [ ] `pyproject.toml` (PEP 621) + committed lockfile
- [ ] prod/dev extras split, no floating pins
- [ ] Python 3.11 + 3.12 matrix
- [ ] `pre-commit`: ruff format, ruff check, mypy, secret scan
- [ ] Docker build from lockfile succeeds from scratch

**DoD:** pre-commit blocks a deliberately bad commit.

### W03 · Test harness + CI baseline — 9 – 15 Nov
- [ ] pytest seeded with ~100 pure-function tests
- [ ] Coverage floor set, ratchet enforced
- [ ] ruff + mypy blocking, required checks on PRs
- [ ] CI green, under 10 minutes

**DoD:** a PR with a lint error cannot merge.

## Phase 2 · Engineering correctness & V&V

### W04 · V&V framework — 16 – 22 Nov
- [ ] `docs/verification/` skeleton
- [ ] 25+ benchmark cases as golden files
- [ ] Tolerance policy published
- [ ] Independent-tool cross-checks (STAAD / MIDAS / CSI)

**DoD:** every benchmark maps to a module and fails the build on drift.

### W05 · Formula correctness — 23 – 29 Nov
- [ ] Hypothesis property tests on all formula modules
- [ ] SI/FPS unit-system guards
- [ ] Significant-figure + rounding rules encoded
- [ ] Input domain validation

**DoD:** zero known silent-failure paths.

### W06 · Code compliance engine — 30 Nov – 6 Dec
- [ ] Clause-level IRC / IS / AASHTO / EN mapping
- [ ] Load-combination engine (IRC:6 / EN 1990)
- [ ] Calc sheet export citing clauses, with utilisation ratios
- [ ] Traceability matrix: check → clause → test → benchmark

**DoD:** matrix has no gaps.

## Phase 3 · Interoperability & drawing standards

### W07 · Drawing standards & CAD output — 7 – 13 Dec
- [ ] ISO 13567 / IS 962 layer naming, line weights, text heights
- [ ] Standard title block, scales, revision table
- [ ] Deterministic DXF (byte-identical for identical input)
- [ ] PDF/A-1b export, veraPDF validated

**DoD:** DXF opens clean in AutoCAD, BricsCAD and LibreCAD; drawing diffs gated.

### W08 · Interoperability — 14 – 20 Dec
- [ ] IFC 4.3 export via ifcopenshell
- [ ] Excel BOQ with live formulas
- [ ] JSON project schema documented
- [ ] Importer fuzzing

**DoD:** round-trip export → import → compare for every format, loss budget defined.

### W09 · Data model & versioning — 21 – 27 Dec
- [ ] Pydantic v2 project model
- [ ] Schema version field + migration engine
- [ ] `.bcad` container spec published
- [ ] Autosave + crash recovery

**DoD:** forward/backward migrations pass; corrupted file recovers.

## Phase 4 · Platform hardening, security & performance

### W10 · API & platform hardening — 28 Dec – 3 Jan
- [ ] `/v1` API + published OpenAPI
- [ ] Auth (JWT/OAuth2), RBAC, rate limits, idempotency
- [ ] Node/Express layer removed or explicitly scoped
- [ ] Contract tests + k6 load test to p95 budget

**DoD:** no undocumented endpoints.

### W11 · Security, privacy, compliance — 4 – 10 Jan
- [ ] SAST + dependency + container scanning
- [ ] CycloneDX SBOM per release, signed artifacts
- [ ] DSC digital signature on issued PDFs
- [ ] Threat model + DPDP Act 2023 / GDPR note

**DoD:** zero high/critical CVEs.

### W12 · Performance & reliability — 11 – 17 Jan
- [ ] Published performance budgets
- [ ] Benchmarks gated in CI
- [ ] Structured logs + error tracking
- [ ] Backup/restore drill, capacity limits documented

**DoD:** a regression beyond threshold fails the build.

## Phase 5 · Release engineering, compliance & launch

### W13 · UX, accessibility, packaging — 18 – 24 Jan
- [ ] WCAG 2.2 AA audit ≥ 90
- [ ] i18n: English + Hindi, all strings externalised
- [ ] Code-signed Windows installer
- [ ] Offline / desktop mode validated

**DoD:** installer installs on a clean Windows VM.

### W14 · Docs, DX, governance — 25 – 31 Jan
- [ ] Docs site built in CI
- [ ] Verification manual published
- [ ] CONTRIBUTING, ADRs, semver + changelog automation
- [ ] Deprecation policy, support SLA

**DoD:** a new contributor ships a change in under a day.

### W15 · v1.0 release & certification — 1 – 7 Feb
- [ ] Signed `v1.0.0` tag + SLSA provenance
- [ ] Three external projects validated end-to-end
- [ ] Independent checker sign-off
- [ ] Case study + published benchmark table

**DoD:** written sign-off from an independent engineer.

---

## Scoreboard

| Metric | W03 | W08 | W15 |
|---|---|---|---|
| Coverage (core / overall) | 30% / 20% | 60% / 45% | 85% / 70% |
| V&V benchmarks passing | 0 | 15 | 30+, in tolerance |
| CI runtime | < 10 min | < 12 min | < 12 min |
| High/critical CVEs | unknown | 0 | 0 |
| Fresh clone → running | broken | one command | one command |
| Clause-cited checks | 0% | 50% | 100% |

## Trim order if behind

W13 desktop bundle → W11 container scanning → W10 load test → W8 DWG.
**Never trim W04, W05, W06, W15.**

## Risks

| Risk | Mitigation |
|---|---|
| W09–W10 land on holidays | Front-load W09; keep W10 to API + auth only |
| mypy on 5k untyped LOC stalls | Strict only on `packages/` core; legacy relaxed |
| Solo bandwidth | Cut scope, never cut verification |
| Benchmark data unavailable | Textbook + hand calcs first, cross-tool later |
