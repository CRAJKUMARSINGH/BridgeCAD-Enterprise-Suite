"""Command-line interface for Bridge GAD calculations."""

import argparse
import logging
from bridge_gad.logger_config import configure_logging
from bridge_gad.geometry import summarize
from bridge_gad.io_utils import save_results_to_excel
from bridge_gad.config import DEFAULT_E, DEFAULT_I

logger = logging.getLogger(__name__)


def main() -> None:
    """Command-line interface for Bridge_GAD calculations."""
    configure_logging(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Bridge_GAD: Compute basic beam parameters (Moment, Shear, Deflection)"
    )
    parser.add_argument("--span", type=float, required=True, help="Span length of beam (m)")
    parser.add_argument("--load", type=float, required=True, help="Uniformly distributed load (kN/m)")
    parser.add_argument("--E", type=float, default=DEFAULT_E, help="Modulus of Elasticity (kN/m²)")
    parser.add_argument("--I", type=float, default=DEFAULT_I, help="Moment of Inertia (m⁴)")
    parser.add_argument("--output", type=str, help="Optional: Path to save Excel results")

    args = parser.parse_args()

    logger.info("Computing parameters for span=%.2f m, load=%.2f kN/m", args.span, args.load)
    results = summarize(args.span, args.load, args.E, args.I)

    print("\n=== Bridge_GAD Results ===")
    for key, val in results.items():
        print(f"{key:15s}: {val:10.4f}")

    if args.output:
        save_results_to_excel(results, args.output)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
