# Contributing to BridgeCAD Enterprise Suite

Thanks for helping. This project is engineering software — correctness beats
cleverness, and traceability beats speed.

**Before you start:** read [GUIDE.md](GUIDE.md) §3 (design invariants) and §11
(what you may and may not claim). Contributions that break an invariant will be
asked to change regardless of how good they are otherwise.

---

## 1. Setup

```bash
git clone https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite.git
cd BridgeCAD-Enterprise-Suite
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
make lint && make test
```

Pre-commit runs: ruff (lint + format), mypy, bandit, gitleaks,
trailing-whitespace, and commitizen. Do not bypass with `--no-verify` unless you
say why in the PR.

---

## 2. Find something to work on

Good first issues are labelled `good-first-issue`. The highest-value open work
right now, in order:

1. Real geometry for drawing sheets 2–7 (see `GUIDE.md` §12, Phase 2)
2. Traceable BOQ — replace heuristic multipliers with sourced quantities
3. Implement the 120 stubbed QA rules in `validation_registry.py`
4. Upload hardening: size cap, `.xlsx`-only allowlist, RFC 7807 error bodies

Open an issue **before** a large PR so we can agree the approach.

---

## 3. Branch and commit conventions

```
feat/<scope>-<short-desc>      feat/draw-sheet5-wingwall-geometry
fix/<scope>-<short-desc>       fix/io-enum-case-insensitive-lookup
docs/<short-desc>              docs/excel-contract-units
chore/<short-desc>             chore/pin-ruff-version
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
(enforced by commitizen). Scope is the package name without the prefix:
`core`, `io`, `draw`, `bill`, `qa`, `export`, `plugins`, `ai`, `infra`, `cli`,
`api`, `ui`, `web`, `docs`, `ci`.

```
feat(draw): add wing wall geometry to sheet5 pier/abutment details
fix(io): case-insensitive enum lookup for legacy lowercased workbooks
docs(guide): document the 7-sheet scaffold limitation
```

Breaking changes: add `!` and a `BREAKING CHANGE:` footer.

---

## 4. Code standards

- **Python 3.11+**, full type hints on public functions. mypy must pass.
- **ruff** for lint and format. Line length per `pyproject.toml`.
- **No new runtime dependency** in `bridgecad-core` — it is the leaf package.
- **Pydantic v2** for all data models. No bare dicts crossing package boundaries.
- Docstrings on every public module, class and function. Say *why*, not *what*.
- Pure functions in `geometry/`. No I/O, no globals, no side effects.
- Units in the name when ambiguous: `span_length_m`, `width_mm`, `load_kn`.

### Hard rules

1. `BridgeProject` is the only in-memory truth. Do not introduce a parallel model.
2. Drawing, billing and QA never import each other. Only `export` fans out.
3. A change that breaks an Excel round-trip is wrong, even if tests pass.
4. Missing input returns an explicit `not_calculated` with a reason. Never
   silently substitute a plausible default.

---

## 5. Tests

Every PR needs tests. Minimum bar:

| Change | Required |
|---|---|
| New geometry function | unit test with hand-computed expected values |
| New QA rule | one passing and one failing fixture |
| New plugin | smoke test producing valid DXF |
| Bug fix | regression test that fails before the fix |
| New export format | round-trip or byte-stability test |

```bash
make test                      # unit
pytest tests/integration       # full pipeline
python tests/e2e/run_e2e.py    # 28 fixtures
python rc1_smoke.py            # release gate
```

Benchmarks matter: QA < 200 ms, BOQ < 500 ms, one sheet < 3 s, seven sheets
< 15 s. If your change pushes past those, say so in the PR.

---

## 6. What CI runs

Both workflows run in parallel on every push and PR:

- `suite-ci.yml` — 6 jobs: lint, typecheck, unit, e2e, rc1-smoke, react-build
- `ci.yml` — legacy app: lint, tests, PII scan, dependency audit

The PII scan is strict. **Do not commit personal contact details** — email
addresses or phone numbers — into tracked source. Route contact through GitHub
issues and tag `support` or `rks-legal`.

A red CI is never merged. If a job is flaky, fix the flake, don't retry-loop it.

---

## 7. Adding a package

1. Create `packages/bridgecad-<name>/` with `pyproject.toml`, `bridgecad_<name>/__init__.py`, `tests/__init__.py`
2. Register it in the root workspace config
3. Declare dependencies — keep the graph acyclic
4. Add the package to the `GUIDE.md` package map
5. Add a CI job if it needs its own matrix entry

## 8. Adding a plugin

See **[docs/plugin-authoring.md](docs/plugin-authoring.md)**.

## 9. Adding a QA rule

Rules live in `packages/bridgecad-core/bridgecad_core/validation_registry.py`
as `RuleSpec` entries, tiered critical / warning / info, with a stable ID
(`V001`–`V150`). Register first, implement second — a registered-but-stubbed
rule is better than an undocumented heuristic.

## 10. Documentation rules

Two rules keep our docs from drifting:

1. **One fact, one place.** Entry points, versions and paths live in `GUIDE.md`
   only. Other docs link to it. Every contradiction in this repo's history came
   from a restated fact.
2. **Retire, don't fork.** When a doc is superseded, delete it or move it to
   `archive/`. Never leave `X.md` and `X_NEW.md` side by side.

If your PR changes behaviour, update the doc in the same PR. A PR that changes
behaviour and not docs is incomplete.

---

## 11. Pull request checklist

- [ ] Branch name follows the convention
- [ ] Commits are conventional and atomic
- [ ] `make lint && make test` pass locally
- [ ] New code has tests; bug fixes have a regression test
- [ ] `python tests/e2e/run_e2e.py` still passes 28/28
- [ ] No new dependency in `bridgecad-core`
- [ ] Design invariants respected (GUIDE.md §3)
- [ ] Docs updated in the same PR
- [ ] No PII committed
- [ ] PR description states what changed, why, and how it was verified

---

## 12. Review

One maintainer approval required. Expect first response within a week.
Reviewers check correctness, invariant adherence, test quality and doc impact —
in that order. Nitpicks are labelled `nit:` and are optional.

---

## 13. Questions

Open an issue and tag it `support`. Professional-services and legal enquiries:
tag `rks-legal`.
