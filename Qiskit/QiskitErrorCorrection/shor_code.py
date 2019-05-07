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
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister


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


    def encode_register(self, circuit, qubits):
        """
        Creates an error-protected qubit, wrapping the original with 8 spares that
        protect against bit and/or phase flips.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the preparation gates to
            qubits (QuantumRegister): The register that will become the logical 
                error-protected qubit. The original qubit can be in any state, but it
                must be the first element. All of the other qubits must be |0>.
        """

        # Copy q0 into q3 and q6 - these 3 qubits will form 3 "blocks" of qubits
        for i in [3, 6]:
            circuit.cx(qubits[0], qubits[i])

        # Give q1 and q2 the same phase as q0, and repeat for the other two blocks
        for i in [0, 3, 6]:
            circuit.h(qubits[i])
            circuit.cx(qubits[i], qubits[i + 1])
            circuit.cx(qubits[i], qubits[i + 2])


    def decode_register(self, circuit, qubits):
        """
        Converts an error-protected logical qubit back into a single qubit by reversing
        the encoding operation.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the unpreparation gates to
            qubits (QuantumRegister): The logical error-encoded qubit
        """

        # Decouple the phases for each of the groups
        for i in [6, 3, 0]:
            circuit.cx(qubits[i], qubits[i + 2])
            circuit.cx(qubits[i], qubits[i + 1])
            circuit.h(qubits[i])

        # Decouple the groups
        for i in [6, 3]:
            circuit.cx(qubits[0], qubits[i])


    def detect_bit_flip_error(self, circuit, block, parity_qubits, parity_measurement):
        """
        Detects which qubit (if any) in the given block was flipped.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the detection gates to
            block (QuantumRegister): The block of 3 qubits to check for bit flips
            parity_qubits (QuantumRegister): The ancilla qubits to use when determining
                which qubit was flipped
            parity_measurement (ClassicalRegister): The classical register used to
                measure the parity qubits

        Remarks:
            This is essentially just the 3-qubit bit flip code. For an explanation of what
            this parity measurement is doing and how it works, check that code first.
        """

        # Check if q0 and q1 have the same value
        circuit.cx(block[0], parity_qubits[0])
        circuit.cx(block[1], parity_qubits[0])
        
        # Check if q0 and q2 have the same value
        circuit.cx(block[0], parity_qubits[1])
        circuit.cx(block[2], parity_qubits[1])

        # Measure the parity values
        circuit.measure(parity_qubits, parity_measurement)


    def detect_phase_flip_error(self, circuit, qubits, parity_qubits, parity_measurement):
        """
        Detects which block (if any) had its phase flipped.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the detection gates to
            qubits (QuantumRegister): The logical quantum register to check for errors
            parity_qubits (QuantumRegister): The ancilla qubits to use when determining
                which qubit had its phase flipped
            parity_measurement (ClassicalRegister): The classical register used to
                measure the parity qubits
        """
        
        # Bring the register from the Z basis to the X basis so we can measure the
        # phase differences between blocks
        for qubit in qubits:
            circuit.h(qubit)

        # Compare the phases of all 6 qubits from the 1st and 2nd blocks. If any of the
        # qubits in a block had its phase flipped, the entire block will show a phase
        # flip. Like the bit flip measurements, this parity qubit will show a 1 if 
        # the 1st and 2nd blocks have different phases.
        for i in range(0, 6):
            circuit.cx(qubits[i], parity_qubits[0])

        # Do the phase parity measurement for the 1st and 3rd blocks.
        for i in [0, 1, 2, 6, 7, 8]:
            circuit.cx(qubits[i], parity_qubits[1])

        # Put the qubits back into the Z basis
        for qubit in qubits:
            circuit.h(qubit)

        # Measure the parity values
        circuit.measure(parity_qubits, parity_measurement)


    def correct_errors(self, circuit, qubits, parity_qubits, parity_measurement):
        """
        Corrects any errors that have occurred within the logical qubit register.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the error correction to
            qubits (QuantumRegister): The logical qubit register to check and correct
            parity_qubits (QuantumRegister): The ancilla qubits to use when determining
                which qubit has an error
            parity_measurement (ClassicalRegister): The classical register used to
                measure the parity qubits
        """

        # Correct bit flips on the first block - look at the 3-qubit Bit Flip code for an
        # explanation of how the classical register's output maps to the qubit to flip.
        self.detect_bit_flip_error(circuit, [ qubits[0], qubits[1], qubits[2] ],
                                                    parity_qubits, parity_measurement)
        circuit.x(qubits[1]).c_if(parity_measurement, 0b01)
        circuit.x(qubits[2]).c_if(parity_measurement, 0b10)
        circuit.x(qubits[0]).c_if(parity_measurement, 0b11)
        circuit.reset(parity_qubits)    # My implementation reuses the parity qubits for each
                                        # measurement, to cut down on the overall circuit size
                                        # which speeds the simulation up considerably.

        # Correct bit flips on the second block
        self.detect_bit_flip_error(circuit, [ qubits[3], qubits[4], qubits[5] ],
                                                    parity_qubits, parity_measurement)
        circuit.x(qubits[4]).c_if(parity_measurement, 0b01)
        circuit.x(qubits[5]).c_if(parity_measurement, 0b10)
        circuit.x(qubits[3]).c_if(parity_measurement, 0b11)
        circuit.reset(parity_qubits)

        # Correct bit flips on the third block
        self.detect_bit_flip_error(circuit, [ qubits[6], qubits[7], qubits[8] ], 
                                                    parity_qubits, parity_measurement)
        circuit.x(qubits[7]).c_if(parity_measurement, 0b01)
        circuit.x(qubits[8]).c_if(parity_measurement, 0b10)
        circuit.x(qubits[6]).c_if(parity_measurement, 0b11)
        circuit.reset(parity_qubits)

        # Correct any phase flips. Flipping any qubit in the broken block will end up putting
        # the entire block back into the correct phase, so I just pick the first qubit of each one.
        self.detect_phase_flip_error(circuit, qubits,
                                                    parity_qubits, parity_measurement)
        circuit.z(qubits[3]).c_if(parity_measurement, 0b01)
        circuit.z(qubits[6]).c_if(parity_measurement, 0b10)
        circuit.z(qubits[0]).c_if(parity_measurement, 0b11)


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
