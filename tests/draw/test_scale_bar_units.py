"""A graphic scale must encode the same physical distance it labels."""
import math
import ezdxf
import pytest
from bridgecad_draw.primitives import scale_bar

@pytest.mark.parametrize('denom',[50,100,200,400])
@pytest.mark.parametrize('length',[0.5,2.0,5.0])
def test_scale_bar_paper_geometry_and_metre_labels(denom,length):
    doc=ezdxf.new();m=doc.modelspace()
    scale_bar(m,10,20,denom,segments=4,seg_len_m=length,text_height=2.5)
    labels={e.dxf.text:e for e in m.query('TEXT')}
    assert f'{4*length:g}m' in labels
    start=labels['0m'].dxf.align_point
    end=labels[f'{4*length:g}m'].dxf.align_point
    assert end.x-start.x==pytest.approx(4*length*1000/denom)
    # The outer outline must span the same paper length as the scale ticks.
    outline=next(e for e in m.query('LWPOLYLINE') if e.dxf.layer=='SYM-SCALE')
    xs=[p[0] for p in outline.get_points()]
    assert max(xs)-min(xs)==pytest.approx(4*length*1000/denom)

@pytest.mark.parametrize('args',[{'scale_denom':0},{'scale_denom':math.inf},
    {'seg_len_m':-1},{'seg_len_m':math.nan},{'segments':2.5},
    {'segments':True},{'text_height':0}])
def test_invalid_scale_bar_inputs_raise(args):
    doc=ezdxf.new();params=dict(scale_denom=100,seg_len_m=2,segments=4,text_height=2.5)
    params.update(args)
    with pytest.raises(ValueError):scale_bar(doc.modelspace(),0,0,**params)
    assert len(doc.modelspace())==0
