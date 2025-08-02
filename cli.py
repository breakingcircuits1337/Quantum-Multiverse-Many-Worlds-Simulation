import argparse
import logging
from multiverse.simulation import QuantumSystem, Universe, dump_multiverse
from multiverse.viz import render_tree

logger = logging.getLogger(__name__)

def demo(style: str = "plain", json_path: str = None) -> None:
    # 1. Start with a single root universe with a superposition.
    initial_amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root_universe = Universe(
        system=QuantumSystem(initial_amplitudes),
        weight=1.0
    )
    logger.info("--- Quantum Multiverse Simulation (Many-Worlds Interpretation) ---")
    logger.info(f"Created root universe: {root_universe.id}")
    # 2. Measure spin_z
    root_universe.measure('spin_z')
    # 3. Try to measure spin_z again (should print warning)
    root_universe.measure('spin_z')
    # 4. Measure charge in the first child
    children = root_universe.children()
    if children:
        u2 = children[0]
        u2.system = QuantumSystem({'positive': 1/2**0.5 + 0j, 'negative': 1/2**0.5 + 0j})
        u2.measure('charge')
        u2.measure('charge')
    # 5. Print the final state
    logger.info("\n--- Final Multiverse State ---")
    render_tree(root_universe, style=style)
    # 6. Optionally dump to JSON
    if json_path:
        dump_multiverse(root_universe, json_path)

def main() -> None:
    parser = argparse.ArgumentParser(description="Quantum Multiverse (Many-Worlds) Simulation CLI")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose (DEBUG) logging')
    parser.add_argument('--style', default='plain', choices=['plain', 'rich'], help='Tree rendering style (plain/rich)')
    parser.add_argument('--json', type=str, default=None, help='Write full multiverse to JSON file')
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    subparsers.add_parser("demo", help="Run the demonstration simulation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    if args.command is None or args.command == "demo":
        demo(style=args.style, json_path=args.json)

if __name__ == "__main__":
    main()