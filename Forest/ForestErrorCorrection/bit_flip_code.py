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


class BitFlipCode(unittest.TestCase):
    """
    This class implements the simple 3-qubit error correction code. It
    employs 2 extra qubits to protect 1 original qubit, and can recover from
    one bit flip on any qubit (but does not offer any phase flip protection).
    See the paper at https://arxiv.org/pdf/0905.2794.pdf for more details.
    """
    

    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def encode_register(self, qubits):
        """
        Creates an error-protected logical qubit, transforming A|000> + B|100> into
        A|000> + B|111> which will be used for the 3-qubit error correction code.
        This returns a Program so that it can be inverted for decoding.

        Parameters:
            qubits (list[QubitPlaceholder]): The register that will become the logical 
                error-protected qubit. The original qubit can be in any state, but it
                must be the first element. All of the other qubits must be |0>.
        
        Returns:
            A Program that encodes the qubit into a logical register.
        """

        program = Program(
            CNOT(qubits[0], qubits[1]),
            CNOT(qubits[0], qubits[2])
        )

        return program


    def detect_error(self, program, qubits):
        """
        Detects a bit-flip error on one of the three qubits in a logical qubit register.

        Parameters:
            program (Program): The program to add the error detection to
            qubits (list[QubitPlaceholder]): The logical qubit register to check for errors

        Returns:
            A MemoryReference list representing the parity measurements. The first one
            contains the parity of qubits 0 and 1, and the second contains the parity
            of qubits 0 and 2.
        """

        # The plan here is to check if q0 and q1 have the same parity (00 or 11), and if q0 and q2
        # have the same parity. If both checks come out true, then there isn't an error. Otherwise,
        # if one of the checks reveals a parity discrepancy, we can use the other check to tell us
        # which qubit is broken.
        
        parity_qubits = QubitPlaceholder.register(2)
        parity_measurement = program.declare("parity_measurement", "BIT", 2)

        # Check if q0 and q1 have the same value
        program += CNOT(qubits[0], parity_qubits[0])
        program += CNOT(qubits[1], parity_qubits[0])
        
        # Check if q0 and q2 have the same value
        program += CNOT(qubits[0], parity_qubits[1])
        program += CNOT(qubits[2], parity_qubits[1])

        # Measure the parity values and return the measurement register
        program += MEASURE(parity_qubits[0], parity_measurement[0])
        program += MEASURE(parity_qubits[1], parity_measurement[1])

        return parity_measurement


    def correct_errors(self, program, qubits):
        """
        Corrects any errors that have occurred within the logical qubit register.

        Parameters:
            program (Program): The program to add the error correction to
            qubits (list[QubitPlaceholder]): The logical qubit register to check and correct
        """

        # Determine which qubit (if any) is broken.
        parity_measurements = self.detect_error(program, qubits)

        # The parity measurements will be as follows:
        # 
        # 00 = none are different
        # 01 = 0 and 2 are different but 0 and 1 are the same, so 2 is broken
        # 10 = 0 and 1 are different but 0 and 2 are the same, so 1 is broken
        # 11 = 0 and 1 are different, and 0 and 2 are different, so 0 is broken
        # 
        # In pyQuil, we can create multiple quantum programs that can act as individual
        # branch bodies of a classical if/else statement, so we can switch based on the
        # parity measurement results. These lines will fix the broken qubit based on this
        # measurement.

        # if parity[0] == 1
        if_parity_0 = Program()
        #   if parity[1] == 1, then flip q0, otherwise flip q1.
        if_parity_0.if_then(parity_measurements[1], X(qubits[0]), X(qubits[1]))

        # if parity[0] == 0
        if_not_parity_0 = Program()
        #   if parity[1] == 1, then flip q2, else do nothing.
        if_not_parity_0.if_then(parity_measurements[1], X(qubits[2]), Program())

        # Append the branches to the original program
        program.if_then(parity_measurements[0], if_parity_0, if_not_parity_0)

    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_bit_flip_test(self, description, enable_bit_flip):
        """
        Runs a collection of tests on the bit-flip ECC.

        Parameters:
            description (name): A description for this batch of tests
            enable_bit_flip (bool): True to run the tests where bit flip errors
                are involved, False to leave bit flips off
        """

        number_of_qubits = 3
        number_of_parity_qubits = 2
        number_of_random_tests = 25
        try:
            run_tests(description, number_of_qubits, number_of_parity_qubits,
                      number_of_random_tests, self, enable_bit_flip, False)
        except ValueError as error:
            self.fail(repr(error))


    def test_no_flip(self):
        """
        Runs the bit-flip ECC on all of the test cases without actually
        flipping any bits. This is helpful to make sure the test harness works
        as intended when no errors are introduced.
        """

        self.run_bit_flip_test("normal (no error)", False)


    def test_flip(self):
        """
        Runs the bit-flip ECC on all of the test cases with bit-flipping
        enabled, to make sure the code can identify and correct errors.
        """

        self.run_bit_flip_test("bit flip", True)

        

if __name__ == '__main__':
    unittest.main()