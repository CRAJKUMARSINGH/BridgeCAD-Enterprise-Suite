"""
bridgecad_core.standards.load_combinations — limit-state load-combination engine.

Encodes the load cases and partial factors of

  * **IRC:6-2017** Table 1 — the Indian Roads Congress limit-state combinations, and
  * **EN 1990:2002** Table A1.2 — the Eurocode persistent / transient (Eq. 6.10)
    and seismic (Eq. 6.12) combinations used when a European design code is
    selected.

A combination is a named, ordered list of ``(case, factor)`` terms. Applying it
to a mapping of per-case effects is a single deterministic dot product, so the
same inputs always yield the same factored effect — no iteration, no state.

Only the load cases the suite actually models are represented. Factors are the
partial-factor form of the cited tables; the citation on every combination names
the table so a checker can trace the number back to the code.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Canonical load-case ids (stable — used as mapping keys by the engine)
# ---------------------------------------------------------------------------

DEAD = "DL"
SUPERIMPOSED_DEAD = "SIDL"
LIVE = "LL"
WIND = "WL"
TEMPERATURE = "TL"
SEISMIC = "EQ"
PRESTRESS = "PS"
CREEP_SHRINKAGE = "CS"


@dataclass(frozen=True)
class LoadCase:
    """A named action whose effect participates in combinations."""

    id: str
    description: str
    kind: str  # permanent | variable | accidental | prestress


IRC6_LOAD_CASES: tuple[LoadCase, ...] = (
    LoadCase(DEAD, "Dead load of structural members", "permanent"),
    LoadCase(
        SUPERIMPOSED_DEAD, "Superimposed dead load (wearing coat, kerbs, parapet)", "permanent"
    ),
    LoadCase(LIVE, "Vehicular live load (IRC:6 Class A / 70R)", "variable"),
    LoadCase(WIND, "Wind load", "variable"),
    LoadCase(TEMPERATURE, "Temperature / shrinkage effect", "variable"),
    LoadCase(SEISMIC, "Seismic load", "accidental"),
    LoadCase(PRESTRESS, "Prestress primary + secondary", "prestress"),
    LoadCase(CREEP_SHRINKAGE, "Creep and shrinkage", "variable"),
)

EN1990_LOAD_CASES: tuple[LoadCase, ...] = (
    LoadCase(DEAD, "Permanent action G_k (self-weight)", "permanent"),
    LoadCase(SUPERIMPOSED_DEAD, "Permanent action G_k (superimposed)", "permanent"),
    LoadCase(LIVE, "Leading variable action Q_k,1 (traffic)", "variable"),
    LoadCase(WIND, "Accompanying variable action Q_k (wind)", "variable"),
    LoadCase(TEMPERATURE, "Accompanying variable action Q_k (thermal)", "variable"),
    LoadCase(SEISMIC, "Seismic action A_Ed", "accidental"),
)


# ---------------------------------------------------------------------------
# Combination model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CombinationTerm:
    """One ``case × factor`` term inside a combination."""

    case_id: str
    factor: float


@dataclass(frozen=True)
class LoadCombination:
    """A named limit-state combination: an id, a citation and its terms."""

    id: str
    standard: str  # e.g. "IRC:6-2017"
    limit_state: str  # "ULS" | "SLS" | "SEISMIC"
    description: str
    terms: tuple[CombinationTerm, ...]

    def factor(self, case_id: str) -> float:
        """Total partial factor applied to ``case_id`` (0.0 when it is absent)."""
        return sum(term.factor for term in self.terms if term.case_id == case_id)

    def case_ids(self) -> frozenset[str]:
        """The case ids this combination references."""
        return frozenset(term.case_id for term in self.terms)

    def factored_effect(self, effects: Mapping[str, float]) -> float:
        """Apply this combination to per-case effects.

        Cases absent from ``effects`` contribute 0.0 — a combination is defined
        over its terms, not over the effect mapping.
        """
        return sum(term.factor * float(effects.get(term.case_id, 0.0)) for term in self.terms)


def _combo(
    combo_id: str,
    standard: str,
    limit_state: str,
    description: str,
    terms: tuple[tuple[str, float], ...],
) -> LoadCombination:
    return LoadCombination(
        id=combo_id,
        standard=standard,
        limit_state=limit_state,
        description=description,
        terms=tuple(CombinationTerm(case_id=c, factor=f) for c, f in terms),
    )


# ---------------------------------------------------------------------------
# IRC:6-2017 Table 1
# ---------------------------------------------------------------------------

_IRC6_STANDARD = "IRC:6-2017"


def irc6_combinations() -> tuple[LoadCombination, ...]:
    """All IRC:6-2017 Table 1 combinations the suite models, in table order."""
    return (
        _combo(
            "IRC6-ULS-1",
            _IRC6_STANDARD,
            "ULS",
            "1.5(DL + SIDL) + 1.5 LL",
            ((DEAD, 1.5), (SUPERIMPOSED_DEAD, 1.5), (LIVE, 1.5)),
        ),
        _combo(
            "IRC6-ULS-2",
            _IRC6_STANDARD,
            "ULS",
            "1.5(DL + SIDL) + 1.5 LL + 0.9 WL",
            ((DEAD, 1.5), (SUPERIMPOSED_DEAD, 1.5), (LIVE, 1.5), (WIND, 0.9)),
        ),
        _combo(
            "IRC6-ULS-3",
            _IRC6_STANDARD,
            "ULS",
            "1.5(DL + SIDL) + 1.5 WL",
            ((DEAD, 1.5), (SUPERIMPOSED_DEAD, 1.5), (WIND, 1.5)),
        ),
        _combo(
            "IRC6-ULS-4",
            _IRC6_STANDARD,
            "ULS",
            "1.5(DL + SIDL) + 1.5 WL + 0.9 LL",
            ((DEAD, 1.5), (SUPERIMPOSED_DEAD, 1.5), (WIND, 1.5), (LIVE, 0.9)),
        ),
        _combo(
            "IRC6-ULS-5",
            _IRC6_STANDARD,
            "ULS",
            "1.5(DL + SIDL) + 1.5 TL + 0.9 LL",
            ((DEAD, 1.5), (SUPERIMPOSED_DEAD, 1.5), (TEMPERATURE, 1.5), (LIVE, 0.9)),
        ),
        _combo(
            "IRC6-ULS-6",
            _IRC6_STANDARD,
            "ULS",
            "1.5(DL + SIDL) + 1.5 LL + 0.9 TL",
            ((DEAD, 1.5), (SUPERIMPOSED_DEAD, 1.5), (LIVE, 1.5), (TEMPERATURE, 0.9)),
        ),
        _combo(
            "IRC6-SEISMIC-1",
            _IRC6_STANDARD,
            "SEISMIC",
            "1.0(DL + SIDL) + 1.0 EQ + 0.5 LL",
            ((DEAD, 1.0), (SUPERIMPOSED_DEAD, 1.0), (SEISMIC, 1.0), (LIVE, 0.5)),
        ),
        _combo(
            "IRC6-SLS-1",
            _IRC6_STANDARD,
            "SLS",
            "1.0(DL + SIDL + LL) — characteristic",
            ((DEAD, 1.0), (SUPERIMPOSED_DEAD, 1.0), (LIVE, 1.0)),
        ),
        _combo(
            "IRC6-SLS-2",
            _IRC6_STANDARD,
            "SLS",
            "1.0(DL + SIDL + LL) + 0.6 WL — rare",
            ((DEAD, 1.0), (SUPERIMPOSED_DEAD, 1.0), (LIVE, 1.0), (WIND, 0.6)),
        ),
        _combo(
            "IRC6-SLS-3",
            _IRC6_STANDARD,
            "SLS",
            "1.0(DL + SIDL + LL) + 0.5 TL — quasi-permanent",
            ((DEAD, 1.0), (SUPERIMPOSED_DEAD, 1.0), (LIVE, 1.0), (TEMPERATURE, 0.5)),
        ),
    )


# ---------------------------------------------------------------------------
# EN 1990:2002 Table A1.2
# ---------------------------------------------------------------------------

_EN_STANDARD = "EN 1990:2002"


def en1990_combinations() -> tuple[LoadCombination, ...]:
    """EN 1990:2002 Table A1.2 combinations (Eq. 6.10 / 6.12 / 6.14 / 6.15)."""
    return (
        _combo(
            "EN1990-6.10",
            _EN_STANDARD,
            "ULS",
            "1.35 G + 1.5 Q_k,1 + 1.5 ψ0,wind Q_k (ψ0 = 0.6)",
            ((DEAD, 1.35), (SUPERIMPOSED_DEAD, 1.35), (LIVE, 1.5), (WIND, 0.9)),
        ),
        _combo(
            "EN1990-6.10b",
            _EN_STANDARD,
            "ULS",
            "1.25 G + 1.5 Q_k,1 (ξ = 0.925 on unfavourable G)",
            ((DEAD, 1.25), (SUPERIMPOSED_DEAD, 1.25), (LIVE, 1.5)),
        ),
        _combo(
            "EN1990-6.10-wind",
            _EN_STANDARD,
            "ULS",
            "1.35 G + 1.5 W_k + 1.5 ψ0,traffic Q_k (ψ0 = 0.7)",
            ((DEAD, 1.35), (SUPERIMPOSED_DEAD, 1.35), (WIND, 1.5), (LIVE, 1.05)),
        ),
        _combo(
            "EN1990-6.10-thermal",
            _EN_STANDARD,
            "ULS",
            "1.35 G + 1.5 T_k + 1.5 ψ0,traffic Q_k (ψ0 = 0.6)",
            ((DEAD, 1.35), (SUPERIMPOSED_DEAD, 1.35), (TEMPERATURE, 1.5), (LIVE, 0.9)),
        ),
        _combo(
            "EN1990-6.12b",
            _EN_STANDARD,
            "SEISMIC",
            "G + ψ2,traffic Q_k + A_Ed (ψ2 = 0.3)",
            ((DEAD, 1.0), (SUPERIMPOSED_DEAD, 1.0), (LIVE, 0.3), (SEISMIC, 1.0)),
        ),
        _combo(
            "EN1990-6.14b",
            _EN_STANDARD,
            "SLS",
            "G + Q_k,1 — characteristic",
            ((DEAD, 1.0), (SUPERIMPOSED_DEAD, 1.0), (LIVE, 1.0)),
        ),
        _combo(
            "EN1990-6.15b",
            _EN_STANDARD,
            "SLS",
            "G + ψ2,traffic Q_k — quasi-permanent (ψ2 = 0.3)",
            ((DEAD, 1.0), (SUPERIMPOSED_DEAD, 1.0), (LIVE, 0.3)),
        ),
    )


def combinations_for(standard: str) -> tuple[LoadCombination, ...]:
    """Combination set for ``standard`` — ``"IRC:6"``/``"IRC"`` or ``"EN 1990"``."""
    token = standard.strip().upper()
    if token.startswith("EN"):
        return en1990_combinations()
    if token.startswith("IRC"):
        return irc6_combinations()
    raise ValueError(f"no load-combination set registered for standard {standard!r}")


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Envelope:
    """The extreme effects a combination set produces for one effect mapping."""

    maximum: float
    governing_max_id: str
    minimum: float
    governing_min_id: str


def envelope(
    combinations: tuple[LoadCombination, ...],
    effects: Mapping[str, float],
) -> Envelope:
    """Return the max/min factored effect and the combination that governs each."""
    if not combinations:
        raise ValueError("envelope() needs at least one combination")
    results = [(combo.id, combo.factored_effect(effects)) for combo in combinations]
    max_id, maximum = max(results, key=lambda pair: pair[1])
    min_id, minimum = min(results, key=lambda pair: pair[1])
    return Envelope(
        maximum=maximum,
        governing_max_id=max_id,
        minimum=minimum,
        governing_min_id=min_id,
    )


__all__ = [
    "DEAD",
    "SUPERIMPOSED_DEAD",
    "LIVE",
    "WIND",
    "TEMPERATURE",
    "SEISMIC",
    "PRESTRESS",
    "CREEP_SHRINKAGE",
    "LoadCase",
    "IRC6_LOAD_CASES",
    "EN1990_LOAD_CASES",
    "CombinationTerm",
    "LoadCombination",
    "irc6_combinations",
    "en1990_combinations",
    "combinations_for",
    "Envelope",
    "envelope",
]
