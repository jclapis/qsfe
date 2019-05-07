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


class SuperdenseCodingTests(unittest.TestCase):
    """
    This class contains a simple implementation of the superdense coding protocol.
    
    Note that unlike the other fundamental algorithms, this class uses a "circuit"
    instance variable to represent the quantum circuit that holds the superdense coding
    protocol. This is another example of Qiskit's flexibility with respect to circuits
    and registers.
    """


    def setUp(self):
        """
        Iniitalizes the unit test class.
        """

        self.circuit = QuantumCircuit()
    

    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def encode_message(self, buffer, pair_a):
        """
        Encodes two bits of information into an entangled qubit.

        Parameters:
            buffer (list[bool]): The two bits to encode into the qubit.
            pair_a (QuantumRegister): The qubit to encode the information into. This
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
            self.circuit.x(pair_a) # X if the low bit is 1
        if(buffer[0]):
            self.circuit.z(pair_a) # Z if the high bit is 1


    def decode_message(self, pair_a, pair_b):
        """
        Decodes two bits of information from an entangled pair of qubits.

        Parameters:
            pair_a (QuantumRegister): The "remote" qubit that was modified by the encoding
                process.
            pair_b (QuantumRegister): The "local" qubit that we received, which wasn't
                directly modified.

        Returns:
            a_measurement (ClassicalRegister): The measurement of the "remote" qubit.
            b_measurement (ClassicalRegister): The measurement of the "local" qubit.
        """

        a_measurement = ClassicalRegister(1, "a_measurement") 
        b_measurement = ClassicalRegister(1, "b_measurement")
        self.circuit.add_register(a_measurement, b_measurement)
        
        self.circuit.cx(pair_a, pair_b)
        self.circuit.h(pair_a)

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
        self.circuit.measure(pair_a, a_measurement)
        self.circuit.measure(pair_b, b_measurement)

        # Note that the classical registers are returned here, instead of being added
        # to the circuit during the test execution function, as another demonstration
        # of Qiskit's flexibility.
        return (a_measurement, b_measurement)

    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_test(self, description, iterations, buffer):
        """
        Runs the superdense coding algorithm on the given classical buffer.

        Parameters:
            description (str): A description of the test, for logging.
            iterations (int): The number of times to run the circuit.
            buffer (list[Bool]): The buffer containing the two bits to send.
        """
        
        # Construct the registers and circuit.
        print(f"Running test: {description}")
        pair_a = QuantumRegister(1, "pair_a")
        pair_b = QuantumRegister(1, "pair_b")
        self.circuit.add_register(pair_a, pair_b)

        # Entangle the qubits together
        self.circuit.h(pair_a)
        self.circuit.cx(pair_a, pair_b)

        # Encode the buffer into the qubits, then decode them into classical measurements
        self.encode_message(buffer, pair_a)
        self.decode_message(pair_a, pair_b)

        # Run the circuit N times.
        simulator = Aer.get_backend('qasm_simulator')
        simulation = execute(self.circuit, simulator, shots=iterations)
        result = simulation.result()
        counts = result.get_counts(self.circuit)

        # Check each result to make sure the result always matched the original buffer
        for(state, count) in counts.items():
            state = state.replace(" ", "") # Get rid of spaces between qubits

            # Read the bits in little-endian ordering...
            first_bit = (state[1] == "1")
            second_bit = (state[0] == "1")

            if(first_bit != buffer[0] or second_bit != buffer[1]):
                self.fail(f"Test {description} failed. Expected [{1 if buffer[0] == True else 0}" +
                            f"{1 if buffer[1] == True else 0}], but got [{state[1]}{state[0]}].")
        
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
