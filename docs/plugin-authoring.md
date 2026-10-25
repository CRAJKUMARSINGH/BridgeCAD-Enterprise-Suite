# Authoring a plugin

A plugin teaches the engine about one bridge type: its span range, its typical
values, and where its drawing geometry differs from the default.

## Scaffold

```bash
python scripts/scaffold_plugin.py my_bridge_type
```

## Layout

```
packages/bridgecad-plugins/bridgecad_plugins/plugins/<name>/
├── manifest.json      # identity, span range, standards, sheet overrides
├── defaults.yaml      # typical values for the type
└── draw_overrides.py  # per-sheet geometry overrides
```

## `manifest.json`

```json
{
  "name": "psc_boxgirder",
  "display_name": "PSC Box Girder",
  "span_range_m": [20, 45],
  "standards": ["IRC:5", "IRC:6", "IRC:112", "IRC:SP:55"],
  "categories": ["major_bridge"],
  "sheet_overrides": ["sheet3_cross_section", "sheet5_pier_abutment_details"],
  "defaults_file": "defaults.yaml",
  "version": "1.0.0"
}
```

`span_range_m` is inclusive and validated — a project outside the range gets a
warning, not a hard failure, because engineers do stretch ranges.

## `defaults.yaml`

Typical values, applied only where the workbook leaves a field blank. **Never
override an explicit input.** Include a source note per value so an engineer can
see where a number came from.

```yaml
superstructure:
  girder_depth_m: 2.1        # IRC:112 proportioning, L/20 for 42 m span
  web_thickness_mm: 300      # IRC:112 min
  camber_percent: 2.5        # IRC:112 Cl. 6.5
```

## `draw_overrides.py`

Override geometry per sheet. Signatures match the sheet module.

```python
from bridgecad_draw.sheets import sheet3_cross_section as base

def draw(msp, project, mapper, layers):
    """PSC box section replaces the I/T girder section."""
    base.draw_kerbs(msp, project, mapper, layers)
    base.draw_parapets(msp, project, mapper, layers)
    _draw_box_cell(msp, project, mapper, layers)   # box-specific
    base.draw_camber_curve(msp, project, mapper, layers)
```

Call the base first, then specialise. Overrides **must not mutate the model** —
read from `project`, draw to `msp`.

## Registration

Plugins are discovered by `PluginRegistry.discover_builtin()`, which scans the
`plugins/` directory for valid manifests. A plugin with an invalid manifest is
skipped with a logged reason, never a crash.

```bash
bridgecad-cli plugin list
bridgecad-cli plugin info psc_boxgirder
```

Built-in today: `rcc_tbeam` (6–30 m), `psc_igirder` (20–45 m),
`box_culvert` (2–8 m). Planned: `psc_boxgirder`, `solid_slab`, `voided_slab`,
`arch_bridge`, `steel_composite`, `pipe_culvert`, `cable_stayed`.

## Testing

Required before a plugin PR is merged:

```python
def test_psc_boxgirder_produces_valid_dxf():
    """All 7 sheets generate, all extents finite, all geometry non-empty."""
```

Plus: a span-range boundary test, and a check that `defaults.yaml` does not
override an explicitly set field.

## Checklist

- [ ] Manifest validates against the schema
- [ ] Span range is defensible against IRC practice
- [ ] `defaults.yaml` has a source note per value
- [ ] Overrides call base before specialising
- [ ] Overrides do not mutate the model
- [ ] Smoke test generates valid DXF on all 7 sheets
- [ ] Added to the plugin table in `GUIDE.md`
- [ ] A template exists for the type (or an issue says why not)

## Adding a template too

Templates live in `templates/<category>/<variant>.xlsx`, generated from the
plugin's defaults. 5 categories × 5 variants = 25 planned.
