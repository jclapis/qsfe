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


# This file contains helper functions that make it easier to work
# with quantum oracles.

from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister


def run_flip_marker_as_phase_marker(circuit, oracle, qubits, oracle_args):
    """
    Runs an oracle, flipping the phase of the input array if the result was |1>
    instead of flipping the target qubit.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        oracle (function): The oracle to run
        qubits (QuantumRegister): The register to run the oracle on
        oracle_args (anything): An oracle-specific argument object to pass to
            the oracle during execution
    """

    # Add the phase-flip ancilla qubit to the circuit if it doesn't already
    # exist, and set it up in the |-> state
    phase_flip_target = QuantumRegister(1, "phase_flip_target")
    if not phase_flip_target in circuit.qregs:
        circuit.add_register(phase_flip_target)
        circuit.x(phase_flip_target)
        circuit.h(phase_flip_target)

    # Run the oracle with the phase-flip ancilla as the target - when the
    # oracle flips this target, it will actually flip the phase of the input
    # instead of entangling it with the target.
    if oracle_args is None:
        oracle(circuit, qubits, phase_flip_target)
    else:
        oracle(circuit, qubits, phase_flip_target, oracle_args)


def multicontrolled_x(circuit, controls, targets):
    """
    Performs the X gate on target qubits, with an arbitrary number of control qubits.
    This is an extension of the Toffoli gate.

    Parameters:
        circuit (QuantumCircuit): The circuit being constructed
        controls (QuantumRegister): The qubits to use as the controls for the X gate
        targets (QuantumRegister): The qubits to flip with the X gate
    """
    
    # Basically, the way this works is it performs the Toffoli gate with the first
    # two qubits in the control register with the first qubit of an ancilla register
    # as the target, then it runs the Toffoli gate with the 3rd control qubit and
    # the 1st ancilla on the 2nd ancilla, and so on. At the end, it runs Toffoli
    # with the last control qubit and the last ancilla on the target qubits.

    # Add a register for control ancilla qubits - note that this is only useful
    # if, for any given circuit, the control register always has the same number
    # of qubits.
    control_ancilla = QuantumRegister(len(controls) - 2, "control_ancilla")
    if not control_ancilla in circuit.qregs:
        circuit.add_register(control_ancilla)

    # Set up the first ancilla qubit
    circuit.ccx(controls[0], controls[1], control_ancilla[0])

    # Set up the rest of the ancilla qubits
    for i in range(0, len(control_ancilla) - 1):
        circuit.ccx(controls[i + 2], control_ancilla[i], control_ancilla[i + 1])

    # Perform the final Toffoli gate on all of the target qubits
    for target in targets:
        circuit.ccx(controls[len(controls) - 1], control_ancilla[len(controls) - 3], target)

    # Disentangle from the ancilla, resetting them
    for i in range(len(control_ancilla) - 2, -1, -1):
        circuit.ccx(controls[i + 2], control_ancilla[i], control_ancilla[i + 1])
    circuit.ccx(controls[0], controls[1], control_ancilla[0])