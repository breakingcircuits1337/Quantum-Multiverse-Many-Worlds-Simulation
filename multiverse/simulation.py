from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, TYPE_CHECKING, Any, Callable
import uuid
import logging
import json

EPS: float = 1e-9

logger = logging.getLogger(__name__)

# Plugin/observer architecture
UNIVERSE_CREATION_OBSERVERS: List[Callable[['Universe', str], None]] = []
POST_MEASUREMENT_HOOKS: List[Callable[['Universe', str], None]] = []

# Decoherence model registration
DECOHERENCE_MODELS: List[Callable[['Universe'], None]] = []

def register_decoherence_model(fn: Callable[['Universe'], None]) -> None:
    """Register a decoherence model to be applied to each new Universe after branching.

    Args:
        fn: Callable taking (Universe,) and applying decoherence in-place or returning a new system.
    """
    DECOHERENCE_MODELS.append(fn)

def register_universe_creation_observer(fn: Callable[['Universe', str], None]) -> None:
    """Register a function to be called whenever a new Universe is created via branching.

    Args:
        fn: Callable taking (Universe, outcome_state:str).
    """
    UNIVERSE_CREATION_OBSERVERS.append(fn)

def register_post_measurement_hook(fn: Callable[['Universe', str], None]) -> None:
    """Register a function to be called after a measurement is performed.

    Args:
        fn: Callable taking (Universe, observable_name:str).
    """
    POST_MEASUREMENT_HOOKS.append(fn)

@dataclass(slots=True)
class QuantumSystem:
    """Represents a quantum system with complex amplitudes for each basis state.

    Attributes:
        amplitudes: A dictionary mapping bitstring state names to complex amplitudes.
            For N qubits, keys must be bitstrings of length N.

    Example:
        sys = QuantumSystem({'00': 1/2**0.5 + 0j, '11': 1/2**0.5 + 0j})  # Bell state
    """
    amplitudes: Dict[str, complex]

    def __post_init__(self) -> None:
        """Copy amplitudes and normalize on initialization."""
        self.amplitudes = dict(self.amplitudes)
        self.normalize()

    @property
    def num_qubits(self) -> int:
        """Returns the number of qubits in the system."""
        if not self.amplitudes:
            return 0
        n = {len(k) for k in self.amplitudes}
        if len(n) != 1:
            raise ValueError("All state keys must have the same length (number of qubits).")
        return next(iter(n))

    def normalize(self) -> None:
        """Normalizes amplitudes so that the sum of |amp|^2 equals 1.

        Raises:
            ValueError: If all amplitudes are zero or normalization fails.
        """
        norm_sq: float = sum(abs(a) ** 2 for a in self.amplitudes.values())
        if norm_sq < EPS:
            raise ValueError("All amplitudes are zero, cannot normalize.")
        norm = norm_sq ** 0.5
        for k in self.amplitudes:
            self.amplitudes[k] /= norm
        norm_sq_after = sum(abs(a) ** 2 for a in self.amplitudes.values())
        if abs(norm_sq_after - 1.0) > EPS:
            raise ValueError("Normalization failed: Probabilities do not sum to 1.0.")

    @property
    def probabilities(self) -> Dict[str, float]:
        """Returns the Born probabilities for each state.

        Returns:
            Dict mapping each state to its probability (|amp|^2).
        """
        return {state: abs(amp) ** 2 for state, amp in self.amplitudes.items()}

    def subset_probabilities(self, qubits: List[int]) -> Dict[str, float]:
        """Returns probabilities for outcomes of the specified qubits (indices 0 = MSB).

        Args:
            qubits: List of qubit indices to measure (0 = MSB).

        Returns:
            Dict mapping outcome bitstrings to summed probability.
        """
        n = self.num_qubits
        result: Dict[str, float] = {}
        for state, amp in self.amplitudes.items():
            bits = ''.join(state[i] for i in qubits)
            result[bits] = result.get(bits, 0.0) + abs(amp) ** 2
        return result

    def collapse_on_subset(self, qubits: List[int], outcome: str) -> "QuantumSystem":
        """Collapse to a subsystem outcome, renormalizing amplitudes.

        Args:
            qubits: Indices specifying which qubits are measured (0 = MSB).
            outcome: Bitstring outcome for the subsystem (same length as qubits).

        Returns:
            QuantumSystem: New system with only states compatible with outcome.
        """
        n = self.num_qubits
        survivors = {}
        for state, amp in self.amplitudes.items():
            if ''.join(state[i] for i in qubits) == outcome:
                survivors[state] = amp
        if not survivors:
            # This should not happen if probabilities were checked before
            raise ValueError("No compatible states for outcome in collapse.")
        return QuantumSystem(survivors)

    def is_definite(self) -> Optional[str]:
        """Determines if the system is in a definite state.

        Returns:
            The state name if the system is definite (amplitude 1+0j), else None.
        """
        definite: Optional[str] = None
        for state, amp in self.amplitudes.items():
            if abs(amp - 1.0) < EPS:
                if definite is not None:
                    return None
                definite = state
            elif abs(amp) > EPS:
                return None
        return definite

    def is_definite_subset(self, qubits: List[int]) -> Optional[str]:
        """Determines if the subsystem is already in a definite state.

        Args:
            qubits: Indices of the measured qubits.

        Returns:
            The outcome bitstring if definite, else None.
        """
        seen: Optional[str] = None
        for state, amp in self.amplitudes.items():
            if abs(amp) > EPS:
                bits = ''.join(state[i] for i in qubits)
                if seen is None:
                    seen = bits
                elif bits != seen:
                    return None
        return seen

    def __repr__(self) -> str:
        """String representation of the system showing amplitudes."""
        return "QuantumSystem(" + \
            ", ".join(f"{k}: {v.real:.3f}{'+' if v.imag >= 0 else ''}{v.imag:.3f}j"
                      for k, v in self.amplitudes.items()) + \
            ")"

@dataclass(slots=True)
class Universe:
    """A universe in the multiverse, with a specific quantum system, weight, and history.

    Attributes:
        system: QuantumSystem for this universe.
        weight: Born rule probability weight.
        history: List of log/history strings.
        measured_observables: Set of observables already measured.
        id: Unique universe ID.
        child_universes: Dict[str, Universe] for each outcome (created lazily).
        _pending_branches: Internal dict of pending branches (for lazy expansion).

    Example:
        root = Universe(system=QuantumSystem({'00': 1/2**0.5 + 0j, '11': 1/2**0.5 + 0j}))
    """
    system: QuantumSystem
    weight: float = 1.0
    history: List[str] = field(default_factory=lambda: ["Universe Created"])
    measured_observables: Set[str] = field(default_factory=set)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    child_universes: Dict[str, "Universe"] = field(default_factory=dict, init=False)
    # _pending_branches: Dict[outcome, Tuple[prob, qubits]]
    _pending_branches: Optional[Dict[str, tuple[float, List[int]]]] = field(default=None, init=False, repr=False)

    def measure(self, observable_name: str = "qubits", qubits: Optional[List[int]] = None) -> List["Universe"]:
        """Perform a measurement (deferred branching) on this universe.

        Args:
            observable_name: Name of the observable to measure.
            qubits: List of qubit indices to measure (None = all).

        Returns:
            Empty list (branches created lazily by .children()).
        """
        return Measurement(observable_name, qubits).apply(self)

    def _expand_child(self, state: str) -> "Universe":
        """Create and store the child Universe for a given outcome bitstring if not present.

        Args:
            state: The outcome bitstring (for measured qubits, e.g. '0', '1', '01').

        Returns:
            Universe: The new or cached child Universe.

        Raises:
            ValueError: If state is not a valid pending branch.
        """
        if self._pending_branches is None or state not in self._pending_branches:
            raise ValueError(f"No pending branch for state '{state}' in Universe {self.id}")
        if state in self.child_universes:
            return self.child_universes[state]
        prob, qubits = self._pending_branches[state]
        if qubits is None or len(qubits) == self.system.num_qubits:
            # Full measurement, behave as before
            collapsed_amplitudes: Dict[str, complex] = {s: (1+0j if s == state else 0j) for s in self.system.amplitudes}
            new_system = QuantumSystem(collapsed_amplitudes)
        else:
            # Partial measurement: collapse on subset
            new_system = self.system.collapse_on_subset(qubits, state)
        child_weight = self.weight * prob
        child_measured = set(self.measured_observables)
        child = Universe(
            system=new_system,
            weight=child_weight,
            history=list(self.history),
            measured_observables=child_measured
        )

        # Apply all registered decoherence models to the new Universe
        for decoherence_fn in DECOHERENCE_MODELS:
            try:
                decoherence_fn(child)
            except Exception as e:
                logger.warning(f"Decoherence model error: {e}")

        self.child_universes[state] = child
        logger.info(f"  -> Created Universe {child.id} for qubits {qubits} outcome '{state}' (w={child_weight:.5f}) [on demand]")
        # Call observers
        for obs in UNIVERSE_CREATION_OBSERVERS:
            try:
                obs(child, state)
            except Exception as e:
                logger.warning(f"Universe creation observer error: {e}")
        return child

    def children(self) -> List["Universe"]:
        """Expand all pending branches and return the list of children.

        Returns:
            List of Universe instances for each outcome state.
        """
        if self._pending_branches is None:
            return list(self.child_universes.values())
        for state in self._pending_branches:
            if state not in self.child_universes:
                self._expand_child(state)
        self._pending_branches = None
        return list(self.child_universes.values())

    def to_dict(self, *, expand_lazy: bool = True) -> Dict[str, Any]:
        """Serialize this Universe and its children to a dict.

        Args:
            expand_lazy (bool): If True, triggers full lazy expansion for all pending branches.

        Returns:
            Dict[str, Any]: Recursive dict structure representing the multiverse.

        Example:
            d = universe.to_dict()
            import json; print(json.dumps(d, indent=2))
        """
        if expand_lazy:
            children = self.children()
        else:
            children = list(self.child_universes.values())
        return {
            "id": self.id,
            "weight": self.weight,
            "system": {k: [v.real, v.imag] for k, v in self.system.amplitudes.items()},
            "history": list(self.history),
            "measured_observables": list(self.measured_observables),
            "children": [c.to_dict(expand_lazy=expand_lazy) for c in children],
        }

def dump_multiverse(universe: Universe, path: str, *, expand_lazy: bool = True) -> None:
    """Dump the entire universe tree as JSON to a file.

    Args:
        universe (Universe): The root Universe.
        path (str): Path to write JSON file.
        expand_lazy (bool): If True, triggers full lazy expansion for all pending branches.

    Example:
        dump_multiverse(root, "output.json")
    """
    data = universe.to_dict(expand_lazy=expand_lazy)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Multiverse dumped to {path}")

@dataclass(slots=True)
class Measurement:
    """Represents a quantum measurement operation (observable, possibly partial).

    Attributes:
        observable_name: The name of the observable to measure.
        qubits: List of qubit indices to measure (None = all).

    Example:
        Measurement('qubits', qubits=[0]).apply(universe)
    """
    observable_name: str
    qubits: Optional[List[int]] = None

    def apply(self, universe: Universe) -> List[Universe]:
        """Performs the measurement, deferring branch creation.

        Args:
            universe: The Universe to measure.

        Returns:
            [] always; branches are created lazily.

        Raises:
            None (logs warnings if repeated or definite).
        """
        if self.observable_name in universe.measured_observables:
            logger.warning(f"--> Universe {universe.id} already measured observable '{self.observable_name}'; no new branches created.")
            return []
        n_qubits = universe.system.num_qubits
        qubits = self.qubits if self.qubits is not None else list(range(n_qubits))
        if not qubits or len(qubits) == n_qubits:
            # Full measurement: check for definite state as before
            definite = universe.system.is_definite()
            if definite is not None:
                logger.info(f"--> Universe {universe.id} has a definite state: '{definite}'; no new branches created.")
                return []
        else:
            # Partial measurement: check for definite subset
            definite_subset = universe.system.is_definite_subset(qubits)
            if definite_subset is not None:
                logger.info(f"--> Universe {universe.id} qubits {qubits} already definite: '{definite_subset}'; no new branches created.")
                return []
        logger.info(f"\nPerforming measurement '{self.observable_name}' on qubits {qubits} in Universe {universe.id} (w={universe.weight:.5f})...")
        logger.info(f"System amplitudes: {universe.system}")
        logger.info("Splitting universe (branches will be created on demand)...")

        # Remove any existing pending branches (in case of repeated measure)
        universe._pending_branches = None
        universe.child_universes.clear()

        if not qubits or len(qubits) == universe.system.num_qubits:
            probs = universe.system.probabilities
            pending: Dict[str, tuple[float, List[int]]] = {}
            for state, prob in probs.items():
                if prob < EPS:
                    continue
                pending[state] = (prob, qubits)
        else:
            probs = universe.system.subset_probabilities(qubits)
            pending: Dict[str, tuple[float, List[int]]] = {}
            for outcome, prob in probs.items():
                if prob < EPS:
                    continue
                pending[outcome] = (prob, qubits)
        if not pending:
            logger.warning(f"No nonzero-probability branches for Universe {universe.id}")
            return []

        universe.measured_observables.add(self.observable_name)
        universe.history.append(f"Measurement '{self.observable_name}' on qubits {qubits} performed, branches deferred: {list(pending.keys())}")
        universe._pending_branches = pending
        logger.info(f"  -> Branches for observable '{self.observable_name}' will be created lazily for outcomes: {list(pending.keys())}")
        for hook in POST_MEASUREMENT_HOOKS:
            try:
                hook(universe, self.observable_name)
            except Exception as e:
                logger.warning(f"Post-measurement hook error: {e}")
        return []