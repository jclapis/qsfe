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
import math


class SuperpositionTests(unittest.TestCase):
    """
    This class contains some basic tests to show how ProjectQ deals with qubits in superposition.
    Each of these tests will create a circuit that prepares a superposition, simulates the circuit
    multiple times, and measures the qubits after each iteration. The number of times that each 
    qubit is in the |0〉 state is recorded, and these results are compared to the expected probabilities
    for each test.
    """


    def run_test(self, test_function, description, iterations, target_probabilities, margin):
        """
        Runs a given superposition preparation function as a unit test.

        Parameters:
            test_function (function): The function that implements the actual test, by
                converting the qubits into the target state.
            description (str): A description of the test, for logging.
            iterations (int): The number of times to run the circuit before calculating
                each qubit's |0〉 probability.
            target_probabilities (list[float]): The expected probabilities for each qubit
                of being in the |0〉 state.
            margin (float): The allowed error margin for each qubit's probability.

        Remarks:
            ProjectQ doesn't actually build a standalone circuit / program object like
            the other python frameworks; it actually runs the simulation instruction-by-
            instruction, line-by-line right here in the Python code. This is a lot closer
            to how Q# does things. Because of this, we don't actually build a circuit as
            an object and pass it around; instead, we just run the whole simulation in
            a for loop.
        """
        
        print(f"Running test: {description}")
        number_of_qubits = len(target_probabilities)

        zero_counts = [0] * number_of_qubits
        
        # Create the engine and the qubit register (it's more efficient to create it
        # and reuse it outside of the loop than rebuilding it every iteration).
        engine = MainEngine()
        qubits = engine.allocate_qureg(number_of_qubits)

        # Run the test N times.
        for i in range(0, iterations):
            # Run the test function, which will put the qubits into the desired state
            test_function(qubits)

            # Measure the qubits
            for qubit in qubits:
                Measure | qubit

            # Flush the engine, ensuring all of the simulation is done
            engine.flush()

            # Increment the zero count for any qubit that was measured to be |0>
            for i in range(0, number_of_qubits):
                if int(qubits[i]) == 0:
                    zero_counts[i] += 1
                else:
                    # Reset the qubit to |0> since we're reusing the register. Note that
                    # ProjectQ doesn't have a Reset function, so we have to do it manually.
                    X | qubits[i]

        # Compare the probabilities with the targets
        target_string = "Target: [ "
        result_string = "Result: [ "
        for i in range(number_of_qubits):
            target_probability = target_probabilities[i]
            measured_probability = zero_counts[i] / iterations # Python 3 automatically does float division

            target_string += "{:.4f}".format(target_probability) + " ";
            result_string += "{:.4f}".format(measured_probability) + " ";

            discrepancy = abs(target_probability - measured_probability)
            if(discrepancy > margin):
                self.fail(f"Test {description} failed. Qubit {i} had a |0> probability of " +
					f"{measured_probability}, but it should have been {target_probability} " +
					f"(with a margin of {margin}).")

        # If the test passed, print the results.
        target_string += "]"
        result_string += "]"
        print(target_string)
        print(result_string)
        print("Passed!")
        print()


    def identity_function(self, qubits):
        """
        Applies the identity (I) gate to the qubits in the given register.

        Parameters:
            qubits (Qureg): The qubit register being tested
        """

        # Note: ProjectQ doesn't actually have an I gate, so this test does absolutely
        # nothing.


    def test_identity(self):
        """
        This tests the Identity gate, which does nothing. It's used to test that qubits
        are initialized to |0〉 in ProjectQ.
        """

        iterations = 10000
        target_probabilities = [1]
        self.run_test(self.identity_function, "Identity", 10000, target_probabilities, 0)


    def invert_function(self, qubits):
        """
        Applies the X gate to the register.

        Parameters:
            qubits (Qureg): The qubit register being tested
        """

        for qubit in qubits:
            X | qubit


    def test_invert(self):
        """
        This tests the X gate, which should flip qubits from |0〉 to |1〉. Each qubit should be |1〉
        with 100% probability after this test.
        """

        iterations = 10000
        target_probabilities = [0, 0]
        self.run_test(self.invert_function, "Invert", 10000, target_probabilities, 0)


    def hadamard_function(self, qubits):
        """
        Applies the H gate to the register.

        Parameters:
            qubits (Qureg): The qubit register being tested
        """

        for qubit in qubits:
            H | qubit


    def test_hadamard(self):
        """
        This tests the H gate, which should put the qubits in a uniform superposition of |0〉 to |1〉.
        Each qubit should have a 50% chance of being |0〉.
        """

        iterations = 10000
        target_probabilities = [0.5, 0.5, 0.5, 0.5]
        self.run_test(self.hadamard_function, "Hadamard", 10000, target_probabilities, 0.02)


    def arbitrary_rotation_function(self, qubits):
        """
        This function will perform rotations around the Bloch sphere so that each qubit has an evenly-
        incrementing chance of being in the |0〉 state. For example, for 3 qubits, it will be 
        0% for the first, 50% for the second, and 100% for the third. For 4 qubits, it will be
        0%, 33%, 66%, and 100%.

        Parameters:
            qubits (Qureg): The qubit register being tested
        """
        
        # Calculate the probabilities for each qubit, and add the rotation gates
        interval = 1 / (len(qubits) - 1)
        for i in range(0, len(qubits)):
            target_probability = i * interval

            # To get this probability, we have to rotate around the Y axis
			# (AKA just moving around on the X and Z plane) by this angle. 
			# The Bloch equation is |q> = cos(θ/2)|0> + e^iΦ*sin(θ/2)|1>,
			# where θ is the angle from the +Z axis on the Z-X plane, and Φ
			# is the angle from the +X axis on the X-Y plane. Since we aren't
			# going to bring imaginary numbers into the picture for this test,
			# we can leave Φ at 0 and ignore it entirely. We just want to rotate
			# along the unit circle defined by the Z-X plane, thus a rotation
			# around the Y axis.
			# 
			# The amplitude of |0> is given by cos(θ/2) as shown above. The
			# probability of measuring |0> is the amplitude squared, so
			# P = cos²(θ/2). So to get the angle, it's:
			# √P = cos(θ/2)
			# cos⁻¹(√P) = θ/2
			# θ = 2cos⁻¹(√P)
			# Then we just rotate the qubit by that angle around the Y axis,
			# and we should be good.
			#
			# See https://en.wikipedia.org/wiki/Bloch_sphere for more info on
			# the Bloch sphere, and how rotations around it affect the qubit's
			# probabilities of measurement.
            angle = 2 * math.acos(math.sqrt(target_probability))
            Ry(angle) | qubits[i]


    def test_arbitrary_rotation(self):
        """
        This tests arbitrary rotations around the Y axis (so the X-Z plane) to make sure ProjectQ
        can deal with any given superposition.
        """
        
        # This test is run a bunch of times on various intervals, ranging from 50% to 1/6
		# (16.667%).
        for i in range(2, 7):
            
            interval = 1 / i    # The amount to increase each qubit's probability by, relative to the previous qubit
            step_string = "{:.4f}".format(100 / i)  # The decimal representation of the interval, as a percent
            target_probabilities = [0] * (i + 1)    # This will store the desired probabilities of each qubit
            for j in range(0, i + 1):
                target_probability = j * interval
                target_probabilities[j] = target_probability

            # Run the test
            self.run_test(self.arbitrary_rotation_function, f"Rotation with steps of 1/{i} ({step_string}%)", 2000, target_probabilities, 0.05)



if __name__ == '__main__':
    unittest.main()