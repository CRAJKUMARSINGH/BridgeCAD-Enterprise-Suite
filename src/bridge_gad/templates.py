#!/usr/bin/env python3
"""
Bridge Design Templates Library
Pre-configured templates for common bridge types
Integrates best practices from all 3 Bridge applications
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class BridgeTemplate:
    """Bridge design template"""
    name: str
    description: str
    bridge_type: str
    parameters: Dict[str, Any]
    tags: List[str]
    difficulty: str  # 'simple', 'medium', 'complex'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class TemplateLibrary:
    """Library of pre-configured bridge templates"""

    def __init__(self):
        self.templates = self._create_default_templates()

    def _create_default_templates(self) -> Dict[str, BridgeTemplate]:
        """Create default template library"""
        templates = {}

        # 1. Simple Single-Span Slab Bridge
        templates['simple_slab'] = BridgeTemplate(
            name="Simple Slab Bridge",
            description="Single-span concrete slab bridge for small crossings",
            bridge_type="slab",
            parameters={
                'SCALE1': 100,
                'SCALE2': 50,
                'SKEW': 0,
                'DATUM': 100,
                'TOPRL': 110,
                'LBRIDGE': 15000,  # 15m span
                'NSPAN': 1,
                'CCBR': 7500,  # 7.5m width
                'SLABTH': 600,  # 600mm thick
                'WCTH': 75,
                'LASLAB': 5000,
                'ABTLEN': 8000,
                'ABTH': 3000,
                'ABTW': 1000,
            },
            tags=['simple', 'single-span', 'slab', 'beginner'],
            difficulty='simple'
        )

        # 2. Multi-Span Beam Bridge
        templates['multi_span_beam'] = BridgeTemplate(
            name="Multi-Span Beam Bridge",
            description="Three-span beam bridge for medium crossings",
            bridge_type="beam",
            parameters={
                'SCALE1': 150,
                'SCALE2': 75,
                'SKEW': 0,
                'DATUM': 100,
                'TOPRL': 115,
                'LBRIDGE': 75000,  # 75m total (3x25m)
                'NSPAN': 3,
                'SPAN1': 25000,
                'SPAN2': 25000,
                'SPAN3': 25000,
                'CCBR': 10000,  # 10m width
                'SLABTH': 250,
                'WCTH': 75,
                'LASLAB': 6000,
                'ABTLEN': 11000,
                'ABTH': 4000,
                'ABTW': 1200,
                'PIERTW': 1500,
                'PIERTH': 2500,
                'CAPB': 2000,
                'CAPH': 600,
                'FUTW': 3000,
                'FUTD': 2000,
            },
            tags=['multi-span', 'beam', 'intermediate'],
            difficulty='medium'
        )

        # 3. Skew Bridge
        templates['skew_bridge'] = BridgeTemplate(
            name="Skew Bridge",
            description="Single-span bridge with 30-degree skew angle",
            bridge_type="slab",
            parameters={
                'SCALE1': 120,
                'SCALE2': 60,
                'SKEW': 30,  # 30-degree skew
                'DATUM': 100,
                'TOPRL': 112,
                'LBRIDGE': 20000,  # 20m span
                'NSPAN': 1,
                'CCBR': 8000,
                'SLABTH': 700,
                'WCTH': 75,
                'LASLAB': 5500,
                'ABTLEN': 9000,
                'ABTH': 3500,
                'ABTW': 1100,
            },
            tags=['skew', 'single-span', 'slab', 'advanced'],
            difficulty='medium'
        )

        # 4. Large Multi-Span Bridge
        templates['large_bridge'] = BridgeTemplate(
            name="Large Multi-Span Bridge",
            description="Five-span bridge for major crossings",
            bridge_type="beam",
            parameters={
                'SCALE1': 200,
                'SCALE2': 100,
                'SKEW': 0,
                'DATUM': 100,
                'TOPRL': 120,
                'LBRIDGE': 150000,  # 150m total (5x30m)
                'NSPAN': 5,
                'SPAN1': 30000,
                'SPAN2': 30000,
                'SPAN3': 30000,
                'SPAN4': 30000,
                'SPAN5': 30000,
                'CCBR': 12000,  # 12m width (dual carriageway)
                'SLABTH': 300,
                'WCTH': 75,
                'LASLAB': 7000,
                'ABTLEN': 13000,
                'ABTH': 5000,
                'ABTW': 1500,
                'PIERTW': 2000,
                'PIERTH': 3000,
                'CAPB': 2500,
                'CAPH': 700,
                'FUTW': 4000,
                'FUTD': 2500,
            },
            tags=['large', 'multi-span', 'beam', 'advanced'],
            difficulty='complex'
        )

        # 5. Complex 23-Span Bridge
        templates['complex_23_span'] = BridgeTemplate(
            name="Complex 23-Span Bridge",
            description="Large-scale bridge with 23 spans for major infrastructure",
            bridge_type="beam",
            parameters={
                'SCALE1': 300,
                'SCALE2': 150,
                'SKEW': 0,
                'DATUM': 100,
                'TOPRL': 125,
                'LBRIDGE': 690000,  # 690m total (23x30m)
                'NSPAN': 23,
                'CCBR': 14000,  # 14m width
                'SLABTH': 350,
                'WCTH': 75,
                'LASLAB': 8000,
                'ABTLEN': 15000,
                'ABTH': 6000,
                'ABTW': 1800,
                'PIERTW': 2500,
                'PIERTH': 3500,
                'CAPB': 3000,
                'CAPH': 800,
                'FUTW': 5000,
                'FUTD': 3000,
            },
            tags=['complex', 'multi-span', 'beam', 'expert', 'large-scale'],
            difficulty='complex'
        )

        # Generate individual span lengths for 23-span bridge
        for i in range(1, 24):
            templates['complex_23_span'].parameters[f'SPAN{i}'] = 30000

        return templates

    def get_template(self, name: str) -> BridgeTemplate:
        """Get template by name"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name]

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                'name': t.name,
                'description': t.description,
                'bridge_type': t.bridge_type,
                'difficulty': t.difficulty,
                'tags': t.tags
            }
            for t in self.templates.values()
        ]

    def get_by_difficulty(self, difficulty: str) -> List[BridgeTemplate]:
        """Get templates by difficulty level"""
        return [t for t in self.templates.values() if t.difficulty == difficulty]

    def get_by_tag(self, tag: str) -> List[BridgeTemplate]:
        """Get templates by tag"""
        return [t for t in self.templates.values() if tag in t.tags]

    def save_template(self, template: BridgeTemplate, output_dir: Path):
        """Save template to JSON file"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = template.name.lower().replace(' ', '_') + '.json'
        filepath = output_dir / filename

        with open(filepath, 'w') as f:
            f.write(template.to_json())

        return filepath

    def save_all_templates(self, output_dir: Path):
        """Save all templates to JSON files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for template in self.templates.values():
            filepath = self.save_template(template, output_dir)
            saved_files.append(filepath)

        return saved_files


# Convenience functions
def get_template(name: str) -> BridgeTemplate:
    """Get a bridge template by name"""
    library = TemplateLibrary()
    return library.get_template(name)


def list_all_templates() -> List[Dict[str, Any]]:
    """List all available templates"""
    library = TemplateLibrary()
    return library.list_templates()


def create_templates_directory(output_dir: str = 'templates'):
    """Create templates directory with all JSON files"""
    library = TemplateLibrary()
    return library.save_all_templates(Path(output_dir))
