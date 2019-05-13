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


import unittest
from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *
import os


class EntanglementTests(unittest.TestCase):
    """
    This class contains some basic tests to show how Forest deals with entanglement.
    """


    def run_test(self, description, program, qubits, iterations, valid_states):
        """
        Runs a given program as a unit test, measuring the results and ensuring that the
        resulting state matches one of the provided target states.

        Parameters:
            description (str): A human-readable description of the test, which will be printed to the log.
            program (Program): The program to run during the test.
            qubits (list[QubitPlaceholder]): The qubits used in the program.
            iterations (int): The number of times to run the test and check that the results match
                a valid state.
            valid_states (list[string]): A list of valid states that the qubits could be in. Each time
                the test is run, this function will check the result and make sure that it matches one
                of these states. If it doesn't match any of these states, the test has failed.
        """
        
        print(f"Running test: {description}")
        number_of_qubits = len(valid_states[0])
        number_of_valid_states = len(valid_states)
        
        # Construct the measurement and append it to the program. In this case, we don't care about the
        # individual qubits - we just want the overall result of all of the qubits together, so we can
        # use the measure() function instead of measure_each() like we did in the superposition tests.
        measurement = program.declare("ro", "BIT", number_of_qubits)
        for i in range(0, number_of_qubits):
            program += MEASURE(qubits[i], measurement[i])

        # Run the program N times.
        assigned_program = address_qubits(program)
        assigned_program.wrap_in_numshots_loop(iterations)
        computer = get_qc(f"{number_of_qubits}q-qvm", as_qvm=True)
        executable = computer.compile(assigned_program)
        results = computer.run(executable)

        # Check each result to make sure it's one of the valid states
        success_message = ""
        counts = {}
        for result in results:
            # Create a state string from the individual bits
            state_string = ""
            for bit in result:
                state_string += str(bit)
            if state_string not in counts:
                counts[state_string] = 0;
            counts[state_string] += 1;

            if state_string not in valid_states:
                self.fail(f"Test {description} failed. Resulting state {state_string} " + 
						"didn't match any valid target states.")
            
        for (state_string, count) in counts.items():
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

        # Construct the program
        valid_states = ["00", "11"]
        qubits = QubitPlaceholder.register(len(valid_states[0]))
        program = Program()

        # Add the gates
        program += H(qubits[0])
        program += CNOT(qubits[0], qubits[1])

        # Run the test
        self.run_test("Bell State", program, qubits, 1000, valid_states)


    def test_ghz_state(self):
        """
	    Tests an extension of the Bell State, called the GHZ State,
	    which is just the same thing but with more than two qubits.
        """

        # Construct the program
        valid_states = ["00000000", "11111111"]
        qubits = QubitPlaceholder.register(len(valid_states[0]))
        program = Program()

        # Add the gates
        program += H(qubits[0])
        for i in range(1, len(qubits)):
            program += CNOT(qubits[0], qubits[i])

        # Run the test
        self.run_test("GHZ State", program, qubits, 1000, valid_states)


    def test_phase_flip(self):
        """
	    Tests the entangled phase flip to show that you can change a
        qubit just by changing its entangled partner.
        """

        # Construct the program
        valid_states = ["10"]
        qubits = QubitPlaceholder.register(len(valid_states[0]))
        entangle = Program(
            H(qubits[0]),
            CNOT(qubits[0], qubits[1])
        )
        program = Program(entangle);
        program += Z(qubits[1])
        program += entangle.dagger();   # dagger() is pyQuil's way of creating
                                        # the adjoint version of circuits / programs, the
                                        # first Python framework to do it in my tests!


        # Run the test
        self.run_test("entangled phase flip", program, qubits, 1000, valid_states)


    def test_multi_control(self):
        """
        Tests entanglement with more than one control qubit.

        NOTE: This will currently fail because pyQuil has a bug with controlled gates
        and QubitPlaceholder: https://github.com/rigetti/pyquil/issues/905
        Once that gets fixed, I'll revisit this function.
        """

        # Construct the program and the qubits - we're going to use 2 separate registers,
        # where one will be a bunch of control qubits and the other will be a single target
        # qubit.
        valid_states = ["0000", "0010", "0100", "0110", "1000", "1010", "1100", "1111"]
        controls = QubitPlaceholder.register(len(valid_states[0]) - 1)
        target = QubitPlaceholder()
        program = Program()

        # Hadamard the first three qubits - these will be the controls
        for control in controls:
            program += H(control);

        # pyQuil supports gates that are controlled by arbitrary many qubits, so
        # we don't need to mess with Toffoli gates or custom multi-control implementations.
        # We just have to chain a bunch of controlled() calls for each control qubit.
        gate = X(target)
        for control in controls:
            gate = gate.controlled(control)
        program += gate

        # Run the test
        self.run_test("multi-controlled operation", program, controls + [target], 1000, valid_states)



if __name__ == '__main__':
    unittest.main()
