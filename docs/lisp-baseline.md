# LISP baseline audit

The suite began as an AutoLISP solid-slab GAD. The enhancement diluted the
geometric basis; this page records where, so the dilution is bounded rather
than discovered one defect at a time.

Run `python scripts/refs_lisp.py references/lisp/*.lsp` first — the inventory
answers columns 2 and 5 mechanically.

| # | Question | LISP | Suite today | Disposition |
| --- | --- | --- | --- | --- |
| 1 | Is deck top derived from road level minus wearing coat, or is the coat a separate band? | — | coat separate since the cap/dirt-wall fix | restored |
| 2 | Is the dirt wall placed off the cap rear or off the shaft? | — | cap rear | restored |
| 3 | Does the coat terminate at the approach-slab end or the deck end? | — | approach-slab end | restored |
| 4 | Are cap depth and projection parameters or constants? | — | parameters on `Substructure` | restored |
| 5 | Are layers emitted from a table or inline? | — | table (`layers.py`) | no defect |

Disposition values: `restored`, `superseded (reason)`, `no defect`,
`still open`.

Rows 1–3 are geometry; a `superseded` there needs an IRC clause, not an
opinion.

## ATTACHED ASSETS audit and bounded incorporation (2026-11-13)

The checked-in folder contains a preserved .lsp listing, raw article text,
an explanatory Markdown archive and an explicitly derived/unverified module
map. The observed LISP list has 13 functions, not the explanatory archive's
nine-function claim. The derived map must not be used as source evidence for
well, girder or other absent modules.

Run the real archive through the comment-aware inventory without executing it:

```powershell
python scripts/refs_lisp.py "ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp" -o artifacts/lisp_inventory.md
```

The inventory now records SHA-256, excludes comments/string literals from
function detection, reports only assignment targets for setq, and distinguishes
static command occurrences from runtime entity counts. Layer-like strings are
only lexical candidates; their absence does not prove missing geometry.

The core battered_side_outline helper now accepts optional front_break_h_m,
back_break_h_m and toe_batter_1n. They preserve source abt1's independent alfbl,
albbl and altb geometry; zero transition-height defaults retain the old outline.
These new inputs are not yet exposed through the workbook, API, catalogue or
browser controls. Their explicit model/mapper/renderer wiring requires further
fixtures and engineering review. No original asset was changed or executed.

See BRIDGECAD_ATTACHED_ASSETS_LISP_PATCH.md for the source-to-code mapping,
known archive inconsistencies, complete incremental diff and application gates.
