"""Guide #1 Step 2 — the abutment datum resolver.

Done-when from the patch guide: on a fixture project ``wc_bot == slab_top`` and
``cap_top < app_bot``. The extra cases pin the two properties that keep the
class of bug from returning: the ladder is strictly ordered top-to-bottom, and
an unset dirt wall still resolves (the resolver is total).
"""

from __future__ import annotations

import itertools
from decimal import Decimal

from bridgecad_core.abutment_stack import AbutmentStack, resolve_abutment_stack


def test_wearing_coat_bottom_equals_slab_top(project):
    st = resolve_abutment_stack(project)
    assert isinstance(st, AbutmentStack)
    assert st.wc_bot == st.slab_top


def test_cap_top_sits_below_the_approach_slab_soffit(project):
    st = resolve_abutment_stack(project)
    assert st.cap_top < st.app_bot


def test_stack_is_strictly_ordered_from_road_down(project):
    st = resolve_abutment_stack(project)
    ladder = [st.wc_bot, st.deck_bot, st.cap_top, st.cap_bot]
    assert all(a > b for a, b in itertools.pairwise(ladder))


def test_unset_dirt_wall_still_resolves(blank_project):
    """An unset dirt wall must not make the resolver raise — it defaults to the
    approach-slab thickness, the thinnest wall ABT-005 permits."""
    blank_project.substructure = blank_project.substructure.model_copy(
        update={"dirt_wall_height_m": None}
    )
    st = resolve_abutment_stack(blank_project)
    app_t = Decimal(str(blank_project.substructure.approach_slab_thickness_mm)) / Decimal("1000")
    assert st.app_bot - st.cap_top == app_t
