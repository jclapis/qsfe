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


# This file contains the implementation for Grover's algorithm.
# It's an intriguing approach at "reversing a function" - essentially
# if you have a function f(x) = y, Grover's algorithm figures out
# x given f and y. If you're interested in trying all possible inputs of a
# fixed search space (like, say, finding the password for for an encrypted
# file or something), Grover can do it in O(√N) steps instead of brute
# force searching the entire space (which is O(N)).


from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *
from utility import run_flip_marker_as_phase_marker
import oracles


def grover_iteration(program, ancilla_cache, oracle, qubits, oracle_args):
    """
    Runs a single iteration of the main loop in Grover's algorithm,
	which is the oracle followed by the diffusion operator.

    Parameters:
        program (Program): The program being constructed
        ancilla_cache (dict[string, QubitPlaceholder]): A collection of ancilla qubits
            that have been allocated in the program for use, paired with a name to help
            determine when they're free for use.
        oracle (function): The oracle that flags the correct answer to
            the problem being solved (essentially, this should just
            implement the function as a quantum program)
        qubits (list[QubitPlaceholder]): The register to run the oracle on
        oracle_args (anything): An oracle-specific argument object to pass to the
            oracle during execution
    """

    # Run the oracle on the input to see if it was a correct result
    run_flip_marker_as_phase_marker(program, ancilla_cache, oracle, qubits, oracle_args)

    # Run the diffusion operator
    for qubit in qubits:
        program += H(qubit)
    run_flip_marker_as_phase_marker(program, ancilla_cache, oracles.check_if_all_zeros, 
                                    qubits, None)
    for qubit in qubits:
        program += H(qubit)


def grover_search(program, ancilla_cache, oracle, qubits, oracle_args):
    """
    Runs Grover's algorithm on the provided oracle, turning the input into
	a superposition where the correct answer's state has a very large amplitude
	relative to all of the other states.

    Parameters:
        program (Program): The program being constructed
        ancilla_cache (dict[string, QubitPlaceholder]): A collection of ancilla qubits
            that have been allocated in the program for use, paired with a name to help
            determine when they're free for use.
        oracle (function): The oracle that flags the correct answer to
            the problem being solved (essentially, this should just
            implement the function as a quantum program)
        qubits (list[QubitPlaceholder]): The register to run the oracle on
        oracle_args (anything): An oracle-specific argument object to pass to the
            oracle during execution
    """

    # Run the algorithm for √N iterations.
    for qubit in qubits:
        program += H(qubit)
    iterations = round(2 ** (len(qubits) / 2))
    for i in range(0, iterations):
        grover_iteration(program, ancilla_cache, oracle, qubits, oracle_args)


def run_grover_search(number_of_qubits, oracle, oracle_args):
    """
    Uses Grover's quantum search to find the single answer to a problem
    with high probability.

    Parameters:
        number_of_qubits (int): The number of qubits that the oracle expects
            (the number of qubits that the answer will contain)
        oracle (function): The oracle that flags the correct answer to
            the problem being solved (essentially, this should just
            implement the function as a quantum program)
        oracle_args (anything): An oracle-specific argument object to pass to the
            oracle during execution

    Returns:
        A list[int] that represents the discovered answer as a bit string
    """

    # Build the program and run the search
    qubits = QubitPlaceholder.register(number_of_qubits)
    program = Program()
    grover_search(program, {}, oracle, qubits, oracle_args)
    measurement = program.declare("ro", "BIT", number_of_qubits)
    for i in range(0, len(qubits)):
        program += MEASURE(qubits[i], measurement[i])

    # Run the program.
    assigned_program = address_qubits(program)
    computer = get_qc(f"{number_of_qubits + 1}q-qvm", as_qvm=True)
    computer.compiler.client.rpc_timeout = None
    executable = computer.compile(assigned_program)
    results = computer.run(executable)

    # Measure the potential solution and return it
    for result in results:
        solution = []
        for bit in result:
            solution += [bit]
        return solution
