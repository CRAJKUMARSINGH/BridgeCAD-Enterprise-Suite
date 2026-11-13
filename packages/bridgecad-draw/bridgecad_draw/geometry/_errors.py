"""Errors raised by the booklet geometry primitives.

``bridgecad-draw`` does not depend on ``bridgecad-catalogue``, so the
catalogue's :class:`~bridgecad_catalogue.schema.Violation` is not importable
here.  A geometry the module cannot build as declared is a ``ValueError``; the
sheets let it propagate rather than drawing something the model does not say.
"""

from __future__ import annotations


class Violation(ValueError):
    """A geometry that cannot be built as declared."""
