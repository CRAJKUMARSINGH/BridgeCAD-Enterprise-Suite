"""Core functionality for Bridge GAD Generator.

FIXES applied:
  GENSPARK-001 — config_file is now optional; falls back to Settings() defaults
  REPLIT-001   — BridgeDrawing._draw_* methods now delegate to BridgeGADGenerator
  BOLT-003     — compute_load / two_opt moved to routing.py; removed from this file
  QODER-004    — two_opt O(n³) kept in routing.py, not here
  KIMI-001     — removed module-level logging.basicConfig call (library anti-pattern)
"""

import logging
from pathlib import Path
from typing import Optional

import ezdxf
from ezdxf import units

from .config import Settings

# FIX KIMI-001: use getLogger only — do NOT call basicConfig in a library module
logger = logging.getLogger(__name__)


class BridgeDrawing:
    """Thin wrapper that delegates real drawing to BridgeGADGenerator.

    Kept for API backward-compatibility; all drawing logic lives in
    bridge_generator.BridgeGADGenerator.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.doc = None
        self.msp = None
        self._excel_path: Optional[Path] = None
        self._setup_document()

    def _setup_document(self) -> None:
        """Set up the DXF document with appropriate settings."""
        self.doc = ezdxf.new("R2010", setup=True)
        self.doc.units = units.M
        self.msp = self.doc.modelspace()
        self._setup_layers()

    def _setup_layers(self) -> None:
        """Set up layers from configuration."""
        for layer_name in self.settings.output.layers.values():
            if layer_name not in self.doc.layers:
                self.doc.layers.add(name=layer_name, color=7, linetype="CONTINUOUS")

    def set_excel_source(self, excel_path: Path) -> None:
        """Provide the Excel file that draw_bridge() will read."""
        self._excel_path = excel_path

    def draw_bridge(self) -> None:
        """Generate bridge drawing by delegating to BridgeGADGenerator."""
        logger.info("Starting bridge drawing generation via BridgeGADGenerator")
        if self._excel_path is None:
            logger.warning("No Excel source set — drawing will be empty")
            return
        try:
            from .bridge_generator import BridgeGADGenerator
            gen = BridgeGADGenerator(acad_version="R2010")
            if gen.read_variables_from_excel(self._excel_path):
                gen.setup_document()
                gen.draw_layout_and_axes()
                gen.draw_bridge_superstructure()
                gen.draw_piers_elevation()
                gen.draw_abutments()
                gen.draw_plan_view()
                gen.add_dimensions_and_labels()
                # Transfer the generated document
                self.doc = gen.doc
                self.msp = gen.msp
        except Exception as e:
            logger.error(f"draw_bridge delegation failed: {e}")
        logger.info("Bridge drawing generation completed")

    def save(self, output_path: Optional[Path] = None) -> None:
        """Save the drawing to a file."""
        if output_path is None:
            output_dir = Path(self.settings.output.directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"bridge_gad.{self.settings.output.format.lower()}"
        logger.info(f"Saving drawing to {output_path}")
        self.doc.saveas(str(output_path))


def generate_bridge_drawing(
    excel_file: Path,
    config_file: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """Generate a bridge drawing from an Excel file.

    Args:
        excel_file:  Path to the Excel file containing bridge parameters.
        config_file: Optional YAML config; uses Settings() defaults when absent.
        output_path: Optional output path; derived from settings when absent.

    Returns:
        Path to the generated DXF file.
    """
    # FIX GENSPARK-001: config is optional — fall back to defaults
    if config_file and config_file.exists():
        settings = Settings.from_yaml(config_file)
    else:
        settings = Settings()

    bridge = BridgeDrawing(settings)
    bridge.set_excel_source(excel_file)
    bridge.draw_bridge()

    if output_path is None:
        output_dir = Path(settings.output.directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"bridge_gad.{settings.output.format.lower()}"

    bridge.save(output_path)
    logger.info(f"Drawing saved: {output_path}")
    return output_path
