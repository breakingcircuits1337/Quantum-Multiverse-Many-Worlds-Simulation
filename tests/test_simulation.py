import pytest
from multiverse.simulation import QuantumSystem, Universe

def test_weight_conservation():
    # Setup: root universe with two equal amplitude states
    amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amplitudes), weight=1.0)
    children = root.measure('spin_z')
    total_weight = sum(child.weight for child in children)
    assert abs(total_weight - root.weight) < 1e-9

def test_repeat_measurement_blocked(capsys):
    amplitudes = {'up': 1/2**0.5 + 0j, 'down': 1/2**0.5 + 0j}
    root = Universe(system=QuantumSystem(amplitudes), weight=1.0)
    children1 = root.measure('spin_z')
    children2 = root.measure('spin_z')
    # Should not produce new children
    assert children2 == []
    # Optionally, check printed warning
    captured = capsys.readouterr()
    assert "already measured observable" in captured.out