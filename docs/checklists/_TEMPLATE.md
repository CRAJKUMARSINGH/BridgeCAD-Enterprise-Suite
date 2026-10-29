# Sheet {N} — {TITLE} — review checklist

**Sheet key:** `{FRAME_KEY}` · **Scale:** {SCALE} · **Module:** `{MODULE}`
**Required before review:** every `AUTO` and `SCRIPT` row `☑`.

## A. Frame and scale

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| A1 | Geometry lies inside the declared frame | `inside_frame` | AUTO | ☐ |
| A2 | Declared scale matches drawn extent, or sheet reads NTS with a scale bar | `scale_honest` | AUTO | ☐ |
| A3 | Paper-space layout exists and viewport is at the declared scale | `viewport_scale` | AUTO | ☐ |
| A4 | No duplicated geometry | `no_duplicate_geometry` | AUTO | ☐ |
| A5 | No zero-length lines | `no_zero_length_lines` | AUTO | ☐ |

## B. Title block and issue

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| B1 | All 12 mandatory fields populated | `title_block_complete` | AUTO | ☐ |
| B2 | Sheet number and total match the manifest | `sheet_numbering` | AUTO | ☐ |
| B3 | Issue status block present and non-empty | `issue_status_present` | AUTO | ☐ |
| B4 | Revision strip drawn from revision history | `MANUAL: revision strip has no assertion yet` | MANUAL | ☐ |
| B5 | Scale cell reads the true ratio or `NTS` — not blank, not guessed | `MANUAL: TB text content beyond presence` | MANUAL | ☐ |

## C. Text and dimensions

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| C1 | Every text height from the six legal paper values | `text_heights` | AUTO | ☐ |
| C2 | ≥ 10 native DIMENSION entities | `dimension_count` | AUTO | ☐ |
| C3 | Every dimension carries `dimlfac` 1000 | `dimension_scale` | AUTO | ☐ |
| C4 | Every note line carries a bracketed source | `notes_sourced` | AUTO | ☐ |
| C5 | Dimension text legible at A1 without zoom | `MANUAL: legibility at print size` | MANUAL | ☐ |

## D. Content

{CONTENT_ROWS}

## E. Layers

{LAYER_ROWS}

## F. Cross-sheet

{CROSS_ROWS}

## Sign-off

| | |
|---|---|
| Reviewer (chartered/equiv., independent of author) | |
| Date | |
| Blocker marks raised | |
| Residual `major`/`minor` accepted, with rationale | |
| Signed | ☐ |

> Reviewed at A1 on paper against the cited clauses. Geometry, dimensions,
> levels, notes and title block are fit to issue for the stated purpose.
