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


import unittest
from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *
from pyquil.api import WavefunctionSimulator
import math


class DebuggingFeatures(unittest.TestCase):
    """
    This class contains demonstrations of Forest's debugging and diagnostic features.
    """


    def test_statevector(self):
        """
        This function demonstrates how to get the statevector of a register in Forest.
        """
        
        qubits = QubitPlaceholder.register(3)
        program = Program()
        program += H(qubits[0])
        program += X(qubits[2])
        program += CNOT(qubits[0], qubits[1])

        measurement = program.declare("ro", "BIT", 3)
        for i in range(0, 3):
            program += MEASURE(qubits[i], measurement[i])

        assigned_program = address_qubits(program)        
        simulator = WavefunctionSimulator()
        statevector = simulator.wavefunction(assigned_program)
        print(statevector.amplitudes)
