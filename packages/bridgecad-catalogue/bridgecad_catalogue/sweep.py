"""Expand ``--sweep key=lo:hi:step`` into a validated override matrix."""

from __future__ import annotations

from decimal import Decimal
from itertools import product

from .schema import VARIABLES, Violation


def parse(expr: str) -> tuple[str, list[object]]:
    key, _, spec = expr.partition("=")
    if not spec:
        raise Violation(f"--sweep wants key=lo:hi:step, got {expr!r}")
    s = VARIABLES.get(key)
    if s is None or s.choices:
        raise Violation(f"{key} is not sweepable (needs a numeric range)")
    parts = spec.split(":")
    if len(parts) != 3:
        raise Violation(f"--sweep wants key=lo:hi:step, got {expr!r}")
    lo, hi, step = (Decimal(x) for x in parts)
    if step <= 0:
        raise Violation(f"--sweep step must be positive, got {step}")
    out: list[object] = []
    v = lo
    while v <= hi:
        out.append(s.coerce(v))
        v += step
    return key, out


def matrix(exprs: list[str]) -> list[dict[str, object]]:
    parsed = [parse(e) for e in exprs]
    return [
        dict(zip([k for k, _ in parsed], combo, strict=True))
        for combo in product(*[vals for _, vals in parsed])
    ]
