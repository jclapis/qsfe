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
from projectq import MainEngine
from projectq.ops import *
from projectq.meta import Dagger, Control
from utility import reset


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

        self.name = str(gate)
        self.gate = gate


    def prepare_state(self, qubit):
        """
        Prepares a qubit in the test state.

        Parameters:
            qubit (Qureg): The qubit to prepare in the test state
        """

        self.gate | qubit



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
            qubit (Qureg): The qubit to prepare in the test state
        """

        Rx(self.x_angle) | qubit
        Ry(self.y_angle) | qubit
        Rz(self.z_angle) | qubit


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
    # test_states.append(SingleGateTestState(I))    # ProjectQ doesn't have an I gate
    test_states.append(SingleGateTestState(H))
    test_states.append(SingleGateTestState(X))
    test_states.append(SingleGateTestState(Y))
    test_states.append(SingleGateTestState(Z))
    test_states.append(SingleGateTestState(S))

    # Add random rotation tests
    for i in range(0, number_of_random_cases):
        test_states.append(RandomRotationTestState())

    return test_states


def run_tests(description, number_of_qubits, number_of_random_tests,
              ecc_instance, enable_bit_flip, enable_phase_flip):
    """
    Runs the unit tests with the provided error-correction code.

    Parameters:
        description (str): A description of the current test run
        number_of_qubits (int): The number of qubits the ECC uses for
            its encoded register
        number_of_random_tests (int): The number of random rotation test
            cases to run
        ecc_instance (TestCase): An instance of a unit-test class that 
            implements the error-correction code to be tested
        enable_bit_flip (bool): True to run the tests where bit flip errors
            are involved, False to leave bit flips off
        enable_phase_flip (bool): True to run the tests where phase flip errors
            are involved, False to leave phase flips off
    """
    
    engine = MainEngine()
    register = engine.allocate_qureg(number_of_qubits)
    test_states = generate_test_states(number_of_random_tests)
    number_of_bit_flip_tests = number_of_qubits if enable_bit_flip else 0
    number_of_phase_flip_tests = number_of_qubits if enable_phase_flip else 0
    
    for test_state in test_states:
        print(f"Testing {description}, initial state = {test_state.name}.")

        for bit_flip_index in range(-1, number_of_bit_flip_tests):
            for phase_flip_index in range(-1, number_of_phase_flip_tests):

                # Prepare the original qubit and encode it with the ECC
                test_state.prepare_state(register[0])
                ecc_instance.encode_register(register)

                # Simulate a bit and/or phase flip
                if bit_flip_index >= 0:
                    X | register[bit_flip_index]
                if phase_flip_index >= 0:
                    Z | register[phase_flip_index]

                # Run the ECC to correct for the errors
                ecc_instance.correct_errors(register)

                # Reverse the qubit and register preparation, which should put everything
                # back in the |0...0> state
                with Dagger(engine):
                    test_state.prepare_state(register[0])
                    ecc_instance.encode_register(register)
                
                # Measure the register
                for i in range(0, number_of_qubits - 1):
                    qubit = register[i]
                    Measure | qubit
                    if int(qubit) == 1:
                        raise ValueError(f"Test {test_state.name} failed with {bit_flip_index} flipped, " +
                            f"{phase_flip_index} phased. Qubit {i} was 1. ")

        print("Passed!")
        print("")