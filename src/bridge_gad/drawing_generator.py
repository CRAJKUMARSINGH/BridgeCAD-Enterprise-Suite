#!/usr/bin/env python3
"""
Bridge Drawing Generator

Main class for generating professional bridge drawings with support
for multiple bridge types and output formats.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .bridge_types import BridgeType, OutputFormat
from .parameters import BridgeParameters, DrawingConfiguration

logger = logging.getLogger(__name__)


class BridgeDrawingGenerator:
    """Main class for generating bridge drawings"""

    def __init__(self, parameters: BridgeParameters, config: Optional[DrawingConfiguration] = None):
        """Initialize the drawing generator

        Args:
            parameters: Bridge configuration parameters
            config: Drawing configuration (optional)
        """
        self.params = parameters
        self.config = config or DrawingConfiguration()

        # Get coordinate transformation functions
        self.transforms = parameters.get_coordinate_transformations()

        # Drawing state
        self.doc = None  # DXF document
        self.msp = None  # DXF model space
        self.figure = None  # Matplotlib figure
        self.elements = []  # Drawing elements for multi-format support

        # Setup logging for this instance
        self.logger = logging.getLogger(f"{__name__}.{self.params.bridge_type.value}")

        # Bridge-specific drawing strategies
        self.drawing_strategies = {
            BridgeType.SLAB: self._draw_slab_bridge,
            BridgeType.BEAM: self._draw_beam_bridge,
            # Additional bridge types can be added here
        }

        self.logger.info(f"Initialized drawing generator for {self.params.bridge_type.value} bridge")

    def generate_drawing(self, output_formats: Optional[List[OutputFormat]] = None) -> Dict[OutputFormat, str]:
        """Generate bridge drawing in specified formats

        Args:
            output_formats: List of output formats (uses parameter default if None)

        Returns:
            Dictionary mapping output format to file path
        """
        if output_formats is None:
            output_formats = self.params.output_formats

        results = {}

        try:
            # Generate the drawing using appropriate strategy
            strategy = self.drawing_strategies.get(self.params.bridge_type)
            if not strategy:
                raise NotImplementedError(f"Bridge type {self.params.bridge_type.value} not implemented")

            self.logger.info(f"Generating {self.params.bridge_type.value} bridge drawing")
            strategy()

            # Export to requested formats
            for format_type in output_formats:
                if format_type == OutputFormat.ALL:
                    # Generate all supported formats
                    for fmt in [OutputFormat.DXF, OutputFormat.PDF, OutputFormat.SVG, OutputFormat.PNG]:
                        file_path = self._export_format(fmt)
                        results[fmt] = file_path
                else:
                    file_path = self._export_format(format_type)
                    results[format_type] = file_path

            self.logger.info(f"Successfully generated {len(results)} output files")
            return results

        except Exception as e:
            self.logger.error(f"Failed to generate drawing: {e}")
            raise

    def _draw_slab_bridge(self):
        """Draw slab bridge (enhanced version of original functionality)"""
        self.logger.info("Drawing slab bridge elevation and plan")

        # Initialize DXF document
        self._setup_dxf()

        # Draw main structural elements
        self._draw_slab_elevation()
        self._draw_slab_plan()
        self._draw_abutments()
        self._draw_supports()

        # Add annotations and dimensions
        self._add_title_block()
        self._add_grid_lines()
        self._add_dimensions()

        self.logger.info("Slab bridge drawing completed")

    def _draw_beam_bridge(self):
        """Draw beam bridge (from superior implementations)"""
        self.logger.info("Drawing beam bridge elevation and plan")

        # Initialize DXF document
        self._setup_dxf()

        # Draw beam-specific elements
        self._draw_beam_elevation()
        self._draw_beam_plan()
        self._draw_beam_supports()

        # Add professional annotations
        self._add_title_block()
        self._add_grid_lines()
        self._add_dimensions()

        self.logger.info("Beam bridge drawing completed")

    def _setup_dxf(self):
        """Setup DXF document with professional layers and styles"""
        try:
            import ezdxf

            self.doc = ezdxf.new("R2010", setup=True)
            self.msp = self.doc.modelspace()

            # Setup professional layers
            self._setup_professional_layers()
            self._setup_text_styles()
            self._setup_dimension_styles()

            self.logger.info("DXF document setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup DXF document: {e}")
            raise

    def _setup_professional_layers(self):
        """Setup professional DXF layers with colors and descriptions"""
        layers = [
            ("STRUCTURE", 1, "Main structural elements"),
            ("DIMENSIONS", 6, "Dimension lines and text"),
            ("ANNOTATIONS", 3, "Text and labels"),
            ("CENTERLINES", 4, "Center lines"),
            ("HATCHING", 9, "Section hatching"),
            ("DETAILS", 2, "Detail elements"),
            ("GRID", 8, "Grid lines and axes"),
            ("FOUNDATION", 5, "Foundation elements")
        ]

        for name, color, description in layers:
            try:
                layer = self.doc.layers.new(name=name)
                layer.dxf.color = color
                layer.description = description
            except Exception as e:
                self.logger.warning(f"Could not create layer {name}: {e}")

    def _setup_text_styles(self):
        """Setup professional text styles"""
        try:
            self.doc.styles.new("MAIN_TEXT", dxfattribs={
                'font': 'arial.ttf',
                'height': 2.5,
                'width': 0.8
            })

            self.doc.styles.new("TITLE_TEXT", dxfattribs={
                'font': 'arial.ttf',
                'height': 5.0,
                'width': 1.0
            })

            self.doc.styles.new("DIMENSION_TEXT", dxfattribs={
                'font': 'arial.ttf',
                'height': 2.0,
                'width': 0.8
            })
        except Exception as e:
            self.logger.warning(f"Could not create text styles: {e}")

    def _setup_dimension_styles(self):
        """Setup professional dimension styles"""
        try:
            dimstyle = self.doc.dimstyles.new('PROFESSIONAL')
            dimstyle.dxf.dimasz = 2.0  # Arrow size
            dimstyle.dxf.dimtxt = 2.5  # Text height
            dimstyle.dxf.dimexe = 1.0  # Extension line extension
            dimstyle.dxf.dimexo = 0.6  # Extension line offset
            dimstyle.dxf.dimgap = 0.6  # Gap between dimension line and text
            dimstyle.dxf.dimtxsty = "DIMENSION_TEXT"
        except Exception as e:
            self.logger.warning(f"Could not create dimension style: {e}")

    def _draw_slab_elevation(self):
        """Draw slab bridge elevation view"""
        # Main deck slab
        left_x = self.transforms['hpos'](self.params.left)
        right_x = self.transforms['hpos'](self.params.right)
        top_y = self.transforms['vpos'](110.0)  # RTL equivalent
        bottom_y = self.transforms['vpos'](109.0)  # Soffit

        # Draw deck rectangle
        deck_points = [
            (left_x, top_y),
            (right_x, top_y),
            (right_x, bottom_y),
            (left_x, bottom_y),
            (left_x, top_y)
        ]

        self.msp.add_lwpolyline(deck_points, close=True,
                                dxfattribs={'layer': 'STRUCTURE', 'lineweight': 50})

        self.logger.debug("Drew slab elevation")

    def _draw_slab_plan(self):
        """Draw slab bridge plan view (offset for plan view)"""
        plan_offset = -200  # mm offset for plan view

        left_x = self.transforms['hpos'](self.params.left)
        right_x = self.transforms['hpos'](self.params.right)
        top_y = self.params.deck_width * 1000 / 2 + plan_offset
        bottom_y = -self.params.deck_width * 1000 / 2 + plan_offset

        # Draw plan rectangle
        plan_points = [
            (left_x, top_y),
            (right_x, top_y),
            (right_x, bottom_y),
            (left_x, bottom_y),
            (left_x, top_y)
        ]

        self.msp.add_lwpolyline(plan_points, close=True,
                                dxfattribs={'layer': 'STRUCTURE', 'lineweight': 25})

        self.logger.debug("Drew slab plan")

    def _draw_abutments(self):
        """Draw bridge abutments"""
        # Simple abutment representation
        abt_width = 2000  # 2m abutments

        for x_pos in [self.params.left, self.params.right]:
            x_center = self.transforms['hpos'](x_pos)

            # Abutment rectangle
            abutment_points = [
                (x_center - abt_width / 2, self.transforms['vpos'](105.0)),
                (x_center + abt_width / 2, self.transforms['vpos'](105.0)),
                (x_center + abt_width / 2, self.transforms['vpos'](110.0)),
                (x_center - abt_width / 2, self.transforms['vpos'](110.0)),
                (x_center - abt_width / 2, self.transforms['vpos'](105.0))
            ]

            self.msp.add_lwpolyline(abutment_points, close=True,
                                    dxfattribs={'layer': 'STRUCTURE'})

        self.logger.debug("Drew abutments")

    def _draw_supports(self):
        """Draw intermediate supports if any"""
        if self.params.supports <= 0:
            return

        span_length = self.params.span_length
        support_spacing = span_length / (self.params.supports + 1)

        for i in range(1, self.params.supports + 1):
            support_x = self.params.left + i * support_spacing
            x_pos = self.transforms['hpos'](support_x)

            # Simple pier representation
            pier_points = [
                (x_pos - 500, self.transforms['vpos'](102.0)),
                (x_pos + 500, self.transforms['vpos'](102.0)),
                (x_pos + 500, self.transforms['vpos'](110.0)),
                (x_pos - 500, self.transforms['vpos'](110.0)),
                (x_pos - 500, self.transforms['vpos'](102.0))
            ]

            self.msp.add_lwpolyline(pier_points, close=True,
                                    dxfattribs={'layer': 'STRUCTURE'})

        self.logger.debug(f"Drew {self.params.supports} supports")

    def _draw_beam_elevation(self):
        """Draw beam bridge elevation.

        FIX CURSOR-005: raise NotImplementedError instead of silently
        producing a slab drawing when the user selects BridgeType.BEAM.
        """
        raise NotImplementedError(
            "Beam bridge elevation drawing is not yet implemented. "
            "Please use BridgeType.SLAB or contribute a beam implementation."
        )

    def _draw_beam_plan(self):
        """Draw beam bridge plan — not yet implemented (FIX CURSOR-005)."""
        raise NotImplementedError(
            "Beam bridge plan drawing is not yet implemented."
        )

    def _draw_beam_supports(self):
        """Draw beam-specific supports — not yet implemented (FIX CURSOR-005)."""
        raise NotImplementedError(
            "Beam bridge support drawing is not yet implemented."
        )

    def _add_title_block(self):
        """Add professional title block"""
        # Title block position (bottom right)
        title_x, title_y = 200000, 20000
        title_w, title_h = 180000, 60000

        # Title block border
        self.msp.add_lwpolyline([
            (title_x, title_y),
            (title_x + title_w, title_y),
            (title_x + title_w, title_y + title_h),
            (title_x, title_y + title_h),
            (title_x, title_y)
        ], dxfattribs={'layer': 'STRUCTURE'})

        # Drawing title
        self.msp.add_text(
            self.params.drawing_title,
            dxfattribs={
                'insert': (title_x + 5000, title_y + title_h - 15000),
                'height': 4000,
                'style': 'TITLE_TEXT',
                'layer': 'ANNOTATIONS'
            }
        )

        # Project information
        info_lines = [
            f"Project: {self.params.project_name}",
            f"Scale: 1:{int(self.params.scale1)}",
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            f"Bridge Type: {self.params.bridge_type.value.title()}",
            f"Span: {self.params.span_length}m x {self.params.deck_width}m"
        ]

        for i, line in enumerate(info_lines):
            self.msp.add_text(
                line,
                dxfattribs={
                    'insert': (title_x + 5000, title_y + 35000 - i * 8000),
                    'height': 2500,
                    'style': 'MAIN_TEXT',
                    'layer': 'ANNOTATIONS'
                }
            )

        self.logger.debug("Added title block")

    def _add_grid_lines(self):
        """Add reference grid lines"""
        if not self.config.show_grid:
            return

        # This would implement comprehensive grid system
        self.logger.debug("Grid lines feature - to be implemented")

    def _add_dimensions(self):
        """Add professional dimensions"""
        # Add span dimension
        left_x = self.transforms['hpos'](self.params.left)
        right_x = self.transforms['hpos'](self.params.right)
        dim_y = self.transforms['vpos'](115.0)  # Above bridge

        # Create dimension line (simplified)
        self.msp.add_line((left_x, dim_y), (right_x, dim_y),
                          dxfattribs={'layer': 'DIMENSIONS'})

        # Dimension text
        mid_x = (left_x + right_x) / 2
        self.msp.add_text(
            f"{self.params.span_length:.1f}m",
            dxfattribs={
                'insert': (mid_x, dim_y + 2000),
                'height': 2000,
                'style': 'DIMENSION_TEXT',
                'layer': 'DIMENSIONS'
            }
        )

        self.logger.debug("Added dimensions")

    def _export_format(self, format_type: OutputFormat) -> str:
        """Export drawing to specified format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{self.params.project_name}_{self.params.bridge_type.value}_{timestamp}"

        if format_type == OutputFormat.DXF:
            filename = f"{base_filename}.dxf"
            if self.doc:
                self.doc.saveas(filename)
                self.logger.info(f"Exported DXF: {filename}")
            return filename

        elif format_type == OutputFormat.PDF:
            filename = f"{base_filename}.pdf"
            self._export_pdf(filename)
            return filename

        elif format_type == OutputFormat.SVG:
            filename = f"{base_filename}.svg"
            self._export_svg(filename)
            return filename

        elif format_type == OutputFormat.PNG:
            filename = f"{base_filename}.png"
            self._export_png(filename)
            return filename

        else:
            raise NotImplementedError(f"Export format {format_type.value} not implemented")

    def _export_pdf(self, filename: str):
        """Export to PDF format (placeholder)"""
        self.logger.info(f"PDF export placeholder: {filename}")
        # This would implement PDF export using reportlab

    def _export_svg(self, filename: str):
        """Export to SVG format (placeholder)"""
        self.logger.info(f"SVG export placeholder: {filename}")
        # This would implement SVG export

    def _export_png(self, filename: str):
        """Export to PNG format (placeholder)"""
        self.logger.info(f"PNG export placeholder: {filename}")
        # This would implement PNG export using matplotlib
