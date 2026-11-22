"""Measure both exported views, using a dimensioned line to recover scale."""
import ezdxf
import pytest
from . import contract
from bridgecad_draw import sheet5_pier_abutment_details as sheet5


@pytest.mark.parametrize('diameter_mm', [50, 100, 150])
def test_user_weep_diameter_agrees_in_both_views(tmp_path, diameter_mm):
    data = contract._fixture_data('tests/e2e/fixtures/simple_12m.json')
    project = contract._build_from_fixture(data)
    project.substructure.weep_hole_diameter_mm = diameter_mm
    assert project.substructure.weep_hole_diameter_mm == diameter_mm
    out = tmp_path / 'sheet5.dxf'
    sheet5.generate(project, out)
    msp = ezdxf.readfile(out).modelspace()
    cap_lines = [e for e in msp.query('LINE[layer=="ABUT-PROF"]')
                 if abs(e.dxf.start.y - e.dxf.end.y) < 1e-6]
    assert len(cap_lines) == 1
    scale = abs(cap_lines[0].dxf.end.x-cap_lines[0].dxf.start.x) / float(
        project.substructure.abutment_length_m)
    holes = list(msp.query('CIRCLE[layer=="ABUT-PROF"]'))
    assert len(holes) == 4  # two in transverse view, two in longitudinal view
    assert any(e.dxf.center.y > 200 for e in holes)
    assert any(e.dxf.center.y < 200 for e in holes)
    for hole in holes:
        measured_metres = 2 * hole.dxf.radius / scale
        assert measured_metres == pytest.approx(diameter_mm / 1000)
