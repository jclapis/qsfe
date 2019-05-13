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


# This file demonstrates an issue with the address_qubits() function where
# it will drop CONTROLLED gate modifiers, as reported in
# https://github.com/rigetti/pyquil/issues/905.

from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *


# Create the registers and program
controls = QubitPlaceholder.register(3)
target = QubitPlaceholder.register(1)
program = Program()

# Hadamard the first three qubits - these will be the controls
for control in controls:
    program += H(control);

# Add a triple-controlled X gate
gate = Z(target[0])
for control in controls:
    gate = gate.controlled(control)
program += gate

# Measure the qubits
qubits = controls + target
number_of_qubits = len(qubits)
measurement = program.declare("ro", "BIT", number_of_qubits)
for i in range(0, number_of_qubits):
    program += MEASURE(qubits[i], measurement[i])

# Run the program
assigned_program = address_qubits(program)          # The X gate is no longer controlled here
computer = get_qc(f"{number_of_qubits}q-qvm", as_qvm=True)
executable = computer.compile(assigned_program)     # Compiling here will fail
results = computer.run(executable)