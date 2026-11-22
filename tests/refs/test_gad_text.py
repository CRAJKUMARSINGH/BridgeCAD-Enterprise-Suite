"""Input preservation tests; these are not renderer acceptance tests."""
from dataclasses import replace
from pathlib import Path
import re
import pytest
from bridgecad_refs.gad_text import HEADER, BRIDGE, SPAN, ABUTMENT, loads, dumps, read, write


def fixture_text():
    # Distinct values make ordering swaps visible. Illustrative, not design input.
    header = [100, 25, 15, 90, 110, 1200, 1260, 10, 1, 2]
    survey = [1200, 95.125, 1260, 96.375]
    bridge = [2, 30, 1210, 105.125, 104, .3, .2, 7.5, .65, .55, .15,
              103.8, 103, 1.5, 1, 10, 6, 1]
    spans = [10, 96, 1, 3, 8, 12, 97, 1.2, 3.5, 8.5]
    abutment = [.3, .75, 1.2, 10, 98, 1, 97, 1.5, 1, 3, 98]
    return '\n'.join(map(str, header + survey + bridge + spans + abutment)) + '\n'


def test_roundtrip_and_positions(tmp_path):
    data = loads(fixture_text())
    assert data.survey == ((1200, 95.125), (1260, 96.375))
    assert data.bridge[3] == 105.125
    assert data.span_records[1] == (12, 97, 1.2, 3.5, 8.5)
    assert data.abutment == (.3, .75, 1.2, 10, 98, 1, 97, 1.5, 1, 3, 98)
    path = tmp_path / 'gad.txt'
    write(path, data)
    assert read(path) == data
    assert loads('\ufeff' + fixture_text().replace('\n', '\r\n')) == data


def test_schema_matches_active_archive_reads():
    source = (Path(__file__).resolve().parents[2] / 'ATTACHED ASSETS' /
              'LISP_Solid_Slab_GAD_In_Toto.lsp').read_text()
    source = '\n'.join(line.split(';', 1)[0] for line in source.splitlines())
    fields = re.findall(r'\(setq\s+(\w+)\s+\((?:atof|atoi)\s+\(read-line f\)\)', source, re.I)
    assert tuple(k.lower() for k in fields) == HEADER + ('x', 'y') + BRIDGE + SPAN + ABUTMENT


@pytest.mark.parametrize('line,value', [(0,'0'),(1,'-1'),(2,'90'),(3,'90.5'),
    (9,'-1'),(9,'1000000000'),(14,'0'),(14,'2.5'),(20,'NaN'),(21,'inf'),(22,'oops')])
def test_invalid_input(line, value):
    lines = fixture_text().splitlines()
    lines[line] = value
    with pytest.raises(ValueError): loads('\n'.join(lines))


@pytest.mark.parametrize('text', [fixture_text().rsplit('\n',2)[0],
                                  fixture_text() + '999\n', fixture_text() + '\n'])
def test_missing_or_extra_lines(text):
    with pytest.raises(ValueError): loads(text)


def test_bad_write_preserves_destination(tmp_path):
    path = tmp_path / 'gad.txt'; path.write_text('existing')
    data = loads(fixture_text())
    with pytest.raises(ValueError): write(path, replace(data, survey=()))
    assert path.read_text() == 'existing'
    with pytest.raises(ValueError): dumps(replace(data, abutment=(1,)))
