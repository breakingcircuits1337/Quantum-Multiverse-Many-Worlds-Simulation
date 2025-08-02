from typing import Any
from .simulation import Universe
import logging

logger = logging.getLogger(__name__)

def render_tree(universe: Universe, prefix: str = "", is_last: bool = True) -> None:
    """
    Iterative tree rendering. Expands children lazily.
    """
    stack = []
    # Each stack item: (universe, prefix, is_last)
    stack.append((universe, prefix, is_last))
    while stack:
        node, pfx, last = stack.pop()
        probs = node.system.probabilities
        state_str = ", ".join(f"{k}:{probs[k]:.2f}" for k in probs)
        line = pfx + ("└── " if last else "├── ") + f"Universe {node.id} (w={node.weight:.5f}): {{{state_str}}}"
        logger.info(line)
        child_list = node.children()
        if child_list:
            new_pfx = pfx + ("    " if last else "│   ")
            for i in range(len(child_list)-1, -1, -1):
                child = child_list[i]
                is_last_child = (i == len(child_list)-1)
                stack.append((child, new_pfx, is_last_child))
                # Print history of last child after all its children
                if is_last_child:
                    # Defer history print after child is processed
                    stack.append((HistoryNode(child), new_pfx, True))
        elif hasattr(node, "history"):
            # For leaf, print history
            logger.info(f"{pfx}└── History: {node.history}")

class HistoryNode:
    def __init__(self, universe: Universe):
        self.universe = universe
        self.history = universe.history