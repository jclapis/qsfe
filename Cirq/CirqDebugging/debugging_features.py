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
import cirq
import math


class DebuggingFeatures(unittest.TestCase):
    """
    This class contains demonstrations of Cirq's debugging and diagnostic features.
    """


    def test_step_by_step_circuit_inspection(self):
        """
        This function demonstrates how to use Cirq to print the state vector of every
        step (moment) in a circuit. It also shows how to get the state vector at each
        step, and how to print it in ket notation.
        """

        qubits = cirq.NamedQubit.range(3, prefix="qubit")
        circuit = cirq.Circuit()
        circuit.append(cirq.H.on_each(*qubits))
        circuit.append(cirq.X(qubits[2]))
        circuit.append(cirq.CNOT(qubits[2], qubits[0]))
        circuit.append(cirq.measure_each(*qubits))

        simulator = cirq.Simulator()
        steps = simulator.simulate_moment_steps(circuit)        # Step through each moment of the circuit
        for step in steps:
            print(step.state_vector())                          # Print the entire state vector for all of the qubits in the circuit
            print(cirq.dirac_notation(step.state_vector()))     # Print the state vector in big-endian ket (Dirac) notation
            print("")


    def test_print_circuit_diagram(self):
        """
        This function shows how to print ASCII-based circuit diagrams.
        """

        qubits = cirq.NamedQubit.range(3, prefix="qubit")
        circuit = cirq.Circuit()
        circuit.append(cirq.H.on_each(*qubits))
        circuit.append(cirq.X(qubits[2]))
        circuit.append(cirq.CNOT(qubits[2], qubits[0]))
        circuit.append(cirq.measure_each(*qubits))

        print(circuit.to_text_diagram())    # Print the circuit as an ASCII diagram


    def test_set_explicit_initial_state(self):
        """
        This shows how to set the initial state of the qubits in a circuit.
        """
        
        qubits = cirq.NamedQubit.range(3, prefix="qubit")
        circuit = cirq.Circuit()
        circuit.append(cirq.H.on_each(*qubits))
        circuit.append(cirq.X(qubits[2]))
        circuit.append(cirq.CNOT(qubits[2], qubits[0]))
        circuit.append(cirq.measure_each(*qubits))

        simulator = cirq.Simulator()
         # Set the initial state to 2, which is |010> (this can also be an entire state vector if you need to get fine-grained
         # or set up superpositions)
        steps = simulator.simulate_moment_steps(circuit, initial_state=2)
