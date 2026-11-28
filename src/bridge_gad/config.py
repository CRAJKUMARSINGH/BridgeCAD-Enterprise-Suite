from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
import yaml


# Bridge-specific config
class BridgeConfig(BaseModel):
    spans: int = 3
    span_lengths: List[float] = [30.0, 35.0, 30.0]
    deck_width: float = 12.0
    girder_spacing: float = 3.0
    girder_depth: float = 1.5
    deck_thickness: float = 0.2


# Drawing-specific config
class DrawingConfig(BaseModel):
    paper_size: str = "A3"
    scale: float = 100.0
    line_weight: float = 0.35
    text_height: float = 2.5


# Output configuration
class OutputConfig(BaseModel):
    directory: str = "output"
    format: str = "DXF"
    layers: Dict[str, str] = {
        "outline": "BRIDGE_OUTLINE",
        "dimensions": "DIMENSIONS",
        "text": "TEXT",
        "centerline": "CENTERLINE",
    }


class Settings(BaseModel):
    """Application settings.

    FIX BOLT-005: alpha/beta/max_hops are routing fields unrelated to bridge
    drawing.  They are kept here for backward-compatibility with config.yaml
    but are now clearly documented as routing-only.  Bridge parameters live
    in the `bridge` sub-model.
    """

    # --- Routing / load-balancing fields (used by routing.py only) ---
    alpha: float = Field(0.85, ge=0, le=1, description="Routing cost weight for distance")
    beta: float = Field(0.15, ge=0, le=1, description="Routing cost weight for load")
    max_hops: int = Field(8, ge=1, description="Maximum routing hops")
    seed: int = 42

    # --- General ---
    log_level: str = "INFO"

    # --- Bridge drawing ---
    bridge: BridgeConfig = BridgeConfig()
    drawing: DrawingConfig = DrawingConfig()
    output: OutputConfig = OutputConfig()

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        with path.open() as f:
            data = yaml.safe_load(f)
        return cls(**(data or {}))


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """Load settings from configuration file or use defaults."""
    if config_path and config_path.exists():
        return Settings.from_yaml(config_path)
    return Settings()
