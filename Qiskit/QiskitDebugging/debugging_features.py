# ========================================================================
# Copyright (C) 2019 The MITRE Corporation.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================


import vs_test_path_fixup
import unittest
import math
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import execute
from qiskit import Aer
from qiskit.extensions.simulator import snapshot


class DebuggingFeatures(unittest.TestCase):
    """
    This class contains demonstrations of Qiskit's debugging and diagnostic features.
    """


    def test_step_by_step_circuit_inspection(self):
        """
        This function demonstrates how to use Qiskit to print the state vector of every
        step (moment) in a circuit. It also shows how to get the state vector at each
        step, and how to print it in ket notation.
        """
        
        qubits = QuantumRegister(3)
        bits = ClassicalRegister(3)
        circuit = QuantumCircuit(qubits, bits)
        circuit.h(qubits[0])
        circuit.snapshot("step 1")  # This is a snapshot - the simulator will store the statevector at this point
        circuit.x(qubits[2])
        circuit.cx(qubits[0], qubits[1])
        circuit.snapshot("step 2")
        circuit.barrier(qubits)
        circuit.measure(qubits, bits)
        circuit.snapshot("step 3")
        
        simulator = Aer.get_backend('qasm_simulator')
        simulation = execute(circuit, simulator, shots=1)
        snapshots = simulation.result().results[0].data.snapshots.statevector   # Get the statevectors for all of the snapshots
        for(name, state) in snapshots.items():
            print(f"{name}: {state}")
            print("")


    def test_print_circuit_diagram(self):
        """
        This function shows how to print ASCII-based circuit diagrams.
        """

        qubits = QuantumRegister(3)
        bits = ClassicalRegister(3)
        circuit = QuantumCircuit(qubits, bits)
        circuit.h(qubits[0])
        circuit.x(qubits[2])
        circuit.cx(qubits[0], qubits[1])
        circuit.barrier(qubits)
        circuit.measure(qubits, bits)

        print(circuit)    # Print the circuit as an ASCII diagram


    def test_set_explicit_initial_state(self):
        """
        This shows how to set the initial state of the qubits in a circuit.
        """
        
        initial_statevector = [
            complex(0, 0), complex(0, 0), complex(1, 0), complex(0, 0), 
            complex(0, 0), complex(0, 0), complex(0, 0), complex(0, 0)
        ]

        qubits = QuantumRegister(3)
        bits = ClassicalRegister(3)
        circuit = QuantumCircuit(qubits, bits)
        circuit.initialize(initial_statevector, qubits)
        circuit.measure(qubits, bits)
        
        simulator = Aer.get_backend('qasm_simulator')
        simulation = execute(circuit, simulator, shots=1)
        print(simulation.result().get_counts(circuit))
