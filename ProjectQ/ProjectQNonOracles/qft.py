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
# (QFT) algorithm. I'm basing it off of the program diagram defined in the Wikipedia
# article:
# https://en.wikipedia.org/wiki/Quantum_Fourier_transform
# Essentially, this is the quantum version of the discrete Fourier transform (or,
# more accurately, this is the INVERSE DFT).
# 
# Note: ProjectQ actually has its own QFT gate, but I also provide my own implementation
# here for completeness.


from projectq import MainEngine
from projectq.ops import *
from projectq.meta import Dagger, Control
from utility import reset
import math


def swap_register(qubits):
    """
    Swaps all of the qubits in a register, effectively reversing it.

    Parameters:
        qubits (Qureg): The register to reverse
    """

    for i in range(0, len(qubits) // 2):
        Swap | (qubits[i], qubits[len(qubits) - 1 - i])


def qft(qubits):
    """
    Performs an in-place quantum fourier transform on the given register.

    Parameters:
        qubits (Qureg): The register to apply the QFT to

    Remarks:
        Note that by the established conventions, the QFT corresponds to the
        inverse classical DFT, and the adjoint QFT corresponds to the normal DFT.
    """
    
    register_length = len(qubits)

    for i in range(0, register_length):
        # Each qubit starts with a Hadamard
        H | qubits[i]

        # Go through the rest of the qubits that follow this one,
        # we're going to use them as control qubits on phase-shift
		# gates. The phase-shift gate is basically a gate that rotates
		# the |1> portion of a qubit's state around the Z axis of the
		# Bloch sphere by Φ, where Φ is the angle from the +X axis on
		# the X-Y plane.
		# 
		# pyQuil provides this with the PHASE and CPHASE gates. Note that
        # this is the same as the RZ gate (just with a global phase applied
        # which doesn't matter).
        # 
        # For more info on the phase-shift gate, look at the "phase shift"
        # section of this Wiki article:
        # https://en.wikipedia.org/wiki/Quantum_logic_gate
        for j in range(i + 1, register_length):
            # According to the program diagram, the controlled RΦ gates
			# change the "m" value as described above. The first one
			# is always 2, and then it iterates from there until the
			# last one.
            m = j - i + 1
            y = 2 * math.pi / 2 ** m

            # Perform the rotation, controlled by the jth qubit on the
			# ith qubit, with e^(2πi/2^m)

            CRz(y) | (qubits[j], qubits[i])


    # The bit order is going to be backwards after the QFT so this just
	# reverses it.
    swap_register(qubits)
