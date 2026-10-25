# The Excel contract

One workbook. 14 sheets. 427 mapped fields. This is the only external contract
in the system — everything downstream reads `BridgeProject`, which this file
defines the shape of.

**Never hand-build a workbook.** Generate one:

```bash
bridgecad-cli template new --type <type> -o bridge.xlsx
```

## Sheet set

| # | Sheet | Purpose | Required |
|---|---|---|---|
| 1 | ProjectMaster | identity, client, location, revision | ✅ |
| 2 | BridgeSelection | bridge category, type, plugin target | ✅ |
| 3 | GeometryInput | spans, skew, width, levels | ✅ |
| 4 | Superstructure | girder/slab, camber, wearing course | ✅ |
| 5 | Substructure | piers, abutments, caps | ✅ |
| 6 | FoundationDetails | footing / pile / well, dimensions | ✅ |
| 7 | Approaches | embankment, protection works | ○ |
| 8 | HydraulicData | HFL, LWL, scour, freeboard | ✅ |
| 9 | Materials | concrete grade, steel grade, prestress | ✅ |
| 10 | BearingsJoints | bearing schedule, expansion joints | ○ |
| 11 | ComponentsLib | reusable component definitions | ○ |
| 12 | DrawingControl | scales, sheet sizes, title block fields | ○ |
| 13 | Calculations | derived values, locked | ○ |
| 14 | ValidationModel | rule toggles, tolerance overrides | ○ |

✅ required · ○ has IRC-derived defaults

## Minimum viable input

A valid workbook needs: span count, span lengths, skew, carriageway width, deck
levels (sheet 3); HFL, LWL, scour (sheet 8); foundation type and dimensions
(sheet 6); concrete and steel grade (sheet 9). Everything else defaults from
IRC proportioning rules.

## Cell conventions

- **Yellow** — input. Editable.
- **Grey, locked** — calculated. Do not edit; it will be overwritten.
- Dropdowns are enum-backed. Off-list values are rejected, not coerced.
- Numeric validation is per-cell, with units enforced by column name suffix.

## Units — non-negotiable

Units are in the field name. `_m` metres, `_mm` millimetres, `_kn` kilonewtons,
`_mpa` megapascals, `_deg` degrees. A field with no suffix is dimensionless or a
count. Mixed-unit fields are a bug.

## Field naming

`span_length_1 … span_length_n` for repeated fields. Readers fall back through
the `span_length_N` pattern, so a workbook with `span_length_1` only still
parses. `SPAN1`-style legacy names are accepted for the legacy app only.

## Validation states

Parsing returns one state per field, before any heavy work:

| State | Meaning | Action |
|---|---|---|
| `valid` | in range, correct type | none |
| `warning` | parses, outside typical range | review |
| `blocked` | missing or wrong type | must fix |
| `unsupported` | valid but no engine handles it yet | expect degraded output |

`blocked` fails the parse. `unsupported` never silently degrades — it is
recorded in the manifest.

## Round-trip rule

`Excel → model → Excel` must drift ≤5%, cosmetic only. If a change makes a
workbook fail to round-trip, the change is wrong — even if all tests pass.

Round-trip is tested on one canonical workbook schema across all 25 templates.

## Enum deserialisation

Enums deserialise by exact name first, then by documented alias, then by
int value. Case-insensitive matching applies **only** where the legacy workbook
writer historically lower-cased values. No fuzzy matching.

## Generated templates

Templates are generated, styled, dropdown-validated, and sheet-protected
against calculated-cell edits. 25 are planned (5 categories × 5 variants);
5 exist today. Adding one → [plugin-authoring.md](plugin-authoring.md).

## Changing the schema

1. Add or change the Pydantic field in `bridgecad_core/models.py`
2. Mirror it in `bridgecad_io/excel_template.py` and `excel_reader.py`
3. Add a round-trip test
4. Update this file and the field table
5. Bump the schema version and note it in `CHANGELOG.md`

A schema change without a round-trip test will be sent back.
