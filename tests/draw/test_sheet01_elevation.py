"""The browser GAD draws each end assembly once from the selected profile."""

from pathlib import Path


FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "src"
SOURCE = FRONTEND / "sheets" / "Sheet01Overview.tsx"


def test_end_assemblies_share_one_profile_and_are_mirrored():
    body = SOURCE.read_text(encoding="utf-8")
    elevation = body.split('className="elevation"')[1].split('className="plan"')[0]

    assert "supports.filter((support) => support.end)" in elevation
    assert 'data-abutment={name}' in elevation
    assert 'name: i === 0 ? "A1" : i === count ? "A2"' in body
    assert "outboard: i === 0 ? -1 : 1" in body
    assert "ABUTMENT_PROFILES[abutment]" in elevation
    assert "outboard * (u - .5)" in elevation
    for part in ("abutment-fill", "abutment-cap", "footing-fill", "approach-slab", "dirt-wall", "dirt-wall-weep"):
        assert f'className="{part}"' in elevation
    assert 'className="barrier"' in elevation
    assert 'height={capBottomY - roadY}' in elevation


def test_plan_and_elevation_use_the_same_pier_joint_locations():
    body = SOURCE.read_text(encoding="utf-8")
    assert "const piers = supports.slice(1, -1);" in body
    assert body.count('piers.map(({ name, x }) => <line') == 2
    assert body.count('data-joint={name}') == 2
    assert ".gad-joint {" in (FRONTEND / "styles.css").read_text(encoding="utf-8")
