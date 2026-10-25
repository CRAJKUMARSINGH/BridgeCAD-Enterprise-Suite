# Standards coverage

Which standards the engine enforces, where each is wired in, and how to add a
rule. Engineering correctness lives here.

## Coverage

| Standard | Scope | Enforced in | State |
|---|---|---|---|
| IRC:5 | Road bridges — general features | geometry, validation, QA | ✅ |
| IRC:6 | Loads and load combinations | validation, QA | ✅ |
| IRC:21 | Concrete bridge design | validation, span/depth | ✅ |
| IRC:83 | Bearings | bearing schedule, QA | ✅ |
| IRC:SP:55 | Drawing practice, layers | 53 layer definitions | ✅ |
| IRC:SP:114 | Seismic design | zone presets, QA | ✅ |
| MORTH 2024-25 | Schedule of rates | BOQ pricing | ✅ |

## Where it lives

```
packages/bridgecad-core/bridgecad_core/standards/
├── irc_sp55.py        layer + drawing practice
├── irc_05.py          hydraulic
├── irc_21.py          structural
└── morth_specs.py     rate schedules
standards/
├── irc_sp55_drawing.yaml
├── irc_05_hydraulic.yaml
├── irc_21_structural.yaml
├── morth_rates_2024.yaml
├── state_pwd_multipliers.yaml
└── state_pwd_overrides/
```

Python modules hold logic; YAML holds data. Changing a rate or a table means
editing YAML, not Python.

## Key limits

- **Span/depth**: $$10 \le L/d \le 20$$ — enforced in the validator *and* the
  optimiser. Violations are critical, not warnings.
- **Freeboard**: checked against HFL per IRC:5.
- **Scour**: computed and compared; the foundation must clear it.
- **Camber**: parabolic, per IRC:112 Clause 6.5.
- **Seismic**: zone presets drive the load combination set.

## Owner presets

NHAI, PWD, MORTH and RAILWAY presets exist — they adjust freeboard, parapet
height, cross-fall, drainage spacing and per-lane width. Select in
`ProjectMaster`. Presets adjust *within* IRC limits; they never override a
critical rule.

## Rate schedule

`standards/morth_rates_2024.yaml` — 90 seeded items across chapters 300, 401,
500, 600, 800, 1600, 1700, 1800, 2400, 2500–2900. Lookup order:

1. State PWD override (`state_pwd_overrides/<state>.yaml`)
2. State multiplier (`state_pwd_multipliers.yaml`)
3. MORTH base rate

The rate source is recorded per line — `MORTH_2024_25`, `PWD_OVERRIDE`, or
`missing`. Never infer a rate silently.

## Rule tiers

150 rule specs: **25 critical · 75 warning · 50 info**. 30 implemented.

- **Critical** — fails the design. Structural, hydraulic, geometric.
- **Warning** — passes but is out of typical range. Needs engineer judgement.
- **Info** — advisory.

Compliance is a weighted 0–100 score with sub-scores for IRC:5, IRC:112 and
IRC:SP:55, graded A+ → F.

## Adding a rule

```python
# packages/bridgecad-core/bridgecad_core/validation_registry.py
RuleSpec(
    id="V151",
    tier="critical",
    standard="IRC:112",
    clause="12.2",
    description="Deck slab thickness must be >= 200 mm for the given span.",
    implemented=True,
)
```

Then implement `check_v151(project) -> Finding` in `validation.py` and add both
a passing and a failing fixture. Rules are **registered before implemented** —
a registered-but-stubbed rule beats an undocumented heuristic.

Rule IDs are permanent. Never renumber; deprecate and add.

## Tolerance policy

A rule may only claim `verified` once an engineer has approved its tolerance
against reference output. Until then it is `estimated`. This distinction shows
up in the QA report and the manifest.

## Sources of truth

`sample-gad-drawings/` holds the reference corpus — 28 GAD drawings the E2E
fixtures are derived from. When a rule and a reference drawing disagree, the
drawing wins and the rule gets a bug report.
