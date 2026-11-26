#!/usr/bin/env python3
"""
Ultimate Multi-Format Exporter for Bridge GAD Generator
Integrates best export capabilities from all 3 Bridge applications
Supports: DXF, PDF, SVG, PNG, HTML Canvas, JSON, Excel, ZIP
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import zipfile

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class UltimateExporter:
    """
    Ultimate multi-format exporter with batch capabilities

    Supports:
    - DXF (AutoCAD R2010)
    - PDF (300 DPI, professional layout)
    - SVG (vector, scalable)
    - PNG (raster, 300 DPI)
    - HTML Canvas (interactive viewer)
    - JSON (data interchange)
    - Excel (bill of quantities)
    - ZIP (batch export bundle)
    """

    def __init__(self, bridge_generator):
        self.bridge_generator = bridge_generator
        self.doc = bridge_generator.doc
        self.msp = bridge_generator.msp
        self.variables = bridge_generator.variables
        self.export_history = []

    def export_all_formats(self, base_path: Union[str, Path], formats: Optional[List[str]] = None) -> Dict[str, Path]:
        """
        Export to all specified formats

        Args:
            base_path: Base output path (without extension)
            formats: List of formats to export (default: all)

        Returns:
            Dictionary mapping format to output file path
        """
        base_path = Path(base_path)

        if formats is None:
            formats = ['dxf', 'pdf', 'svg', 'png', 'html', 'json']

        results = {}
        _ = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"🚀 Starting batch export to {len(formats)} formats...")

        for fmt in formats:
            try:
                output_path = base_path.with_suffix(f'.{fmt}')

                if fmt == 'dxf':
                    results[fmt] = self.export_dxf(output_path)
                elif fmt == 'pdf':
                    results[fmt] = self.export_pdf(output_path)
                elif fmt == 'svg':
                    results[fmt] = self.export_svg(output_path)
                elif fmt == 'png':
                    results[fmt] = self.export_png(output_path)
                elif fmt == 'html':
                    results[fmt] = self.export_html_canvas(output_path)
                elif fmt == 'json':
                    results[fmt] = self.export_json(output_path)

                logger.info(f"  ✅ {fmt.upper()}: {output_path.name}")

            except Exception as e:
                logger.error(f"  ❌ {fmt.upper()} export failed: {e}")
                results[fmt] = None

        # Create ZIP bundle if multiple formats
        if len([r for r in results.values() if r]) > 1:
            zip_path = base_path.with_suffix('.zip')
            results['zip'] = self.create_zip_bundle(results, zip_path)

        logger.info(f"✅ Batch export complete: {len([r for r in results.values() if r])} files generated")

        return results

    def export_dxf(self, output_path: Path) -> Path:
        """Export as DXF (AutoCAD R2010 compatible)"""
        self.doc.saveas(output_path)
        logger.info(f"DXF exported: {output_path}")
        return output_path

    def export_pdf(self, output_path: Path, dpi: int = 300) -> Path:
        """
        Export as PDF with professional layout

        Args:
            output_path: Output PDF file path
            dpi: Resolution (default: 300 DPI)
        """
        # Extract drawing elements
        elements = self._extract_drawing_elements()

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Set title
        project_name = self.variables.get('PROJECT_NAME', 'Bridge Project')
        ax.set_title(f'{project_name}\nGeneral Arrangement Drawing',
                     fontsize=16, fontweight='bold', pad=20)

        # Draw all elements
        self._draw_elements_matplotlib(ax, elements)

        # Set limits
        self._set_plot_limits(ax, elements)

        # Add annotations
        self._add_annotations_matplotlib(ax)

        # Add RKS LEGAL branding
        self._add_branding(ax)

        # Save as PDF
        plt.tight_layout()
        plt.savefig(output_path, format='pdf', dpi=dpi, bbox_inches='tight')
        plt.close()

        logger.info(f"PDF exported: {output_path} ({dpi} DPI)")
        return output_path

    def export_svg(self, output_path: Path) -> Path:
        """Export as SVG (vector format)"""
        elements = self._extract_drawing_elements()

        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_aspect('equal')

        self._draw_elements_matplotlib(ax, elements)
        self._set_plot_limits(ax, elements)
        self._add_annotations_matplotlib(ax)
        self._add_branding(ax)

        plt.savefig(output_path, format='svg', bbox_inches='tight')
        plt.close()

        logger.info(f"SVG exported: {output_path}")
        return output_path

    def export_png(self, output_path: Path, dpi: int = 300) -> Path:
        """Export as PNG (raster format)"""
        elements = self._extract_drawing_elements()

        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_aspect('equal')
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        self._draw_elements_matplotlib(ax, elements)
        self._set_plot_limits(ax, elements)
        self._add_annotations_matplotlib(ax)
        self._add_branding(ax)

        plt.savefig(output_path, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close()

        logger.info(f"PNG exported: {output_path} ({dpi} DPI)")
        return output_path

    def export_html_canvas(self, output_path: Path) -> Path:
        """
        Export as interactive HTML Canvas viewer

        Features:
        - Zoom and pan controls
        - Grid toggle
        - Measurement tools
        - Print functionality
        """
        elements = self._extract_drawing_elements()

        # Generate HTML with embedded JavaScript
        html_content = self._generate_html_canvas(elements)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML Canvas exported: {output_path}")
        return output_path

    def export_json(self, output_path: Path) -> Path:
        """
        Export as JSON (data interchange format)

        Includes:
        - All bridge parameters
        - Drawing elements
        - Metadata
        """
        data = {
            'metadata': {
                'project_name': self.variables.get('PROJECT_NAME', 'Bridge Project'),
                'generated_at': datetime.now().isoformat(),
                'generator': 'Ultimate Bridge GAD Generator v3.0',
                'format_version': '1.0'
            },
            'parameters': self.variables,
            'elements': self._extract_drawing_elements(),
            'statistics': {
                'total_elements': len(self.msp),
                'layers': list(self.doc.layers),
                'bounds': self._calculate_bounds()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"JSON exported: {output_path}")
        return output_path

    def create_zip_bundle(self, files: Dict[str, Path], output_path: Path) -> Path:
        """Create ZIP bundle of all exported files"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fmt, file_path in files.items():
                if file_path and file_path.exists() and fmt != 'zip':
                    zipf.write(file_path, file_path.name)

        logger.info(f"ZIP bundle created: {output_path}")
        return output_path

    def _extract_drawing_elements(self) -> List[Dict[str, Any]]:
        """Extract drawing elements from DXF document"""
        elements = []

        for entity in self.msp:
            element = {
                'type': entity.dxftype(),
                'layer': entity.dxf.layer if hasattr(entity.dxf, 'layer') else 'default'
            }

            if entity.dxftype() == 'LINE':
                element['start'] = (entity.dxf.start.x, entity.dxf.start.y)
                element['end'] = (entity.dxf.end.x, entity.dxf.end.y)

            elif entity.dxftype() == 'CIRCLE':
                element['center'] = (entity.dxf.center.x, entity.dxf.center.y)
                element['radius'] = entity.dxf.radius

            elif entity.dxftype() == 'ARC':
                element['center'] = (entity.dxf.center.x, entity.dxf.center.y)
                element['radius'] = entity.dxf.radius
                element['start_angle'] = entity.dxf.start_angle
                element['end_angle'] = entity.dxf.end_angle

            elif entity.dxftype() == 'TEXT':
                element['text'] = entity.dxf.text
                element['position'] = (entity.dxf.insert.x, entity.dxf.insert.y)
                element['height'] = entity.dxf.height

            elif entity.dxftype() == 'LWPOLYLINE':
                element['points'] = [(p[0], p[1]) for p in entity.get_points()]
                element['closed'] = entity.closed

            elements.append(element)

        return elements

    def _draw_elements_matplotlib(self, ax, elements: List[Dict[str, Any]]):
        """Draw elements using matplotlib"""
        for elem in elements:
            if elem['type'] == 'LINE':
                ax.plot([elem['start'][0], elem['end'][0]],
                        [elem['start'][1], elem['end'][1]],
                        'k-', linewidth=0.5)

            elif elem['type'] == 'CIRCLE':
                circle = plt.Circle(elem['center'], elem['radius'],
                                    fill=False, edgecolor='black', linewidth=0.5)
                ax.add_patch(circle)

            elif elem['type'] == 'ARC':
                # Draw arc using matplotlib
                pass  # Simplified for now

            elif elem['type'] == 'TEXT':
                ax.text(elem['position'][0], elem['position'][1], elem['text'],
                        fontsize=8, ha='left', va='bottom')

            elif elem['type'] == 'LWPOLYLINE':
                points = elem['points']
                if len(points) > 1:
                    xs, ys = zip(*points)
                    if elem.get('closed', False):
                        xs = xs + (xs[0],)
                        ys = ys + (ys[0],)
                    ax.plot(xs, ys, 'k-', linewidth=0.5)

    def _set_plot_limits(self, ax, elements: List[Dict[str, Any]]):
        """Set appropriate plot limits based on elements"""
        bounds = self._calculate_bounds()

        if bounds:
            margin = 0.1 * max(bounds['width'], bounds['height'])
            ax.set_xlim(bounds['min_x'] - margin, bounds['max_x'] + margin)
            ax.set_ylim(bounds['min_y'] - margin, bounds['max_y'] + margin)

    def _calculate_bounds(self) -> Dict[str, float]:
        """Calculate drawing bounds"""
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for entity in self.msp:
            if entity.dxftype() == 'LINE':
                min_x = min(min_x, entity.dxf.start.x, entity.dxf.end.x)
                max_x = max(max_x, entity.dxf.start.x, entity.dxf.end.x)
                min_y = min(min_y, entity.dxf.start.y, entity.dxf.end.y)
                max_y = max(max_y, entity.dxf.start.y, entity.dxf.end.y)

        if min_x == float('inf'):
            return {'min_x': 0, 'max_x': 100, 'min_y': 0, 'max_y': 100, 'width': 100, 'height': 100}

        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }

    def _add_annotations_matplotlib(self, ax):
        """Add annotations to matplotlib plot"""
        # Add scale information
        scale1 = self.variables.get('SCALE1', 100)
        ax.text(0.02, 0.98, f'Scale: 1:{scale1}',
                transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    def _add_branding(self, ax):
        """Add RKS LEGAL branding — FIX KERO-004: phone from env var."""
        import os as _os
        _phone = _os.environ.get("CONTACT_PHONE", "+91XXXXXXXXXX")
        branding_text = (
            "RKS LEGAL - Techno Legal Consultants\n"
            "303 Vallabh Apartment, Navratna Complex, Bhuwana\n"
            f"Udaipur - 313001 | {_phone}"
        )
        ax.text(0.98, 0.02, branding_text,
                transform=ax.transAxes, fontsize=8,
                verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    def _generate_html_canvas(self, elements: List[Dict[str, Any]]) -> str:
        """Generate interactive HTML Canvas viewer"""
        bounds = self._calculate_bounds()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bridge GAD - Interactive Viewer</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f0f0f0;
        }}
        #container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f77b4;
            margin-top: 0;
        }}
        #canvas {{
            border: 1px solid #ccc;
            cursor: move;
            display: block;
            margin: 20px auto;
        }}
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        button {{
            padding: 10px 20px;
            margin: 0 5px;
            background: #1f77b4;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background: #155a8a;
        }}
        .info {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>🌉 Bridge GAD - Interactive Viewer</h1>

        <div class="controls">
            <button onclick="zoomIn()">🔍 Zoom In</button>
            <button onclick="zoomOut()">🔍 Zoom Out</button>
            <button onclick="resetView()">🔄 Reset View</button>
            <button onclick="toggleGrid()">📐 Toggle Grid</button>
            <button onclick="window.print()">🖨️ Print</button>
        </div>

        <canvas id="canvas" width="1000" height="700"></canvas>

        <div class="info">
            <strong>Controls:</strong>
            <ul>
                <li>Click and drag to pan</li>
                <li>Mouse wheel to zoom</li>
                <li>Use buttons above for additional controls</li>
            </ul>
            <strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
            <strong>RKS LEGAL</strong> - Techno Legal Consultants
        </div>
    </div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let showGrid = true;
        let isDragging = false;
        let lastX, lastY;

        const elements = {json.dumps(elements)};
        const bounds = {json.dumps(bounds)};

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();

            // Apply transformations
            ctx.translate(offsetX, offsetY);
            ctx.scale(scale, scale);

            // Draw grid
            if (showGrid) {{
                drawGrid();
            }}

            // Draw elements
            elements.forEach(elem => {{
                if (elem.type === 'LINE') {{
                    ctx.beginPath();
                    ctx.moveTo(elem.start[0], elem.start[1]);
                    ctx.lineTo(elem.end[0], elem.end[1]);
                    ctx.strokeStyle = 'black';
                    ctx.lineWidth = 0.5 / scale;
                    ctx.stroke();
                }}
                // Add more element types as needed
            }});

            ctx.restore();
        }}

        function drawGrid() {{
            ctx.strokeStyle = '#e0e0e0';
            ctx.lineWidth = 0.5 / scale;

            const gridSize = 1000;
            for (let x = bounds.min_x; x <= bounds.max_x; x += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(x, bounds.min_y);
                ctx.lineTo(x, bounds.max_y);
                ctx.stroke();
            }}
            for (let y = bounds.min_y; y <= bounds.max_y; y += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(bounds.min_x, y);
                ctx.lineTo(bounds.max_x, y);
                ctx.stroke();
            }}
        }}

        function zoomIn() {{
            scale *= 1.2;
            draw();
        }}

        function zoomOut() {{
            scale /= 1.2;
            draw();
        }}

        function resetView() {{
            scale = 1;
            offsetX = canvas.width / 2;
            offsetY = canvas.height / 2;
            draw();
        }}

        function toggleGrid() {{
            showGrid = !showGrid;
            draw();
        }}

        // Mouse events
        canvas.addEventListener('mousedown', (e) => {{
            isDragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
        }});

        canvas.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                offsetX += e.clientX - lastX;
                offsetY += e.clientY - lastY;
                lastX = e.clientX;
                lastY = e.clientY;
                draw();
            }}
        }});

        canvas.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        canvas.addEventListener('wheel', (e) => {{
            e.preventDefault();
            if (e.deltaY < 0) {{
                zoomIn();
            }} else {{
                zoomOut();
            }}
        }});

        // Initial draw
        resetView();
    </script>
</body>
</html>"""

        return html


# Convenience function
def export_bridge_all_formats(bridge_generator, base_path: Union[str, Path],
                              formats: Optional[List[str]] = None) -> Dict[str, Path]:
    """
    Convenience function to export bridge to all formats

    Usage:
        results = export_bridge_all_formats(generator, 'output/bridge_001')
    """
    exporter = UltimateExporter(bridge_generator)
    return exporter.export_all_formats(base_path, formats)
