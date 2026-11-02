# Interoperability and the loss budget

What leaves this suite, what can be read back, and exactly what is lost on the
way. The budget below is enforced by `pytest -q tests/interop`; a format whose
measured loss exceeds its stated budget fails the build.

## What each format is for

| Format | Direction | Read by |
|---|---|---|
| `.bridgecad.json` | round-trip | this suite, the API, any script |
| sub-model `.csv` roster | round-trip | spreadsheets, reviewers, diff tools |
| 14-sheet `.xlsx` workbook | round-trip | design offices, [the Excel contract](excel-contract.md) |
| IFC 4.3 (`.ifc`) | export only | BIM tools (Revit, ArchiCAD, BlenderBIM) |
| DWG (`.dwg`) | export only | AutoCAD / BricsCAD, via the ODA File Converter |

Round-trip means: write the project, read it back with the matching reader in
`bridgecad-io`, and compare the two model dumps field by field. The comparison
is numeric, so `350` and `350.0` are the same value.

## Loss budget

| Format | Direction | Budget | Enforced by |
|---|---|---|---|
| JSON | round-trip | **zero loss** — every declared field | `test_json_round_trip_is_lossless` |
| CSV | round-trip | **zero loss** — every declared field | `test_csv_round_trip_is_lossless` |
| Excel | round-trip | **zero loss** — every declared field | `test_excel_round_trip_is_lossless` |
| IFC 4.3 | export only | geometry only; no design-analysis parameters | `test_ifc_export_passes_the_express_rule_validator` |
| DWG | export only | byte conversion of the DXF; no model loss | `test_dwg_export_converts_or_explains_what_is_missing` |

### Why Excel is lossless rather than "within 5%"

[GUIDE.md](../GUIDE.md) §4 sets the floor at ≤5%, cosmetic drift only. This
suite does better and holds itself to it:

- The writer derives the rows it emits from the Pydantic model
  (`model_fields` + the shared `_fields` codec), and the reader parses the same
  field set through the same codec. Both sides therefore agree **by
  construction** — there is no hand-maintained column list to drift.
- Calculated fields (`calculations`, `validation`) are engine-owned outputs.
  A workbook's copies of them are rewritten by the engine on the next run, so
  they are excluded from the input contract on both sides.
- Numeric cells carry a *spelling* as well as a value. Excel stores `350.0`,
  JSON stores `"350"` and both mean the same quantity; the budget is stated on
  the number, not on the text.

## The published JSON schema

`.bridgecad.json` is governed by a published JSON Schema (Draft 2020-12),
`docs/schema/bridgeproject.schema.json`. It is generated from the Pydantic
model rather than written by hand, so it cannot drift away from the reader that
has to accept it:

```bash
python scripts/export_project_schema.py --check   # exit 1 if the schema is stale
```

## Malformed input contract

A truncated or corrupt import must produce a typed error, never a bare
traceback. Every importer in `bridgecad-io` answers with
`JsonParseError` / `CsvParseError` / `ExcelParseError`, each of which:

- inherits from `BridgeCADError`, so a caller can catch the whole family;
- names the file that failed;
- carries a `suggestion` a human can act on.

`tests/interop/test_fuzz.py` fuzzes all three importers with arbitrary and
truncated payloads and fails if any of them leaks an internal `zipfile`, `json`
or Pydantic exception.

## Running the lane

```bash
uv pip install -e ".[dev,ifc,draw]" openpyxl
pytest -q tests/interop
```

`ifcopenshell` (the `ifc` extra), `ezdxf` (the `draw` extra), the ODA File
Converter and a licensed DWG reader are all optional. A missing optional
component **skips** its test with the reason printed — a skip is never a silent
pass.

## Related

- [excel-contract.md](excel-contract.md) — the 14-sheet workbook, sheet by sheet
- [api-reference.md](api-reference.md) — `bridgecad-io` public surface
- [drafting-standard.md](drafting-standard.md) — what the DXF and DWG carry
