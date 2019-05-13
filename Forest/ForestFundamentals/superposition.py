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


# import vs_test_path_fixup     # Might not need this for pyQuil since the compiler and simulator are run as 
                                # separate processes, we'll see as we go.
import unittest
from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *
import math


class SuperpositionTests(unittest.TestCase):
    """
    This class contains some basic tests to show how pyQuil deals with qubits in superposition.
    Each of these tests will create a program that prepares a superposition, simulates the program
    multiple times, and measures the qubits after each iteration. The number of times that each 
    qubit is in the |0〉 state is recorded, and these results are compared to the expected probabilities
    for each test.
    """


    def run_test(self, program, qubits, description, iterations, target_probabilities, margin):
        """
        Runs a given program as a unit test.

        Parameters:
            program (Program): The program to run during the test.
            qubits (list[QubitPlaceholder]): The qubits used in the program.
            description (str): A description of the test, for logging.
            iterations (int): The number of times to run the program before calculating 
                each qubit's |0〉 probability.
            target_probabilities (list[float]): The expected probabilities for each qubit
                of being in the |0〉 state.
            margin (float): The allowed error margin for each qubit's probability.
        """
        
        print(f"Running test: {description}")
        number_of_qubits = len(program.get_qubits())
        
        # Reserve a block of classical memory to put qubit measurements into. Note that the first argument
        # NEEDS TO BE "ro" for this to work; I tried it with other stuff and it breaks the simulator. Look
        # at the source for QuantumComputer.run, and you'll see why: it has "ro" hardcoded as the memory
        # variable where measurements get stored.
        measurement = program.declare("ro", "BIT", number_of_qubits)

        # Measure each qubit out to a classical memory bit
        for i in range(0, number_of_qubits):
            program += MEASURE(qubits[i], measurement[i])

        # Allocate the placeholder qubits to real ones with actual indices
        assigned_program = address_qubits(program)

        # Set the number of iterations / shots to run the program for
        assigned_program.wrap_in_numshots_loop(iterations)

        # Get a quantum computer using the "anything-goes" machine model, where
        # each qubit is connected to every other qubit. We don't care about physical
        # topology constraints for this evaluation. The "as_qvm" property ensures that
        # this is a simulator, not a real Rigetti machine.
        computer = get_qc(f"{number_of_qubits}q-qvm", as_qvm=True)

        # Compile the program to Quil
        executable = computer.compile(assigned_program)

        # Run the Quil program on the simulator
        results = computer.run(executable)

        # Get the |0〉 counts for each individual qubit
        zero_counts = [0] * number_of_qubits
        for result in results:
            for i in range(0, number_of_qubits):
                if result[i] == 0: 
                    zero_counts[i] += 1
                
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


    def test_identity(self):
        """
        This tests the Identity gate, which does nothing. It's used to test that qubits
        are initialized to |0〉 in pyQuil.
        """

        target_probabilities = [1]

        # pyQuil actually has multiple ways to represent qubits. The most common way is just with an int,
        # which corresponds to the qubit's index on the machine running the program. I personally prefer
        # the "QubitPlaceholder" approach, which creates "virtual" qubits that aren't actually allocated
        # to physical indices until runtime - this lets you remap the physical qubit layout really easily
        # instead of having to completely rewrite the program if you want to change which qubits go where.
        # It requires a little extra work on the development side, but it's a very useful feature to have.
        qubits = QubitPlaceholder.register(len(target_probabilities))

        # Construct the program and add the gates
        program = Program()
        program += I(qubits[0])   # This shows how to run a gate on a single qubit

        # Run the test
        self.run_test(program, qubits, "Identity", 10000, target_probabilities, 0)


    def test_invert(self):
        """
        This tests the X gate, which should flip qubits from |0〉 to |1〉. Each qubit should be |1〉
        with 100% probability after this test.
        """

        # Construct the program
        target_probabilities = [0, 0]
        qubits = QubitPlaceholder.register(len(target_probabilities))
        program = Program()

        # Add the gates
        for qubit in qubits:
            program += X(qubit)

        # Run the test
        self.run_test(program, qubits, "Invert", 10000, target_probabilities, 0)


    def test_hadamard(self):
        """
        This tests the H gate, which should put the qubits in a uniform superposition of |0〉 to |1〉.
        Each qubit should have a 50% chance of being |0〉.
        """

        # Construct the program
        target_probabilities = [0.5, 0.5, 0.5, 0.5]
        qubits = QubitPlaceholder.register(len(target_probabilities))
        program = Program()

        # Add the gates
        for qubit in qubits:
            program += H(qubit)

        # Run the test
        self.run_test(program, qubits, "Hadamard", 10000, target_probabilities, 0.02)


    def test_arbitrary_rotation(self):
        """
        This tests arbitrary rotations around the Y axis (so the X-Z plane) to make sure pyQuil
        can deal with any given superposition.
        """
        
        # This test will perform rotations around the Bloch sphere so that each qubit has an evenly-
        # incrementing chance of being in the |0〉 state. For example, for 3 qubits, it will be 
        # 0% for the first, 50% for the second, and 100% for the third. For 4 qubits, it will be
        # 0%, 33%, 66%, and 100%.
        # 
        # This test is run a bunch of times on various intervals, ranging from 50% to 1/6
		# (16.667%).
        for i in range(2, 7):
            
            interval = 1 / i    # The amount to increase each qubit's probability by, relative to the previous qubit
            target_probabilities = [0] * (i + 1)    # This will store the desired probabilities of each qubit
            step_string = "{:.4f}".format(100 / i)  # The decimal representation of the interval, as a percent

            # Construct the program
            qubits = QubitPlaceholder.register(len(target_probabilities))
            program = Program()
            
            # Calculate the probabilities for each qubit, and add the rotation gates
            for j in range(0, i + 1):
                target_probability = j * interval
                target_probabilities[j] = target_probability

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
                program += RY(angle, qubits[j])

            # Run the test
            self.run_test(program, qubits, f"Rotation with steps of 1/{i} ({step_string}%)", 2000, target_probabilities, 0.05)



if __name__ == '__main__':
    unittest.main()