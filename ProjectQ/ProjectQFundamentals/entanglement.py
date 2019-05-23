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
from projectq import MainEngine
from projectq.ops import *
from projectq.meta import Dagger, Control
import os
from utility import reset


class EntanglementTests(unittest.TestCase):
    """
    This class contains some basic tests to show how ProjectQ deals with entanglement.
    """


    def run_test(self, description, test_function, iterations, valid_states):
        """
        Runs a given function as a unit test, measuring the results and ensuring that the
        resulting state matches one of the provided target states.

        Parameters:
            description (str): A human-readable description of the test, which will be printed to the log.
            test_function (function): The function that implements the actual test, by
                converting the qubits into the target state.
            iterations (int): The number of times to run the test and check that the results match
                a valid state.
            valid_states (list[string]): A list of valid states that the qubits could be in. Each time
                the test is run, this function will check the result and make sure that it matches one
                of these states. If it doesn't match any of these states, the test has failed.
        """
        
        print(f"Running test: {description}")
        number_of_qubits = len(valid_states[0])
        number_of_valid_states = len(valid_states)

        engine = MainEngine()
        qubits = engine.allocate_qureg(number_of_qubits)

        # Run the test N times.
        counts = {}
        for i in range(0, iterations):
            # Run the test function, which will put the qubits into the desired state
            test_function(qubits)

            # Measure the qubits
            for qubit in qubits:
                Measure | qubit

            # Flush the engine, ensuring all of the simulation is done
            engine.flush()

            # Check the result to make sure it's one of the valid states
            state_string = ""
            for qubit in qubits:
                state_string += str(int(qubit))
            if state_string not in counts:
                counts[state_string] = 0;
            counts[state_string] += 1;

            if state_string not in valid_states:
                self.fail(f"Test {description} failed. Resulting state {state_string} " + 
						"didn't match any valid target states.")

            # Reset the qubits so the experiment can run again
            reset(qubits)

        # If all of the results are valid, print them out with a success message.
            
        success_message = ""
        for (state_string, count) in counts.items():
            success_message += f"Found state [{state_string}] {count} times.{os.linesep}"
        print(success_message)
        print("Passed!")


    def create_bell_state(self, qubits):
        """
        Entangles two qubits to produce the first Bell State 1/√2(|00> + |11>).

        Parameters:
            qubits (Qureg): The qubit register being tested
        """

        H | qubits[0]
        CNOT | (qubits[0], qubits[1])


    def test_bell_state(self):
        """
	    Tests the simplest possible entanglement - the Bell State.
	    This should produce two even possibilities where both qubits
	    have the same result 100% of the time: |00> or |11>.
        """

        valid_states = ["00", "11"]
        self.run_test("Bell State", self.create_bell_state, 1000, valid_states)


    def create_ghz_state(self, qubits):
        """
        Creates the GHZ state using all of the provided qubits.

        Parameters:
            qubits (Qureg): The qubit register being tested
        """

        H | qubits[0]
        for i in range(1, len(qubits)):
            CNOT | (qubits[0], qubits[i])


    def test_ghz_state(self):
        """
	    Tests an extension of the Bell State, called the GHZ State,
	    which is just the same thing but with more than two qubits.
        """

        valid_states = ["00000000", "11111111"]
        self.run_test("GHZ State", self.create_ghz_state, 1000, valid_states)


    def phase_flip_function(self, qubits):
        """
        Flips the first of the provided qubits indirectly via entanglement.

        Parameters:
            qubits (Qureg): The qubit register being tested
        """

        self.create_ghz_state(qubits)
        Z | qubits[1]
        with Dagger(qubits.engine):     # This is how ProjectQ does adjoint code.
            self.create_ghz_state(qubits)


    def test_phase_flip(self):
        """
	    Tests the entangled phase flip to show that you can change a
        qubit just by changing its entangled partner.
        """

        valid_states = ["10"]
        self.run_test("entangled phase flip", self.phase_flip_function, 1000, valid_states)


    def supercontrolled_x(self, qubits):
        """
        This is a multicontrolled X gate, using all but the last qubit as controls to flip
        the last qubit.

        Parameters:
            qubits (Qureg): The qubit register being tested
        """

        # This is a shortcut for applying a gate to a bunch of qubits at once. Not sure if it
        # saves time over a for loop, but it's nice to have.
        All(H) | qubits[:-1]

        # Use all of the qubits but the last one as controls - this is how arbitrary
        # controls work in ProjectQ. Note that you can put whatever you want in this block,
        # classical or quantum. This is going to be very useful for debugging.
        with Control(qubits.engine, qubits[:-1]):
            X | qubits[-1]  # Flip the last qubit


    def test_multi_control(self):
        """
        Tests entanglement with more than one control qubit.
        """

        valid_states = ["0000", "0010", "0100", "0110", "1000", "1010", "1100", "1111"]
        self.run_test("multi-controlled operation", self.supercontrolled_x, 1000, valid_states)



if __name__ == '__main__':
    unittest.main()
