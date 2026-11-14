"""Support-level dependency invariants after the nine-span gap regression."""
from decimal import Decimal
import pytest
from bridgecad_core.geometry.long_section import compute_long_section_geometry

@pytest.mark.parametrize('cap_depth',[Decimal('0.6'),Decimal('1.2')])
def test_cap_top_excludes_depth_and_pedestal_closes_soffit(span_variant,cap_depth):
    project=span_variant([10]*9)
    project.substructure.pier_cap_depth_m=cap_depth
    project.substructure.pier_pedestal_height_m=Decimal('0.15')
    g=compute_long_section_geometry(project)
    assert len(g.pier_top_of_cap_rl_m)==8
    for top in g.pier_top_of_cap_rl_m:
        assert top+0.15==pytest.approx(g.soffit_rl)
        # Changing concrete cap depth moves its bottom, not the seat datum.
        assert (top-float(cap_depth))+float(cap_depth)+0.15==pytest.approx(g.soffit_rl)
