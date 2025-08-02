import argparse
import logging
from multiverse.simulation import QuantumSystem, Universe, dump_multiverse
from multiverse.viz import render_tree

logger = logging.getLogger(__name__)

def demo(style: str = "plain", json_path: str = None, sample: int = 0) -> None:
    """Run the demonstration simulation and optionally export JSON.

    Args:
        style: Tree rendering style ('plain' or 'rich').
        json_path: Path to JSON file for export (optional).
        sample: Number of observer samples to draw.

    Returns:
        None

    Example:
        demo(style="rich", json_path="output.json", sample=5)
    """
    import math
    from multiverse.simulation import sample_observer
    logger.info("--- Quantum Multiverse Simulation (Many-Worlds Interpretation) ---")
    # Bell state: 2 qubits, entangled
    amps = {
        '00': 1 / math.sqrt(2),
        '11': 1 / math.sqrt(2)
    }
    root_universe = Universe(
        system=QuantumSystem(amps),
        weight=1.0
    )
    logger.info(f"Created root universe (Bell state): {root_universe.id}")
    # Measure first qubit (qubits=[0])
    root_universe.measure('qubits', qubits=[0])
    # Expand children, each should have definite {00} or {11}
    children = root_universe.children()
    logger.info("After measuring first qubit in Bell state, possible branches:")
    for child in children:
        logger.info(f"Branch outcome: {list(child.system.amplitudes.keys())}, weight={child.weight}")
    # 2. Show rich tree
    logger.info("\n--- Final Multiverse State ---")
    render_tree(root_universe, style=style)
    # 3. Optionally dump to JSON
    if json_path:
        dump_multiverse(root_universe, json_path)
    # 4. Optionally sample observers
    if sample > 0:
        logger.info(f"\n--- Sampling {sample} observers ---")
        sampled_ids = []
        for _ in range(sample):
            leaf = sample_observer(root_universe)
            sampled_ids.append(leaf.id)
        logger.info(f"Sampled universe ids: {' '.join(sampled_ids)}")

def main() -> None:
    """Entrypoint for the Quantum Multiverse CLI.

    Parses command-line arguments and runs the demo.

    Example:
        python cli.py --style rich --json out.json --sample 10
    """
    parser = argparse.ArgumentParser(description="Quantum Multiverse (Many-Worlds) Simulation CLI")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose (DEBUG) logging')
    parser.add_argument('--style', default='plain', choices=['plain', 'rich'], help='Tree rendering style (plain/rich)')
    parser.add_argument('--json', type=str, default=None, help='Write full multiverse to JSON file')
    parser.add_argument('--sample', type=int, default=0, help='Number of observer samples to draw and print')
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    subparsers.add_parser("demo", help="Run the demonstration simulation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    if args.command is None or args.command == "demo":
        demo(style=args.style, json_path=args.json, sample=args.sample)

if __name__ == "__main__":
    main()