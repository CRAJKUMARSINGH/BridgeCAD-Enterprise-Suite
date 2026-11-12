"""Maharashtra PWD booklet catalogue — the control surface over the 15 standard types.

Composed of four parts:

* :mod:`bridgecad_catalogue.schema` — every controllable field, its unit, legal
  range and the clause that sets it.
* :mod:`bridgecad_catalogue.registry` — the 15 booklet-faithful type cards.
* :mod:`bridgecad_catalogue.resolve` — card + overrides → a buildable parameter set.
* :mod:`bridgecad_catalogue.sweep` — ``key=lo:hi:step`` → a validated override matrix.
"""

from __future__ import annotations

from . import registry, resolve, schema, sweep

__all__ = ["registry", "resolve", "schema", "sweep"]
