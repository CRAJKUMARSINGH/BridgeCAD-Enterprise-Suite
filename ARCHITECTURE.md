# Architecture

> **Status:** W01 deliverable · verified 2026-10-29 against `main`.
> **Authority:** [GUIDE.md §3](GUIDE.md) wins every conflict. This page is the
> short, navigable view — components, data flow, boundaries, ownership.

## 1. System context

**One parametric Excel workbook in. A 7-sheet standards-compliant bridge GAD
package, a priced Bill of Quantities, and a QA compliance report out.**

```
Excel workbook
   │
   ▼
bridgecad_io ──► BridgeProject (Pydantic v2, single in-memory truth)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
  bridgecad_draw  bridgecad_bill  bridgecad_qa
   7 DXF sheets    priced BOQ      150 rules → grade
        └─────────────┼─────────────┘
                      ▼
              bridgecad_export ──► ZIP + manifest.json
```

The Suite lives at the **repository root**; there is no subfolder to descend
into. Legacy generators (`streamlit_app_ultimate.py`, `src/bridge_gad/`) are
fenced off and labelled LEGACY in [README.md](README.md).

## 2. Packages

| Package | Responsibility |
|---|---|
| `bridgecad-core` | enums, Pydantic models, geometry maths, validation, quantities |
| `bridgecad-io` | Excel template / reader / writer, CSV + JSON adapters |
| `bridgecad-draw` | layers, primitives, title blocks, 7 sheets, engines, booklet |
| `bridgecad-bill` | MORTH rates DB, hierarchical processor, formatters |
| `bridgecad-qa` | rules engine, compliance scoring, reports, recommendations |
| `bridgecad-export` | orchestrator, ZIP bundler, versioner |
| `bridgecad-plugins` | manifest schema, registry, runner, installer |
| `bridgecad-ai` | optimiser, estimator, comparator, param suggester |
| `bridgecad-infra` | db, repositories, cache, storage, auth, logging |

## 3. Interfaces

| App | Stack | Surface |
|---|---|---|
| `apps/cli-console` | Typer | 10 command groups |
| `apps/api-gateway` | FastAPI | `/bridges` `/draw` `/bills` `/qa` `/exports` `/plugins` `/health` |
| `apps/streamlit-ui` | Streamlit | 15 tabs |
| `apps/web-console` | React + Vite + TS | 6 pages |

Entry point for a zero-install check: `python -m bridgecad`.

## 4. Design invariants — do not break these

1. **`BridgeProject` is the only in-memory truth.** Every consumer reads it.
2. **The Excel workbook is the only external contract.** 14 sheets, 1:1 with
   the Pydantic models.
3. **`bridgecad-core` is a leaf.** It imports no other Suite package.
4. **Draw, Bill and QA never call each other.** Only `bridgecad-export` fans out.
5. **Plugins override drawing behaviour; they never mutate the model.**

## 5. Boundaries — enforced, not documented

Invariants 3–5 are machine-checked. The contract lives in
[import_linter_contract.ini](import_linter_contract.ini) and runs in CI:

| Contract | Rule |
|---|---|
| `core-is-a-leaf` | `bridgecad_core` imports no other Suite package |
| `draw-bill-qa-are-isolated` | `draw` / `bill` / `qa` never import each other or `export` |
| `only-export-fans-out` | only `export` may import `draw` / `bill` / `qa` |

A change that violates a boundary fails the `import-linter` CI job before merge.

## 6. Ownership

Code ownership is declared in [.github/CODEOWNERS](.github/CODEOWNERS):
design invariants and standards need the strongest review; docs governance
keeps "one fact, one place".

## 7. Extending the Suite

- **New bridge type** → author a plugin: [docs/plugin-authoring.md](docs/plugin-authoring.md).
- **New QA rule** → register it in `bridgecad_qa`; see [docs/standards.md](docs/standards.md).
- **New drawing sheet** → follow [docs/drafting-standard.md](docs/drafting-standard.md).

## 8. Where the truth lives

| Question | Authoritative source |
|---|---|
| Entry points, versions, paths | [GUIDE.md](GUIDE.md) |
| Every doc, indexed | [DOCS_INDEX.md](DOCS_INDEX.md) |
| What may and may not be claimed | [GUIDE.md §11](GUIDE.md) |

Verified against `main` on **2026-10-29**. If this page disagrees with
[GUIDE.md](GUIDE.md), the guide wins.
