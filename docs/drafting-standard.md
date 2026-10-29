# Drafting Standard

Status: **draft, week 50**. Clause citations provisional until the week-45 audit.

This is the human-readable statement of the rules the harness enforces. Where
this document and the code disagree, the code is wrong only if this document is
right — and `scripts/check_drafting_standard.py` fails the build on any
disagreement so nobody has to arbitrate by memory.

Values in the tables below are the authority. The code constants are generated
to match.

---

## 1. Sheet sizes and frames

| Item | Value |
|---|---|
| Sheet size | A1, 841 × 594 mm |
| Frame inset | 20 mm left, 10 mm top/right/bottom |
| Title block | 180 × 65 mm, bottom right |
| Sidebar (notes/legend) | 90 mm, left of the drawing region |

A2 is not used. A0 is not used. A3 is used only for detail sheets already
carrying a `1:10` or finer scale, and only with a stated reason in the sheet
module docstring.

## 2. Text heights

Paper millimetres. Six values exist. Nothing else may appear.

| Class | Height | Use |
|---|---|---|
| `TITLE` | 10.0 | sheet title in the title block |
| `SUBTITLE` | 7.0 | view titles, drawing number |
| `SUBHEAD` | 5.0 | table column headers, section heads |
| `NOTE` | 3.5 | notes, general text |
| `DIM` | 3.5 | dimension text |
| `SMALL` | 2.5 | level values, bar marks, rebar callouts |

The ratio between adjacent sizes is √2. A new size is a decision, not a
convenience.

`TextSizer.h()` is the only way to obtain a height. A literal `2.5` in a sheet
module is a defect.

## 3. Line weights

Paper millimetres, by layer. Set on the layer, never on the entity.

| Weight | Layers |
|---|---|
| 1.00 | `STRUC-OUTLINE`, `SUPER-DECK` (cut edge) |
| 0.70 | `SUB-PIER`, `SUB-ABUT`, `FOUND-CAP`, `FOUND-WELL`, `FOUND-OPEN` |
| 0.50 | `SUPER-KERB`, `SUPER-PARAPET`, `SUPER-WEARING`, `SUB-BEARING`, `SUB-EXPJOINT` |
| 0.35 | `FOUND-PILE`, `STRUC-REBAR`, `STRUC-DETAIL`, `CIVIL-HFL`, `CIVIL-SCOUR` |
| 0.25 | `CIVIL-CHAINAGE`, `TEXT-NOTE`, `TEXT-DIM`, `TEXT-LEVEL` |
| 0.18 | `HATCH-*`, `SYM-*`, `CIVIL-GROUND` |
| 0.13 | `GRID`, `CONSTRUCTION` |

`SYM-*` at 0.18 is deliberately light: symbols must not compete with the
geometry they annotate.

## 4. Layers

Naming: `DISCIPLINE-ELEMENT[-QUALIFIER]`, upper case, hyphen separated.
`SUPER-` deck and above, `SUB-` substructure, `FOUND-` below cap bottom,
`CIVIL-` site and water, `STRUC-` reinforcement and details, `TEXT-`,
`HATCH-`, `SYM-`, `DIM-`, `GRID`, `CONSTRUCTION`.

- One concept per layer. `SUB-PIER` is not `SUB-PIER-AND-CAP`.
- A sheet declares `LAYERS_USED` and uses exactly that set.
- An unused declared layer is a defect, not a spare.
- Colour is by weight, not decoration. No true-colour layers.

## 5. Dimensions

- Native `DIMENSION` entities only. No dimension drawn as lines and text.
- `dimlfac = 1000` everywhere — model is millimetres, dimension text is metres.
- Prefix from the layer: `+` on levels, `CW=` on carriageway, `ø` on bars.
- Text above the dimension line, line unbroken, 2 mm gap.
- 2.5 mm text, 2.5 mm arrow, 0.8 mm arrow size, extension line 1.5 mm beyond
  the dimension line.
- Dimension to the feature, never to a hatch edge or a centreline where a face
  exists.
- Chain dimensions from a single datum. Overall dimension outside the chain.
- Two dimensions of the same feature on two sheets is allowed only where one is
  the controlling dimension and the other is marked `(REF)`.

## 6. Levels

`±0.000` datum, three decimals, always signed except at datum. Level text sits
on `TEXT-LEVEL` with a small triangle marker on `SYM-LEVEL`. A level is not a
dimension and is never dimensioned.

## 7. Hatching

| Material | Pattern | Scale |
|---|---|---|
| Concrete | `ANSI31` | 1.0 |
| Bituminous | `AR-SAND` | 0.5 |
| Earth / backfill | `ANSI37` | 1.5 |
| Rock | `AR-RSHKE` | 2.0 |

Hatch angle 45° except where it would run parallel to the boundary. Hatch on
`HATCH-<material>`, boundary on the geometry layer. Hatch scale changes with
plot scale, never with the model.

## 8. Linetypes

Registered linetypes only, from `linetypes.py`. `CENTER` for centrelines,
`HIDDEN` for buried, `PHANTOM` for protection works and limits of excavation.
Pattern scale is set at 10 paper mm and adjusted by `LTSCALE` only.

## 9. Notes

Format: `N. text (SOURCE)`. Source in brackets, always. `SOURCE` is a clause
from `TRACEABILITY.md`, a borelog ID, a schedule row, or `PROJECT` for a
project-specific decision.

Note numbering restarts per sheet. Notes are grouped: general, materials,
workmanship, testing. A note that applies to one element belongs on the detail,
not in the general notes.

## 10. Scales

Preferred, in order: 1:200, 1:100, 1:50, 1:25, 1:20, 1:10.

- Plans and sections 1:200.
- Cross sections 1:50.
- Foundations and pier details 1:50 / 1:25.
- Bearings and joints 1:10.

`NTS` is legal only for a schematic with a scale bar. Vertical exaggeration is
declared in the title block and carries two scale bars.

## 11. Title block

Twelve mandatory fields. `—` where a field is genuinely unknown. Never a
plausible default.

Revision strip from `revision_history`, newest first, max 5 rows.

## 12. Issue status

`PRELIMINARY` / `FOR REVIEW` / `FOR APPROVAL` / `FOR CONSTRUCTION` / `AS BUILT`.
Present on every sheet. A sheet without it is not issuable.

## 13. Symbols

From `symbols.py` only, one per `SYM-` layer. Symbols are drawn at paper size —
they do not scale with the model. A symbol that needs a legend entry gets one;
a symbol that needs two legend entries is two symbols.

## 14. Break lines

`SYM-BREAK` only. Zig-zag, 3 mm amplitude. On structural members, on strata
with no borelog, and on long runs of uniform section. Not on the deck outline.

## 15. What the harness checks

`dxf_assert.py` enforces sections 1, 2, 4, 5 (`dimlfac`, entity type, count),
9 (`SOURCE` brackets), 10 (declared scale honesty), 11 and 12.

Sections 3, 6, 7, 8, 13 and 14 are enforced only in part. The rest is the
reviewer's job, listed as `MANUAL` rows in the per-sheet checklists.

## 16. Deviations

A deviation needs a line in the sheet module docstring, the reason, and a
`minor` mark against the sheet. Three deviations of the same rule means the rule
is wrong — change the rule in the same commit.
