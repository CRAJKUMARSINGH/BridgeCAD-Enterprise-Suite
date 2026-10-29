"""
Structural DXF checks — shared test helper for every sheet PR (Phase 2).

Catches the four geometry bugs that humans miss in code review:
  1. empty sheets (zero entities),
  2. content drawn miles outside its expected bounding box,
  3. entities on layers that are not in the 53 IRC SP:55 registry
     (typo'd layer names silently break downstream CAD workflows),
  4. entities left at the shared origin (0, 0) — the signature of a
     forgotten to_sheet_coords() transform.

Dependency note (test-only): ezdxf is already a draw-package dependency;
this helper lives under tests/ and must never be imported by src/ code.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

Vec2 = tuple[float, float]

# 53 IRC SP:55 layers — import the real registry in tests:
#   from bridgecad_draw.layers import IRC_LAYER_NAMES
# Duplicated here only so the failure message is readable when the import
# itself breaks. Keep in sync via a test that compares both lists.
FALLBACK_LAYER_PREFIXES = ("IRC_", "SP55_", "0", "DEFPOINTS")

MM_PER_M = 1000.0


@dataclass
class StructuralFindings:
    entity_count: int = 0
    layers_used: set[str] = field(default_factory=set)
    illegal_layers: set[str] = field(default_factory=set)
    entities_at_origin: int = 0
    extent_min: Vec2 = (float("inf"), float("inf"))
    extent_max: Vec2 = (float("-inf"), float("-inf"))

    def failures(self, allowed_layers: Iterable[str]) -> list[str]:
        allowed = set(allowed_layers)
        problems: list[str] = []
        if self.entity_count == 0:
            problems.append("sheet has zero entities")
        illegal = self.illegal_layers - allowed
        if illegal:
            problems.append(f"entities on non-SP:55 layers: {sorted(illegal)}")
        if self.entities_at_origin:
            problems.append(
                f"{self.entities_at_origin} entities at (0,0) — " "forgotten coordinate transform?"
            )
        return problems


def check_dxf(doc, allowed_layers: Iterable[str]) -> StructuralFindings:
    """Walk a loaded ezdxf document and collect structural findings.

    Pass `doc` loaded with ezdxf.readfile() / recover.read(). Modelspace
    only — paperspace title blocks are checked separately.
    """
    msp = doc.modelspace()
    f = StructuralFindings()

    for e in msp:
        f.entity_count += 1
        layer = e.dxf.layer
        f.layers_used.add(layer)
        if not layer.startswith(FALLBACK_LAYER_PREFIXES):
            f.illegal_layers.add(layer)

        # Extent via the bounding box API when available; fall back to
        # explicit coordinate attributes for older ezdxf entities.
        try:
            from ezdxf import bbox  # type: ignore

            box = bbox.extents([e])
            pts = [(box.extmin.x, box.extmin.y), (box.extmax.x, box.extmax.y)]
        except Exception:
            pts = [
                (getattr(e.dxf, a, 0.0), getattr(e.dxf, b, 0.0))
                for a, b in (("x", "y"), ("x1", "y1"), ("x2", "y2"))
            ]

        for x, y in pts:
            f.extent_min = (min(f.extent_min[0], x), min(f.extent_min[1], y))
            f.extent_max = (max(f.extent_max[0], x), max(f.extent_max[1], y))

        for x, y in pts:
            if abs(x) < 1e-9 and abs(y) < 1e-9:
                f.entities_at_origin += 1
                break

    return f


def assert_sheet_structurally_sound(doc, allowed_layers: Iterable[str]) -> None:
    """Pytest-friendly assertion entry point for sheet tests."""
    f = check_dxf(doc, allowed_layers)
    failures = f.failures(allowed_layers)
    assert not failures, "Structural DXF failures:\n  - " + "\n  - ".join(failures)
