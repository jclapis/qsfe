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
import os


class EntanglementTests(unittest.TestCase):
    """
    This class contains some basic tests to show how Cirq deals with entanglement.
    """


    def run_test(self, description, circuit, qubits, iterations, valid_states):
        """
        Runs a given circuit as a unit test, measuring the results and ensuring that the
        resulting state matches one of the provided target states.

        Parameters:
            description (str): A human-readable description of the test, which will be printed to the log.
            circuit (Circuit): The circuit to run during the test.
            qubits (list[Qid]): The qubits used in the circuit.
            iterations (int): The number of times to run the test and check that the results match
                a valid state.
            valid_states (list[string]): A list of valid states that the qubits could be in. Each time
                the test is run, this function will check the result and make sure that it matches one
                of these states. If it doesn't match any of these states, the test has failed.
        """
        
        print(f"Running test: {description}")
        number_of_qubits = len(valid_states[0])
        number_of_valid_states = len(valid_states)
        
        # Construct the measurement and append it to the circuit. In this case, we don't care about the
        # individual qubits - we just want the overall result of all of the qubits together, so we can
        # use the measure() function instead of measure_each() like we did in the superposition tests.
        circuit.append(cirq.measure(*qubits, key="result"))

        # Run the circuit N times.
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=iterations)
        result_states = result.histogram(key="result")

        # Check each result to make sure it's one of the valid states
        success_message = ""
        for(state, count) in result_states.items():
            # Turn the state (which is just an integer) into a binary string for easy comparison
            state_string = bin(state)[2:].zfill(len(qubits))

            if state_string not in valid_states:
                self.fail(f"Test {description} failed. Resulting state {state_string} " + 
						"didn't match any valid target states.")
            
            success_message += f"Found state [{state_string}] {count} times.{os.linesep}"

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
        qubits = cirq.NamedQubit.range(len(valid_states[0]), prefix="qubit")
        circuit = cirq.Circuit()

        # Add the gates
        circuit.append(cirq.H(qubits[0]))
        circuit.append(cirq.CNOT(qubits[0], qubits[1]))

        # Run the test
        self.run_test("Bell State", circuit, qubits, 1000, valid_states)


    def test_ghz_state(self):
        """
	    Tests an extension of the Bell State, called the GHZ State,
	    which is just the same thing but with more than two qubits.
        """

        # Construct the circuit
        valid_states = ["00000000", "11111111"]
        qubits = cirq.NamedQubit.range(len(valid_states[0]), prefix="qubit")
        circuit = cirq.Circuit()

        # Add the gates
        circuit.append(cirq.H(qubits[0]))
        for i in range(1, len(qubits)):
            circuit.append(cirq.CNOT(qubits[0], qubits[i]))

        # Run the test
        self.run_test("GHZ State", circuit, qubits, 1000, valid_states)


    def test_phase_flip(self):
        """
	    Tests the entangled phase flip to show that you can change a
        qubit just by changing its entangled partner.

        Note that Cirq doesn't support the concept of an "adjoint" 
        circuit, so we have to explicitly write out inverse operations manually.
        """

        # Construct the circuit
        valid_states = ["10"]
        qubits = cirq.NamedQubit.range(len(valid_states[0]), prefix="qubit")
        circuit = cirq.Circuit()

        # Add the gates
        gates = [
            cirq.H(qubits[0]),
            cirq.CNOT(qubits[0], qubits[1]),
            cirq.Z(qubits[1]),
            cirq.CNOT(qubits[0], qubits[1]),
            cirq.H(qubits[0])
        ]
        circuit.append(gates)

        # Run the test
        self.run_test("entangled phase flip", circuit, qubits, 1000, valid_states)


    def test_multi_control(self):
        """
        Tests entanglement with more than one control qubit.
        """

        # Construct the circuit and the qubits - we're going to use 2 separate registers,
        # where one will be a bunch of control qubits and the other will be a single target
        # qubit.
        valid_states = ["0000", "0010", "0100", "0110", "1000", "1010", "1100", "1111"]
        controls = cirq.NamedQubit.range(len(valid_states[0]) - 1, prefix="control")
        target = cirq.NamedQubit(name="target")
        circuit = cirq.Circuit()

        # Hadamard the first three qubits - these will be the controls
        circuit.append(cirq.H.on_each(*controls))

        # Cirq supports gates that are controlled by arbitrary many qubits, so
        # we don't need to mess with Toffoli gates or custom multi-control implementations.
        # We can just call controlled_by, and it will take care of the rest.
        circuit.append(cirq.X(target).controlled_by(*controls))

        # Run the test
        self.run_test("multi-controlled operation", circuit, controls + [target], 1000, valid_states)



if __name__ == '__main__':
    unittest.main()
