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


class SuperpositionTests(unittest.TestCase):
    """
    This class contains some basic tests to show how Cirq deals with qubits in superposition.
    Each of these tests will create a circuit that prepares a superposition, simulates the circuit
    multiple times, and measures the qubits after each iteration. The number of times that each 
    qubit is in the |0〉 state is recorded, and these results are compared to the expected probabilities
    for each test.
    """


    def run_test(self, circuit, qubits, description, iterations, target_probabilities, margin):
        """
        Runs a given circuit as a unit test.

        Parameters:
            circuit (Circuit): The circuit to run during the test.
            qubits (list[Qid]): The qubits used in the circuit.
            description (str): A description of the test, for logging.
            iterations (int): The number of times to run the circuit before calculating 
                each qubit's |0〉 probability.
            target_probabilities (list[float]): The expected probabilities for each qubit
                of being in the |0〉 state.
            margin (float): The allowed error margin for each qubit's probability.
        """
        
        print(f"Running test: {description}")
        number_of_qubits = len(target_probabilities)
        
        # Construct the measurement and append it to the circuit. In Cirq, we can construct
        # measurements for each individual qubit and assign that measurement a unique name,
        # which we can then look up in simulation results to get the measurement results for
        # that specific qubit. We can also just measure an entire register at once, as a
        # big-endian integer. For this experiment, measuring the qubit individually is more
        # useful.
        circuit.append(cirq.measure_each(*qubits))

        # Run the circuit N times, and count the results.
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=iterations)

        # Get the |0〉 counts for each individual qubit
        zero_counts = [0] * number_of_qubits
        for i in range(number_of_qubits):
            measurements = result.histogram(key=f"qubit{i}")
            zero_counts[i] = measurements[0]
                
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
        are initialized to |0〉 in Cirq.
        """

        # Construct the circuit
        target_probabilities = [1]
        qubits = cirq.NamedQubit.range(len(target_probabilities), prefix="qubit")
        circuit = cirq.Circuit()

        # Add the gates
        circuit.append(cirq.I(qubits[0]))   # This shows how to run a gate on a single qubit

        # Run the test
        self.run_test(circuit, qubits, "Identity", 10000, target_probabilities, 0)


    def test_invert(self):
        """
        This tests the X gate, which should flip qubits from |0〉 to |1〉. Each qubit should be |1〉
        with 100% probability after this test.
        """

        # Construct the circuit
        target_probabilities = [0, 0]
        qubits = cirq.NamedQubit.range(len(target_probabilities), prefix="qubit")
        circuit = cirq.Circuit()

        # Add the gates
        circuit.append(cirq.X.on_each(*qubits)) # This shows how to apply a gate to all of the 
                                                # qubits in a register

        # Run the test
        self.run_test(circuit, qubits, "Invert", 10000, target_probabilities, 0)


    def test_hadamard(self):
        """
        This tests the H gate, which should put the qubits in a uniform superposition of |0〉 to |1〉.
        Each qubit should have a 50% chance of being |0〉.
        """

        # Construct the circuit
        target_probabilities = [0.5, 0.5, 0.5, 0.5]
        qubits = cirq.NamedQubit.range(len(target_probabilities), prefix="qubit")
        circuit = cirq.Circuit()

        # Add the gates
        circuit.append(cirq.H.on_each(*qubits))

        # Run the test
        self.run_test(circuit, qubits, "Hadamard", 10000, target_probabilities, 0.02)


    def test_arbitrary_rotation(self):
        """
        This tests arbitrary rotations around the Y axis (so the X-Z plane) to make sure Cirq
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

            # Construct the circuit
            qubits = cirq.NamedQubit.range(len(target_probabilities), prefix="qubit")
            circuit = cirq.Circuit()
            
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
                circuit.append(cirq.Ry(angle).on(qubits[j]))

            # Run the test
            self.run_test(circuit, qubits, f"Rotation with steps of 1/{i} ({step_string}%)", 2000, target_probabilities, 0.05)



if __name__ == '__main__':
    unittest.main()