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


# This file contains implementations for some common and useful
# quantum oracles. The way I'm going to define an oracle here is this:
# it's a function that takes in an arbitrary input qubit register and
# a single "result" qubit, runs some kind of code to check for a
# certain value or condition or something, and flips the result qubit
# if the input meets that condition / passes that check. Oracles are
# basically quantum "if-statements" that conform to a standard
# function signature.
# 
# The signature I'm describing here is called a "bit-flip" oracle,
# because it flips the result qubit if the input meets the specific
# condition the oracle checks for. This is usually the easiest way
# to write them from a conceptual understanding and maintainability
# perspective, and I have some utility functions in the utility
# module that convert them to other kinds of oracles automatically
# (like "phase-flip" ones, which are usually a lot more useful from
# an algorithm perspective).
# 
# Note that some oracles also take a context-specific argument that
# can provide some extra information the oracle needs in order to run.

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
import utility
import q_math


def always_zero(circuit, qubits, target):
    """
    This oracle always "returns" zero, so it never flips the target qubit.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        qubits (QuantumRegister): The register to run the oracle on
        target (QuantumRegister): The target qubit to flip if the input
            satisfies the oracle
    """

    # This literally does nothing, no matter what the input is.


def always_one(circuit, qubits, target):
    """
    This oracle always "returns" one, so it always flips the target qubit.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        qubits (QuantumRegister): The register to run the oracle on
        target (QuantumRegister): The target qubit to flip if the input
            satisfies the oracle
    """

    circuit.x(target)


def check_if_all_ones(circuit, qubits, target):
    """
    This is a quantum oracle that will flip the target qubit if
    and only if the entire input register was all ones - that is,
    it was in the state |1...1>.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        qubits (QuantumRegister): The register to run the oracle on
        target (QuantumRegister): The target qubit to flip if the input
            satisfies the oracle
    """

    # Run a supercontrolled X gate with all of the input qubits as controls
    utility.multicontrolled_x(circuit, qubits, target)


def check_if_all_zeros(circuit, qubits, target):
    """
    This is a quantum oracle that will flip the target qubit if
    and only if the entire input register was all zeros - that is,
    it was in the state |0...0>.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        qubits (QuantumRegister): The register to run the oracle on
        target (QuantumRegister): The target qubit to flip if the input
            satisfies the oracle
    """

    # Same as above, but flip the input first - if it's all 0's, then
    # after the flip it will be all 1's and the control will work.
    circuit.x(qubits)
    utility.multicontrolled_x(circuit, qubits, target)
    circuit.x(qubits)
    

def check_if_register_matches_bit_string(circuit, qubits, target, bit_string):
    """
    This is a quantum oracle that will flip the target qubit if
    the input register is in the same state as the provided bit string - that is,
    if the bit string is 01011, it will flip the target if the input register
    is |01011>.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        qubits (QuantumRegister): The register to run the oracle on
        target (QuantumRegister): The target qubit to flip if the input
            satisfies the oracle
        bit_string (list[bool]): The bit string to compare the input register
            to, where False represents |0> and True represents |1>
    """

    # Like the above two oracles, this will end up running a multicontrolled X gate.
    # This one just selectively flips all of the qubits where the input string is 0.
    for i in range(0, len(bit_string)):
        if bit_string[i] == 0:
            circuit.x(qubits[i])

    check_if_all_ones(circuit, qubits, target)

    for i in range(0, len(bit_string)):
        if bit_string[i] == 0:
            circuit.x(qubits[i])


def check_for_odd_number_of_ones(circuit, qubits, target):
    """
    This oracle checks to see if there are an odd number of |1> qubits in the
    input. It will flip the target qubit if there are, or leave it alone if
    there are an even number of |1> qubits.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        qubits (QuantumRegister): The register to run the oracle on
        target (QuantumRegister): The target qubit to flip if the input
            satisfies the oracle
    """

    # If there are an odd number of |1> qubits, we want the target to get
    # flipped. If there are an even number, we want to leave it alone.
    # Consider a simple two-qubit register. Here is the desired result
    # in table form (where the first two terms are the input register and
    # the third term is the target qubit):
    # 000  =>  000
    # 010  =>  011
    # 100  =>  101
    # 110  =>  110
    # This is kind of like XORing across all of the qubits. However, since
    # we know the target qubit is going to start in |0> (or at least, all we
    # care about is flipping it from whatever arbitrary state it could be
    # in), the XOR op basically ends up doing the same thing as CNOT. So to
    # do a bunch of XORs on all of the input qubits, we just have to CNOT
    # the target over and over, using each input qubit as the control.
    for qubit in qubits:
        circuit.cx(qubit, target)


def check_if_qubit_is_one(circuit, qubits, target, index):
    """
    This oracle checks to see if the qubit in the Nth position is |0> or
    |1>. "Nth" here means the qubit in the input array at the given index.
    If it's |1>, it flips the target qubit.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        qubits (QuantumRegister): The register to run the oracle on
        target (QuantumRegister): The target qubit to flip if the input
            satisfies the oracle
        index (int): The 0-based index of the qubit to check
    """

    # Quick sanity check
    if index < 0 or index > len(qubits) - 1:
        raise "Can't check if the qubit is |0> or |1> because the index was out of bounds."

    # This really is as easy as you think: CNOT the target with the Nth qubit.
    circuit.cx(qubits[index], target)


def check_xor_pad(circuit, pad_key, target, extra_args):
    """
    This is a bit-flipping oracle that checks to see if the provided
    pad key, XOR'd with the encoded message, provides the desired result.
    Basically this checks to see if the provided pad was used to encrypt
    the original message.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        pad_key (QuantumRegister): The qubit array containing the candidate
            pad key that you want to check for correctness.
        target (QuantumRegister): The target qubit in the oracle. If the pad
            is correct, this is the bit that will get flipped.
        extra_args (list[bool], list[bool]): A tuple that contains the following
            values:
            encoded_message: The "ciphertext", or in this case, the encrypted
                version of the original message that was XOR'd with the actual pad
            desired_result: The "plaintext", or in this case, the original message
                before it got encrypted. This is used to validate that the pad gives
                the correct answer.
    """

    # Unpack the extra args
    (encoded_message, desired_result) = extra_args

    # Set encoded_message = pad_key XOR encoded_message, then check to see if it's in
    # the desired state
    q_math.inplace_xor(circuit, encoded_message, pad_key)
    check_if_register_matches_bit_string(circuit, pad_key, target, desired_result)
    q_math.inplace_xor(circuit, encoded_message, pad_key)
