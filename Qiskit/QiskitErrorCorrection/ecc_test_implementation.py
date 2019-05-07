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
import random
import math
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import execute
from qiskit import Aer


class SingleGateTestState:
    """
    This class represents a test case that uses a single gate to prepare the
    test qubit's state.
    """

    def __init__(self, name, gate_name, adjoint_gate_name):
        """
        Creates a SingleGateTestState instance.

        Parameters:
            name (str): The name of this test case
            gate_name (str): The name of the function in the QuantumCircuit class
                that implements the gate for this test case
            adjoint_gate_name (str): The name of the function in the QuantumCircuit
                class that implements the reverse (adjoint) of the gate for this
                test case
        """

        self.name = name
        self.gate_name = gate_name
        self.adjoint_gate_name = adjoint_gate_name


    def prepare_state(self, circuit, qubit):
        """
        Prepares a qubit in the test state.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the preparation gate to
            qubit (QuantumRegister): The qubit to prepare in the test state
        """

        gate = getattr(circuit, self.gate_name)
        gate(qubit)


    def unprepare_state(self, circuit, qubit):
        """
        Unprepares a qubit from the test state, returning it to the |0> state if
        it was in the test state. This will run the adjoint of the preparation
        function.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the unpreparation gate to
            qubit (QuantumRegister): The qubit that's currently in the test state
        """

        gate = getattr(circuit, self.adjoint_gate_name)
        gate(qubit)



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


    def prepare_state(self, circuit, qubit):
        """
        Prepares a qubit in the test state.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the preparation gates to
            qubit (QuantumRegister): The qubit to prepare in the test state
        """

        circuit.rx(self.x_angle, qubit)
        circuit.ry(self.y_angle, qubit)
        circuit.rz(self.z_angle, qubit)


    def unprepare_state(self, circuit, qubit):
        """
        Unprepares a qubit from the test state, returning it to the |0> state if
        it was in the test state. This will run the adjoint of the preparation
        function.

        Parameters:
            circuit (QuantumCircuit): The circuit to add the unpreparation gates to
            qubit (QuantumRegister): The qubit that's currently in the test state
        """

        circuit.rz(-self.z_angle, qubit)
        circuit.ry(-self.y_angle, qubit)
        circuit.rx(-self.x_angle, qubit)



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
    test_states.append(SingleGateTestState("I", "iden", "iden"))
    test_states.append(SingleGateTestState("H", "h", "h"))
    test_states.append(SingleGateTestState("X", "x", "x"))
    test_states.append(SingleGateTestState("Y", "y", "y"))
    test_states.append(SingleGateTestState("Z", "z", "z"))
    test_states.append(SingleGateTestState("S", "s", "sdg"))

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
    
    simulator = Aer.get_backend('qasm_simulator')
    test_states = generate_test_states(number_of_random_tests)
    number_of_bit_flip_tests = number_of_qubits if enable_bit_flip else 0
    number_of_phase_flip_tests = number_of_qubits if enable_phase_flip else 0
    
    for test_state in test_states:
        print(f"Testing {description}, initial state = {test_state.name}.")

        for bit_flip_index in range(-1, number_of_bit_flip_tests):
            for phase_flip_index in range(-1, number_of_phase_flip_tests):

                # Construct the registers and circuit for this test case
                register = QuantumRegister(number_of_qubits)
                parity_qubits = QuantumRegister(number_of_parity_qubits)
                parity_measurement = ClassicalRegister(number_of_parity_qubits)
                circuit = QuantumCircuit(register, parity_qubits, parity_measurement)

                # Prepare the original qubit and encode it with the ECC
                test_state.prepare_state(circuit, register[0])
                ecc_instance.encode_register(circuit, register)

                # Simulate a bit and/or phase flip
                if bit_flip_index >= 0:
                    circuit.x(register[bit_flip_index])
                if phase_flip_index >= 0:
                    circuit.z(register[phase_flip_index])

                # Run the ECC to correct for the errors
                ecc_instance.correct_errors(circuit, register, parity_qubits, parity_measurement)

                # Reverse the qubit and register preparation, which should put everything
                # back in the |0...0> state
                ecc_instance.decode_register(circuit, register)
                test_state.unprepare_state(circuit, register[0])

                # Measure the register
                register_measurement = ClassicalRegister(number_of_qubits, "register_measurement")
                circuit.add_register(register_measurement)
                circuit.measure(register, register_measurement)

                # Run the circuit
                simulation = execute(circuit, simulator, shots=1)
                result = simulation.result()
                counts = result.get_counts(circuit)
                
                # Evaluate the final measurements
                for (state, count) in counts.items():

                    # Make sure the register is all zeros
                    register_measurement = int(state[0:number_of_qubits], 2) # Convert the first register to an int
                    if register_measurement != 0:
                        raise ValueError(f"Test {test_state.name} failed with {bit_flip_index} flipped, " +
                                f"{phase_flip_index} phased. Measured {bin(register_measurement)} instead of 0. ")

                    # Unfortunately, I couldn't find an easy way to have Qiskit produce an indication of which qubit
                    # (if any) was broken in the test because of the way it handles intermediate measurements with c_if.
                    # Since there isn't any way to execute classical code (like a print statement) based on a classical
                    # register's value in the middle of a simulation, and because the parity qubits get overwritten between
                    # bit flip and phase flip detections, we don't get access to this information.

        print("Passed!")
        print("")