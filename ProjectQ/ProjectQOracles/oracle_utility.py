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

from projectq import MainEngine
from projectq.ops import *
from projectq.meta import Dagger, Control


def run_flip_marker_as_phase_marker(oracle, qubits, oracle_args):
    """
    Runs an oracle, flipping the phase of the input array if the result was |1>
    instead of flipping the target qubit.

    Parameters:
        oracle (function): The oracle to run
        qubits (QuantumRegister): The register to run the oracle on
        oracle_args (anything): An oracle-specific argument object to pass to
            the oracle during execution
    """

    # Allocate an ancilla qubit to act as the oracle's target
    phase_marker_target = qubits.engine.allocate_qubit()
    X | phase_marker_target
    H | phase_marker_target

    # Run the oracle with the phase-flip ancilla as the target - when the
    # oracle flips this target, it will actually flip the phase of the input
    # instead of entangling it with the target.
    if oracle_args is None:
        oracle(qubits, phase_marker_target)
    else:
        oracle(qubits, phase_marker_target, oracle_args)

    # Note: the qubit needs to be in the |0> or |1> state before letting it go
    Measure | phase_marker_target
    del phase_marker_target