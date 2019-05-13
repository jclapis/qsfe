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


import random
import math
from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *


class SingleGateTestState:
    """
    This class represents a test case that uses a single gate to prepare the
    test qubit's state.
    """

    def __init__(self, gate):
        """
        Creates a SingleGateTestState instance.

        Parameters:
            gate (function): The function that implements the gate for this test case
        """

        self.name = gate.__name__
        self.gate = gate


    def prepare_state(self, qubit):
        """
        Prepares a qubit in the test state.

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare in the test state

        Returns:
            A Program that prepares the qubit in the test state.
        """

        program = Program(self.gate(qubit))
        return program



class RandomRotationTestState:
    """
    This class represents a test case that rotates the qubit around all three
    axes of the Bloch sphere by random angles between 0 and pi.
    """

    def __init__(self):
        """
        Creates a RandomRotationTestState instance.
        """
        
        self.x_angle = random.random() * math.pi
        self.y_angle = random.random() * math.pi
        self.z_angle = random.random() * math.pi
        self.name = f"[X = {self.x_angle}, Y = {self.y_angle}, Z = {self.z_angle}]"


    def prepare_state(self, qubit):
        """
        Prepares a qubit in the test state.
        
        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare in the test state

        Returns:
            A Program that prepares the qubit in the test state.
        """

        program = Program(
            RX(self.x_angle, qubit),
            RY(self.y_angle, qubit),
            RZ(self.z_angle, qubit)
        )
        return program



def generate_test_states(number_of_random_cases):
    """
    Creates a list of states to use while testing an error-correction code.
    This will include the I, H, X, Y, Z, and S gates as individual test states that will
    be applied to a qubit in the |0> state. It can also include random uneven rotations
    around the Bloch sphere, if desired.

    Parameters:
        number_of_random_cases (int): The number of random rotation test states
            to include in the list

    Returns:
        A list of test states
    """

    # Add the basic single-gate tests
    test_states = []
    test_states.append(SingleGateTestState(I))
    test_states.append(SingleGateTestState(H))
    test_states.append(SingleGateTestState(X))
    test_states.append(SingleGateTestState(Y))
    test_states.append(SingleGateTestState(Z))
    test_states.append(SingleGateTestState(S))

    # Add random rotation tests
    for i in range(0, number_of_random_cases):
        test_states.append(RandomRotationTestState())

    return test_states


def run_tests(description, number_of_qubits, number_of_parity_qubits, 
              number_of_random_tests, ecc_instance, enable_bit_flip,
              enable_phase_flip):
    """
    Runs the unit tests with the provided error-correction code.

    Parameters:
        description (str): A description of the current test run
        number_of_qubits (int): The number of qubits the ECC uses for
            its encoded register
        number_of_parity_qubits (int): The number of qubits the parity
            checking register in the ECC requires
        number_of_random_tests (int): The number of random rotation test
            cases to run
        ecc_instance (TestCase): An instance of a unit-test class that 
            implements the error-correction code to be tested
        enable_bit_flip (bool): True to run the tests where bit flip errors
            are involved, False to leave bit flips off
        enable_phase_flip (bool): True to run the tests where phase flip errors
            are involved, False to leave phase flips off
    """
    
    computer = get_qc(f"{number_of_qubits + number_of_parity_qubits}q-qvm", as_qvm=True)
    test_states = generate_test_states(number_of_random_tests)
    number_of_bit_flip_tests = number_of_qubits if enable_bit_flip else 0
    number_of_phase_flip_tests = number_of_qubits if enable_phase_flip else 0
    
    for test_state in test_states:
        print(f"Testing {description}, initial state = {test_state.name}.")

        for bit_flip_index in range(-1, number_of_bit_flip_tests):
            for phase_flip_index in range(-1, number_of_phase_flip_tests):

                # Construct the register and program for this test case
                register = QubitPlaceholder.register(number_of_qubits)
                program = Program()

                # Prepare the original qubit and encode it with the ECC
                program += test_state.prepare_state(register[0])
                program += ecc_instance.encode_register(register)

                # Simulate a bit and/or phase flip
                if bit_flip_index >= 0:
                    program += X(register[bit_flip_index])
                if phase_flip_index >= 0:
                    program += Z(register[phase_flip_index])

                # Run the ECC to correct for the errors
                ecc_instance.correct_errors(program, register)

                # Reverse the qubit and register preparation, which should put everything
                # back in the |0...0> state
                program += ecc_instance.encode_register(register).dagger()
                program += test_state.prepare_state(register[0]).dagger()

                # Measure the register
                measurement = program.declare("ro", "BIT", number_of_qubits)
                for i in range(0, number_of_qubits):
                    program += MEASURE(register[i], measurement[i])

                # Run the circuit
                assigned_program = address_qubits(program)
                executable = computer.compile(assigned_program)
                results = computer.run(executable)
                
                # Evaluate the final measurements
                for result in results:
                    for bit in result:
                        # Make sure the register is all zeros
                        if bit == 1:
                            raise ValueError(f"Test {test_state.name} failed with {bit_flip_index} flipped, " +
                                f"{phase_flip_index} phased. Measured {result} instead of all 0. ")

                    # Unfortunately, pyQuil's classical control scheme doesn't let us execute classical code
                    # (like print statements) during an if_then() call, it can only branch quantum code. We could
                    # technically do this with custom Quil code, but that goes a little beyond the scope of this
                    # evaluation.

        print("Passed!")
        print("")