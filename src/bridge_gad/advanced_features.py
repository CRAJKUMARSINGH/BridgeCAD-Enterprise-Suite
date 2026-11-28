"""
Advanced Features Module for Bridge GAD Generator
- 3D Visualization
- Design Templates
- Quality Checks
- Design Comparison
"""

import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BridgeTemplate:
    """Pre-designed bridge templates"""
    name: str
    description: str
    parameters: Dict[str, float]
    bridge_type: str


class BridgeTemplates:
    """Collection of standard bridge designs"""

    TEMPLATES = {
        "rcc_slab_simple": BridgeTemplate(
            name="RCC Slab - Simple Span",
            description="Single span RCC slab bridge (12m span)",
            bridge_type="Simple Slab",
            parameters={
                'NSPAN': 1, 'SPAN1': 12, 'CCBR': 8.0, 'SLBTHE': 0.6,
                'RTL': 110.98, 'DATUM': 100, 'PIERTW': 1.2, 'FUTW': 4.5
            }
        ),
        "rcc_slab_continuous": BridgeTemplate(
            name="RCC Slab - Continuous Span",
            description="3-span continuous RCC slab (4x12m)",
            bridge_type="Continuous Slab",
            parameters={
                'NSPAN': 3, 'SPAN1': 12, 'CCBR': 10.5, 'SLBTHE': 0.75,
                'RTL': 110.98, 'DATUM': 100, 'PIERTW': 1.5, 'FUTW': 5.5
            }
        ),
        "rcc_girder": BridgeTemplate(
            name="RCC Girder Bridge",
            description="Multi-beam RCC girder bridge (4x18m)",
            bridge_type="Girder Bridge",
            parameters={
                'NSPAN': 4, 'SPAN1': 18, 'CCBR': 12.0, 'SLBTHE': 0.9,
                'RTL': 111.5, 'DATUM': 100, 'PIERTW': 2.0, 'FUTW': 6.5
            }
        ),
        "box_culvert": BridgeTemplate(
            name="Box Culvert",
            description="Single cell box culvert (8m span)",
            bridge_type="Box Culvert",
            parameters={
                'NSPAN': 1, 'SPAN1': 8, 'CCBR': 8.0, 'SLBTHE': 0.5,
                'RTL': 110.0, 'DATUM': 100, 'PIERTW': 0.8, 'FUTW': 3.5
            }
        ),
        "arch_bridge": BridgeTemplate(
            name="Arch Bridge",
            description="RCC arch bridge (24m span)",
            bridge_type="Arch",
            parameters={
                'NSPAN': 1, 'SPAN1': 24, 'CCBR': 11.0, 'SLBTHE': 0.8,
                'RTL': 112.0, 'DATUM': 100, 'PIERTW': 2.5, 'FUTW': 7.0
            }
        )
    }

    @classmethod
    def get_template(cls, template_id: str) -> Optional[BridgeTemplate]:
        """Get template by ID"""
        return cls.TEMPLATES.get(template_id)

    @classmethod
    def list_templates(cls) -> Dict[str, str]:
        """List all available templates"""
        return {k: v.name for k, v in cls.TEMPLATES.items()}


class DesignQualityChecker:
    """Validates bridge design against IRC & IS standards"""

    # IRC & IS Code Limits
    STANDARDS = {
        'min_clearance': 5.5,  # Vertical clearance (m)
        'max_slob_slope': 0.33,  # Slab slope ratio
        'min_pier_width': 1.0,  # Minimum pier width (m)
        'min_footing_depth': 0.8,  # Minimum footing depth (m)
        'max_span_slab': 50,  # Maximum simple span for slab (m)
        'max_cantilever': 5,  # Maximum cantilever (m)
        'min_kerb_height': 0.75,  # Minimum kerb height (m)
        'min_kerb_thickness': 0.23,  # Minimum kerb thickness (m)
    }

    def __init__(self, variables: Dict):
        self.variables = variables
        self.issues = []
        self.warnings = []

    def validate(self) -> Dict:
        """Run comprehensive design checks"""
        try:
            self.check_vertical_clearance()
            self.check_span_limits()
            self.check_pier_dimensions()
            self.check_footing_requirements()
            self.check_deck_thickness()
            self.check_kerb_standards()

            return {
                'is_valid': len(self.issues) == 0,
                'critical_issues': self.issues,
                'warnings': self.warnings,
                'compliance_score': self.calculate_score()
            }
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {'is_valid': False, 'error': str(e)}

    def check_vertical_clearance(self):
        """Check vertical clearance IRC 5:2015"""
        rtl = float(self.variables.get('RTL', 110.98))
        datum = float(self.variables.get('DATUM', 100))
        clearance = rtl - datum

        if clearance < self.STANDARDS['min_clearance']:
            self.issues.append(f"Clearance {clearance}m < {self.STANDARDS['min_clearance']}m (IRC 5)")

    def check_span_limits(self):
        """Check span limitations"""
        nspan = int(self.variables.get('NSPAN', 3))
        span1 = float(self.variables.get('SPAN1', 12))

        if span1 > self.STANDARDS['max_span_slab']:
            self.warnings.append(f"Span {span1}m exceeds typical slab bridge limit")

        if nspan > 10:
            self.warnings.append(f"Unusual number of spans: {nspan}")

    def check_pier_dimensions(self):
        """Check pier width requirements"""
        piertw = float(self.variables.get('PIERTW', 1.2))

        if piertw < self.STANDARDS['min_pier_width']:
            self.issues.append(f"Pier width {piertw}m < {self.STANDARDS['min_pier_width']}m minimum")

    def check_footing_requirements(self):
        """Check footing depth"""
        futd = float(self.variables.get('FUTD', 1.0))

        if futd < self.STANDARDS['min_footing_depth']:
            self.warnings.append(f"Footing depth {futd}m may be insufficient")

    def check_deck_thickness(self):
        """Check slab thickness"""
        slbthe = float(self.variables.get('SLBTHE', 0.75))
        span1 = float(self.variables.get('SPAN1', 12))

        min_thickness = span1 / 20  # L/20 rule
        if slbthe < min_thickness:
            self.issues.append(f"Slab thickness {slbthe}m < {min_thickness:.2f}m (L/20 rule)")

    def check_kerb_standards(self):
        """Check kerb dimensions"""
        kerbw = float(self.variables.get('KERBW', 0.23))
        _ = float(self.variables.get('KERBD', 0.15))

        if kerbw < self.STANDARDS['min_kerb_thickness']:
            self.warnings.append(f"Kerb thickness {kerbw}m may be below standard")

    def calculate_score(self) -> int:
        """Calculate design compliance score (0-100)"""
        max_issues = 10
        issue_count = len(self.issues) + len(self.warnings) * 0.5
        score = max(0, 100 - (issue_count / max_issues * 100))
        return int(score)


class Bridge3DVisualizer:
    """Generate 3D visualization data for bridge"""

    def __init__(self, variables: Dict):
        self.variables = variables

    def generate_3d_mesh(self) -> Dict:
        """Generate 3D mesh data (vertices & faces)"""
        try:
            nspan = int(self.variables.get('NSPAN', 3))
            span1 = float(self.variables.get('SPAN1', 12))
            ccbr = float(self.variables.get('CCBR', 11.1))
            slbthe = float(self.variables.get('SLBTHE', 0.75))

            # Deck slab vertices
            vertices = []
            faces = []

            for i in range(nspan + 1):
                x = i * span1
                # Top surface
                for y_pos in [0, ccbr]:
                    vertices.append([x, y_pos, 0])
                # Bottom surface
                for y_pos in [0, ccbr]:
                    vertices.append([x, y_pos, -slbthe])

            # Generate faces (simplified)
            num_verts_per_span = 4
            for span in range(nspan):
                v_idx = span * num_verts_per_span
                # Top face
                faces.append([v_idx, v_idx + num_verts_per_span,
                              v_idx + num_verts_per_span + 1, v_idx + 1])
                # Side faces
                faces.append([v_idx, v_idx + 2, v_idx + num_verts_per_span + 2,
                              v_idx + num_verts_per_span])

            return {
                'vertices': np.array(vertices),
                'faces': faces,
                'metadata': {
                    'spans': nspan,
                    'span_length': span1,
                    'width': ccbr,
                    'thickness': slbthe
                }
            }
        except Exception as e:
            logger.error(f"3D mesh generation error: {e}")
            return {}

    def get_summary_stats(self) -> Dict:
        """Get 3D visualization summary."""
        try:
            mesh = self.generate_3d_mesh()
            # FIX CURSOR-004: guard against None AND empty numpy arrays
            vertices = mesh.get("vertices")
            if vertices is None or not hasattr(vertices, "__len__") or len(vertices) == 0:
                return {}
            return {
                "total_vertices": len(vertices),
                "x_range": [float(vertices[:, 0].min()), float(vertices[:, 0].max())],
                "y_range": [float(vertices[:, 1].min()), float(vertices[:, 1].max())],
                "z_range": [float(vertices[:, 2].min()), float(vertices[:, 2].max())],
                "volume_approximate": float(
                    self.variables.get("SPAN1", 12)
                    * self.variables.get("CCBR", 11.1)
                    * self.variables.get("SLBTHE", 0.75)
                    * self.variables.get("NSPAN", 3)
                ),
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}


class DesignComparator:
    """Compare two bridge designs"""

    def __init__(self, design1: Dict, design2: Dict):
        self.design1 = design1
        self.design2 = design2

    def compare(self) -> Dict:
        """Compare key parameters"""
        comparison = {}

        for key in set(self.design1.keys()) | set(self.design2.keys()):
            val1 = self.design1.get(key, 'N/A')
            val2 = self.design2.get(key, 'N/A')

            try:
                diff = float(val2) - float(val1) if isinstance(val1, (int, float)) and isinstance(val2, (int, float)) else None
                comparison[key] = {
                    'design1': val1,
                    'design2': val2,
                    'difference': diff,
                    'percent_change': (diff / float(val1) * 100) if diff and val1 else None
                }
            except Exception:
                comparison[key] = {'design1': val1, 'design2': val2}

        return comparison

    def get_summary(self) -> str:
        """Generate comparison summary"""
        comparison = self.compare()
        summary = "Design Comparison Summary:\n"

        for key, data in comparison.items():
            if data.get('difference') is not None:
                pct = data.get('percent_change', 0)
                summary += f"  {key}: {data['design1']} → {data['design2']} ({pct:+.1f}%)\n"

        return summary
