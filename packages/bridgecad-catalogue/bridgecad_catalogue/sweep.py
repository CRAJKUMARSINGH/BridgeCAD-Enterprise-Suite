"""Expand ``--sweep key=lo:hi:step`` into a validated override matrix."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from itertools import product

from .schema import VARIABLES, Kind, Violation


def parse(expr: str) -> tuple[str, list[object]]:
    key, _, spec = expr.partition("=")
    if not spec:
        raise Violation(f"--sweep wants key=lo:hi:step, got {expr!r}")
    s = VARIABLES.get(key)
    if s is None or s.kind is not Kind.FREE:
        raise Violation(f"{key} is not sweepable (needs a free variable)")
    if s.choices:
        if ":" in spec:
            raise Violation(f"{key} is not sweepable as a range; use comma-separated choices")
        try:
            values = [Decimal(v.strip()) for v in spec.split(",")]
        except InvalidOperation as exc:
            raise Violation(f"{key}: expected comma-separated numeric choices") from exc
        if not all(v.is_finite() for v in values):
            raise Violation(f"{key}: choices must be finite")
        return key, [s.coerce(v) for v in values]
    parts = spec.split(":")
    if len(parts) != 3:
        raise Violation(f"--sweep wants key=lo:hi:step, got {expr!r}")
    try:
        lo, hi, step = (Decimal(x) for x in parts)
    except InvalidOperation as exc:
        raise Violation(f"--sweep needs numeric lo:hi:step, got {expr!r}") from exc
    if not all(v.is_finite() for v in (lo, hi, step)):
        raise Violation("--sweep bounds and step must be finite")
    if step <= 0:
        raise Violation(f"--sweep step must be positive, got {step}")
    if lo > hi:
        raise Violation("--sweep lower bound must not exceed upper bound")
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
