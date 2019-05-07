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


# This file contains my implementation of the Quantum Fourier Transform
# (QFT) algorithm. I'm basing it off of the circuit diagram defined in the Wikipedia
# article:
# https://en.wikipedia.org/wiki/Quantum_Fourier_transform
# Essentially, this is the quantum version of the discrete Fourier transform (or,
# more accurately, this is the INVERSE DFT).


import cirq
import math


def swap_register(circuit, qubits):
    """
    Swaps all of the qubits in a register, effectively reversing it.

    Parameters:
        circuit (Circuit): The circuit being constructed
        qubits (list[Qid]): The register to reverse
    """

    for i in range(0, len(qubits) // 2):
        circuit.append(cirq.SWAP(qubits[i], qubits[len(qubits) - 1 - i]))


def qft(circuit, qubits):
    """
    Performs an in-place quantum fourier transform on the given register.

    Parameters:
        circuit (Circuit): The circuit being constructed
        qubits (list[Qid]): The register to apply the QFT to

    Remarks:
        Note that by the established conventions, the QFT corresponds to the
        inverse classical DFT, and the adjoint QFT corresponds to the normal DFT.
    """
    
    register_length = len(qubits)

    for i in range(0, register_length):
        # Each qubit starts with a Hadamard
        circuit.append(cirq.H(qubits[i]))

        # Go through the rest of the qubits that follow this one,
        # we're going to use them as control qubits on phase-shift
		# gates. The phase-shift gate is basically a gate that rotates
		# the |1> portion of a qubit's state around the Z axis of the
		# Bloch sphere by Φ, where Φ is the angle from the +X axis on
		# the X-Y plane.
		# 
		# Cirq doesn't provide this gate, but it provides
        # an Rz gate (arbitrary rotation around the Z axis), which is
        # effectively the same thing with a global phase applied. Since
        # global phase doesn't matter, we can use Rz in place of it.
        # 
        # For more info on the phase-shift gate, look at the "phase shift"
        # section of this Wiki article:
        # https://en.wikipedia.org/wiki/Quantum_logic_gate
        for j in range(i + 1, register_length):
            # According to the circuit diagram, the controlled RΦ gates
			# change the "m" value as described above. The first one
			# is always 2, and then it iterates from there until the
			# last one.
            m = j - i + 1
            y = 2 * math.pi / 2 ** m

            # Perform the rotation, controlled by the jth qubit on the
			# ith qubit, with e^(2πi/2^m)
            circuit.append(cirq.Rz(y).on(qubits[i]).controlled_by(qubits[j]))


    # The bit order is going to be backwards after the QFT so this just
	# reverses it.
    swap_register(circuit, qubits)


def iqft(circuit, qubits):
    """
    Performs the inverse in-place quantum fourier transform on the given register.

    Parameters:
        circuit (Circuit): The circuit being constructed
        qubits (list[Qid]): The register to apply the QFT to
    """

    # This is just the adjoint of QFT, so the instructions are in reverse order
    # and the angle used in the Rz gates is negated.
    
    register_length = len(qubits)

    swap_register(circuit, qubits)
    
    for i in range(register_length - 1, -1, -1):
        for j in range(register_length - 1, i, -1):
            m = j - i + 1
            y = 2 * math.pi / 2 ** m
            circuit.append(cirq.Rz(-y).on(qubits[i]).controlled_by(qubits[j]))
        circuit.append(cirq.H(qubits[i]))
