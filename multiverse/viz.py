from typing import Any
from .simulation import Universe
import logging

logger = logging.getLogger(__name__)

def render_tree(universe: Universe, prefix: str = "", is_last: bool = True) -> None:
    probs = universe.system.probabilities
    state_str = ", ".join(f"{k}:{probs[k]:.2f}" for k in probs)
    line = prefix + ("└── " if is_last else "├── ") + f"Universe {universe.id} (w={universe.weight:.5f}): {{{state_str}}}"
    logger.info(line)
    new_prefix = prefix + ("    " if is_last else "│   ")
    child_count = len(universe.child_universes)
    for i, child in enumerate(universe.child_universes):
        is_last_child = (i == child_count - 1)
        render_tree(child, new_prefix, is_last_child)
        if is_last_child:
            logger.info(f"{new_prefix}└── History: {child.history}")