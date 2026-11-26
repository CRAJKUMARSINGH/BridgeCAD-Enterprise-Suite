#!/usr/bin/env python3
"""
BridgeGAD - Professional Bridge General Arrangement Drawing Generator

A comprehensive Python package for generating professional bridge drawings
with support for multiple bridge types, output formats, and modern interfaces.
"""

__version__ = "2.0.0"
__author__ = "BridgeGAD Development Team"

# Import main classes for easy access
from .bridge_types import (
    BridgeType,
    OutputFormat,
    MaterialType,
    LoadType,
    get_bridge_type_display_name,
    get_output_format_extension
)

from .parameters import (
    BridgeParameters,
    DrawingConfiguration,
    create_default_parameters,
    validate_parameter_ranges
)

from .drawing_generator import BridgeDrawingGenerator

# Package-level convenience functions


def create_slab_bridge(span_length: float, deck_width: float, **kwargs) -> BridgeParameters:
    """Create parameters for a slab bridge"""
    return BridgeParameters(
        bridge_type=BridgeType.SLAB,
        span_length=span_length,
        deck_width=deck_width,
        **kwargs
    )


def create_beam_bridge(span_length: float, deck_width: float, supports: int = 0, **kwargs) -> BridgeParameters:
    """Create parameters for a beam bridge"""
    return BridgeParameters(
        bridge_type=BridgeType.BEAM,
        span_length=span_length,
        deck_width=deck_width,
        supports=supports,
        **kwargs
    )


def generate_bridge_drawing(parameters: BridgeParameters, output_formats=None) -> dict:
    """
    High-level function to generate bridge drawing

    Args:
        parameters: Bridge configuration parameters
        output_formats: List of output formats (optional)

    Returns:
        Dictionary mapping output format to file path
    """
    generator = BridgeDrawingGenerator(parameters)
    return generator.generate_drawing(output_formats)


# Setup logging for the package
import logging


def setup_logging(level=logging.INFO):
    """Setup logging for the BridgeGAD package"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create logger for the package
    logger = logging.getLogger(__name__)
    logger.info(f"BridgeGAD v{__version__} initialized")

# FIX KIMI-001: do NOT call basicConfig at library import time — that hijacks
# the host application's logging configuration (Streamlit, uvicorn, etc.).
# Call bridge_gad.setup_logging() explicitly in your own entry point if you
# want BridgeGAD's default format.


# Export main classes and functions
__all__ = [
    # Main classes
    'BridgeDrawingGenerator',
    'BridgeParameters',
    'DrawingConfiguration',

    # Enums
    'BridgeType',
    'OutputFormat',
    'MaterialType',
    'LoadType',

    # Convenience functions
    'create_slab_bridge',
    'create_beam_bridge',
    'generate_bridge_drawing',
    'create_default_parameters',
    'validate_parameter_ranges',

    # Utility functions
    'get_bridge_type_display_name',
    'get_output_format_extension',
    'setup_logging',

    # Package info
    '__version__',
    '__author__'
]
