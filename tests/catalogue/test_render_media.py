"""Print-media and white-paper visibility regressions."""
from pathlib import Path
import importlib.util
import ezdxf
import pytest
from PIL import Image, ImageChops
from bridgecad_draw.engines.png_engine import paper_size_inches, render_png

@pytest.mark.parametrize('paper,w,h',[('A0',1189,841),('A1',841,594),('A2',594,420),('A3',420,297),('A4',297,210)])
def test_media_orientation(paper,w,h):
    assert paper_size_inches(paper,'landscape') == (w/25.4,h/25.4)
    assert paper_size_inches(paper,'portrait') == (h/25.4,w/25.4)

@pytest.mark.parametrize('paper,orientation',[('Letter','portrait'),('A3','sideways')])
def test_invalid_media_is_rejected(paper,orientation):
    with pytest.raises(ValueError): paper_size_inches(paper,orientation)

def test_aci7_schedule_visible_on_white_and_media_dimensions(tmp_path):
    doc=ezdxf.new('R2010');m=doc.modelspace()
    m.add_lwpolyline([(0,0),(100,0),(100,40),(0,40)],close=True)
    m.add_text('Schedule row',dxfattribs={'height':3,'insert':(10,20),'color':7})
    dxf=tmp_path/'table.dxf';doc.saveas(dxf)
    target=tmp_path/'table.png';render_png(dxf,target,dpi=30,size_in=paper_size_inches('A3','portrait'))
    with Image.open(target) as image:
        assert abs(image.width-297/25.4*30)<2
        assert abs(image.height-420/25.4*30)<2
        rgb=image.convert('RGB')
        assert ImageChops.difference(rgb,Image.new('RGB',rgb.size,'white')).getbbox() is not None

def test_cli_accepts_png_media_in_dry_run(capsys):
    path=Path(__file__).resolve().parents[2]/'scripts/generate_all_pwd_gads.py'
    spec=importlib.util.spec_from_file_location('pwd_media_cli',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.main(['--type','BR-I-2022-002','--render-paper','A3','--render-orientation','portrait','--dry-run'])==0
    assert '1 variant(s)' in capsys.readouterr().out
