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
