# Quantum Multiverse Simulator (Many-Worlds Interpretation)

## Overview

This is a Python simulator for the quantum multiverse, inspired by the Many-Worlds Interpretation (MWI) of quantum mechanics. The simulator models quantum systems in superposition, and when measurements are performed, the universe "branches" into all possible outcomes. This package supports lazy branching, plugin hooks, visualization, JSON export, and more.

## Features

- **Quantum Superposition:** Model quantum systems with complex amplitudes for arbitrary states.
- **Lazy Branching:** Universes only branch when required (explore as deeply as you wish).
- **Definite State Detection:** Recognizes when a system is already in a definite state.
- **Measurement Protection:** Prevent repeated measurements of the same observable.
- **Weight Tracking:** Each universe tracks its Born probability weight.
- **Rich Logging:** Uses Python logging for all output; configurable verbosity.
- **Pretty Tree Visualization:** Visualize the multiverse with a colored tree (using `rich`) or plain ASCII.
- **JSON Export:** Dump the full multiverse structure for analysis or visualization.
- **Plugin Hooks:** Register observers for universe creation and post-measurement actions.
- **Extensible API:** Add new observables, plugins, or decoherence models.
- **Tested & Typed:** Full test suite (`pytest`) and strict typing (`mypy`).

## Quick Start

### Installation

```bash
pip install -r requirements.txt
# requirements.txt should include: rich, pytest, mypy
```

### Running the Demo

```bash
python cli.py
```

**Options:**
- Use `--style rich` for colored tree output:
  ```bash
  python cli.py --style rich
  ```
- Export to JSON:
  ```bash
  python cli.py --json multiverse.json
  ```
- Increase verbosity (DEBUG):
  ```bash
  python cli.py --verbose
  ```

## API Usage

```python
from multiverse.simulation import Universe, QuantumSystem, register_universe_creation_observer, dump_multiverse

# Create a root universe in equal superposition
amps = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
root = Universe(system=QuantumSystem(amps), weight=1.0)

# Register a universe creation observer
def my_observer(child, state):
    print(f"Created universe {child.id} for outcome '{state}'")
register_universe_creation_observer(my_observer)

# Perform a measurement (lazy branch)
root.measure('spin_z')
children = root.children()  # Triggers branch creation

# Export to JSON
dump_multiverse(root, "tree.json")
```

## Extending

- **Writing Plugins / Observers:**
    - Register a function with `register_universe_creation_observer` or `register_post_measurement_hook`.
    - Observers receive the new universe and the state/outcome.
    - Post-measurement hooks receive the universe and observable name.
- **Adding New Observables:**
    - Use arbitrary string names for new observables in `measure`.
    - Add custom logic or plugins as needed.
- **Decoherence Models:**
    - Use hooks to implement environment-induced decoherence or other physics.

## Development

- Run all tests:
    ```bash
    pytest
    ```
- Check type safety:
    ```bash
    mypy --strict multiverse/
    ```