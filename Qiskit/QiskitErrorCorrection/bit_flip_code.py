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


    def encode_register(self, circuit, qubits):
        """
        Creates an error-protected logical qubit, transforming A|000> + B|100> into
        A|000> + B|111> which will be used for the 3-qubit error correction code.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the preparation gates to
            qubits (QuantumRegister): The register that will become the logical 
                error-protected qubit. The original qubit can be in any state, but it
                must be the first element. All of the other qubits must be |0>.
        """

        circuit.cx(qubits[0], qubits[1])
        circuit.cx(qubits[0], qubits[2])


    def decode_register(self, circuit, qubits):
        """
        Converts an error-protected logical qubit back into a single qubit by turning 
        the A|000> + B|111> state back into the A|000> + B|100> state.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the unpreparation gates to
            qubits (QuantumRegister): The logical error-encoded qubit
        """
        
        circuit.cx(qubits[0], qubits[2])
        circuit.cx(qubits[0], qubits[1])


    def detect_error(self, circuit, qubits, parity_qubits, parity_measurement):
        """
        Detects a bit-flip error on one of the three qubits in a logical qubit register.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the error detection to
            qubits (QuantumRegister): The logical qubit register to check for errors
            parity_qubits (QuantumRegister): The ancilla qubits to use when determining
                which bit was flipped
            parity_measurement (ClassicalRegister): The classical register used to
                measure the parity qubits
        """

        # The plan here is to check if q0 and q1 have the same parity (00 or 11), and if q0 and q2
        # have the same parity. If both checks come out true, then there isn't an error. Otherwise,
        # if one of the checks reveals a parity discrepancy, we can use the other check to tell us
        # which qubit is broken.

        # Check if q0 and q1 have the same value
        circuit.cx(qubits[0], parity_qubits[0])
        circuit.cx(qubits[1], parity_qubits[0])
        
        # Check if q0 and q2 have the same value
        circuit.cx(qubits[0], parity_qubits[1])
        circuit.cx(qubits[2], parity_qubits[1])

        # Measure the parity values and return the measurement register
        circuit.measure(parity_qubits, parity_measurement)


    def correct_errors(self, circuit, qubits, parity_qubits, parity_measurement):
        """
        Corrects any errors that have occurred within the logical qubit register.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the error correction to
            qubits (QuantumRegister): The logical qubit register to check and correct
            parity_qubits (QuantumRegister): The ancilla qubits to use when determining
                which bit has an error
            parity_measurement (ClassicalRegister): The classical register used to
                measure the parity qubits
        """

        # Determine which qubit (if any) is broken.
        self.detect_error(circuit, qubits, parity_qubits, parity_measurement)

        # In Qiskit, we can't modify a quantum circuit in the middle of
        # an operation based on a classical register with a normal if statement;
        # we have to append c_if to gates to do it. That has the unfortunate
        # side-effect of meaning we can't do if-blocks, and we can't directly
        # control a gate on more than one variable, so we have to think about things
        # a little differently.
        # 
        # The returned circuit will have the first bit == 1 if 0 and 1 are different,
        # and the second bit == 1 if 0 and 2 are different. To get c_if to work, we have
        # to treat these two as two bits of an integer. Note that the bit order of the
        # measurement will be reversed because Qiskit will read the register as little-endian.
        # 
        # 00 = none are different
        # 01 (measured as 10) = 0 and 2 are different but 0 and 1 are the same, so 2 is broken
        # 10 (measured as 01) = 0 and 1 are different but 0 and 2 are the same, so 1 is broken
        # 11 = 0 and 1 are different, and 0 and 2 are different, so 0 is broken
        #
        # These lines will fix the broken qubit based on this measurement.
        circuit.x(qubits[1]).c_if(parity_measurement, 0b01)
        circuit.x(qubits[2]).c_if(parity_measurement, 0b10)
        circuit.x(qubits[0]).c_if(parity_measurement, 0b11)

    
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