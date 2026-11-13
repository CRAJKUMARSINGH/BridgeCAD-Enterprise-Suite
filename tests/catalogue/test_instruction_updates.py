"""Regression checks for applicable v.md proposals against the current catalogue."""
from decimal import Decimal
import importlib.util
from pathlib import Path

import pytest
from PIL import Image

from bridgecad_catalogue import registry, sweep
from bridgecad_catalogue.resolve import resolve
from bridgecad_catalogue.schema import Violation

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pwd_instruction_generator", ROOT / "scripts/generate_all_pwd_gads.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def test_choice_sweep_is_numeric_and_can_be_resolved():
    variants = sweep.matrix(["carriageway_width=3.5,7.5,11"])
    assert [x['carriageway_width'] for x in variants] == [Decimal('3.5'), Decimal('7.5'), Decimal('11')]
    assert all(resolve(registry.by_id('BR-I-2022-009'), x) for x in variants)


@pytest.mark.parametrize('expr', ['carriageway_width=3.5,bad', 'carriageway_width=3.5,', 'carriageway_width=3.5,8', 'carriageway_width=NaN', 'span_length_m=NaN:20:1', 'span_length_m=10:20:Infinity', 'span_length_m=20:10:1', 'span_length_m=a:20:1', 'total_length_m=1:2:1', 'foundation_type=1:2:1'])
def test_bad_sweeps_are_rejected(expr):
    with pytest.raises(Violation):
        sweep.parse(expr)


@pytest.mark.parametrize('card', registry.load(), ids=lambda c: c['id'])
def test_every_existing_identity_still_builds(card):
    params = resolve(card, {})
    params['id'] = card['id']
    generator._build_project(params)


@pytest.mark.parametrize('field', ['superstructure_type', 'foundation_type', 'abutment_type', 'bearing_type', 'pier_material'])
def test_unknown_identity_does_not_become_a_plausible_default(field):
    params = resolve(registry.by_id('BR-I-2022-001'), {})
    params['id'] = 'BR-I-2022-001'
    params[field] = 'MISSPELLED'
    with pytest.raises(KeyError):
        generator._build_project(params)


def test_blank_png_is_reported(monkeypatch, tmp_path):
    from bridgecad_draw.engines import png_engine
    def blank(source, target, dpi):
        Image.new('RGB', (20, 20), 'white').save(target)
    monkeypatch.setattr(png_engine, 'render_png', blank)
    assert 'entirely blank' in generator._render_pngs([Path('test.dxf')], tmp_path)[0]


def test_render_exception_is_reported(monkeypatch, tmp_path):
    from bridgecad_draw.engines import png_engine
    def broken(*args, **kwargs):
        raise RuntimeError('injected rendering failure')
    monkeypatch.setattr(png_engine, 'render_png', broken)
    assert 'injected rendering failure' in generator._render_pngs([Path('test.dxf')], tmp_path)[0]


def test_nonblank_png_is_accepted(monkeypatch, tmp_path):
    from bridgecad_draw.engines import png_engine
    def ink(source, target, dpi):
        image = Image.new('RGB', (20, 20), 'white')
        image.putpixel((10, 10), (0, 0, 0))
        image.save(target)
    monkeypatch.setattr(png_engine, 'render_png', ink)
    assert generator._render_pngs([Path('test.dxf')], tmp_path) == []


def test_partial_rejection_is_not_a_success(capsys):
    # SBC=15 rejects the OPEN foundation card but the RAFT card can still resolve.
    assert generator.main(['--type', 'BR-I-2022-001', '--type', 'BR-I-2022-003', '--set', 'sbc_t_per_m2=15', '--dry-run']) == 1
    assert '[REJECT]' in capsys.readouterr().out


def test_generation_is_deterministic_and_reports_render_status(monkeypatch, tmp_path):
    import json
    from bridgecad_draw.engines import png_engine
    params = resolve(registry.by_id('BR-I-2022-001'), {})
    params['id'] = 'BR-I-2022-001'
    monkeypatch.setenv('SKIP_PNG', '1')
    assert generator.generate_one(params, tmp_path / 'a')[1]
    assert generator.generate_one(params, tmp_path / 'b')[1]
    a = tmp_path / 'a' / params['id']
    b = tmp_path / 'b' / params['id']
    files = list(a.glob('*.dxf'))
    assert len(files) == 9
    assert all(f.read_bytes() == (b / f.name).read_bytes() for f in files)
    assert json.loads((a / 'render-status.json').read_text())['png'] == 'skipped'
    monkeypatch.delenv('SKIP_PNG')
    def blank(source, target, dpi):
        Image.new('RGB', (20, 20), 'white').save(target)
    monkeypatch.setattr(png_engine, 'render_png', blank)
    result = generator.generate_one(params, tmp_path / 'c')
    assert not result[1]
    assert json.loads((tmp_path / 'c' / params['id'] / 'render-status.json').read_text())['png'] == 'failed'
