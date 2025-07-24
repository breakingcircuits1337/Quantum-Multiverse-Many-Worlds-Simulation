import random
import uuid

class QuantumSystem:
    """
    Represents a simple quantum system that can be in a superposition of states.
    For this simulation, we'll use a simple qubit with 'up' and 'down' states.
    """
    def __init__(self, states):
        """
        Initializes the quantum system.
        Args:
            states (dict): A dictionary where keys are state names and values 
                           are their probabilities. e.g., {'up': 0.5, 'down': 0.5}
        """
        # Ensure probabilities sum to 1
        if not abs(sum(states.values()) - 1.0) < 1e-9:
            raise ValueError("Probabilities of all states must sum to 1.")
        self.states = states

    def __repr__(self):
        """String representation of the system's state."""
        return f"QuantumSystem({self.states})"

class Universe:
    """
    Represents a single universe in the multiverse. Each universe has its own
    history and a specific state for its quantum system.
    """
    def __init__(self, system_state, history=None):
        """
        Initializes a universe.
        Args:
            system_state (dict): The state of the quantum system in this universe.
            history (list, optional): The history of events that led to this universe.
                                      Defaults to None.
        """
        self.id = str(uuid.uuid4())[:8] # A unique ID for this universe
        self.system = QuantumSystem(system_state)
        self.history = history if history is not None else ["Universe Created"]
        self.child_universes = [] # To hold universes that branch from this one

    def measure(self):
        """
        Performs a quantum measurement.
        According to the Many-Worlds Interpretation, this doesn't collapse the
        wave function, but instead splits the universe into multiple branches,
        one for each possible outcome.
        """
        # Prevent splitting a universe that has already been measured and collapsed
        if len(self.system.states) == 1:
            print(f"--> Universe {self.id} has a definite state; no new branches created.")
            return

        print(f"\nPerforming measurement in Universe {self.id}...")
        print(f"System is in superposition: {self.system.states}")
        print("Splitting universe...")

        # For each possible state, a new universe is created (a branch)
        for state, probability in self.system.states.items():
            # In the new universe, the system has "collapsed" to this specific state.
            new_system_state = {s: (1.0 if s == state else 0.0) for s in self.system.states}
            
            # Create a new history log for the new branch
            new_history = self.history + [f"Measured and branched into '{state}' state (Prob: {probability*100}%)"]
            
            # Create the new universe
            new_universe = Universe(new_system_state, new_history)
            self.child_universes.append(new_universe)
            print(f"  -> Created new Universe {new_universe.id} for outcome '{state}'.")

    def __repr__(self):
        """String representation of the universe."""
        return (f"Universe(ID={self.id}, "
                f"SystemState={self.system.states}, "
                f"History={self.history})")

def print_multiverse(universe, prefix="", is_last=True):
    """
    Recursively prints a tree-like structure of the multiverse.
    """
    # Print the current universe's info
    print(prefix + ("└── " if is_last else "├── ") + f"Universe {universe.id}: {universe.system.states}")
    
    # Update the prefix for child nodes
    new_prefix = prefix + ("    " if is_last else "│   ")
    
    # Recursively print child universes (branches)
    child_count = len(universe.child_universes)
    for i, child in enumerate(universe.child_universes):
        is_last_child = (i == child_count - 1)
        print_multiverse(child, new_prefix, is_last_child)
        if is_last_child:
            print(f"{new_prefix}└── History: {child.history}")


# --- Main Simulation ---
if __name__ == "__main__":
    # 1. Start with a single root universe.
    # Its quantum system is in a perfect superposition.
    initial_state = {'up': 0.5, 'down': 0.5}
    root_universe = Universe(system_state=initial_state)

    print("--- Quantum Multiverse Simulation (Many-Worlds Interpretation) ---")
    print(f"Created root universe: {root_universe.id}")

    # 2. Perform the first measurement on the root universe.
    # This will cause it to split into two branches.
    root_universe.measure()

    # 3. Let's perform another measurement in one of the new universes.
    # We'll add a new quantum property to measure, like 'charge'.
    if root_universe.child_universes:
        # Let's pick the first child universe to continue our experiment
        universe_to_measure_again = root_universe.child_universes[0]
        
        # We introduce a new quantum property to this universe's system
        universe_to_measure_again.system = QuantumSystem({'positive': 0.5, 'negative': 0.5})
        
        # Now, measure this new property. This will cause another split.
        universe_to_measure_again.measure()


    # 4. Print the final state of the multiverse, showing all branches.
    print("\n--- Final Multiverse State ---")
    print_multiverse(root_universe)


