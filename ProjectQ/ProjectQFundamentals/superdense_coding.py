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
from utility import reset


class SuperdenseCodingTests(unittest.TestCase):
    """
    This class contains a simple implementation of the superdense coding protocol.
    """
    

    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def encode_message(self, buffer, pair_a):
        """
        Encodes two bits of information into an entangled qubit.

        Parameters:
            buffer (list[bool]): The two bits to encode into the qubit.
            pair_a (Qureg): The qubit to encode the information into. This
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
            X | pair_a  # X if the low bit is 1
        if(buffer[0]):
            Z | pair_a  # Z if the high bit is 1


    def decode_message(self, pair_a, pair_b):
        """
        Decodes two bits of information from an entangled pair of qubits.

        Parameters:
            pair_a (Qureg): The "remote" qubit that was modified by the encoding
                process.
            pair_b (Qureg): The "local" qubit that we received, which wasn't
                directly modified.

        Returns:
            The decoded classical buffer.
        """

        CNOT | (pair_a, pair_b)
        H | pair_a

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
        Measure | pair_a
        Measure | pair_b
        return (int(pair_a), int(pair_b))

    
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
        
        # Construct the engine and qubits
        print(f"Running test: {description}")
        engine = MainEngine()
        pair_a = engine.allocate_qubit()
        pair_b = engine.allocate_qubit()

        desired_a_state = int(buffer[0])
        desired_b_state = int(buffer[1])

        for i in range(0, iterations):
            # Entangle the qubits together
            H | pair_a
            CNOT | (pair_a, pair_b)

            # Encode the buffer into the qubits, then decode them into classical measurements
            self.encode_message(buffer, pair_a)
            (a_measurement, b_measurement) = self.decode_message(pair_a, pair_b)
        
            # Check the first qubit to make sure it was the expected value
            if a_measurement != desired_a_state:
                self.fail(f"Test {description} failed. The first bit should have been {desired_a_state} " +
                            f"but it was {a_measurement}.")
            
            # Check the second qubit to make sure it was the expected value
            if b_measurement != desired_b_state:
                self.fail(f"Test {description} failed. The first bit should have been {desired_b_state} " +
                            f"but it was {b_measurement}.")

            # Reset and run again!
            reset([pair_a, pair_b])
            engine.flush()

        print(f"The first qubit was {desired_a_state} all {iterations} times.")
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
