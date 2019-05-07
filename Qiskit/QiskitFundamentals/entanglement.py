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
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import execute
from qiskit import Aer
import os


class EntanglementTests(unittest.TestCase):
    """
    This class contains some basic tests to show how Qiskit deals with entanglement.
    """


    def run_test(self, description, circuit, iterations, valid_states):
        """
        Runs a given circuit as a unit test, measuring the results and ensuring that the
        resulting state matches one of the provided target states.

        Parameters:
            description (str): A human-readable description of the test, which will be printed to the log.
            circuit (QuantumCircuit): The circuit to run during the test.
            iterations (int): The number of times to run the test and check that the results match
                a valid state.
            valid_states (list[string]): A list of valid states that the qubits could be in. Each time
                the test is run, this function will check the result and make sure that it matches one
                of these states. If it doesn't match any of these states, the test has failed.
        """
        
        print(f"Running test: {description}")
        number_of_qubits = len(valid_states[0])
        number_of_valid_states = len(valid_states)
        
        # Construct the measurement and append it to the circuit
        qubits = circuit.qregs[0]
        bits = ClassicalRegister(number_of_qubits)
        circuit.add_register(bits)
        circuit.barrier(qubits)
        circuit.measure(qubits, bits)

        # Run the circuit N times.
        simulator = Aer.get_backend('qasm_simulator')
        simulation = execute(circuit, simulator, shots=iterations)
        result = simulation.result()
        counts = result.get_counts(circuit)

        # Check each result to make sure it's one of the valid states
        success_message = ""
        for(state, count) in counts.items():
            if state not in valid_states:
                self.fail(f"Test {description} failed. Resulting state {state} " + 
						"didn't match any valid target states.")

            success_message += f"Found state [{state}] {count} times.{os.linesep}"

        # If all of the results are valid, print them out with a success message.
        print(success_message)
        print("Passed!")


    def test_bell_state(self):
        """
	    Tests the simplest possible entanglement - the Bell State.
	    This should produce two even possibilities where both qubits
	    have the same result 100% of the time: |00> or |11>.
        """

        # Construct the circuit
        valid_states = ["00", "11"]
        qubits = QuantumRegister(len(valid_states[0]))
        circuit = QuantumCircuit(qubits)

        # Add the gates
        circuit.h(qubits[0])
        circuit.cx(qubits[0], qubits[1])

        # Run the test
        self.run_test("Bell State", circuit, 1000, valid_states)


    def test_ghz_state(self):
        """
	    Tests an extension of the Bell State, called the GHZ State,
	    which is just the same thing but with more than two qubits.
        """

        # Construct the circuit
        valid_states = ["00000000", "11111111"]
        qubits = QuantumRegister(len(valid_states[0]))
        circuit = QuantumCircuit(qubits)

        # Add the gates
        circuit.h(qubits[0])
        for i in range(1, len(qubits)):
            circuit.cx(qubits[0], qubits[i])

        # Run the test
        self.run_test("GHZ State", circuit, 1000, valid_states)


    def test_phase_flip(self):
        """
	    Tests the entangled phase flip to show that you can change a
        qubit just by changing its entangled partner.

        Note that Qiskit doesn't support the concept of an "adjoint" 
        circuit, so we have to explicitly write out inverse operations manually.
        """

        # Construct the circuit
        valid_states = ["01"] # This is "10" in other languages, but Qiskit uses
                              # little-endian registers so it's written backwards.
        qubits = QuantumRegister(len(valid_states[0]))
        circuit = QuantumCircuit(qubits)

        # Add the gates
        circuit.h(qubits[0])
        circuit.cx(qubits[0], qubits[1])
        circuit.z(qubits[1])
        circuit.cx(qubits[0], qubits[1])
        circuit.h(qubits[0])

        # Run the test
        self.run_test("entangled phase flip", circuit, 1000, valid_states)


    def test_multi_control(self):
        """
        Tests entanglement with more than one control qubit.

        Note that Qiskit doesn't support arbitrarily controlled operations,
        so we have to explicitly write out a decomposition into Toffoli gates.
        """

        # Construct the circuit
        valid_states = ["0000", "0100", "0010", "0110", "0001", "0101", "0011", "1111"]
        qubits = QuantumRegister(len(valid_states[0]))
        circuit = QuantumCircuit(qubits)

        # Hadamard the first three qubits - these will be the controls
        circuit.h(qubits[0])
        circuit.h(qubits[1])
        circuit.h(qubits[2])

        # Qiskit supports Toffoli gates, which we can use to do arbitrary controlled
        # operations. We just need an ancilla qubit to contain the CCNOT of the first
        # two control qubits, then we can CCNOT that ancilla with the third control
        # qubit on the target.
        # For a more thorough example, take a look at this post:
        # https://quantumcomputing.stackexchange.com/questions/2177/how-can-i-implement-an-n-bit-toffoli-gate
        # 
        # Note that I'm adding the ancilla explicitly as a separate register, so the
        # run_test method can still just grab the original register for the measurement
        # without touching the ancilla.
        ancilla = QuantumRegister(1)
        circuit.add_register(ancilla)
        circuit.ccx(qubits[0], qubits[1], ancilla[0])
        circuit.ccx(qubits[2], ancilla[0], qubits[3])
        circuit.ccx(qubits[0], qubits[1], ancilla[0])

        # Run the test
        self.run_test("multi-controlled operation", circuit, 1000, valid_states)



if __name__ == '__main__':
    unittest.main()
