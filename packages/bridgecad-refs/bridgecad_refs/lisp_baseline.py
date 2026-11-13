"""Inventory an AutoLISP GAD source without executing it.

Lexical inspection only: comments and string literals are distinguished from
code symbols. No AutoLISP is executed, and static command occurrences must not
be interpreted as emitted-entity counts or engineering capability.
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

_LAYER = re.compile(r'"(?P<layer>[A-Z][A-Z0-9_-]*(?:-[A-Z0-9]+)+)"')
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
    sha256: str = ""


def _tokens(text: str) -> list[tuple[str, str]]:
    """Read lexical tokens only; never evaluate AutoLISP or open its data files.

    Ignore line and nested block comments. Keep quoted strings separate from
    symbols so prose and strings cannot invent definitions or assignments.
    """
    tokens: list[tuple[str, str]] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace() or ch == "\ufeff":
            i += 1
        elif text.startswith(";|", i):
            depth = 1
            i += 2
            while i < len(text) and depth:
                if text.startswith(";|", i):
                    depth += 1
                    i += 2
                elif text.startswith("|;", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("Unterminated AutoLISP block comment")
        elif ch == ";":
            end = text.find("\n", i)
            i = len(text) if end < 0 else end + 1
        elif ch == '"':
            i += 1
            value = ""
            while i < len(text) and text[i] != '"':
                if text[i] == "\\" and i + 1 < len(text):
                    value += text[i + 1]
                    i += 2
                else:
                    value += text[i]
                    i += 1
            if i >= len(text):
                raise ValueError("Unterminated AutoLISP string")
            tokens.append(("string", value))
            i += 1
        elif ch in "()'":
            tokens.append((ch, ch))
            i += 1
        else:
            end = i
            while i < len(text) and not text[i].isspace() and text[i] not in "();'\"":
                i += 1
            tokens.append(("atom", text[end:i]))
    return tokens


def _expression_end(tokens: list[tuple[str, str]], index: int) -> int:
    while index < len(tokens) and tokens[index][0] == "'":
        index += 1
    if index >= len(tokens):
        return index
    if tokens[index][0] != "(":
        return index + 1
    depth = 1
    index += 1
    while index < len(tokens) and depth:
        if tokens[index][0] == "(":
            depth += 1
        elif tokens[index][0] == ")":
            depth -= 1
        index += 1
    return index


def _setq_from_tokens(tokens: list[tuple[str, str]]) -> list[str]:
    names: list[str] = []
    for i in range(len(tokens) - 1):
        if tokens[i][0] != "(" or (tokens[i + 1][0] != "atom" or tokens[i + 1][1].lower() != "setq"):
            continue
        j = i + 2
        while j < len(tokens) and tokens[j][0] != ")":
            if tokens[j][0] != "atom" or j + 1 >= len(tokens) or tokens[j + 1][0] == ")":
                break
            names.append(tokens[j][1])
            j = _expression_end(tokens, j + 1)
    return names


def _setq_symbols(text: str) -> list[str]:
    return _setq_from_tokens(_tokens(text))


def inventory(path: str | Path) -> LispInventory:
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig", errors="replace")
    tokens = _tokens(text)
    # AutoLISP symbols are case-insensitive; string content keeps its case.
    tokens = [(kind, value.lower() if kind == "atom" else value) for kind, value in tokens]
    inv = LispInventory(path=str(path), sha256=hashlib.sha256(raw).hexdigest())
    commands = {"LINE", "PLINE", "RECTANG", "CIRCLE", "TEXT", "MTEXT", "HATCH", "DIMLINEAR", "INSERT"}
    for i in range(len(tokens) - 2):
        if tokens[i][0] != "(":
            continue
        if tokens[i + 1] == ("atom", "defun") and tokens[i + 2][0] == "atom":
            inv.defuns.append(tokens[i + 2][1])
        if tokens[i + 1] == ("atom", "command") and tokens[i + 2][0] == "string":
            cmd = tokens[i + 2][1].upper()
            if cmd in commands:
                inv.entity_counts[cmd] = inv.entity_counts.get(cmd, 0) + 1
    inv.layers = sorted({value for kind, value in tokens if kind == "string" and _LAYER.fullmatch('"' + value + '"')})
    inv.setq_names = _setq_from_tokens(tokens)
    inv.numeric_literal_count = sum(bool(re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value)) for kind, value in tokens if kind == "atom")

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
        f"Files: {len(inventories)} · static drawing-command occurrences: {total_entities} · "
        f"candidate layer-like strings: {len(layers)} · `setq` symbols: {len(names)}",
        "",
        "Static inspection only: no AutoCAD execution, runtime entity count, or geometric fidelity is established.",
        "",
        "## Source provenance",
        "",
        "| source | SHA-256 | functions observed |",
        "| --- | --- | --- |",
        *[f"| `{i.path}` | `{i.sha256}` | {', '.join(f'`{n}`' for n in i.defuns)} |" for i in inventories],
        "",
        "## Parametrisation",
        "",
        "Counts exclude comments and keep literal values distinct from assigned symbols.",
        "Numeric constants alone do not establish a defect; review their meaning and units.",
        "",
        f"- numeric literals: {sum(i.numeric_literal_count for i in inventories)}",
        f"- `setq` symbols: {len(names)}",
        "",
        "## Geometry of interest",
        "",
        "| element | candidate layer-like strings |",
        "| --- | --- |",
    ]
    for key in _GEOMETRY_OF_INTEREST:
        hits = sorted({h for i in inventories for h in i.interest_hits[key]})
        lines.append(f"| {key} | {', '.join(f'`{h}`' for h in hits) or '**none**'} |")
    lines += ["", "## Candidate layer-like strings", ""]
    lines += [f"- `{layer}`" for layer in layers]
    return "\n".join(lines) + "\n"


__all__ = ["LispInventory", "inventory", "report"]
