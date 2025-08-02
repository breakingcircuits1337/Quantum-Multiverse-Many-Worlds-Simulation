import pytest
from multiverse.simulation import QuantumSystem, Universe, EPS

def test_weight_conservation() -> None:
    amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amplitudes), weight=1.0)
    children = root.measure('spin_z')
    total_weight = sum(child.weight for child in children)
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
            children = u.measure(f'obs_{i}')
            if children:
                new_leaves.extend(children)
            else:
                new_leaves.append(u)
        current_leaves = new_leaves
    # Now, all leaves are those with no children
    leaves = [u for u in current_leaves if not u.child_universes]
    total_weight = sum(u.weight for u in leaves)
    assert abs(total_weight - 1.0) < EPS