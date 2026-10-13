# BridgeCAD Enterprise Suite — SKELETON (M0 Scaffold)

> Auto-generated. Root: `BridgeCAD Enterprise Suite/`
> Exit criteria M0: `make lint`, `make test`, `make dev` run (exit 0).

```
BridgeCAD Enterprise Suite/
├── 00_REPORT_Trust_Assessment_and_Synthesis.md      ✅  (saved draft report)
├── 01_ACTION_PLAN_M0_to_M10.md                      ✅  (saved action plan)
├── pyproject.toml                                    ✅  (monorepo root / tooling)
├── Makefile                                          ✅  (20+ targets)
├── docker-compose.yml                                ✅  (api+db+cache+storage+worker+jaeger)
├── .env.example                                      ✅  (40+ env vars)
├── .gitignore                                        ✅  (Python/Node/IDE/Secrets)
│
├── apps/
│   ├── streamlit-ui/                                 ✅  (M0: 15-tab placeholder UI)
│   │   ├── pyproject.toml
│   │   └── app.py
│   │
│   ├── web-console/                                  ✅  (React + Vite + TS + Tailwind)
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json / tsconfig.node.json
│   │   ├── tailwind.config.js / postcss.config.js
│   │   ├── index.html
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── index.css
│   │       └── App.tsx
│   │
│   ├── cli-console/                                  ✅  (Typer 20+ stub commands)
│   │   ├── pyproject.toml
│   │   └── bridgecad_cli/
│   │       ├── __init__.py
│   │       └── main.py
│   │
│   └── api-gateway/                                  ✅  (FastAPI 5 routers + health)
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── bridgecad_api/
│           ├── __init__.py
│           └── main.py
│
├── packages/
│   ├── bridgecad-core/                               ✅  (types + 14-sheet models + 150 rules)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_core/
│   │   │   ├── __init__.py
│   │   │   ├── types.py
│   │   │   ├── models.py                              (BridgeProject + 13 sub-models)
│   │   │   ├── validation.py                          (RulesEngine, ValidationReport)
│   │   │   ├── quantities.py                          (BillOfQuantities, extract_quantities)
│   │   │   ├── costs.py                               (RateLookup, compute_cost)
│   │   │   ├── geometry/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── plan.py
│   │   │   │   ├── long_section.py
│   │   │   │   ├── cross_section.py
│   │   │   │   └── foundation.py
│   │   │   └── standards/
│   │   │       ├── __init__.py
│   │   │       ├── irc_sp55.py
│   │   │       ├── irc_05.py
│   │   │       ├── irc_21.py
│   │   │       └── morth_specs.py
│   │   └── tests/__init__.py
│   │
│   ├── bridgecad-io/                                 ✅  (Excel + CSV + JSON)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_io/
│   │   │   ├── __init__.py
│   │   │   ├── excel_template.py
│   │   │   ├── excel_reader.py
│   │   │   ├── excel_writer.py
│   │   │   ├── csv_adapter.py
│   │   │   └── json_adapter.py
│   │   └── tests/__init__.py
│   │
│   ├── bridgecad-draw/                               ✅  (5 engines × 7 sheets)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_draw/
│   │   │   ├── __init__.py
│   │   │   ├── primitives.py
│   │   │   ├── titleblocks.py
│   │   │   ├── layers.py
│   │   │   ├── booklet.py
│   │   │   ├── engines/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dxf_engine.py / svg_engine.py / pdf_engine.py
│   │   │   │   ├── png_engine.py / three_engine.py
│   │   │   └── sheets/
│   │   │       ├── __init__.py
│   │   │       ├── sheet1_plan.py  ..  sheet7_bill_of_quantities.py
│   │   └── tests/__init__.py
│   │
│   ├── bridgecad-plugins/                            ✅  (registry + 10 plugins)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_plugins/
│   │   │   ├── __init__.py
│   │   │   ├── registry.py / runner.py / installer.py / manifest_schema.py
│   │   │   └── plugins/
│   │   │       ├── rcc_tbeam/        manifest.json, draw_overrides.py, defaults.yaml
│   │   │       ├── psc_igirder/      (same triple)
│   │   │       ├── psc_boxgirder/
│   │   │       ├── solid_slab/
│   │   │       ├── voided_slab/
│   │   │       ├── arch_bridge/
│   │   │       ├── steel_composite/
│   │   │       ├── box_culvert/
│   │   │       ├── pipe_culvert/
│   │   │       └── cable_stayed/
│   │   └── tests/__init__.py
│   │
│   ├── bridgecad-bill/                               ✅  (rates DB + processor + 4 formatters)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_bill/
│   │   │   ├── __init__.py
│   │   │   ├── models.py / rates_db.py / processor.py / statements.py
│   │   │   └── formatters/
│   │   │       ├── __init__.py
│   │   │       ├── excel_formatter.py / pdf_formatter.py
│   │   │       ├── html_formatter.py / csv_formatter.py
│   │   └── tests/__init__.py
│   │
│   ├── bridgecad-qa/                                 ✅  (rules + compliance + reports + recs)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_qa/
│   │   │   ├── __init__.py
│   │   │   ├── rules_engine.py / compliance.py
│   │   │   ├── reports.py / recommendations.py
│   │   └── tests/__init__.py
│   │
│   ├── bridgecad-export/                             ✅  (orchestrator + ZIP + versioner)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_export/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py / bundler.py / booklet.py / versioner.py
│   │   └── tests/__init__.py
│   │
│   ├── bridgecad-ai/                                 ✅  (optimizer / estimator / comparator / suggester)
│   │   ├── pyproject.toml
│   │   ├── bridgecad_ai/
│   │   │   ├── __init__.py
│   │   │   ├── optimizer.py / estimator.py / comparator.py / param_suggester.py
│   │   └── tests/__init__.py
│   │
│   └── bridgecad-infra/                              ✅  (DB / cache / queue / storage / log / metrics / auth)
│       ├── pyproject.toml
│       ├── bridgecad_infra/
│       │   ├── __init__.py
│       │   ├── db.py / repositories.py / cache.py / queue.py / storage.py
│       │   ├── logging_setup.py / metrics.py / auth.py
│       └── tests/__init__.py
│
├── templates/                                        ✅  (5 dirs × 5 variants each = 25 planned)
│   ├── minor_bridges/
│   ├── major_bridges/
│   ├── viaducts/
│   ├── culverts/
│   └── robs_rubs_fobs/
│
├── standards/                                        ✅  (rulebooks YAML + state overrides)
│   ├── irc_sp55_drawing.yaml
│   ├── irc_05_hydraulic.yaml
│   ├── irc_21_structural.yaml
│   ├── morth_rates_2024.yaml                         (15 seed items)
│   ├── state_pwd_multipliers.yaml                    (MH/GJ/RJ/KA/UP/TN)
│   └── state_pwd_overrides/
│
├── tests/                                            ✅  (e2e / integration / benchmarks)
│   ├── conftest.py
│   ├── e2e/
│   │   ├── __init__.py
│   │   └── fixtures/
│   ├── integration/
│   │   └── __init__.py
│   └── benchmarks/
│       └── __init__.py
│
├── migrations/                                       ✅  (alembic scaffold)
│   ├── alembic.ini
│   └── versions/
│
├── docs/                                             ✅  (sphinx placeholder)
│   └── README.txt
│
└── scripts/                                          ✅  (repo tooling)
    ├── m0_scaffold_packages.py                       (generator used by this build)
    ├── scaffold_plugin.py                            (create new plugin)
    ├── lint_standards.py                             (lint YAML rulebooks)
    └── regression_test_suite.py                      (M9 E2E runner placeholder)
```

---

### M0 Health Check (run after cloning)

```bash
cd "BridgeCAD Enterprise Suite"

# 1. Verify scaffold tree (match above)
find . -maxdepth 3 -type d | sort           # on *nix
# or: python scripts\m0_scaffold_packages.py --dry-run (idempotent)

# 2. Lint / typecheck stubs
make lint                                    # ruff → exit 0
make typecheck                               # mypy → exit 0 (or warn on empty)

# 3. Unit + integration tests
make test                                    # pytest → exit 0 (no tests yet)

# 4. CLI "dev" smoke (prints version + codename)
make dev
# Expected: 🌉 BridgeCAD 0.1.0  codename: BRIDGECAD-OSS-1.0

# 5. FastAPI health (optional: pip install -e apps/api-gateway first)
#    make api → visit http://localhost:8000/health → {"status":"ok", ...}
```

### Next: M1 Core Domain (3 weeks)

Proceed per `01_ACTION_PLAN_M0_to_M10.md` → M1 (enums / pydantic / 150 rules / geometry).
