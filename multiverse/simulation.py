from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, TYPE_CHECKING
import uuid
import logging

EPS: float = 1e-9

logger = logging.getLogger(__name__)

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
    child_universes: List["Universe"] = field(default_factory=list, init=False)

    def measure(self, observable_name: str) -> List["Universe"]:
        return Measurement(observable_name).apply(self)

@dataclass(slots=True)
class Measurement:
    observable_name: str

    def apply(self, universe: Universe) -> List[Universe]:
        if self.observable_name in universe.measured_observables:
            logger.warning(f"--> Universe {universe.id} already measured observable '{self.observable_name}'; no new branches created.")
            return []
        definite = universe.system.is_definite()
        if definite is not None:
            logger.info(f"--> Universe {universe.id} has a definite state: '{definite}'; no new branches created.")
            return []
        logger.info(f"\nPerforming measurement '{self.observable_name}' in Universe {universe.id} (w={universe.weight:.5f})...")
        logger.info(f"System amplitudes: {universe.system}")
        logger.info("Splitting universe...")

        children: List[Universe] = []
        probs = universe.system.probabilities
        for state, prob in probs.items():
            if prob < EPS:
                continue
            collapsed_amplitudes: Dict[str, complex] = {s: (1+0j if s == state else 0j) for s in universe.system.amplitudes}
            new_system = QuantumSystem(collapsed_amplitudes)
            child_weight = universe.weight * prob
            child_measured = set(universe.measured_observables)
            child_measured.add(self.observable_name)
            new_history = universe.history + [
                f"Measured '{self.observable_name}', branched into '{state}' (Prob: {prob*100:.2f}%)"
            ]
            child = Universe(
                system=new_system,
                weight=child_weight,
                history=new_history,
                measured_observables=child_measured
            )
            universe.child_universes.append(child)
            children.append(child)
            logger.info(f"  -> Created Universe {child.id} for outcome '{state}' (w={child_weight:.5f})")
        return children