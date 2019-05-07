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


import vs_test_path_fixup
import unittest
import cirq
from utility import run_flip_marker_as_phase_marker
import oracles


class DeutschJozsa(unittest.TestCase):
    """
    This class contains the implementation and tests for the Deutsch-Jozsa algorithm.
    It checks a given function f(x) that takes in a register and outputs a single bit,
    to see whether or not it's "constant" or "balanced". Constant means it always
    returns 0 (or always 1) for all possible inputs. Balanced means it returns 0 for
    half of the possible inputs and 1 for the other half.
    Normally this would take N/2 + 1 checks (N = the number of possible inputs) in order
    to prove with 100% certainty that the algorithm was one or the other, but the DJ
    algorithm takes advantage of the way the Hadamard gate works to cause quantum
    interference, which can produce the answer in only 1 check.

    This is a "toy" algorithm in the sense that it was invented by mathematicians as
    the first simple example of a problem that offers a speedup with quantum computers
    compared to classical computers, but it's a super contrived problem with no real
    practical applications.
    """
    
    
    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def check_if_constant_or_balanced(self, circuit, oracle, qubits, oracle_args):
        """
        Runs the Deutsch-Jozsa algorithm on the provided oracle, determining
        whether it's constant or balanced.

        Parameters:
            circuit (Circuit): The circuit being constructed
            oracle (function): The oracle to check
            qubits (list[Qid]): The register to run the oracle on
            oracle_args (anything): An oracle-specific argument object to pass to
                the oracle during execution
        """

        # Initialize the register to |+...+>
        circuit.append(cirq.H.on_each(*qubits))

        # Run the oracle in phase-flip mode. Any of the superposition states that
        # triggered the oracle will have their phase flipped. The only way to get
        # back to the |0...0> state with a mass-Hadamard operation is if all of
        # the phases are the same, which corresponds to a constant function. A
        # balanced function will only flip half of them, which will put the register
        # into some other state that's not |0...0> after a mass-Hadamard.
        run_flip_marker_as_phase_marker(circuit, oracle, qubits, oracle_args)

        # Bring the register back to the computational basis and measure each
		# qubit. If it's |0...0>, we know it's constant. If it's literally anything
		# else, it's balanced.
        circuit.append(cirq.H.on_each(*qubits))
        circuit.append(cirq.measure(*qubits, key="result"))
        
    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_test(self, oracle_name, oracle, should_be_constant, number_of_qubits, oracle_args):
        """
        Runs the Deutsch-Jozsa algorithm on the provided oracle, ensuring that it
        correctly identifies the oracle as constant or balanced.

        Parameters:
            oracle_name(str): The name of the oracle being tested
            oracle (function): The oracle to run the algorithm on
            should_be_constant (bool): True if the oracle is a constant function, false
                if it's balanced.
            number_of_qubits (int): The number of qubits to use for the oracle's input
                register
            oracle_args (anything): An oracle-specific argument object to pass to the
                oracle during execution
        """
        
        # Construct the circuit
        print(f"Running test: {oracle_name}")
        register = cirq.NamedQubit.range(number_of_qubits, prefix="qubit")
        circuit = cirq.Circuit()

        # Run the Deutsch-Jozsa algorithm on the oracle
        self.check_if_constant_or_balanced(circuit, oracle, register, oracle_args)
        
        # Run the circuit.
        simulator = cirq.Simulator()
        result = simulator.run(circuit, repetitions=1)
        result_states = result.histogram(key="result")

        # Check to see if the resulting input measurement is all 0s, and if that
        # matches the expected behavior or not
        for(state, count) in result_states.items():
            is_constant = (state == 0)
            if(is_constant != should_be_constant):
                self.fail(f"Test failed: {oracle_name} should be " +
                          "{\"constant\" if should_be_constant else \"balanced\"}" +
                          " but the algorithm says it was " +
                          "{\"balanced\" if should_be_constant else \"constant\"}")
        
        print("Passed!")
        print()


    def test_constant_zero(self):
        """
        Runs the test on the constant zero function.
        """

        self.run_test("constant zero", oracles.always_zero, True, 10, None)


    def test_constant_one(self):
        """
        Runs the test on the constant one function.
        """

        self.run_test("constant zero", oracles.always_one, True, 10, None)


    def test_odd_number_of_ones(self):
        """
        Runs the test on the odd number of |1> state check.
        """

        self.run_test("odd number of |1> check", oracles.check_for_odd_number_of_ones, False, 10, None)


    def test_nth_qubit_parity(self):
        """
        Runs the test on the Nth-qubit parity check function.
        """

        for i in range(0, 10):
            self.run_test(f"q{i} parity check", oracles.check_if_qubit_is_one, False, 10, i)


    
if __name__ == '__main__':
    unittest.main()