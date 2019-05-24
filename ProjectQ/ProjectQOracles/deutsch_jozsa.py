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
from projectq.meta import Dagger, Control
from utility import reset
from oracle_utility import run_flip_marker_as_phase_marker
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


    def check_if_constant_or_balanced(self, oracle, qubits, oracle_args):
        """
        Runs the Deutsch-Jozsa algorithm on the provided oracle, determining
        whether it's constant or balanced.

        Parameters:
            oracle (function): The oracle to check
            qubits (Qureg): The register to run the oracle on
            oracle_args (anything): An oracle-specific argument object to pass to
                the oracle during execution
        """

        # Initialize the register to |+...+>
        All(H) | qubits

        # Run the oracle in phase-flip mode. Any of the superposition states that
        # triggered the oracle will have their phase flipped. The only way to get
        # back to the |0...0> state with a mass-Hadamard operation is if all of
        # the phases are the same, which corresponds to a constant function. A
        # balanced function will only flip half of them, which will put the register
        # into some other state that's not |0...0> after a mass-Hadamard.
        run_flip_marker_as_phase_marker(oracle, qubits, oracle_args)

        # Bring the register back to the computational basis and measure each
		# qubit. If it's |0...0>, we know it's constant. If it's literally anything
		# else, it's balanced.
        # Note that because we can run classical code in-between quantum instructions
        # in ProjectQ, we don't actually need to measure every qubit - we can evaluate
        # each qubit one-by-one, and as soon as one of them is 0, we can immediately
        # return since we know the function is balanced. However, the simulator will
        # complain about leaving qubits in superpositions alive at the time of
        # deallocation, so it's good to clean them up via measurement anyway.
        for qubit in qubits:
            H | qubit
            Measure | qubit

        for qubit in qubits:
            if int(qubit) == 1:
                return False

        return True
        
    
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
        
        print(f"Running test: {oracle_name}")
        engine = MainEngine()
        register = engine.allocate_qureg(number_of_qubits)

        # Run the Deutsch-Jozsa algorithm on the oracle
        is_constant = self.check_if_constant_or_balanced(oracle, register, oracle_args)

        # Check to see if the results match the expected behavior or not
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