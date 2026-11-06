"""Sheet 01 elevation must carry an abutment foundation and a deck top.

Defect report: the GAD elevation rendered the abutments as bare fill rectangles
with no footing, and nothing above the deck soffit — "devoid of abutment
foundation and top". This guard fails if either structure is removed.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "frontend" / "src" / "sheets" / "Sheet01Overview.tsx"
STYLES = ROOT / "frontend" / "src" / "styles.css"

#: The joint between the abutment stem and the footing crown. Both bodies must
#: reference it, otherwise the stem floats above its foundation.
JOINT = "footingY"


def _elevation_block() -> str:
    body = SOURCE.read_text(encoding="utf-8")
    start = body.index('className="elevation"')
    end = body.index('className="view-gap"')
    return body[start:end]


def test_elevation_draws_the_foundation_and_the_deck_top():
    elev = _elevation_block()

    assert 'className="barrier"' in elev, "the deck top (barrier/kerb) is no longer drawn"
    assert elev.count('className="abutment-fill"') >= 2, "one or both abutment stems are missing"
    assert elev.count('className="abutment-cap"') >= 2, "the abutment caps (LISP ALCW/ALCD) are missing"
    assert elev.count('className="footing-fill"') >= 2, "the abutments have no foundation"
    assert elev.count(JOINT) >= 2, "the abutments are no longer seated on their footings"


def test_elevation_draws_the_dirt_wall_and_approach_slabs():
    """LISP abt1(): the dirt wall (DWTH) rises to road level at the abutment back,
    and the thinner approach slabs (APTHK/LASLAB) run out from both deck ends."""
    elev = _elevation_block()

    assert elev.count('className="dirt-wall"') >= 2, "the abutment-top dirt wall is missing"
    assert elev.count('className="approach-slab"') >= 2, "the approach slabs are missing"


def test_the_new_sheet01_classes_are_styled():
    styles = STYLES.read_text(encoding="utf-8")
    for rule in (".barrier {", ".dirt-wall {", ".dirt-wall-weep {", ".approach-slab {", ".abutment-cap {"):
        assert rule in styles, f"Sheet 01 draws {rule[:-2].strip()} with no CSS rule — it renders invisibly"


def test_the_dirt_wall_is_drained_by_weep_holes():
    """prewallcivil.com/dirt-wall-in-bridge-abutment: a dirt wall must be drained.

    Weep holes (with a granular/geotextile filter) relieve the hydrostatic
    pressure the retained embankment would otherwise build up behind the wall,
    so the elevation must show them and say so.
    """
    elev = _elevation_block()
    assert elev.count('className="dirt-wall-weep"') >= 2, (
        "the dirt wall has no weep holes — hydrostatic pressure builds up behind it"
    )
    assert "WEEP HOLES" in elev, "the dirt-wall drainage (weep holes) is not called out"


def _number(body: str, name: str) -> float:
    match = re.search(rf"const {name} = (\d+(?:\.\d+)?);", body)
    assert match, f"{name} is no longer a literal constant — the elevation geometry is unverifiable"
    return float(match.group(1))


def test_the_dirt_wall_is_thinner_than_the_abutment_body():
    """Defect report: the dirt wall was drawn as wide as the whole abutment and
    seated outside the deck end, so it read as a second, taller abutment.
    LISP abt1(): the dirt wall is a thin wall (DWTH) at the deck end; the
    abutment face is flush at x1 = abtl and its cap carries inward."""
    body = SOURCE.read_text(encoding="utf-8")

    dirt_wall = _number(body, "dirtWallWidth")
    for wider in ("capWidth", "stemWidth"):
        assert dirt_wall < _number(body, wider), (
            f"the dirt wall ({dirt_wall}) is not thinner than the {wider} "
            f"({_number(body, wider)}) — it reads as a second, taller abutment"
        )

    for line in _elevation_block().splitlines():
        if 'className="dirt-wall"' in line:
            assert "Width" not in line or "dirtWallWidth" in line, (
                "the dirt wall is drawn with the abutment width — it must be DWTH thin, not the abutment body"
            )


def test_the_dirt_wall_rises_to_road_level_over_the_cap():
    """LISP enhanced_abt1(): the dirt wall runs (x14, capb) → (x14, RTL) — from
    the cap soffit to road level, outside the abutment face. It must not be a
    stub confined to the deck band, and the cap must be drawn beneath it."""
    elev = _elevation_block()
    body = SOURCE.read_text(encoding="utf-8")

    for line in elev.splitlines():
        if 'className="dirt-wall"' in line:
            assert "roadY" in line and "capBottomY" in line, (
                "the dirt wall must span the cap soffit (capBottomY) up to road level (roadY)"
            )

    assert re.search(r"const capBottomY = soffitY \+ capDepth;", body), (
        "the cap soffit (capBottomY) is no longer derived from the deck soffit and the cap depth"
    )
    assert re.search(r"const capDepth = \d+;", body), "the cap depth (LISP ALCD) is missing"


