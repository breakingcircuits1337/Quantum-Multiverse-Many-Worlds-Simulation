from typing import Any, Optional
from .simulation import Universe
import logging

logger = logging.getLogger(__name__)

def render_tree(
    universe: Universe,
    *,
    style: str = "plain",
    console: Optional[Any] = None
) -> None:
    """
    Render the multiverse tree.
    - style: 'plain' (default, iterative logging), or 'rich' (if rich installed).
    - console: rich Console instance (optional, used only if style='rich').
    """
    if style == "rich":
        try:
            from rich.tree import Tree
            from rich.console import Console
            from rich.text import Text
        except ImportError:
            logger.warning("The 'rich' library is not installed. Falling back to plain style.")
            style = "plain"

    if style == "plain":
        _render_tree_plain(universe)
        return

    # --- RICH STYLE ---
    def _node_label(u: Universe) -> str:
        probs = u.system.probabilities
        state_str = ", ".join(f"{k}:{probs[k]:.2f}" for k in probs)
        return f"[bold cyan]Universe {u.id}[/] (w={u.weight:.5f}): {{[magenta]{state_str}[/]}}"

    def _leaf_history(u: Universe) -> str:
        return "[dim]History: " + repr(u.history) + "[/dim]"

    def build_rich_tree(u: Universe) -> Tree:
        main_tree = Tree(_node_label(u))
        stack = [(u, main_tree)]
        while stack:
            node, tree_parent = stack.pop()
            child_list = node.children()
            for i, child in enumerate(child_list):
                t = tree_parent.add(_node_label(child))
                stack.append((child, t))
                # If this is a leaf, add its history as a child node
                if not child.children():
                    t.add(_leaf_history(child))
        return main_tree

    if console is None:
        from rich.console import Console
        console = Console()
    tree = build_rich_tree(universe)
    console.print(tree)

def _render_tree_plain(universe: Universe) -> None:
    """
    Iterative tree rendering. Expands children lazily. (Plain style for logging)
    """
    stack = []
    # Each stack item: (universe, prefix, is_last)
    stack.append((universe, "", True))
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
                if is_last_child:
                    stack.append((HistoryNode(child), new_pfx, True))
        elif hasattr(node, "history"):
            logger.info(f"{pfx}└── History: {node.history}")

class HistoryNode:
    def __init__(self, universe: Universe):
        self.universe = universe
        self.history = universe.history