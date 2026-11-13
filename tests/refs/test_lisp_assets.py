"""Static archive provenance and independently stated legacy invariants."""
from pathlib import Path
import hashlib
import pytest
from bridgecad_refs.lisp_baseline import inventory, report
from bridgecad_draw.dxf_engine import CoordMapper
from bridgecad_core.geometry.abutment_profiles import battered_side_outline

ROOT = Path(__file__).resolve().parents[2]


def test_inventory_ignores_comments_strings_and_collects_assignment_targets(tmp_path):
    path=tmp_path/'source.lsp'
    path.write_text('''; (defun fake () (command "LINE"))
;| (defun blocked ()) ;| (setq nested 9) |; |;
(defun REAL ()
 (setq x 1 y (+ x 2) note "semi; (defun invented ())")
 (SETQ points '(1 2 3) alias x)
 (command "LINE" '(0 0) '(1 1) ""))
''')
    inv=inventory(path)
    assert inv.defuns==['real']
    assert inv.setq_names==['x','y','note','points','alias']
    assert inv.entity_counts=={'LINE':1}
    assert inv.sha256==hashlib.sha256(path.read_bytes()).hexdigest()
    assert 'static drawing-command occurrences' in report([inv])


def test_string_escape_does_not_turn_comment_into_code(tmp_path):
    path=tmp_path/'source.lsp'
    path.write_text('(setq label "a \\\"quoted\\\" ; value" x 3)')
    assert inventory(path).setq_names==['label','x']


@pytest.mark.parametrize('text',[';| no terminator','(setq x "no terminator)'])
def test_unterminated_literals_report_error(tmp_path,text):
    path=tmp_path/'bad.lsp';path.write_text(text)
    with pytest.raises(ValueError,match='Unterminated'):inventory(path)


def test_actual_preservation_copy_has_thirteen_observed_functions():
    path=ROOT/'ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp'
    inv=inventory(path)
    assert inv.defuns==['opn','reed','vpos','hpos','v2pos','h2pos','st','layout','cs','pier','pt','p2t','abt1']
    assert not {'draw_well','draw_girder','gad_init'} & set(inv.defuns)


@pytest.mark.parametrize('delta',[0.125,1.0,3.75])
def test_lisp_relative_metre_to_mm_invariant(delta):
    # reed(): hs=vs=1; hpos/vpos use 1000 * the difference from origin.
    mapper=CoordMapper(datum_rl=100,origin_ch=1200,x_offset=20,y_offset=30)
    assert mapper.hpos(1200+delta)-mapper.hpos(1200)==pytest.approx(delta*1000)
    assert mapper.vpos(100+delta)-mapper.vpos(100)==pytest.approx(delta*1000)


def test_lisp_section_ratio_invariant():
    # v2pos/h2pos multiply the relative displacement by scale1/scale2.
    mapper=CoordMapper(h_scale=100/25,v_scale=100/25)
    assert mapper.h_len(1.25)==5000
    assert mapper.v_len(.5)==2000


def test_abt1_two_face_batters_preserve_independent_runs():
    # abt1: x5-x3=(capb-alfbl)/alfb; x14-x12=(capb-albbl)/albb.
    profile=battered_side_outline(2,cap_w_m=1,cap_d_m=.5,face_batter_1n=3,
        back_batter_1n=10,toe_m=.5,foot_d_m=1,above_m=.4,dirt_w_m=.3)
    assert len(profile.points)==14
    assert profile.points[4][0]-profile.points[2][0]==pytest.approx(2/3)
    assert profile.points[12][0]-profile.points[10][0]==pytest.approx(.2)
    assert profile.points[6]==pytest.approx((1+2/3+.5,1))
    assert profile.points[7][1]==0
    assert profile.cap_bot_y==3


def test_abt1_independent_break_levels_and_toe_batter():
    p=battered_side_outline(2,cap_w_m=1,cap_d_m=.5,face_batter_1n=3,
        back_batter_1n=4,toe_m=.5,foot_d_m=1,above_m=.4,dirt_w_m=.3,
        front_break_h_m=.6,back_break_h_m=.4,toe_batter_1n=2)
    # Source abt1: upper front run=(3-1.6)/3; lower run=(1.6-1)/2.
    assert p.points[4]==pytest.approx((1+1.4/3,1.6))
    assert p.points[5]==pytest.approx((1+1.4/3+.6/2,1))
    # Source back run=(3-1.4)/4 from dirt-wall x=-.3.
    assert p.points[10]==pytest.approx((-.3-1.6/4,1))
    assert p.points[11]==pytest.approx((-.3-1.6/4,1.4))


@pytest.mark.parametrize('kwargs',[{'front_break_h_m':-1},{'back_break_h_m':3},{'toe_batter_1n':0},{'front_break_h_m':float('nan')},{'back_batter_1n':float('inf')}])
def test_abt1_rejects_invalid_breaks_and_batters(kwargs):
    with pytest.raises(ValueError):battered_side_outline(2,**kwargs)
