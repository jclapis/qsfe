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


from ecc_test_implementation import run_tests
import unittest
from projectq import MainEngine
from projectq.ops import *
from projectq.meta import Dagger, Control
from utility import reset


class SteaneCode(unittest.TestCase):
    """
    This class implements Steane's error correction code. It uses 6 extra
    qubits to protect 1 original qubit, and can recover from one bit flip
    and/or one phase flip (not necessarily on the same qubit).
    See the paper at https://link.springer.com/article/10.1007/s11128-015-0988-y
    for more details.
    """


    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def encode_register(self, qubits):
        """
        Creates an error-protected qubit, wrapping the original with 6 spares that
	    protect against bit and/or phase flips.

        Parameters:
            qubits (Qureg): The register that will become the logical 
                error-protected qubit. The original qubit can be in any state, but it
                must be the first element. All of the other qubits must be |0>.

        Remarks:
            The circuit for this preparation (called the encoding circuit) can be seen
            in Figure 8 of this paper:
            https://arxiv.org/pdf/quant-ph/9705031.pdf
        """

        # This is not an intuitive circuit at first glance, unlike the Shor code. I
        # really recommend you read the papers on this code to understand why it works,
        # because it's a very cool idea - it's essentially a quantum version of a classical
        # Hamming code used in normal signal processing.
        for i in [4, 5, 6]:
            H | qubits[i]
        for i in [1, 2]:
            CNOT | (qubits[0], qubits[i])
        for i in [0, 1, 3]:
            CNOT | (qubits[6], qubits[i])
        for i in [0, 2, 3]:
            CNOT | (qubits[5], qubits[i])
        for i in [1, 2, 3]:
            CNOT | (qubits[4], qubits[i])


    def detect_bit_flip_error(self, qubits):
        """
        Detects which physical qubit (if any) in the logical qubit was flipped.

        Parameters:
            qubits (Qureg): The logical error-encoded qubit

        Returns:
            An array of syndrome measurement results.
        """

		# With 7 qubits, there are 8 possible error states: one for nothing being
		# broken, and one for each qubit being broken. You can encode those 8 possibilities
		# into a 3-bit binary number. Steane does exactly this, by organizing the 7
		# qubits into 3 blocks of 4 qubits each and by using 3 ancilla qubits for measurement.
		# The blocks are organized in such a way that 3 of the qubits are unique to any given
		# block, 3 belong to 2 blocks, and the last belongs to all 3 blocks. That way, you
		# can turn the ancilla measurements into the 3-bit binary number that tells you exactly
		# which qubit is broken, and flip it accordingly.
        
        parity_qubits = qubits.engine.allocate_qureg(3)

        for i in [0, 2, 4, 6]:  # Block 0: 0, 2, 4, 6
            CNOT | (qubits[i], parity_qubits[2])
        for i in [1, 2, 5, 6]:  # Block 1: 1, 2, 5, 6
            CNOT | (qubits[i], parity_qubits[1])
        for i in [3, 4, 5, 6]:  # Block 2: 3, 4, 5, 6
            CNOT | (qubits[i], parity_qubits[0])

        parity_measurements = [0, 0, 0]
        for i in range(0, 3):
            Measure | parity_qubits[i]
            parity_measurements[i] = int(parity_qubits[i])
        
        del parity_qubits
        return parity_measurements


    def detect_phase_flip_error(self, qubits):
        """
        Detects which physical qubit (if any) had its phase flipped.

        Parameters:
            qubits (Qureg): The logical error-encoded qubit

        Returns:
            An array of syndrome measurement results.
        """
        
		# The rationale here is the same as the bit flip detection above, with two key
		# differences: first, the ancilla qubits are intialized to |+> and read in the X
		# basis. Second, now we're using the ancilla qubits as the controls during the CNOTs
		# instead of the targets. You might ask, how does this make sense? If we're using
		# them as the controls and then just measuring them, how can we possibly get any
		# useful information from the encoded qubit register?
		# Turns out, if one of the register qubits has a phase flip, then that will propagate
		# back to the control qubit during a CNOT. This is called a phase kickback, and it's used
		# all the time in quantum algorithms. Don't believe me? Try it yourself.
		# Do this sequence on your simulator of choice:
		# Start with |00>, then do H(0); CNOT(0, 1); Z(1); CNOT(0, 1); H(0);
		# You'll end up with |10>.
		# Entanglement is black magic. Fun fact: this property is why phase queries work, and
		# how superdense coding actually does something useful.
        
        parity_qubits = qubits.engine.allocate_qureg(3)

        All(H) | parity_qubits
        for i in [0, 2, 4, 6]:  # Block 0: 0, 2, 4, 6
            CNOT | (parity_qubits[2], qubits[i])
        for i in [1, 2, 5, 6]:  # Block 1: 1, 2, 5, 6
            CNOT | (parity_qubits[1], qubits[i])
        for i in [3, 4, 5, 6]:  # Block 2: 3, 4, 5, 6
            CNOT | (parity_qubits[0], qubits[i])
        All(H) | parity_qubits
        
        parity_measurements = [0, 0, 0]
        for i in range(0, 3):
            Measure | parity_qubits[i]
            parity_measurements[i] = int(parity_qubits[i])
        
        del parity_qubits
        return parity_measurements


    def correct_error(self, qubits, parity_measurements, gate):
        """
        Corrects an error with the specified gate, based on the syndrome parity measurements.

        Parameters:
            qubits (Qureg): The block of 3 qubits to correct
            parity_measurmeents (list[int]): An int list containing the syndrome measurements
                for the qubits
            gate (Gate): The gate to apply to the broken qubit
        """
        
        # The 3 parity qubits used during the bit error and phase error detections will
        # end up encoding a 3-bit number that directly maps to the broken qubit in each
        # operation.
		# Here's the table of possibilities, where each term corresponds to the parity bit index.
		# So for example, 000 means all 3 measurements were 0 and 011 means parity_1 and parity_2
		# were measured to be 1.
		# -----------------------
		# 000 = No error
		# 001 = Error or qubit 0
		# 010 = Error on qubit 1
		# 011 = Error on qubit 2
		# 100 = Error on qubit 3
		# 101 = Error on qubit 4
		# 110 = Error on qubit 5
		# 111 = Error on qubit 6
		# -----------------------
        # In ProjectQ, we can just convert the syndrome measurement to an int and flip the
        # specified qubit. Nice and easy.

        # Convert the measurements to an int - this is basically ported from my Q# implementation
        # of Steane's code. Look how much easier this is when we have classical-code-in-the-middle
        # support! Compare this to the Qiskit and Forest implementations - this is so much more
        # elegant.
        broken_index = 0
        broken_index = broken_index | parity_measurements[2]
        broken_index = broken_index | (parity_measurements[1] << 1)
        broken_index = broken_index | (parity_measurements[0] << 2)

        broken_index = broken_index - 1
        if broken_index >= 0:
            gate | qubits[broken_index]


    def correct_errors(self, qubits):
        """
        Corrects any errors that have occurred within the logical qubit register.

        Parameters:
            qubits (Qureg): The logical qubit register to check and correct
        """

        # Correct bit flips
        parity_measurements = self.detect_bit_flip_error(qubits)
        self.correct_error(qubits, parity_measurements, X)

        # Correct phase flips
        parity_measurements = self.detect_phase_flip_error(qubits)
        self.correct_error(qubits, parity_measurements, Z)

            
    # ====================
	# == Test Case Code ==
	# ====================


    def run_steane_test(self, description, enable_bit_flip, enable_phase_flip):
        """
        Runs a collection of tests on the Steane ECC.

        Parameters:
            description (name): A description for this batch of tests
            enable_bit_flip (bool): True to run the tests where bit flip errors
                are involved, False to leave bit flips off
            enable_phase_flip (bool): True to run the tests where phase flip errors
                are involved, False to leave phase flips off
        """

        number_of_qubits = 7
        number_of_random_tests = 25
        try:
            run_tests(description, number_of_qubits, number_of_random_tests,
                      self, enable_bit_flip, enable_phase_flip)
        except ValueError as error:
            self.fail(repr(error))


    def test_no_flip(self):
        """
        Runs the Steane ECC on all of the test cases without actually flipping
        anything. This is helpful to make sure the test harness works as
        intended when no errors are introduced.
        """

        self.run_steane_test("normal (no error)", False, False)


    def test_bit_flip(self):
        """
        Runs the Steane ECC on all of the test cases with bit-flipping enabled.
        """

        self.run_steane_test("bit flip", True, False)


    def test_phase_flip(self):
        """
        Runs the Steane ECC on all of the test cases with phase-flipping enabled.
        """

        self.run_steane_test("phase flip", False, True)


    def test_combo(self):
        """
        Runs the Steane ECC on all of the test cases with both bit-flipping and 
        phase-flipping enabled.
        """

        self.run_steane_test("combo", True, True)


if __name__ == '__main__':
    unittest.main()
