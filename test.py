import pytest

from qiskit_aer import Aer
from src.adder import quantum_adder

backend = Aer.get_backend('aer_simulator_statevector')

def test_adder():
    for a in range(0, 200, 50):
        for b in range(0, 200, 50):
            res = quantum_adder(a, b, backend)
            binstr = [b[::-1] for b in list(res.keys())]
            res = [int(b, 2) for b in binstr]
            assert a + b == res[0]