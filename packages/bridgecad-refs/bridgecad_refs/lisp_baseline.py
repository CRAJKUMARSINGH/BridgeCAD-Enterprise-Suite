"""Inventory an AutoLISP GAD source without executing it.

Regex-level only: AutoLISP has no stable grammar worth importing for this, and
the questions the audit asks are lexical — which entities are emitted, which
layers are named, which values are parameters versus constants.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_ENTITY = re.compile(
    r'\(\s*command\s+"(?P<cmd>LINE|PLINE|RECTANG|CIRCLE|TEXT|MTEXT|HATCH|DIMLINEAR|INSERT)"',
    re.IGNORECASE,
)
_LAYER = re.compile(r'"(?P<layer>[A-Z][A-Z0-9_-]*(?:-[A-Z0-9]+)+)"')
_SETQ = re.compile(r"\(\s*setq\b", re.IGNORECASE)
_NUMERIC_LITERAL = re.compile(r"(?<![\w.])(?P<num>-?\d+\.\d+)(?![\w.])")
_DEFUN = re.compile(r"\(\s*defun\s+(?P<name>[^\s()]+)", re.IGNORECASE)

# Entities whose presence the audit cares about, matched against layer names
_GEOMETRY_OF_INTEREST = {
    "wearing_coat": re.compile(r"WEAR|WC|ASPH|SURFAC", re.IGNORECASE),
    "dirt_wall": re.compile(r"DIRT|BACK.?WALL|APPROACH.?WALL", re.IGNORECASE),
    "abutment_cap": re.compile(r"CAP|SHELF|SEAT", re.IGNORECASE),
}


@dataclass
class LispInventory:
    path: str
    defuns: list[str] = field(default_factory=list)
    entity_counts: dict[str, int] = field(default_factory=dict)
    layers: list[str] = field(default_factory=list)
    setq_names: list[str] = field(default_factory=list)
    numeric_literal_count: int = 0
    interest_hits: dict[str, list[str]] = field(default_factory=dict)


def _setq_symbols(text: str) -> list[str]:
    """Symbols bound by each ``(setq ...)`` form.

    ``setq`` takes ``name value`` pairs and values may be nested lists, so a
    flat regex cannot find the form's end.  Scan instead: after ``setq``, walk
    the text tracking paren depth and collect the atoms at depth 1 — those are
    the bound names interleaved with their literal values; numeric atoms and
    nested-list contents are not names.
    """
    names: list[str] = []
    for m in _SETQ.finditer(text):
        i = m.end()
        depth = 1
        token = ""
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == "(":
                depth += 1
                token = ""
            elif ch == ")":
                depth -= 1
                token = ""
            elif depth == 1 and not ch.isspace():
                token += ch
            elif ch.isspace() and token:
                if not _NUMERIC_LITERAL.fullmatch(token) and not token.startswith('"'):
                    names.append(token)
                token = ""
            i += 1
        if (
            token
            and depth <= 1
            and not _NUMERIC_LITERAL.fullmatch(token)
            and not token.startswith('"')
        ):
            names.append(token)
    return names


def inventory(path: str | Path) -> LispInventory:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    inv = LispInventory(path=str(path))

    inv.defuns = [m.group("name") for m in _DEFUN.finditer(text)]
    for m in _ENTITY.finditer(text):
        cmd = m.group("cmd").upper()
        inv.entity_counts[cmd] = inv.entity_counts.get(cmd, 0) + 1
    inv.layers = sorted({m.group("layer") for m in _LAYER.finditer(text)})
    inv.setq_names = _setq_symbols(text)
    inv.numeric_literal_count = len(_NUMERIC_LITERAL.findall(text))

    for key, pattern in _GEOMETRY_OF_INTEREST.items():
        inv.interest_hits[key] = [layer for layer in inv.layers if pattern.search(layer)]

    return inv


def report(inventories: list[LispInventory]) -> str:
    """Markdown audit scaffold, one row per question from docs/lisp-baseline.md."""
    total_entities = sum(sum(i.entity_counts.values()) for i in inventories)
    layers = sorted({layer for i in inventories for layer in i.layers})
    names = sorted({n for i in inventories for n in i.setq_names})

    lines = [
        "# LISP baseline inventory",
        "",
        f"Files: {len(inventories)} · entities emitted: {total_entities} · "
        f"distinct layers: {len(layers)} · `setq` symbols: {len(names)}",
        "",
        "## Parametrisation",
        "",
        "Numeric literals versus `setq` symbols is the parametrisation signal:",
        "literals in geometry code mean the value was hard-coded.",
        "",
        f"- numeric literals: {sum(i.numeric_literal_count for i in inventories)}",
        f"- `setq` symbols: {len(names)}",
        "",
        "## Geometry of interest",
        "",
        "| element | layers found in the LISP |",
        "| --- | --- |",
    ]
    for key in _GEOMETRY_OF_INTEREST:
        hits = sorted({h for i in inventories for h in i.interest_hits[key]})
        lines.append(f"| {key} | {', '.join(f'`{h}`' for h in hits) or '**none**'} |")
    lines += ["", "## Layers named", ""]
    lines += [f"- `{layer}`" for layer in layers]
    return "\n".join(lines) + "\n"


__all__ = ["LispInventory", "inventory", "report"]
