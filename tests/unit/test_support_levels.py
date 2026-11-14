"""§3 canonical support-level contract — pure-resolver tests.

These encode the specification's numerical regression fixture (test inputs, not
design guidance) and its authority policy. The fixture's derived shaft height is
2.525 m; the older 6 m shaft-height input must be REJECTED, not forced into a
second view.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from bridgecad_core.geometry.long_section import pier_positions, span_boundaries
from bridgecad_core.geometry.support_levels import (
    AuthorityMode,
    BearingTopology,
    FieldSource,
    ResolutionStatus,
    SupportLevelInput,
    resolve_support_levels,
)

D = Decimal


def _fixture(**overrides) -> SupportLevelInput:
    """The §3 level-controlled slab fixture (explicitly assumed seat pieces)."""
    base = dict(
        support_id="P1",
        road_rl_m=D("102.500"),
        wearing_depth_m=D("0.075"),
        structural_depth_m=D("0.500"),
        bearing_depth_m=D("0.050"),
        bearing_depth_assumed=True,
        pedestal_height_m=D("0.150"),
        pedestal_height_assumed=True,
        cap_depth_m=D("0.800"),
        footing_bottom_rl_m=D("97.400"),
        footing_depth_m=D("1.000"),
    )
    base.update(overrides)
    return SupportLevelInput(**base)


# ---------------------------------------------------------------------------
# The fixture
# ---------------------------------------------------------------------------
def test_fixture_resolves_to_the_specified_levels():
    rec = resolve_support_levels(_fixture())
    assert rec.status is ResolutionStatus.RESOLVED
    assert rec.authority is AuthorityMode.LEVEL_CONTROLLED
    assert rec.structural_soffit_rl_m == D("101.925")
    assert rec.cap_top_rl_m == D("101.725")
    assert rec.cap_bottom_rl_m == D("100.925")
    assert rec.footing_top_rl_m == D("98.400")
    assert rec.footing_bottom_rl_m == D("97.400")
    assert rec.shaft_height_m == D("2.525")


def test_all_interfaces_connect_exactly():
    """cap bottom = shaft top; footing top = shaft base; seat closes onto soffit."""
    rec = resolve_support_levels(_fixture())
    assert rec.cap_bottom_rl_m == rec.shaft_top_rl_m
    assert rec.footing_top_rl_m == rec.shaft_base_rl_m
    # pedestal top + bearing depth closes onto the soffit under this topology
    assert rec.cap_top_rl_m + D("0.150") + D("0.050") == rec.structural_soffit_rl_m
    assert rec.shaft_top_rl_m - rec.shaft_base_rl_m == rec.shaft_height_m


def test_shaft_height_uses_the_declared_tolerance():
    """Pure-resolver equality holds to 1e-6 m, not to a float's last bit."""
    rec = resolve_support_levels(_fixture())
    assert abs(rec.shaft_height_m - D("2.525")) <= D("0.000001")


def test_provenance_marks_assumed_inputs():
    rec = resolve_support_levels(_fixture())
    assert rec.provenance["bearing_depth_m"] is FieldSource.ASSUMED
    assert rec.provenance["pedestal_height_m"] is FieldSource.ASSUMED
    assert rec.provenance["footing_bottom_rl_m"] is FieldSource.SUPPLIED
    assert rec.provenance["footing_top_rl_m"] is FieldSource.DERIVED
    assert rec.provenance["shaft_height_m"] is FieldSource.DERIVED


# ---------------------------------------------------------------------------
# Authority policy
# ---------------------------------------------------------------------------
def test_older_6m_shaft_height_conflicts_and_is_rejected():
    """Level-controlled mode must reject the incompatible 6 m supplied height."""
    rec = resolve_support_levels(_fixture(shaft_height_m=D("6.000")))
    assert rec.status is ResolutionStatus.CONFLICT
    assert rec.shaft_height_m == D("2.525")  # the derived value survives
    assert any(i.code == "E-CONFLICT-SHAFT-HEIGHT" for i in rec.issues)


def test_compatible_supplied_height_is_not_a_conflict():
    rec = resolve_support_levels(_fixture(shaft_height_m=D("2.525")))
    assert rec.status is ResolutionStatus.RESOLVED
    assert rec.shaft_height_m == D("2.525")


def test_missing_footing_depth_is_unresolved_never_guessed():
    rec = resolve_support_levels(_fixture(footing_depth_m=None, shaft_height_m=None))
    assert rec.status is ResolutionStatus.UNRESOLVED
    assert rec.footing_bottom_rl_m is None
    assert rec.shaft_base_rl_m is None
    assert any(i.code == "E-MISSING-FOUNDATION" for i in rec.issues)


def test_height_controlled_proposes_founding_level():
    rec = resolve_support_levels(
        _fixture(shaft_height_m=D("2.525"), footing_bottom_rl_m=None)
    )
    assert rec.authority is AuthorityMode.HEIGHT_CONTROLLED
    assert rec.shaft_base_rl_m == D("98.400")
    assert rec.footing_bottom_rl_m == D("97.400")
    assert rec.provenance["footing_bottom_rl_m"] is FieldSource.PROPOSED
    assert any(i.code == "W-PROPOSED-FOUNDING" for i in rec.issues)
    # a warning is not an error: the geometry is complete but flagged proposed
    assert rec.status is ResolutionStatus.UNRESOLVED


def test_missing_cap_depth_is_unresolved():
    rec = resolve_support_levels(_fixture(cap_depth_m=None))
    assert rec.status is ResolutionStatus.UNRESOLVED
    assert rec.cap_top_rl_m == D("101.725")  # seat still resolves
    assert rec.cap_bottom_rl_m is None
    assert any(i.code == "E-MISSING-CAP-DEPTH" for i in rec.issues)


# ---------------------------------------------------------------------------
# Topology alternatives (never both formulae at once)
# ---------------------------------------------------------------------------
def test_monolithic_topology_has_zero_seat():
    rec = resolve_support_levels(
        _fixture(
            topology=BearingTopology.MONOLITHIC,
            bearing_depth_m=None,
            pedestal_height_m=None,
        )
    )
    assert rec.status is ResolutionStatus.RESOLVED
    assert rec.cap_top_rl_m == rec.structural_soffit_rl_m


def test_combined_seat_subtracts_once():
    rec = resolve_support_levels(
        _fixture(
            topology=BearingTopology.COMBINED_SEAT,
            combined_seat_height_m=D("0.200"),
            bearing_depth_m=D("0.050"),
            pedestal_height_m=D("0.150"),
        )
    )
    assert rec.status is ResolutionStatus.RESOLVED
    # 0.200 applied once — NOT 0.050 + 0.150 + 0.200
    assert rec.cap_top_rl_m == D("101.925") - D("0.200")


def test_separate_topology_without_both_pieces_is_unresolved():
    rec = resolve_support_levels(_fixture(pedestal_height_m=None))
    assert rec.status is ResolutionStatus.UNRESOLVED
    assert any(i.code == "E-MISSING-SEAT-PIECES" for i in rec.issues)


# ---------------------------------------------------------------------------
# Sensitivity — each change moves exactly the right levels
# ---------------------------------------------------------------------------
def test_bearing_depth_moves_seat_levels_exactly_once():
    a = resolve_support_levels(_fixture())
    b = resolve_support_levels(_fixture(bearing_depth_m=D("0.100")))
    delta = D("0.050")
    # cap top and everything below it drop by the bearing change, once
    assert b.cap_top_rl_m == a.cap_top_rl_m - delta
    assert b.shaft_top_rl_m == a.shaft_top_rl_m - delta
    assert b.shaft_height_m == a.shaft_height_m - delta
    # the soffit does not move — it is set by road/wearing/structural depth
    assert b.structural_soffit_rl_m == a.structural_soffit_rl_m


def test_cap_depth_moves_its_bottom_not_the_cap_top_datum():
    a = resolve_support_levels(_fixture())
    b = resolve_support_levels(_fixture(cap_depth_m=D("1.200")))
    assert b.cap_top_rl_m == a.cap_top_rl_m  # datum unchanged
    assert b.cap_bottom_rl_m == a.cap_bottom_rl_m - D("0.400")
    assert b.shaft_height_m == a.shaft_height_m - D("0.400")
    # the foundation did not move
    assert b.footing_bottom_rl_m == a.footing_bottom_rl_m
    assert b.shaft_base_rl_m == a.shaft_base_rl_m


def test_gradient_resolves_support_local_levels():
    """A longitudinal gradient gives each support its own RL, not one soffit."""
    low = resolve_support_levels(_fixture(support_id="A1", road_rl_m=D("102.500")))
    high = resolve_support_levels(_fixture(support_id="A2", road_rl_m=D("102.800")))
    rise = D("0.300")
    assert high.structural_soffit_rl_m == low.structural_soffit_rl_m + rise
    assert high.cap_top_rl_m == low.cap_top_rl_m + rise
    # the seat arithmetic is identical at both supports
    assert (high.structural_soffit_rl_m - high.cap_top_rl_m) == (
        low.structural_soffit_rl_m - low.cap_top_rl_m
    )


# ---------------------------------------------------------------------------
# Founding / shaft base / ground / scour stay distinct
# ---------------------------------------------------------------------------
def test_scour_and_ground_are_not_conflated_with_the_shaft_base():
    rec = resolve_support_levels(
        _fixture(ground_level_rl_m=D("99.100"), scour_level_rl_m=D("96.200"))
    )
    assert rec.shaft_base_rl_m == D("98.400")
    assert rec.ground_level_rl_m == D("99.100")
    assert rec.scour_level_rl_m == D("96.200")
    assert rec.scour_level_rl_m != rec.shaft_base_rl_m
    assert rec.ground_level_rl_m != rec.shaft_base_rl_m


# ---------------------------------------------------------------------------
# Nine-span fixture — eight piers, two abutments, on their own axes
# ---------------------------------------------------------------------------
def test_nine_span_fixture_has_eight_piers_and_two_abutments(span_variant):
    project = span_variant([10] * 9)
    boundaries = span_boundaries(project)
    piers = pier_positions(project)
    assert boundaries == [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
    assert piers == [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    assert len(piers) == 8
    # the two end abutments sit on the first and last support axes
    assert boundaries[0] == 0.0 and boundaries[-1] == 90.0


# ---------------------------------------------------------------------------
# Serialisation for artifacts/gad-acceptance/<fixture>/<commit>/params.resolved.json
# ---------------------------------------------------------------------------
def test_record_serialises_without_losing_decimals():
    rec = resolve_support_levels(_fixture())
    payload = rec.to_json()
    assert payload["support_id"] == "P1"
    assert payload["status"] == "RESOLVED"
    assert payload["authority"] == "LEVEL_CONTROLLED"
    assert payload["levels_m"]["cap_top_rl_m"] == "101.725"
    assert payload["shaft_height_m"] == "2.525"
    assert payload["provenance"]["bearing_depth_m"] == "ASSUMED"


# ---------------------------------------------------------------------------
# Cross-view: every renderer reads the SAME record
# ---------------------------------------------------------------------------
def test_long_section_reads_the_canonical_record(span_variant):
    from bridgecad_core.geometry.long_section import compute_long_section_geometry

    ls = compute_long_section_geometry(span_variant([10] * 9))
    assert len(ls.support_level_records) == 8
    # the long-section cap datum IS the record's cap top — not a re-derivation
    for rec, toc in zip(ls.support_level_records, ls.pier_top_of_cap_rl_m):
        assert float(rec.cap_top_rl_m) == pytest.approx(toc)
        assert float(rec.structural_soffit_rl_m) == pytest.approx(ls.soffit_rl)


def test_abutment_stack_shares_the_canonical_soffit(span_variant):
    from bridgecad_core.abutment_stack import resolve_abutment_stack
    from bridgecad_core.geometry.long_section import compute_long_section_geometry

    project = span_variant([10] * 9)
    ls = compute_long_section_geometry(project)
    stack = resolve_abutment_stack(project)
    # wc_bot and slab_top are the same surface
    assert stack.wc_bot == stack.slab_top
    # deck_bot IS the canonical soffit the long section draws. A supplied
    # surveyed soffit wins over the road-level derivation (gradient/camber put
    # the minimum-span soffit at a different chainage), and both views must
    # land on that one level rather than each subtracting thicknesses again.
    assert float(stack.deck_bot) == pytest.approx(ls.soffit_rl)
    assert stack.record is not None
    assert stack.record.structural_soffit_rl_m == D(str(ls.soffit_rl))
    assert stack.cap_bot < stack.cap_top  # cap depth goes downward
    assert stack.bear_rl < stack.deck_bot  # seat sits below the soffit


def test_typical_pier_foundation_level_reads_the_canonical_contract(project, span_variant):
    """Sheet 4 (foundation) reads its pile-cap top from the canonical record.

    Sheet 4 used to compute ``cap_top = pile_cutoff + cap_thickness`` itself.
    That is the record's own ``footing_top = footing_bottom + footing_depth``,
    so it must come from one place. The single-span fixture has no intermediate
    pier, so the *nominal* typical-pier record must still resolve the same
    founding levels; the nine-span variant's real P1 must agree.
    """
    from bridgecad_core.geometry.long_section import typical_pier_support_level

    fd = project.foundation_details
    bottom = D(str(fd.pile_cutoff_level_m))
    depth = D(str(fd.pile_cap_thickness_mm)) / D("1000")

    single = typical_pier_support_level(project)
    assert single.footing_bottom_rl_m == bottom
    assert single.footing_depth_m == depth
    assert single.footing_top_rl_m == bottom + depth

    nine = typical_pier_support_level(span_variant([10] * 9))
    assert nine.support_id == "P1"
    assert nine.footing_top_rl_m == bottom + depth


def test_drawing_conversion_is_the_only_float_boundary():
    rec = resolve_support_levels(_fixture())
    floats = rec.to_drawing_floats()
    assert floats["cap_top_rl_m"] == pytest.approx(101.725)
    assert floats["footing_bottom_rl_m"] == pytest.approx(97.400)
    assert all(
        isinstance(v, float) or v is None for v in floats.values()
    )
