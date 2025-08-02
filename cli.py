import argparse
from multiverse.simulation import QuantumSystem, Universe
from multiverse.viz import render_tree

def demo() -> None:
    # 1. Start with a single root universe with a superposition.
    initial_amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root_universe = Universe(
        system=QuantumSystem(initial_amplitudes),
        weight=1.0
    )
    print("--- Quantum Multiverse Simulation (Many-Worlds Interpretation) ---")
    print(f"Created root universe: {root_universe.id}")
    # 2. Measure spin_z
    root_universe.measure('spin_z')
    # 3. Try to measure spin_z again (should print warning)
    root_universe.measure('spin_z')
    # 4. Measure charge in the first child
    if root_universe.child_universes:
        u2 = root_universe.child_universes[0]
        u2.system = QuantumSystem({'positive': 1/2**0.5 + 0j, 'negative': 1/2**0.5 + 0j})
        u2.measure('charge')
        u2.measure('charge')
    # 5. Print the final state
    print("\n--- Final Multiverse State ---")
    render_tree(root_universe)

def main() -> None:
    parser = argparse.ArgumentParser(description="Quantum Multiverse (Many-Worlds) Simulation CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    parser_demo = subparsers.add_parser("demo", help="Run the demonstration simulation")
    args = parser.parse_args()
    # If no subcommand, or 'demo', run demo
    if args.command is None or args.command == "demo":
        demo()

if __name__ == "__main__":
    main()