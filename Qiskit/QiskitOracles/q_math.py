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


# This file contains some useful math and logic functions used by some of
# the oracles defined in this assembly.

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister


def inplace_xor(circuit, classic_bits, qubits):
    """
    Performs an XOR on a classical bit string and a qubit array. This
    is an in-place implementation, meaning the qubit array will contain
    the results of the XOR when this function returns.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        classic_bits (list[bool]): The classical bit array to use in the XOR
        qubits (QuantumRegister): The qubit array to use in the XOR
    """

	# My XOR implementation here takes advantage of the fact that
	# we know what the classic bits are. Here's the table, where
	# the first bit is the classic bit and the second is the qubit.
	# The left-hand side is before the XOR, the right-hand is after.
	# |00>  =>  |00>
	# |01>  =>  |01>
	# |10>  =>  |11>
	# |11>  =>  |10>
	# So if the classical bit is a zero, we don't actually have to
	# do anything to the qubit. If the classical bit is one, we just
	# end up flipping the qubit. This is basically just a CNOT with
	# the classical bit as the control!
    for i in range(0, len(classic_bits)):
        if classic_bits[i] == 1:
            circuit.x(qubits[i])


def left_shift(circuit, input, output, amount):
    """
    Left-shifts the input qubit array by the specified number of bits.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        input (QuantumRegister): The register that contains the qubits to shift.
            This can be in any arbitrary state.
        output (QuantumRegister): The register that will hold the shifted qubits.
            This must be in the state |0...0>.
        amount (int): The number of bits to shift the register by.
    """

    if len(input) != len(output):
        raise ValueError("Input and output registers must have the same length.")

    for input_index in range(amount, len(input)):
        output_index = input_index - amount
        circuit.cx(input[input_index], output[output_index])


def right_shift(circuit, input, output, amount):
    """
    Right-shifts the input qubit array by the specified number of bits.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        input (QuantumRegister): The register that contains the qubits to shift.
            This can be in any arbitrary state.
        output (QuantumRegister): The register that will hold the shifted qubits.
            This must be in the state |0...0>.
        amount (int): The number of bits to shift the register by.
    """
    
    if len(input) != len(output):
        raise ValueError("Input and output registers must have the same length.")

    for input_index in range(0, len(input) - amount):
        output_index = input_index + amount
        circuit.cx(input[input_index], output[output_index])