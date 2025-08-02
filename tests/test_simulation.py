import pytest
import json
from multiverse.simulation import (
    QuantumSystem,
    Universe,
    EPS,
    dump_multiverse,
    register_universe_creation_observer,
    register_post_measurement_hook,
)

def test_weight_conservation() -> None:
    amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amplitudes), weight=1.0)
    root.measure('spin_z')
    leaves = root.children()
    total_weight = sum(child.weight for child in leaves)
    assert abs(total_weight - root.weight) < EPS

def test_repeat_measurement_blocked(caplog) -> None:
    amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amplitudes), weight=1.0)
    root.measure('spin_z')
    with caplog.at_level('WARNING'):
        children2 = root.measure('spin_z')
    assert children2 == []
    assert any("already measured observable" in msg for msg in caplog.text.splitlines())

def test_zero_amplitudes_normalize_error() -> None:
    amplitudes = {'up': 0j, 'down': 0j}
    with pytest.raises(ValueError, match="All amplitudes are zero"):
        QuantumSystem(amplitudes)

def test_deep_branching() -> None:
    # Perform 6 sequential distinct measurements, check sum of weights on leaves == 1.0 (within EPS)
    amps = {'s0': 1/2**0.5 + 0j, 's1': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amps), weight=1.0)
    current_leaves = [root]
    for i in range(6):
        new_leaves = []
        for u in current_leaves:
            u.measure(f'obs_{i}')
            children = u.children()
            if children:
                new_leaves.extend(children)
            else:
                new_leaves.append(u)
        current_leaves = new_leaves
    # Now, all leaves are those with no children (no pending branches, no children)
    leaves = [u for u in current_leaves if not u.children()]
    total_weight = sum(u.weight for u in leaves)
    assert abs(total_weight - 1.0) < EPS

def test_json_dump_roundtrip(tmp_path) -> None:
    # Build small tree, dump to json, reload, check number of nodes
    amps = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amps), weight=1.0)
    root.measure('spin_z')
    root.children()
    children = root.children()
    if children:
        c = children[0]
        c.system = QuantumSystem({'left': 1/2**0.5 + 0j, 'right': 1/2**0.5 + 0j})
        c.measure('spin_x')
        c.children()
    outfile = tmp_path / "tree.json"
    dump_multiverse(root, str(outfile))
    with open(outfile, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Check: root + all descendants, count nodes
    def count_nodes(node):
        return 1 + sum(count_nodes(child) for child in node["children"])
    total_nodes = count_nodes(data)
    # There should be root, 2 spin_z children, and for one of them, 2 spin_x children: total 1+2+2=5
    assert total_nodes == 5

def test_entanglement_partial_measurement():
    import math
    # Bell state
    amps = {'00': 1 / math.sqrt(2), '11': 1 / math.sqrt(2)}
    root = Universe(system=QuantumSystem(amps), weight=1.0)
    # Measure first qubit only
    root.measure('qubits', qubits=[0])
    children = root.children()
    assert len(children) == 2
    keys = [set(c.system.amplitudes.keys()) for c in children]
    weights = [c.weight for c in children]
    # Should be [{'00'}, {'11'}] or vice versa
    assert {'00'} in keys and {'11'} in keys
    for c in children:
        # Each child should be in a definite state
        assert len(c.system.amplitudes) == 1
        val = list(c.system.amplitudes.values())[0]
        assert abs(abs(val) - 1.0) < EPS
        assert abs(c.weight - 0.5) < EPS

def test_universe_creation_observer(monkeypatch):
    # Test that observer is called for each child universe created
    calls = []
    def observer(u, state):
        calls.append((u.id, state))
    register_universe_creation_observer(observer)
    amps = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amps), weight=1.0)
    root.measure('spin_z')
    # children() triggers observer
    root.children()
    assert ('up' in {s for (_, s) in calls} and 'down' in {s for (_, s) in calls})

def test_post_measurement_hook():
    # Test that post-measurement hook is called with correct universe and observable
    calls = []
    def hook(u, observable):
        calls.append((u.id, observable))
    register_post_measurement_hook(hook)
    amps = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amps), weight=1.0)
    root.measure('spin_z')
    assert (root.id, 'spin_z') in calls