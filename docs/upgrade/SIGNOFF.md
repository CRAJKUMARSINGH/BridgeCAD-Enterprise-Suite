# Engineer Sign-Off

One row per bridge family. A family is signed only after the reviewer has seen
all 8 sheets of that golden case **printed at A1** and has logged every mark in
`DEFECT-LEDGER.md`.

Reviewer must be a chartered or equivalent bridge engineer independent of the
code author.

| Family | Golden case | Sheets reviewed | Blocker marks open | Signed | Reviewer | Date |
|---|---|---|---|---|---|---|
| RCC slab, single span | `simple_12m` | 8 | | ☐ | | |
| RCC slab, continuous | `continuous_3x12m` | 8 | | ☐ | | |
| PSC girder | `girder_4x18m` | 8 | | ☐ | | |
| Box culvert | `box_culvert_8m` | 8 | | ☐ | | |
| Skew 15° | `skew_15deg` | 8 | | ☐ | | |

## Sign-off statement

> I have reviewed the sheets listed above at A1 against IRC:5, IRC:6, IRC:21,
> IRC:78, IRC:83, IRC:SP:55 and IRC:SP:114. The geometry, dimensions, levels,
> notes and title blocks are, in my professional judgement, fit to be issued for
> the purpose stated on each sheet. Residual `major` and `minor` marks are logged
> in the defect ledger and do not prevent issue.

Reviewer signature: ______________________  Date: __________

## Revocation

A family's tick is cleared if a change to `bridgecad_draw/sheet*.py` or
`bridgecad_core/geometry/**` alters that family's golden package beyond the
visual tolerance. The visual regression job flags the change; a human clears the
tick.
