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
        python cli.py --style rich --json out.json --sample 10 --time-travel
    """
    parser = argparse.ArgumentParser(description="Quantum Multiverse (Many-Worlds) Simulation CLI")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose (DEBUG) logging')
    parser.add_argument('--style', default='plain', choices=['plain', 'rich'], help='Tree rendering style (plain/rich)')
    parser.add_argument('--json', type=str, default=None, help='Write full multiverse to JSON file')
    parser.add_argument('--sample', type=int, default=0, help='Number of observer samples to draw and print')
    parser.add_argument('--time-travel', action='store_true', help='Demonstrate time travel scenario')
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    subparsers.add_parser("demo", help="Run the demonstration simulation")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    if args.command is None or args.command == "demo":
        if args.time_travel:
            demo_time_travel(style=args.style)
        else:
            demo(style=args.style, json_path=args.json, sample=args.sample)

def demo_time_travel(style: str = "plain") -> None:
    """Demonstrate time travel with observer branching and overwriting."""
    import math
    from multiverse.simulation import Observer
    logger.info("--- Quantum Multiverse: Time Travel Demo ---")
    # Create Bell state root
    amps = {'00': 1 / math.sqrt(2), '11': 1 / math.sqrt(2)}
    root = Universe(system=QuantumSystem(amps))
    root.measure('qubits', qubits=[0])
    children = root.children()
    # Pick branch "00"
    branch00 = [c for c in children if '00' in c.system.amplitudes][0]
    alice = Observer(id='Alice', current=branch00)
    logger.info(f"Alice starts at Universe {alice.current.id} ({list(alice.current.system.amplitudes.keys())})")
    # Alice time travels back to root
    alice.travel_back(1, mode='branch')
    logger.info(f"Alice after branch jump: {alice.current.id}")
    # Alice measures second qubit
    alice.current.measure('qubits', qubits=[1])
    leaf = alice.current.children()
    logger.info("After time travel and measuring second qubit, branches:")
    for c in leaf:
        logger.info(f"Universe {c.id} amplitudes={list(c.system.amplitudes.keys())}, weight={c.weight}, overwritten={c.overwritten}")
    # Now test overwrite mode: Bob goes to branch "11"
    branch11 = [c for c in children if '11' in c.system.amplitudes][0]
    bob = Observer(id='Bob', current=branch11)
    bob.travel_back(1, mode='overwrite')
    logger.info(f"Bob after overwrite jump: {bob.current.id}")
    bob.current.measure('qubits', qubits=[1])
    leaf_bob = bob.current.children()
    logger.info("After Bob's overwrite time travel and measuring second qubit, branches:")
    for c in leaf_bob:
        logger.info(f"Universe {c.id} amplitudes={list(c.system.amplitudes.keys())}, weight={c.weight}, overwritten={c.overwritten}")
    # Print tree and jumps
    render_tree(root, style=style)