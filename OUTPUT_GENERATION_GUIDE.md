# Bridge GAD Output Generation Guide

> **Scope note:** this guide targets the **legacy** src/bridge_gad/ output driver, not the Suite. For Suite output see GUIDE.md §5.

## Quick Start

### Generate All Drawings (Recommended)
```bash
python -m bridge_gad.generate_all_drawings output_directory
```

This generates:
- 5 single GAD drawings (DXF + PDF)
- 35 detailed sheet drawings (DXF + PDF) 
- 6 booklet PDFs (5 per-template + 1 master)
- 10 Excel parameter workbooks
- Complete manifest and ZIP bundle

### Generate Custom Variants
```bash
python -m bridge_gad.generate_all_drawings output_directory --n 10 --base-template continuous_3x12m
```

Generate 10 parameterised variants based on a template.

### Custom PDF Layout
```bash
python -m bridge_gad.generate_all_drawings output_directory --pdf-layout A3_landscape
```

Available layouts: A0_landscape, A1_landscape, A2_landscape, A3_landscape, A4_landscape, A4_portrait

## Output Structure

```
output_directory/
├── DXF/
│   ├── 01_gad_single/          # Single GAD drawings
│   └── 02_phase_two_7sheet/    # Detailed 7-sheet packages
├── PDF/
│   ├── 01_gad_single/          # Single GAD PDFs
│   ├── 02_phase_two_7sheet/    # Detailed sheet PDFs
│   └── 03_booklets/            # Complete drawing booklets
├── Workbooks/                  # Excel parameter files
├── Manifests/                  # CSV manifest + JSON summary
└── ZIP_Bundles/                # Complete archive
```

## Key Files

- `ALL_DRAWINGS_COMPLETE.pdf` - Master 40-page booklet with all drawings
- `COMPLETE_DRAWINGS_BUNDLE.zip` - Complete archive (19MB)
- `manifest.csv` - File inventory with sizes and metadata
- `run_summary.json` - Detailed generation statistics

## Templates Available

1. **simple_12m** - Simple 12m span bridge
2. **continuous_3x12m** - Continuous 3-span 12m bridge
3. **girder_4x18m** - Girder bridge 4x18m
4. **box_culvert_8m** - Box culvert 8m
5. **arch_24m** - Arch bridge 24m

## Troubleshooting

### Text Rendering Warnings
Warnings about text rendering are normal - the system has fallback mechanisms to render drawings without text if needed.

### Empty PDFs
If PDFs appear empty, check that:
1. DXF files were generated successfully
2. The DXF contains drawing entities (not just text)
3. Matplotlib backend is properly installed

### Memory Issues
For large batch runs (N > 50), consider:
- Running in smaller batches
- Increasing system memory
- Using the `--seed` parameter for reproducible results

## Integration Examples

### Python Script
```python
from pathlib import Path
from bridge_gad.generate_all_drawings import generate_all_drawings

output_dir = Path("my_bridge_drawings")
result = generate_all_drawings(output_dir)
print(f"Generated: {result['master_pdf']}")
```

### Custom Templates
Add new templates in `src/bridge_gad/bridge_canvas_features.py` under `BRIDGE_TEMPLATES`.

## Performance

- **Single Template:** ~30 seconds
- **All 5 Templates:** ~3 minutes  
- **10 Variants:** ~5 minutes
- **File Sizes:** 64KB-81KB per PDF, 70KB-85KB per DXF

## Requirements

- Python 3.8+
- ezdxf
- matplotlib
- pandas
- openpyxl

Install with: `pip install -r requirements.txt`
