import uuid
from typing import Dict, List, Optional, Set, Any

EPSILON = 1e-9

class QuantumSystem:
    """
    Represents a quantum system with complex amplitudes for each basis state.
    """
    def __init__(self, amplitudes: Dict[str, complex]) -> None:
        # Amplitudes: Dict[str, complex]
        self.amplitudes: Dict[str, complex] = amplitudes.copy()
        self.normalize()

    def normalize(self) -> None:
        """
        Normalize amplitudes so that the sum of |amp|^2 is 1 (within EPSILON).
        """
        norm_sq = sum(abs(a) ** 2 for a in self.amplitudes.values())
        if norm_sq < EPSILON:
            raise ValueError("All amplitudes are zero, cannot normalize.")
        for k in self.amplitudes:
            self.amplitudes[k] /= norm_sq ** 0.5
        # After normalization, check
        norm_sq = sum(abs(a) ** 2 for a in self.amplitudes.values())
        if abs(norm_sq - 1.0) > EPSILON:
            raise ValueError("Normalization failed: Probabilities do not sum to 1.0.")

    @property
    def probabilities(self) -> Dict[str, float]:
        """
        Returns the Born probabilities for each state: |amp|^2
        """
        return {state: abs(amp) ** 2 for state, amp in self.amplitudes.items()}

    def is_definite(self) -> Optional[str]:
        """
        Returns the definite state if only one amplitude is 1+0j and others are zero,
        else None.
        """
        definite = None
        for state, amp in self.amplitudes.items():
            if abs(amp - 1.0) < EPSILON:
                if definite is not None:
                    return None
                definite = state
            elif abs(amp) > EPSILON:
                return None
        return definite

    def __repr__(self) -> str:
        # Format: {'up': 1.0+0.0j, 'down': 0.0+0.0j}
        return "QuantumSystem(" + \
            ", ".join(f"{k}: {v.real:.3f}{'+' if v.imag >= 0 else ''}{v.imag:.3f}j"
                      for k, v in self.amplitudes.items()) + \
            ")"

class Universe:
    """
    A universe in the multiverse, with a specific quantum system, weight, and history.
    """
    def __init__(
        self,
        system: QuantumSystem,
        history: Optional[List[str]] = None,
        weight: float = 1.0,
        measured_observables: Optional[Set[str]] = None
    ) -> None:
        self.id: str = str(uuid.uuid4())[:8]
        self.system: QuantumSystem = system
        self.weight: float = weight
        self.history: List[str] = history if history is not None else ["Universe Created"]
        self.child_universes: List['Universe'] = []
        self.measured_observables: Set[str] = set(measured_observables) if measured_observables else set()

    def measure(self, observable_name: str) -> None:
        """
        Branches the universe for a measurement of observable_name. If already measured,
        prints a warning and does nothing. If the system is definite, prints a message and does nothing.
        """
        if observable_name in self.measured_observables:
            print(f"--> Universe {self.id} already measured observable '{observable_name}'; no new branches created.")
            return

        definite = self.system.is_definite()
        if definite is not None:
            print(f"--> Universe {self.id} has a definite state: '{definite}'; no new branches created.")
            return

        print(f"\nPerforming measurement '{observable_name}' in Universe {self.id} (w={self.weight:.5f})...")
        print(f"System amplitudes: {self.system}")
        print("Splitting universe...")

        probs = self.system.probabilities
        for state, prob in probs.items():
            if prob < EPSILON:
                continue  # skip zero-probability outcome
            # Collapse to that outcome: amplitude 1+0j for the measured state, 0j for others
            collapsed_amplitudes = {s: (1+0j if s == state else 0j) for s in self.system.amplitudes}
            new_system = QuantumSystem(collapsed_amplitudes)
            # Compute child weight
            child_weight = self.weight * prob
            # New measured observables: add this one
            child_measured = set(self.measured_observables)
            child_measured.add(observable_name)
            # Update history
            new_history = self.history + [
                f"Measured '{observable_name}', branched into '{state}' (Prob: {prob*100:.2f}%)"
            ]
            # Create child
            child = Universe(
                new_system,
                history=new_history,
                weight=child_weight,
                measured_observables=child_measured
            )
            self.child_universes.append(child)
            print(f"  -> Created Universe {child.id} for outcome '{state}' (w={child_weight:.5f})")

    def __repr__(self) -> str:
        return (f"Universe(ID={self.id}, w={self.weight:.5f}, "
                f"System={self.system}, "
                f"History={self.history}, "
                f"Measured={self.measured_observables})")

def print_multiverse(universe: Universe, prefix: str = "", is_last: bool = True) -> None:
    """
    Recursively prints a tree-like structure of the multiverse, including weights.
    """
    probs = universe.system.probabilities
    # Format: Universe abc123 (w=0.25): {'up':1.0, 'down':0.0}
    state_str = ", ".join(f"{k}:{probs[k]:.2f}" for k in probs)
    print(prefix + ("└── " if is_last else "├── ") +
          f"Universe {universe.id} (w={universe.weight:.5f}): {{{state_str}}}")

    new_prefix = prefix + ("    " if is_last else "│   ")

    child_count = len(universe.child_universes)
    for i, child in enumerate(universe.child_universes):
        is_last_child = (i == child_count - 1)
        print_multiverse(child, new_prefix, is_last_child)
        if is_last_child:
            print(f"{new_prefix}└── History: {child.history}")

# --- Main Simulation ---
if __name__ == "__main__":
    # 1. Start with a single root universe with a superposition.
    initial_amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}  # |up⟩+|down⟩, normalized

    root_universe = Universe(
        system=QuantumSystem(initial_amplitudes),
        weight=1.0
    )

    print("--- Quantum Multiverse Simulation (Many-Worlds Interpretation) ---")
    print(f"Created root universe: {root_universe.id}")

    # 2. Perform the first measurement (spin_z) on the root universe.
    root_universe.measure('spin_z')

    # Try to measure spin_z again in the root universe (should print warning and do nothing).
    root_universe.measure('spin_z')

    # 3. Perform a second measurement (charge) in one of the new universes.
    if root_universe.child_universes:
        # Pick the first child universe to continue
        universe_to_measure_again = root_universe.child_universes[0]

        # Introduce a new quantum property: 'charge' superposition (e.g. + and -)
        # Let's use equal amplitudes again
        universe_to_measure_again.system = QuantumSystem({'positive': 1/2**0.5 + 0j, 'negative': 1/2**0.5 + 0j})

        # Measure 'charge' in this universe
        universe_to_measure_again.measure('charge')

        # Try to re-measure 'charge'
        universe_to_measure_again.measure('charge')

    # 4. Print the final state of the multiverse, showing all branches and weights.
    print("\n--- Final Multiverse State ---")
    print_multiverse(root_universe)