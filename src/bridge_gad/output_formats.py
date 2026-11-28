"""
Multi-format output handler for Bridge GAD Generator
Supports DXF, DWG, PDF, SVG, and HTML canvas output
"""

from pathlib import Path
from typing import List, Dict
import logging

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np

logger = logging.getLogger(__name__)


class MultiFormatExporter:
    """Handles export to multiple formats: DXF, DWG, PDF, SVG, HTML Canvas"""

    def __init__(self, bridge_generator):
        self.bridge_generator = bridge_generator
        self.doc = bridge_generator.doc
        self.msp = bridge_generator.msp
        self.variables = bridge_generator.variables

    def export(self, output_path: Path, format_type: str = "auto") -> Path:
        """Export to specified format."""
        if format_type == "auto":
            format_type = output_path.suffix.lower().lstrip('.')

        format_type = format_type.lower()

        if format_type in ["dxf"]:
            return self._export_dxf(output_path)
        elif format_type in ["dwg"]:
            return self._export_dwg(output_path)
        elif format_type in ["pdf"]:
            return self._export_pdf(output_path)
        elif format_type in ["svg"]:
            return self._export_svg(output_path)
        elif format_type in ["html", "canvas"]:
            return self._export_html_canvas(output_path)
        elif format_type in ["png", "jpg", "jpeg"]:
            return self._export_image(output_path, format_type)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _export_dxf(self, output_path: Path) -> Path:
        """Export as DXF file."""
        self.doc.saveas(output_path)
        logger.info(f"DXF file exported to: {output_path}")
        return output_path

    def _export_dwg(self, output_path: Path) -> Path:
        """Export as DWG file using ezdxf conversion."""
        try:
            # First save as DXF, then use ezdxf's DWG capabilities
            temp_dxf = output_path.with_suffix('.temp.dxf')
            self.doc.saveas(temp_dxf)

            # For now, we'll save as DXF since DWG requires additional libraries
            # In production, you might want to use ODA File Converter or similar
            dwg_path = output_path.with_suffix('.dxf')  # Fallback to DXF
            self.doc.saveas(dwg_path)

            # Clean up temp file
            if temp_dxf.exists():
                temp_dxf.unlink()

            logger.info(f"DWG file (as DXF) exported to: {dwg_path}")
            return dwg_path

        except Exception as e:
            logger.warning(f"DWG export failed, falling back to DXF: {e}")
            return self._export_dxf(output_path.with_suffix('.dxf'))

    def _export_pdf(self, output_path: Path) -> Path:
        """Export as PDF using matplotlib."""
        # Extract drawing elements from DXF
        elements = self._extract_drawing_elements()

        # Create PDF using matplotlib
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))

        # Set up the plot
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title('Bridge General Arrangement Drawing', fontsize=16, fontweight='bold')

        # Draw all elements
        self._draw_elements_matplotlib(ax, elements)

        # Set appropriate limits
        self._set_plot_limits(ax, elements)

        # Add labels and annotations
        self._add_annotations_matplotlib(ax)

        # Save as PDF
        plt.tight_layout()
        plt.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"PDF file exported to: {output_path}")
        return output_path

    def _export_svg(self, output_path: Path) -> Path:
        """Export as SVG using matplotlib."""
        elements = self._extract_drawing_elements()

        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_aspect('equal')

        # Draw elements
        self._draw_elements_matplotlib(ax, elements)
        self._set_plot_limits(ax, elements)
        self._add_annotations_matplotlib(ax)

        # Save as SVG
        plt.savefig(output_path, format='svg', bbox_inches='tight')
        plt.close()

        logger.info(f"SVG file exported to: {output_path}")
        return output_path

    def _export_image(self, output_path: Path, format_type: str) -> Path:
        """Export as PNG/JPG using matplotlib."""
        elements = self._extract_drawing_elements()

        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        ax.set_aspect('equal')

        # Set background color for JPG
        if format_type.lower() in ['jpg', 'jpeg']:
            fig.patch.set_facecolor('white')
            ax.set_facecolor('white')

        # Draw elements
        self._draw_elements_matplotlib(ax, elements)
        self._set_plot_limits(ax, elements)
        self._add_annotations_matplotlib(ax)

        # Save as image
        plt.savefig(output_path, format=format_type, dpi=300, bbox_inches='tight',
                    facecolor='white' if format_type.lower() in ['jpg', 'jpeg'] else None)
        plt.close()

        logger.info(f"{format_type.upper()} file exported to: {output_path}")
        return output_path

    def _export_html_canvas(self, output_path: Path) -> Path:
        """Export as HTML with canvas visualization."""
        elements = self._extract_drawing_elements()

        # Create HTML with Canvas
        html_content = self._generate_html_canvas(elements)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML Canvas file exported to: {output_path}")
        return output_path

    def _extract_drawing_elements(self) -> Dict[str, List]:
        """Extract drawing elements from DXF document."""
        elements = {
            'lines': [],
            'rectangles': [],
            'polylines': [],
            'texts': [],
            'dimensions': [],
            'arcs': [],
            'circles': []
        }

        try:
            # Iterate through all entities in modelspace
            for entity in self.msp:
                if entity.dxftype() == 'LINE':
                    start = (entity.dxf.start.x, entity.dxf.start.y)
                    end = (entity.dxf.end.x, entity.dxf.end.y)
                    elements['lines'].append({'start': start, 'end': end})

                elif entity.dxftype() == 'LWPOLYLINE':
                    points = [(p[0], p[1]) for p in entity.get_points()]
                    elements['polylines'].append({
                        'points': points,
                        'closed': entity.closed
                    })

                elif entity.dxftype() == 'TEXT':
                    elements['texts'].append({
                        'text': entity.dxf.text,
                        'position': (entity.dxf.insert.x, entity.dxf.insert.y),
                        'height': entity.dxf.height,
                        'rotation': getattr(entity.dxf, 'rotation', 0)
                    })

                elif entity.dxftype() == 'MTEXT':
                    elements['texts'].append({
                        'text': entity.text,
                        'position': (entity.dxf.insert.x, entity.dxf.insert.y),
                        'height': entity.dxf.char_height,
                        'rotation': getattr(entity.dxf, 'rotation', 0)
                    })

                elif entity.dxftype() == 'CIRCLE':
                    elements['circles'].append({
                        'center': (entity.dxf.center.x, entity.dxf.center.y),
                        'radius': entity.dxf.radius
                    })

                elif entity.dxftype() == 'ARC':
                    elements['arcs'].append({
                        'center': (entity.dxf.center.x, entity.dxf.center.y),
                        'radius': entity.dxf.radius,
                        'start_angle': entity.dxf.start_angle,
                        'end_angle': entity.dxf.end_angle
                    })

        except Exception as e:
            logger.warning(f"Error extracting elements: {e}")

        return elements

    def _draw_elements_matplotlib(self, ax, elements):
        """Draw elements using matplotlib."""
        # Draw lines
        for line in elements['lines']:
            x_data = [line['start'][0], line['end'][0]]
            y_data = [line['start'][1], line['end'][1]]
            ax.plot(x_data, y_data, 'k-', linewidth=1)

        # Draw polylines
        for polyline in elements['polylines']:
            if len(polyline['points']) > 1:
                points = np.array(polyline['points'])
                if polyline['closed'] and len(points) > 2:
                    # Create closed polygon
                    poly = Polygon(points, fill=False, edgecolor='black', linewidth=1)
                    ax.add_patch(poly)
                else:
                    # Draw as line
                    ax.plot(points[:, 0], points[:, 1], 'k-', linewidth=1)

        # Draw circles
        for circle in elements['circles']:
            circle_patch = plt.Circle(circle['center'], circle['radius'],
                                      fill=False, edgecolor='black', linewidth=1)
            ax.add_patch(circle_patch)

        # Draw arcs
        for arc in elements['arcs']:
            # Approximate arc with line segments
            angles = np.linspace(np.radians(arc['start_angle']),
                                 np.radians(arc['end_angle']), 50)
            x = arc['center'][0] + arc['radius'] * np.cos(angles)
            y = arc['center'][1] + arc['radius'] * np.sin(angles)
            ax.plot(x, y, 'k-', linewidth=1)

        # Draw texts
        for text in elements['texts']:
            ax.text(text['position'][0], text['position'][1], text['text'],
                    fontsize=8, rotation=text['rotation'], ha='left', va='bottom')

    def _set_plot_limits(self, ax, elements):
        """Set appropriate plot limits based on drawing elements."""
        all_x, all_y = [], []

        # Collect all coordinates
        for line in elements['lines']:
            all_x.extend([line['start'][0], line['end'][0]])
            all_y.extend([line['start'][1], line['end'][1]])

        for polyline in elements['polylines']:
            for point in polyline['points']:
                all_x.append(point[0])
                all_y.append(point[1])

        if all_x and all_y:
            margin_x = (max(all_x) - min(all_x)) * 0.1
            margin_y = (max(all_y) - min(all_y)) * 0.1

            ax.set_xlim(min(all_x) - margin_x, max(all_x) + margin_x)
            ax.set_ylim(min(all_y) - margin_y, max(all_y) + margin_y)

    def _add_annotations_matplotlib(self, ax):
        """Add annotations and labels."""
        bridge_name = f"Bridge Length: {self.variables.get('LBRIDGE', 'N/A')}m"
        spans = f"Number of Spans: {self.variables.get('NSPAN', 'N/A')}"

        # Add text box with bridge info
        textstr = f'{bridge_name}\\n{spans}'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)

    def _generate_html_canvas(self, elements) -> str:
        """Generate HTML with Canvas visualization."""
        html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bridge GAD - Interactive View</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        canvas {{
            border: 1px solid #ccc;
            display: block;
            margin: 20px auto;
            background-color: white;
        }}
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        button {{
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #45a049;
        }}
        .info {{
            background-color: #e7f3ff;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Bridge General Arrangement Drawing</h1>

        <div class="info">
            <h3>Bridge Information:</h3>
            <p><strong>Bridge Length:</strong> {bridge_length}m</p>
            <p><strong>Number of Spans:</strong> {num_spans}</p>
            <p><strong>Span Length:</strong> {span_length}m</p>
        </div>

        <div class="controls">
            <button onclick="zoomIn()">Zoom In</button>
            <button onclick="zoomOut()">Zoom Out</button>
            <button onclick="resetView()">Reset View</button>
            <button onclick="toggleGrid()">Toggle Grid</button>
        </div>

        <canvas id="bridgeCanvas" width="1000" height="700"></canvas>

        <div class="info">
            <p><strong>Instructions:</strong> Use the controls above to zoom and pan. Click and drag to move the view.</p>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('bridgeCanvas');
        const ctx = canvas.getContext('2d');

        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let showGrid = true;

        // Bridge elements data
        const elements = {elements_json};

        function drawGrid() {{
            if (!showGrid) return;

            ctx.strokeStyle = '#e0e0e0';
            ctx.lineWidth = 0.5;

            const gridSize = 50 * scale;
            const startX = (-offsetX % gridSize);
            const startY = (-offsetY % gridSize);

            for (let x = startX; x < canvas.width; x += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}

            for (let y = startY; y < canvas.height; y += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}
        }}

        function transformPoint(x, y) {{
            return [
                (x * scale) + offsetX + canvas.width/2,
                (-y * scale) + offsetY + canvas.height/2  // Flip Y axis
            ];
        }}

        function drawBridge() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            drawGrid();

            // Draw lines
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 2;
            elements.lines.forEach(line => {{
                const [x1, y1] = transformPoint(line.start[0], line.start[1]);
                const [x2, y2] = transformPoint(line.end[0], line.end[1]);

                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();
            }});

            // Draw polylines
            elements.polylines.forEach(polyline => {{
                if (polyline.points.length > 1) {{
                    ctx.beginPath();
                    const [x1, y1] = transformPoint(polyline.points[0][0], polyline.points[0][1]);
                    ctx.moveTo(x1, y1);

                    for (let i = 1; i < polyline.points.length; i++) {{
                        const [x, y] = transformPoint(polyline.points[i][0], polyline.points[i][1]);
                        ctx.lineTo(x, y);
                    }}

                    if (polyline.closed) {{
                        ctx.closePath();
                    }}
                    ctx.stroke();
                }}
            }});

            // Draw text
            ctx.fillStyle = '#000';
            ctx.font = `${{12 * scale}}px Arial`;
            elements.texts.forEach(text => {{
                const [x, y] = transformPoint(text.position[0], text.position[1]);
                ctx.save();
                ctx.translate(x, y);
                ctx.rotate(-text.rotation * Math.PI / 180);
                ctx.fillText(text.text, 0, 0);
                ctx.restore();
            }});
        }}

        function zoomIn() {{
            scale *= 1.2;
            drawBridge();
        }}

        function zoomOut() {{
            scale /= 1.2;
            drawBridge();
        }}

        function resetView() {{
            scale = 1;
            offsetX = 0;
            offsetY = 0;
            drawBridge();
        }}

        function toggleGrid() {{
            showGrid = !showGrid;
            drawBridge();
        }}

        // Mouse interaction
        let isDragging = false;
        let lastMouseX, lastMouseY;

        canvas.addEventListener('mousedown', (e) => {{
            isDragging = true;
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
        }});

        canvas.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                const deltaX = e.clientX - lastMouseX;
                const deltaY = e.clientY - lastMouseY;

                offsetX += deltaX;
                offsetY += deltaY;

                lastMouseX = e.clientX;
                lastMouseY = e.clientY;

                drawBridge();
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
        drawBridge();
    </script>
</body>
</html>
        '''

        # Convert elements to JSON
        import json
        elements_json = json.dumps(elements)

        # Format the template
        return html_template.format(
            bridge_length=self.variables.get('LBRIDGE', 'N/A'),
            num_spans=self.variables.get('NSPAN', 'N/A'),
            span_length=self.variables.get('SPAN1', 'N/A'),
            elements_json=elements_json
        )


def create_multi_format_output(bridge_generator, output_path: Path, formats: List[str]) -> Dict[str, Path]:
    """Create multiple output formats from a bridge generator."""
    exporter = MultiFormatExporter(bridge_generator)
    results = {}

    for format_type in formats:
        try:
            format_output_path = output_path.with_suffix(f'.{format_type}')
            result_path = exporter.export(format_output_path, format_type)
            results[format_type] = result_path
            logger.info(f"Successfully created {format_type.upper()} output: {result_path}")
        except Exception as e:
            logger.error(f"Failed to create {format_type.upper()} output: {e}")
            results[format_type] = None

    return results
