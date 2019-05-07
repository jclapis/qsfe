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

import cirq


def run_flip_marker_as_phase_marker(circuit, oracle, qubits, oracle_args):
    """
    Runs an oracle, flipping the phase of the input array if the result was |1>
    instead of flipping the target qubit.

    Parameters:
        circuit (Circuit): The circuit being constructed
        oracle (function): The oracle to run
        qubits (list[Qid]): The register to run the oracle on
        oracle_args (anything): An oracle-specific argument object to pass to
            the oracle during execution
    """

    # Add the phase-flip ancilla qubit to the circuit if it doesn't already
    # exist, and set it up in the |-> state
    phase_flip_target = cirq.NamedQubit("phase_flip_target")
    if not phase_flip_target in circuit.all_qubits():
        circuit.append([
            cirq.X(phase_flip_target),
            cirq.H(phase_flip_target)
        ])

    # Run the oracle with the phase-flip ancilla as the target - when the
    # oracle flips this target, it will actually flip the phase of the input
    # instead of entangling it with the target.
    if oracle_args is None:
        oracle(circuit, qubits, phase_flip_target)
    else:
        oracle(circuit, qubits, phase_flip_target, oracle_args)