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


class SuperdenseCodingTests(unittest.TestCase):
    """
    This class contains a simple implementation of the superdense coding protocol.
    
    Note that unlike the other fundamental algorithms, this class uses a "program"
    instance variable to represent the quantum program that holds the superdense coding
    protocol. This is another example of pyQuil's flexibility with respect to programs
    and registers.
    """


    def setUp(self):
        """
        Iniitalizes the unit test class.
        """

        self.program = Program()
    

    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def encode_message(self, buffer, pair_a):
        """
        Encodes two bits of information into an entangled qubit.

        Parameters:
            buffer (list[bool]): The two bits to encode into the qubit.
            pair_a (QubitPlaceholder): The qubit to encode the information into. This
                qubit must have already been entangled with another one.
        """

        # Superposition takes advantage of the fact that if you start with |00> + |11>,
		# you can modify it with X and Z on one qubit in a way that will affect both
		# qubits.
		# Nothing, X, Z, and XZ will all produce discrete, measureable states when
		# both qubits are disentangled.
		# We're going to use this lookup table to encode the given bits into the qubit
		# pair:
		# 00 = |00> + |11> (nothing happens)
		# 01 = |01> + |10> (X, the parity is flipped)
		# 10 = |00> - |11> (Z, the phase is flipped)
		# 11 = |01> - |10> (XZ, parity and phase are flipped)

        if(buffer[1]):
            self.program += X(pair_a) # X if the low bit is 1
        if(buffer[0]):
            self.program += Z(pair_a) # Z if the high bit is 1


    def decode_message(self, pair_a, pair_b):
        """
        Decodes two bits of information from an entangled pair of qubits.

        Parameters:
            pair_a (QubitPlaceholder): The "remote" qubit that was modified by the encoding
                process.
            pair_b (QubitPlaceholder): The "local" qubit that we received, which wasn't
                directly modified.

        Returns:
            a_measurement_index (int): The index of the measurement of the "remote" qubit.
            b_measurement_index (int): The index of the measurement of the "local" qubit.
        """

        self.program += CNOT(pair_a, pair_b)
        self.program += H(pair_a)

		# Here's the decoding table based on the states after running
		# them through CNOT(A, B) and H(A):
		# |00> + |11>  =>  |00> + |10>  =>  |00>, so 00 means nothing happened
		# |01> + |10>  =>  |01> + |11>  =>  |01>, so 01 means X happened
		# |00> - |11>  =>  |00> - |10>  =>  |10>, so 10 means Z happened
		# |01> - |10>  =>  |01> - |11>  =>  |11>, so 11 means XZ happened
		# Notice how all 4 options align with the bit string used by the encoding
		# table, so measuring these qubits gives us the original bits where 
		# pair_b corresponds to whether or not X was used, and pair_a corresponds
		# to Z.
        measurement = self.program.declare("ro", "BIT", 2)

        self.program += MEASURE(pair_a, measurement[0])
        self.program += MEASURE(pair_b, measurement[1])

        return (0, 1)

    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_test(self, description, iterations, buffer):
        """
        Runs the superdense coding algorithm on the given classical buffer.

        Parameters:
            description (str): A description of the test, for logging.
            iterations (int): The number of times to run the program.
            buffer (list[Bool]): The buffer containing the two bits to send.
        """
        
        # Construct the registers
        print(f"Running test: {description}")
        pair_a = QubitPlaceholder()
        pair_b = QubitPlaceholder()

        # Entangle the qubits together
        self.program += H(pair_a)
        self.program += CNOT(pair_a, pair_b)

        # Encode the buffer into the qubits, then decode them into classical measurements
        self.encode_message(buffer, pair_a)
        (a_measurement_index, b_measurement_index) = self.decode_message(pair_a, pair_b)

        # Run the program N times.
        assigned_program = address_qubits(self.program)
        assigned_program.wrap_in_numshots_loop(iterations)
        computer = get_qc(f"2q-qvm", as_qvm=True)
        executable = computer.compile(assigned_program)
        results = computer.run(executable)

        # Check the first qubit to make sure it was always the expected value
        desired_a_state = int(buffer[0])
        for result in results:
            if result[a_measurement_index] != desired_a_state:
                self.fail(f"Test {description} failed. The first bit should have been {desired_a_state} " +
                            f"but it was {result[a_measurement_index]}.")
        else:
            print(f"The first qubit was {desired_a_state} all {iterations} times.")
            
        # Check the second qubit to make sure it was always the expected value
        desired_b_state = int(buffer[1])
        for result in results:
            if result[b_measurement_index] != desired_b_state:
                self.fail(f"Test {description} failed. The first bit should have been {desired_b_state} " +
                            f"but it was {result[b_measurement_index]}.")
        else:
            print(f"The second qubit was {desired_b_state} all {iterations} times.")

        print("Passed!")
        print()


    def test_00(self):
        """
        Runs the superdense coding test on [00].
        """

        self.run_test("Superdense [00]", 100, [False, False])


    def test_01(self):
        """
        Runs the superdense coding test on [01].
        """

        self.run_test("Superdense [01]", 100, [False, True])


    def test_10(self):
        """
        Runs the superdense coding test on [10].
        """

        self.run_test("Superdense [10]", 100, [True, False])


    def test_11(self):
        """
        Runs the superdense coding test on [11].
        """

        self.run_test("Superdense [11]", 100, [True, True])



if __name__ == '__main__':
    unittest.main()
