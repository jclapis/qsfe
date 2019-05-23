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


class TeleportationTests(unittest.TestCase):
    """
    This class contains some test implementations of the standard quantum teleportation
    protocols using ProjectQ, along with a few extra variations for good measure.

    Unlike the other frameworks, ProjectQ doesn't create circuit or program objects that
    can be passed around. Quantum operations are invoked line-by-line as they're written
    in the classical code, so this is written more like the Q# implementation than the
    other python frameworks.
    """


    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def prepare_transfer_qubits(self, entanglement_state, transfer_qubit, reproduction_qubit):
        """
        Prepares a pair of entangled qubits that can be used for quantum teleportation.

        Parameters:
            entanglement_state (int): Which of the four entanglement states to put the qubits into.
                0 = |00> + |11>
                1 = |01> + |10>
                2 = |00> - |11>
                3 = |01> - |10>
            transfer_qubit (Qureg): The qubit that will transfer the state of the original qubit
                to the reproduction qubit. This is the "local" qubit of the entangled pair.
            reproduction_qubit (Qureg): The qubit that the original qubit's state will be
                transferred to. This is the "remote" qubit of the entangled pair.
        """
        
        H | transfer_qubit
        CNOT | (transfer_qubit, reproduction_qubit)

        if((entanglement_state & 0b01) == 0b01):
            X | transfer_qubit

        if((entanglement_state & 0b10) == 0b10):
            Z | transfer_qubit


    def measure_message_parameters(self, original_qubit, transfer_qubit):
        """
        Entangles the original qubit with the transfer qubit, and measures them.
        These measurements can then be sent to the "remote end" to reproduce the original qubit.

        Parameters:
            original_qubit (Qureg): The qubit containing the unknown state that will be teleported.
            transfer_qubit (Qureg): The qubit that will transfer the state of the original qubit
                to the reproduction qubit. This is the "local" qubit of the entangled pair.
                qubit measurement.

        Returns:
            An int tuple representing the measured values. The first element is the value of the original
            qubit, and the second element is the value of the transfer qubit.
        """
        
        # Entangle the original qubit with the transfer qubit
        CNOT | (original_qubit, transfer_qubit)
        H | original_qubit
        
        # Measure the original and transfer qubits
        Measure | original_qubit
        Measure | transfer_qubit

        # Return the measurement results
        return (int(original_qubit), int(transfer_qubit))


    def reproduce_original(self, entanglement_state, original_measurement, transfer_measurement, reproduction_qubit):
        """
        Converts the state of the reproduction qubit into the former state of the original qubit.
        This is the actual "teleportation" step.

        Parameters:
            entanglement_state (int): Which of the four entanglement states the transfer and reproduction qubits were
                in at the start of the process.
                0 = |00> + |11>
                1 = |01> + |10>
                2 = |00> - |11>
                3 = |01> - |10>
            original_measurement (int): The value of the original qubit.
            transfer_measurement (int): The value of the transfer qubit.
            reproduction_qubit (Qureg): The qubit that the original qubit's state will be
                transferred to. This is the "remote" qubit of the entangled pair.
        """
        
        # ProjectQ doesn't distinguish between quantum and classical regimes, so control flow isn't
        # a thing. We can actually measure the qubits, get the results back, and run whatever code
        # we want (including classical code) based on the measurements. This is SO MUCH BETTER than
        # the "build a circuit and run it in a black box" model that Qiskit, Cirq, and Forest use.

        if(entanglement_state == 0):
            if transfer_measurement == 1:
                X | reproduction_qubit
            if original_measurement == 1:
                Z | reproduction_qubit

        elif(entanglement_state == 1):
            if transfer_measurement == 0:
                X | reproduction_qubit
            if original_measurement == 1:
                Z | reproduction_qubit
        
        elif(entanglement_state == 2):
            if transfer_measurement == 1:
                X | reproduction_qubit
            if original_measurement == 0:
                Z | reproduction_qubit
        
        elif(entanglement_state == 3):
            if transfer_measurement == 0:
                X | reproduction_qubit
            if original_measurement == 0:
                Z | reproduction_qubit
    

    # ============================
	# == Test State Preparation ==
	# ============================

    
    def prepare_zero_state(self, qubit):
        """
        Prepares the qubit in the |0> state.

        Parameters:
            qubit (Qureg): The qubit to prepare
        """

        # ProjectQ doesn't have an I gate, so this doesn't do anything.


    def prepare_one_state(self, qubit):
        """
        Prepares the qubit in the |1> state.

        Parameters:
            qubit (Qureg): The qubit to prepare
        """
        
        X | qubit


    def prepare_plus_state(self, qubit):
        """
        Prepares the qubit in the |+> state 1/√2(|0> + |1>).

        Parameters:
            qubit (Qureg): The qubit to prepare
        """
        
        H | qubit


    def prepare_minus_state(self, qubit):
        """
        Prepares the qubit in the |-> state 1/√2(|0> - |1>).

        Parameters:
            qubit (Qureg): The qubit to prepare
        """
        
        X | qubit
        H | qubit


    def prepare_i_plus_state(self, qubit):
        """
        Prepares the qubit in the |i+> state 1/√2(|0> + i|1>).

        Parameters:
            qubit (Qureg): The qubit to prepare
        """
        
        H | qubit
        S | qubit


    def prepare_i_minus_state(self, qubit):
        """
        Prepares the qubit in the |i-> state 1/√2(|0> - i|1>).

        Parameters:
            qubit (Qureg): The qubit to prepare
        """
        
        H | qubit
        S | qubit
        Z | qubit


    def prepare_weird_rotation(self, qubit):
        """
        Prepares the qubit in an uneven superposition.

        Parameters:
            qubit (Qureg): The qubit to prepare
        """

        Rx(0.36325) | qubit
        Ry(1.8892345) | qubit
        Rz(2.498235) | qubit
    
    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_test(self, description, iterations, prep_function):
        """
        Runs a unit test of the teleportation protocol with the provided state preparation function.

        Parameters:
            description (str): A description of the test, for logging.
            iterations (int): The number of times to run the program.
            prep_function (function): The function that can prepare (and un-prepare) the desired state
                to be teleported.
        """
        
        print(f"Running test: {description}")
        
        engine = MainEngine()
        original_qubit = engine.allocate_qubit()
        transfer_qubit = engine.allocate_qubit()
        reproduction_qubit = engine.allocate_qubit()

        # Try teleportation using all 4 of the Bell states for the entangled transfer qubit pair
        for entanglement_state in range(0, 4):
            for i in range(0, iterations):

                # Prepare the original qubit in the desired state, and the transfer qubits that will be used to teleport it
                prep_function(original_qubit)
                self.prepare_transfer_qubits(entanglement_state, transfer_qubit, reproduction_qubit)

                # Teleport the original qubit, turning the remote reproduction qubit's state into the original state 
                (original_measurement, transfer_measurement) = self.measure_message_parameters(original_qubit, transfer_qubit)
                self.reproduce_original(entanglement_state, original_measurement, transfer_measurement, reproduction_qubit)

                # Run the adjoint preparation function on the reproduction qubit, and measure it.
                # If it is now in the original state, this should turn it back into |0> every time.
                with Dagger(engine):
                    prep_function(reproduction_qubit)
                    
                # Make sure the result qubit is 0
                Measure | reproduction_qubit

                if int(reproduction_qubit) != 0:
                    self.fail(f"Test {description} failed with entanglement state {entanglement_state}. " +
                            f"Resulting state {result} had a 1 for the result, which means " +
                            "the qubit wasn't teleported properly.")

                reset([original_qubit, transfer_qubit, reproduction_qubit])
                engine.flush()

            print(f"Entanglement state {entanglement_state} passed.");
        
        print("Passed!")
        print()
        

    def test_zero(self):
        """
        Tests teleportation on the |0> state.
        """

        self.run_test("Teleport |0>", 100, self.prepare_zero_state)


    def test_one(self):
        """
        Tests teleportation on the |1> state.
        """

        self.run_test("Teleport |1>", 100, self.prepare_one_state)


    def test_plus(self):
        """
        Tests teleportation on the |+> state.
        """

        self.run_test("Teleport |+>", 100, self.prepare_plus_state)


    def test_minus(self):
        """
        Tests teleportation on the |-> state.
        """

        self.run_test("Teleport |->", 100, self.prepare_minus_state)


    def test_i_plus(self):
        """
        Tests teleportation on the |i+> state.
        """

        self.run_test("Teleport |i+>", 100, self.prepare_i_plus_state)


    def test_i_minus(self):
        """
        Tests teleportation on the |i-> state.
        """

        self.run_test("Teleport |i->", 100, self.prepare_i_minus_state)


    def test_weird_rotation(self):
        """
        Tests teleportation on the uneven superposition.
        """

        self.run_test("Teleport weird rotation", 100, self.prepare_weird_rotation)



if __name__ == '__main__':
    unittest.main()
