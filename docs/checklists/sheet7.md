# Sheet 7 — BILL OF QUANTITIES — review checklist

**Sheet key:** `sheet7_bill_of_quantities` · **Scale:** 1:1 (table) · **Module:** `sheet7_bill_of_quantities.py`
**Required before review:** every `AUTO` and `SCRIPT` row `☑`.

## A. Frame

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| A1 | Table inside frame, nothing clipped | `inside_frame` | AUTO | ☐ |
| A2 | No duplicated geometry | `no_duplicate_geometry` | AUTO | ☐ |

## B. Title block and issue

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| B1 | All 12 mandatory fields | `title_block_complete` | AUTO | ☐ |
| B2 | Numbering matches manifest | `sheet_numbering` | AUTO | ☐ |
| B3 | Issue status present — a BOQ issued as final must say so | `issue_status_present` | AUTO | ☐ |
| B4 | Revision strip | `MANUAL: no assertion` | MANUAL | ☐ |

## C. Text

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| C1 | Legal text heights only | `text_heights` | AUTO | ☐ |
| C2 | Notes sourced | `notes_sourced` | AUTO | ☐ |
| C3 | Column headers unambiguous, units stated | `MANUAL: header check` | MANUAL | ☐ |

## D. Provenance — the whole point of this sheet

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | Every line has a status | `scripts/check_boq_provenance.py` | SCRIPT | ☐ |
| D2 | Every `estimated` line carries a multiplier and a source note | `scripts/check_boq_provenance.py` | SCRIPT | ☐ |
| D3 | Every `calculated` line carries a formula and source fields | `scripts/check_boq_provenance.py` | SCRIPT | ☐ |
| D4 | Every `not_calculated` line carries a reason and no amount | `scripts/check_boq_provenance.py` | SCRIPT | ☐ |
| D5 | Estimated fraction under the stage ceiling | `scripts/check_boq_provenance.py` | SCRIPT | ☐ |
| D6 | No formwork multiplier remains | `MANUAL: factor audit` | MANUAL | ☐ |
| D7 | No rebar t/cum ratio remains | `MANUAL: factor audit` | MANUAL | ☐ |

## E. Arithmetic

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| E1 | Line amounts = quantity × rate | `MANUAL: arithmetic spot-check` | MANUAL | ☐ |
| E2 | Subtotals and totals add up | `MANUAL: total check` | MANUAL | ☐ |
| E3 | No negative quantity | `MANUAL: sign check` | MANUAL | ☐ |
| E4 | Backfill ≤ excavation | `MANUAL: earthwork check` | MANUAL | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
