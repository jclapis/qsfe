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
from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *


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
            qubits (list[QubitPlaceholder]): The register that will become the logical 
                error-protected qubit. The original qubit can be in any state, but it
                must be the first element. All of the other qubits must be |0>.
        
        Returns:
            A Program that encodes the qubit into a logical register.
        """

        program = Program()
        # Copy q0 into q3 and q6 - these 3 qubits will form 3 "blocks" of qubits
        for i in [3, 6]:
            program += CNOT(qubits[0], qubits[i])

        # Give q1 and q2 the same phase as q0, and repeat for the other two blocks
        for i in [0, 3, 6]:
            program += H(qubits[i])
            program += CNOT(qubits[i], qubits[i + 1])
            program += CNOT(qubits[i], qubits[i + 2])

        return program


    def detect_bit_flip_error(self, program, block, parity_qubits, parity_measurement):
        """
        Detects which qubit (if any) in the given block was flipped.

        Parameters:
            program (Program): The program to add the error detection to
            block (list[QubitPlaceholder]): The block of 3 qubits to check for bit flips
            parity_qubits (list[QubitPlaceholder]): The ancilla qubits to use when determining
                which qubit was flipped
            parity_measurement (MemoryReference): The classical register used to
                measure the parity qubits

        Remarks:
            This is essentially just the 3-qubit bit flip code. For an explanation of what
            this parity measurement is doing and how it works, check that code first.
        """
        
        # Check if q0 and q1 have the same value
        program += CNOT(block[0], parity_qubits[0])
        program += CNOT(block[1], parity_qubits[0])
        
        # Check if q0 and q2 have the same value
        program += CNOT(block[0], parity_qubits[1])
        program += CNOT(block[2], parity_qubits[1])

        # Measure the parity values and return the measurement register
        program += MEASURE(parity_qubits[0], parity_measurement[0])
        program += MEASURE(parity_qubits[1], parity_measurement[1])


    def detect_phase_flip_error(self, program, qubits, parity_qubits, parity_measurement):
        """
        Detects which block (if any) had its phase flipped.

        Parameters:
            program (Program): The program to add the detection gates to
            qubits (list[QubitPlaceholder]): The logical quantum register to check for errors
            parity_qubits (list[QubitPlaceholder]): The ancilla qubits to use when determining
                which qubit was flipped
            parity_measurement (MemoryReference): The classical register used to
                measure the parity qubits
        """
        
        # Bring the register from the Z basis to the X basis so we can measure the
        # phase differences between blocks
        for qubit in qubits:
            program += H(qubit)

        # Compare the phases of all 6 qubits from the 1st and 2nd blocks. If any of the
        # qubits in a block had its phase flipped, the entire block will show a phase
        # flip. Like the bit flip measurements, this parity qubit will show a 1 if 
        # the 1st and 2nd blocks have different phases.
        for i in range(0, 6):
            program += CNOT(qubits[i], parity_qubits[0])

        # Do the phase parity measurement for the 1st and 3rd blocks.
        for i in [0, 1, 2, 6, 7, 8]:
            program += CNOT(qubits[i], parity_qubits[1])

        # Put the qubits back into the Z basis
        for qubit in qubits:
            program += H(qubit)

        # Measure the parity values
        program += MEASURE(parity_qubits[0], parity_measurement[0])
        program += MEASURE(parity_qubits[1], parity_measurement[1])


    def generate_classical_control_corrector(self, program, qubits, parity_measurement, gate):
        """
        Adds the error correction branches to the program, based on the parity measurements.

        Parameters:
            program (Program): The program being constructed
            qubits (list[QubitPlaceholder]): The logical error-encoded qubit
            parity_measurement (MemoryReference): The classical register used to
                measure the parity qubits. This should already have the measurement
                results stored in it.
            gate (function): The gate to apply to the broken qubit in order to fix it
        """

        # if parity[0] == 1
        if_parity_0 = Program()
        #   if parity[1] == 1, then flip q0, otherwise flip q1.
        if_parity_0.if_then(parity_measurement[1], gate(qubits[0]), gate(qubits[1]))

        # if parity[0] == 0
        if_not_parity_0 = Program()
        #   if parity[1] == 1, then flip q2, else do nothing.
        if_not_parity_0.if_then(parity_measurement[1], gate(qubits[2]), Program())

        # Append the branches to the original program
        program.if_then(parity_measurement[0], if_parity_0, if_not_parity_0)



    def correct_errors(self, program, qubits):
        """
        Corrects any errors that have occurred within the logical qubit register.

        Parameters:
            program (Program): The program to add the error correction to
            qubits (list[QubitPlaceholder]): The logical qubit register to check and correct
        """
        
        parity_qubits = QubitPlaceholder.register(2)
        parity_measurement = program.declare("parity_measurement", "BIT", 2)

        # Correct bit flips on the first block - look at the 3-qubit Bit Flip code for an
        # explanation of how the classical register's output maps to the qubit to flip.
        block_0 = [qubits[0], qubits[1], qubits[2]]
        self.detect_bit_flip_error(program, block_0, parity_qubits, parity_measurement)
        self.generate_classical_control_corrector(program, block_0, parity_measurement, X)
        for qubit in parity_qubits:
            program += RESET(qubit)

        # Correct bit flips on the second block
        block_1 = [qubits[3], qubits[4], qubits[5]]
        self.detect_bit_flip_error(program, block_1, parity_qubits, parity_measurement)
        self.generate_classical_control_corrector(program, block_1, parity_measurement, X)
        for qubit in parity_qubits:
            program += RESET(qubit)  

        # Correct bit flips on the third block
        block_2 = [qubits[6], qubits[7], qubits[8]]
        self.detect_bit_flip_error(program, block_2, parity_qubits, parity_measurement)
        self.generate_classical_control_corrector(program, block_2, parity_measurement, X)
        for qubit in parity_qubits:
            program += RESET(qubit)  

        # Correct any phase flips. Flipping any qubit in the broken block will end up putting
        # the entire block back into the correct phase, so I just pick the first qubit of each one.
        phase_block = [qubits[0], qubits[3], qubits[6]]
        self.detect_phase_flip_error(program, qubits, parity_qubits, parity_measurement)
        self.generate_classical_control_corrector(program, phase_block, parity_measurement, Z)


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
        number_of_parity_qubits = 2
        number_of_random_tests = 25
        try:
            run_tests(description, number_of_qubits, number_of_parity_qubits,
                      number_of_random_tests, self, enable_bit_flip, enable_phase_flip)
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
