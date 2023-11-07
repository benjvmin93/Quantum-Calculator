from qiskit import transpile, QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import Aer
import numpy as np

def build_encoding_circuit(num_qubits, bin_a, bin_b):
    encoding_circuit = QuantumCircuit(num_qubits - 1, name="Encode")
    for i, b in enumerate(bin_a):
        if int(b) == 1:
            encoding_circuit.x(i)
    for i, b in enumerate(bin_b):
        if int(b) == 1:
            encoding_circuit.x(len(bin_a) + i)
    return encoding_circuit

def build_qft_circuit(len_a):
    qft = QuantumCircuit(len_a + 1, name="QFT")
    for i in range(len_a + 1):
        qft.h(i)
        for k, j in enumerate(range(i + 1, len_a + 1), start=2):
            qft.cp(theta = 2 * np.pi / 2 ** (k), control_qubit=i, target_qubit=j)
    return qft

def build_non_modular_addition_circuit(len_a, len_b):
    num_qubits = len_a + len_b + 1
    circ = QuantumCircuit(num_qubits, name="nMAdd") # Init circuit
    circ.cp(theta = 2 * np.pi / 2, control_qubit=num_qubits - 1, target_qubit=len_a)
    for i in reversed(range(1, len_a)): # Start from last qubit of |a> to first qubit
        for k, j in enumerate(range(i + len_b, num_qubits), start=1): # Start from i + len(b) to last qubit
            control_qubit = j
            target_qubit = i
            circ.cp(theta = 2 * np.pi / 2 ** k, control_qubit=control_qubit, target_qubit=target_qubit, label=f"R{k+1}")
    for k, i in enumerate(range(1 + len_a, num_qubits), start=2):
        circ.cp(theta=2 * np.pi / 2 ** k, control_qubit=i, target_qubit=0)
    return circ

def build_adder_circuit(bin_a, bin_b):
    num_qubits = len(bin_a) + len(bin_b) + 1
    encoding_circuit = build_encoding_circuit(num_qubits, bin_a, bin_b)
    qft = build_qft_circuit(len(bin_a))
    non_modular_addition_circ = build_non_modular_addition_circuit(len(bin_a), len(bin_b))

    # Create a quantum circuit with the number of bits we need to represent our binary integers to add
    circ = QuantumCircuit(QuantumRegister(len(bin_a) + 1, name="a"), QuantumRegister(len(bin_b), name="b"), ClassicalRegister(len(bin_a) + 1))

    # Encode the integer into binary
    circ.append(encoding_circuit, [i for i in range(1, num_qubits)])

    # Apply Toffoli gates
    # First Toffoli gate is 0-controlled on |a1>
    # Second Toffoli gate is 0-controlled on |b1>
    circ.x(1) # Add X gate to ensure 0-control
    circ.toffoli(1 + len(bin_a), 1, 0)
    circ.x(1) # Remove X gate
    circ.x(1 + len(bin_a)) # Add X gate to ensure 0-control
    circ.toffoli(1, 1 + len(bin_a), 0)
    circ.x(1 + len(bin_a)) # Remove X gate

    # Apply QFT on qubit of first integer
    circ.append(qft, [i for i in range(len(bin_a) + 1)])

    circ.append(non_modular_addition_circ, [i for i in range(num_qubits)])
    circ.append(qft.inverse(), [i for i in range(len(bin_a) + 1)])

    circ.measure([i for i in range(len(bin_a) + 1)], [i for i in range(len(bin_a) + 1)])
    return circ

def quantum_adder(a : int, b : int, backend=None) -> int:
    """
    Encode a and b as qubits and perform a + b
    """
    len_binary = 1
    while 2 ** len_binary <= a or 2 ** len_binary <= b: 
        len_binary += 1
    len_binary += 1
    bin_a = bin(a)[2:].zfill(len_binary + 1)
    bin_b = bin(b)[2:].zfill(len_binary + 1)
    circ = build_adder_circuit(bin_a, bin_b)
    if backend is None:
        backend = Aer.get_backend('aer_simulator_statevector')
    
    circ = transpile(circ, backend)
    result = backend.run(circ).result().get_counts(circ)

    return result

def main():
    a = int(input("Enter first number:"))
    b = int(input("Enter second number:"))

    result = quantum_adder(a, b)
    binstr = [b[::-1] for b in list(result.keys())]
    res = [int(b, 2) for b in binstr]

    print(f"Results: {a} + {b} = {binstr} = {res}")

if __name__ == "__main__":
    main()