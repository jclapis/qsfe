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
from projectq import MainEngine
from projectq.ops import *
from projectq.backends import CircuitDrawer
import math


class DebuggingFeatures(unittest.TestCase):
    """
    This class contains demonstrations of ProjectQ's debugging and diagnostic features.
    """


    def test_step_by_step_circuit_inspection(self):
        """
        This function demonstrates how to use ProjectQ to print the state vector of every
        step (moment) in a circuit. It also shows how to get the state vector at each
        step, and how to print it in ket notation.
        """

        engine = MainEngine()
        qubits = engine.allocate_qureg(3)

        # This shows how to print the state after a single step - it's done with the cheat()
        # function. Note that you HAVE to do engine.flush() in order to get the state.
        H | qubits[0]
        engine.flush()
        print(engine.backend.cheat())

        X | qubits[2]
        engine.flush()
        print(engine.backend.cheat())

        CNOT | (qubits[0], qubits[1])
        engine.flush()
        print(engine.backend.cheat())


    def test_print_circuit_diagram(self):
        """
        This function shows how to print LaTeX-based circuit diagrams.
        """
        drawer = CircuitDrawer()
        engine = MainEngine(drawer)
        
        qubits = engine.allocate_qureg(3)
        All(H) | qubits
        X | qubits[2]
        CNOT | (qubits[2], qubits[0])
        for qubit in qubits:
            Measure | qubit

        engine.flush()
        print(drawer.get_latex())


    def test_set_explicit_initial_state(self):
        """
        This shows how to set the initial state of the qubits in a circuit.
        """
        
        initial_statevector = [
            complex(0, 0), complex(0, 0), complex(1, 0), complex(0, 0), 
            complex(0, 0), complex(0, 0), complex(0, 0), complex(0, 0)
        ]

        engine = MainEngine()
        qubits = engine.allocate_qureg(3)

         # Set the initial state to 2, which is |010> (this can also be an entire state vector if you need to get fine-grained
         # or set up superpositions)
        engine.flush()
        engine.backend.set_wavefunction(initial_statevector, qubits)
        print(engine.backend.cheat())

