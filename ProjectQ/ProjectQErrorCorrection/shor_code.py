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


class ShorCode(unittest.TestCase):
    """
    This class implements Shor's error correction code. It employs 8 extra
    qubits to protect 1 original qubit, and can recover from one bit flip
    and/or one phase flip (not necessarily on the same qubit).
    See the paper at https://arxiv.org/pdf/0905.2794.pdf for more details.
    """
    

    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def encode_register(self, qubits):
        """
        Creates an error-protected qubit, wrapping the original with 8 spares that
        protect against bit and/or phase flips.

        Parameters:
            qubits (Qureg): The register that will become the logical 
                error-protected qubit. The original qubit can be in any state, but it
                must be the first element. All of the other qubits must be |0>.
        """

        # Copy q0 into q3 and q6 - these 3 qubits will form 3 "blocks" of qubits
        for i in [3, 6]:
            CNOT | (qubits[0], qubits[i])

        # Give q1 and q2 the same phase as q0, and repeat for the other two blocks
        for i in [0, 3, 6]:
            H | qubits[i]
            CNOT | (qubits[i], qubits[i + 1])
            CNOT | (qubits[i], qubits[i + 2])


    def detect_bit_flip_error(self, block):
        """
        Detects which qubit (if any) in the given block was flipped.

        Parameters:
            block (list[Qureg]): The block of 3 qubits to check for bit flips
            
        Returns:
            A tuple containing the syndrome measurement parity values of the first and second
            qubits, and the first and third qubits respectively.

        Remarks:
            This is essentially just the 3-qubit bit flip code. For an explanation of what
            this parity measurement is doing and how it works, check that code first.
        """
        
        parity_qubits = block[0].engine.allocate_qureg(2)

        # Check if q0 and q1 have the same value
        CNOT | (block[0], parity_qubits[0])
        CNOT | (block[1], parity_qubits[0])
        
        # Check if q0 and q2 have the same value
        CNOT | (block[0], parity_qubits[1])
        CNOT | (block[2], parity_qubits[1])

        # Measure the parity values
        Measure | parity_qubits[0]
        Measure | parity_qubits[1]
        parity_01 = int(parity_qubits[0])
        parity_02 = int(parity_qubits[1])

        # Delete the parity qubits since we don't need them anymore, and return the measurements
        del parity_qubits
        return (parity_01, parity_02)


    def detect_phase_flip_error(self, qubits):
        """
        Detects which block (if any) had its phase flipped.

        Parameters:
            qubits (Qureg): The logical quantum register to check for errors
            
        Returns:
            A tuple containing the syndrome measurement parity values of the first and second
            qubits, and the first and third qubits respectively.
        """
        
        parity_qubits = qubits.engine.allocate_qureg(2)

        # Bring the register from the Z basis to the X basis so we can measure the
        # phase differences between blocks
        All(H) | qubits

        # Compare the phases of all 6 qubits from the 1st and 2nd blocks. If any of the
        # qubits in a block had its phase flipped, the entire block will show a phase
        # flip. Like the bit flip measurements, this parity qubit will show a 1 if 
        # the 1st and 2nd blocks have different phases.
        for i in range(0, 6):
            CNOT | (qubits[i], parity_qubits[0])

        # Do the phase parity measurement for the 1st and 3rd blocks.
        for i in [0, 1, 2, 6, 7, 8]:
            CNOT | (qubits[i], parity_qubits[1])

        # Put the qubits back into the Z basis
        All(H) | qubits
        
        # Measure the parity values
        Measure | parity_qubits[0]
        Measure | parity_qubits[1]
        parity_01 = int(parity_qubits[0])
        parity_02 = int(parity_qubits[1])

        # Delete the parity qubits since we don't need them anymore, and return the measurements
        del parity_qubits
        return (parity_01, parity_02)


    def correct_error(self, qubits, parity_measurements, error_name, gate):
        """
        Corrects an error with the specified gate, based on the syndrome parity measurements.

        Parameters:
            qubits (Qureg): The block of 3 qubits to correct
            parity_measurmeents (int, int): A tuple containing the syndrome measurements
                for the block
            error_name (str): The name of the error that could be on a qubit ("bit" or "phase")
            gate (Gate): The gate to apply to the broken qubit
        """

        # This is the same as the "correct errors" function in the bit flip code.
        (parity_01, parity_02) = parity_measurements
        if parity_01 == 1:
            if parity_02 == 1:
                # The print statements need to be commented out because they print so many
                # times that it actually breaks Visual Studio's test runner. Bummer.
                # At least we know they work, thanks to the bit flip code!
                # print(f"Detected {error_name} flip on qubit 0, correcting it.")
                gate | qubits[0]
            else:
                gate | qubits[1]
        else:
            if parity_02 == 1:
                gate | qubits[2]


    def correct_errors(self, qubits):
        """
        Corrects any errors that have occurred within the logical qubit register.

        Parameters:
            qubits (Qureg): The logical qubit register to check and correct
        """
        
        # Correct bit flips on the first block - look at the 3-qubit Bit Flip code for an
        # explanation of how the classical register's output maps to the qubit to flip.
        block_0 = [qubits[0], qubits[1], qubits[2]]
        parity_measurements = self.detect_bit_flip_error(block_0)
        self.correct_error(block_0, parity_measurements, "bit", X)

        # Correct bit flips on the second block
        block_1 = [qubits[3], qubits[4], qubits[5]]
        parity_measurements = self.detect_bit_flip_error(block_1)
        self.correct_error(block_1, parity_measurements, "bit", X)

        # Correct bit flips on the third block
        block_2 = [qubits[6], qubits[7], qubits[8]]
        parity_measurements = self.detect_bit_flip_error(block_2)
        self.correct_error(block_2, parity_measurements, "bit", X)

        # Correct any phase flips. Flipping any qubit in the broken block will end up putting
        # the entire block back into the correct phase, so I just pick the first qubit of each one.
        phase_block = [qubits[0], qubits[3], qubits[6]]
        parity_measurements = self.detect_phase_flip_error(qubits)
        self.correct_error(phase_block, parity_measurements, "phase", Z)


    # ====================
	# == Test Case Code ==
	# ====================


    def run_shor_test(self, description, enable_bit_flip, enable_phase_flip):
        """
        Runs a collection of tests on the Shor ECC.

        Parameters:
            description (name): A description for this batch of tests
            enable_bit_flip (bool): True to run the tests where bit flip errors
                are involved, False to leave bit flips off
            enable_phase_flip (bool): True to run the tests where phase flip errors
                are involved, False to leave phase flips off
        """

        number_of_qubits = 9
        number_of_random_tests = 25
        try:
            run_tests(description, number_of_qubits, number_of_random_tests,
                      self, enable_bit_flip, enable_phase_flip)
        except ValueError as error:
            self.fail(repr(error))
            

    def test_no_flip(self):
        """
        Runs the Shor ECC on all of the test cases without actually flipping
        anything. This is helpful to make sure the test harness works as
        intended when no errors are introduced.
        """

        self.run_shor_test("normal (no error)", False, False)


    def test_bit_flip(self):
        """
        Runs the Shor ECC on all of the test cases with bit-flipping enabled.
        """

        self.run_shor_test("bit flip", True, False)


    def test_phase_flip(self):
        """
        Runs the Shor ECC on all of the test cases with phase-flipping enabled.
        """

        self.run_shor_test("phase flip", False, True)


    def test_combo(self):
        """
        Runs the Shor ECC on all of the test cases with both bit-flipping and 
        phase-flipping enabled.
        """

        self.run_shor_test("combo", True, True)


if __name__ == '__main__':
    unittest.main()
