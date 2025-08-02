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

def register_universe_creation_observer(fn: Callable[['Universe', str], None]) -> None:
    UNIVERSE_CREATION_OBSERVERS.append(fn)

def register_post_measurement_hook(fn: Callable[['Universe', str], None]) -> None:
    POST_MEASUREMENT_HOOKS.append(fn)

@dataclass(slots=True)
class QuantumSystem:
    amplitudes: Dict[str, complex]

    def __post_init__(self) -> None:
        self.amplitudes = dict(self.amplitudes)
        self.normalize()

    def normalize(self) -> None:
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
        return {state: abs(amp) ** 2 for state, amp in self.amplitudes.items()}

    def is_definite(self) -> Optional[str]:
        definite: Optional[str] = None
        for state, amp in self.amplitudes.items():
            if abs(amp - 1.0) < EPS:
                if definite is not None:
                    return None
                definite = state
            elif abs(amp) > EPS:
                return None
        return definite

    def __repr__(self) -> str:
        return "QuantumSystem(" + \
            ", ".join(f"{k}: {v.real:.3f}{'+' if v.imag >= 0 else ''}{v.imag:.3f}j"
                      for k, v in self.amplitudes.items()) + \
            ")"

@dataclass(slots=True)
class Universe:
    system: QuantumSystem
    weight: float = 1.0
    history: List[str] = field(default_factory=lambda: ["Universe Created"])
    measured_observables: Set[str] = field(default_factory=set)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    # Change: lazy branching
    child_universes: Dict[str, "Universe"] = field(default_factory=dict, init=False)
    _pending_branches: Optional[Dict[str, float]] = field(default=None, init=False, repr=False)

    def measure(self, observable_name: str) -> List["Universe"]:
        return Measurement(observable_name).apply(self)

    def _expand_child(self, state: str) -> "Universe":
        """Create and store the child Universe for a given state if not present."""
        if self._pending_branches is None or state not in self._pending_branches:
            raise ValueError(f"No pending branch for state '{state}' in Universe {self.id}")
        if state in self.child_universes:
            return self.child_universes[state]
        prob = self._pending_branches[state]
        collapsed_amplitudes: Dict[str, complex] = {s: (1+0j if s == state else 0j) for s in self.system.amplitudes}
        new_system = QuantumSystem(collapsed_amplitudes)
        child_weight = self.weight * prob
        child_measured = set(self.measured_observables)
        # The branch being expanded is the last history entry (already added in apply)
        child = Universe(
            system=new_system,
            weight=child_weight,
            history=list(self.history),
            measured_observables=child_measured
        )
        self.child_universes[state] = child
        logger.info(f"  -> Created Universe {child.id} for outcome '{state}' (w={child_weight:.5f}) [on demand]")
        # Call observers
        for obs in UNIVERSE_CREATION_OBSERVERS:
            try:
                obs(child, state)
            except Exception as e:
                logger.warning(f"Universe creation observer error: {e}")
        return child

    def children(self) -> List["Universe"]:
        """Expand all pending branches and return the list of children."""
        if self._pending_branches is None:
            return list(self.child_universes.values())
        for state in self._pending_branches:
            if state not in self.child_universes:
                self._expand_child(state)
        # Once expanded, clear pending
        self._pending_branches = None
        return list(self.child_universes.values())

    def to_dict(self, *, expand_lazy: bool = True) -> Dict[str, Any]:
        """
        Serializes this Universe and its children to a dict. If expand_lazy, triggers expansion.
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
    """
    Dumps the entire universe tree as JSON to the given path.
    """
    data = universe.to_dict(expand_lazy=expand_lazy)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Multiverse dumped to {path}")

@dataclass(slots=True)
class Measurement:
    observable_name: str

    def apply(self, universe: Universe) -> List[Universe]:
        # If already measured, log and return []
        if self.observable_name in universe.measured_observables:
            logger.warning(f"--> Universe {universe.id} already measured observable '{self.observable_name}'; no new branches created.")
            return []
        definite = universe.system.is_definite()
        if definite is not None:
            logger.info(f"--> Universe {universe.id} has a definite state: '{definite}'; no new branches created.")
            return []
        logger.info(f"\nPerforming measurement '{self.observable_name}' in Universe {universe.id} (w={universe.weight:.5f})...")
        logger.info(f"System amplitudes: {universe.system}")
        logger.info("Splitting universe (branches will be created on demand)...")

        # Remove any existing pending branches (in case of repeated measure)
        universe._pending_branches = None
        universe.child_universes.clear()

        probs = universe.system.probabilities
        pending: Dict[str, float] = {}
        for state, prob in probs.items():
            if prob < EPS:
                continue
            pending[state] = prob
        if not pending:
            logger.warning(f"No nonzero-probability branches for Universe {universe.id}")
            return []

        # Add observable to measured_observables and add history once for all branches
        universe.measured_observables.add(self.observable_name)
        universe.history.append(f"Measurement '{self.observable_name}' performed, branches deferred: {list(pending.keys())}")
        universe._pending_branches = pending
        logger.info(f"  -> Branches for observable '{self.observable_name}' will be created lazily for states: {list(pending.keys())}")
        # Call post-measurement hooks
        for hook in POST_MEASUREMENT_HOOKS:
            try:
                hook(universe, self.observable_name)
            except Exception as e:
                logger.warning(f"Post-measurement hook error: {e}")
        # Do not create any children now; only when .children() is called
        return []