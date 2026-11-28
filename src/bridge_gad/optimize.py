"""Optimization module for Bridge GAD Generator."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
from scipy.optimize import minimize

from .config import Settings


@dataclass
class DesignVariables:
    """Design variables for bridge optimization."""
    span_lengths: List[float]
    num_spans: int
    girder_spacing: float
    girder_depth: float
    deck_thickness: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert design variables to dictionary."""
        return {
            'span_lengths': self.span_lengths,
            'num_spans': self.num_spans,
            'girder_spacing': self.girder_spacing,
            'girder_depth': self.girder_depth,
            'deck_thickness': self.deck_thickness
        }


class BridgeOptimizer:
    """Optimizer for bridge design parameters."""

    def __init__(self, settings: Settings):
        """Initialize the bridge optimizer.

        Args:
            settings: Bridge settings and constraints
        """
        self.settings = settings
        self.bridge_cfg = settings.bridge

    def _objective_function(self, x: np.ndarray) -> float:
        """Objective function to minimize (total cost).

        Args:
            x: Design variables as a flat array

        Returns:
            float: Total cost to minimize
        """
        # Extract design variables from x
        n = len(self.bridge_cfg.span_lengths)
        span_lengths = x[:n]
        girder_spacing = x[n]
        girder_depth = x[n + 1]
        deck_thickness = x[n + 2]

        # Simple cost model (can be expanded)
        _ = sum(span_lengths)
        num_girders = self._calculate_num_girders(girder_spacing)

        # Material costs (simplified)
        concrete_volume = self._calculate_concrete_volume(
            span_lengths, girder_depth, deck_thickness, num_girders
        )
        steel_weight = self._calculate_steel_weight(
            span_lengths, girder_depth, num_girders
        )

        # Cost factors (example values, should be configured)
        concrete_cost = 150  # $/m³
        steel_cost = 2.5     # $/kg

        total_cost = (concrete_volume * concrete_cost
                      + steel_weight * steel_cost)

        return total_cost

    def _calculate_num_girders(self, girder_spacing: float) -> int:
        """Calculate number of girders based on spacing and deck width."""
        deck_width = self.bridge_cfg.deck_width
        return int(np.ceil(deck_width / girder_spacing)) + 1

    def _calculate_concrete_volume(
        self,
        span_lengths: List[float],
        girder_depth: float,
        deck_thickness: float,
        num_girders: int
    ) -> float:
        """Calculate total concrete volume."""
        # Calculate deck volume
        deck_volume = sum(span_lengths) * self.bridge_cfg.deck_width * deck_thickness

        # Calculate girder volume (simplified)
        girder_volume = sum(span_lengths) * num_girders * girder_depth * 0.5  # Assuming I-beam

        # Add pier and abutment volumes (simplified)
        substructure_volume = (len(span_lengths) + 1) * 10  # m³ per support (example)

        return deck_volume + girder_volume + substructure_volume

    def _calculate_steel_weight(
        self,
        span_lengths: List[float],
        girder_depth: float,
        num_girders: int
    ) -> float:
        """Calculate total steel weight."""
        # Simplified steel weight calculation
        steel_per_span = 0.5 * sum(span_lengths) * num_girders * girder_depth  # kg (example)
        return steel_per_span

    def _constraints(self, x: np.ndarray) -> Dict:
        """Define optimization constraints."""
        n = len(self.bridge_cfg.span_lengths)
        span_lengths = x[:n]
        _ = x[n]
        _ = x[n + 1]
        _ = x[n + 2]

        constraints = []

        # Example constraints (can be expanded)
        # Min/max span lengths
        for i, length in enumerate(span_lengths):
            constraints.append({
                'type': 'ineq',
                'fun': lambda x, i=i: x[i] - 10.0  # Min span length 10m
            })
            constraints.append({
                'type': 'ineq',
                'fun': lambda x, i=i: 100.0 - x[i]  # Max span length 100m
            })

        # Girder spacing constraints
        constraints.extend([
            {
                'type': 'ineq',
                'fun': lambda x: x[n] - 2.0  # Min girder spacing 2m
            },
            {
                'type': 'ineq',
                'fun': lambda x: 6.0 - x[n]  # Max girder spacing 6m
            }
        ])

        return constraints

    def optimize(self, initial_guess: Optional[Dict] = None) -> DesignVariables:
        """Optimize bridge design parameters.

        Args:
            initial_guess: Optional initial guess for optimization

        Returns:
            DesignVariables: Optimized design variables
        """
        # Set up initial guess
        if initial_guess is None:
            x0 = np.array(
                self.bridge_cfg.span_lengths
                + [self.bridge_cfg.girder_spacing,
                   self.bridge_cfg.girder_depth,
                   0.2]  # deck_thickness
            )
        else:
            x0 = np.array(
                initial_guess['span_lengths']
                + [initial_guess.get('girder_spacing', self.bridge_cfg.girder_spacing),
                   initial_guess.get('girder_depth', self.bridge_cfg.girder_depth),
                   initial_guess.get('deck_thickness', 0.2)]
            )

        # Bounds for variables
        n = len(self.bridge_cfg.span_lengths)
        bounds = [(10.0, 100.0)] * n + [  # Span lengths
            (2.0, 6.0),    # Girder spacing
            (0.5, 3.0),    # Girder depth
            (0.15, 0.3)    # Deck thickness
        ]

        # Run optimization
        result = minimize(
            fun=self._objective_function,
            x0=x0,
            method='SLSQP',
            bounds=bounds,
            constraints=self._constraints(x0),
            options={'maxiter': 100, 'ftol': 1e-6}
        )

        # Extract and return results
        optimized_vars = {
            'span_lengths': result.x[:n].tolist(),
            'num_spans': n,
            'girder_spacing': float(result.x[n]),
            'girder_depth': float(result.x[n + 1]),
            'deck_thickness': float(result.x[n + 2])
        }

        return DesignVariables(**optimized_vars)


def optimize_bridge_design(
    settings: Settings,
    initial_guess: Optional[Dict] = None
) -> Dict[str, Any]:
    """Optimize bridge design based on given settings.

    Args:
        settings: Bridge settings and constraints
        initial_guess: Optional initial guess for optimization

    Returns:
        Dict containing optimized design parameters
    """
    optimizer = BridgeOptimizer(settings)
    result = optimizer.optimize(initial_guess)
    return result.to_dict()
