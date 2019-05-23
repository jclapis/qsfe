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


class TeleportationTests(unittest.TestCase):
    """
    This class contains some test implementations of the standard quantum teleportation
    protocols using pyQuil, along with a few extra variations for good measure.

    Note that pyQuil's program and register system is pretty flexible, so you can achieve this
    a few different ways. This implementation breaks the algorithm down into parts and each
    part constructs its own program. It then merges those programs together and executes the
    "master program".

    You could also do this with a single program, and just pass that around each function.
    That's analogous to how something like Q# works.
    """


    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def prepare_transfer_qubits(self, entanglement_state, transfer_qubit, reproduction_qubit):
        """
        Constructs a program that prepares a pair of entangled qubits that can be used for quantum
        teleportation.

        Parameters:
            entanglement_state (int): Which of the four entanglement states to put the qubits into.
                0 = |00> + |11>
                1 = |01> + |10>
                2 = |00> - |11>
                3 = |01> - |10>
            transfer_qubit (QubitPlaceholder): The qubit that will transfer the state of the original qubit
                to the reproduction qubit. This is the "local" qubit of the entangled pair.
            reproduction_qubit (QubitPlaceholder): The qubit that the original qubit's state will be
                transferred to. This is the "remote" qubit of the entangled pair.

        Returns:
            A program that prepares the entangled qubits.
        """
        
        program = Program(
            H(transfer_qubit),
            CNOT(transfer_qubit, reproduction_qubit)
        )

        if((entanglement_state & 0b01) == 0b01):
            program += X(transfer_qubit)

        if((entanglement_state & 0b10) == 0b10):
            program += Z(transfer_qubit)

        return program


    def measure_message_parameters(self, original_qubit, transfer_qubit, original_measurement, transfer_measurement):
        """
        Constructs a program that entangles the original qubit with the transfer qubit, and measures them.
        These measurements can then be sent to the "remote end" to reproduce the original qubit.

        Parameters:
            original_qubit (QubitPlaceholder): The qubit containing the unknown state that will be teleported.
            transfer_qubit (QubitPlaceholder): The qubit that will transfer the state of the original qubit
                to the reproduction qubit. This is the "local" qubit of the entangled pair.
            original_measurement (MemoryReference): The register that will hold the result of the original
                qubit measurement.
            transfer_measurement (MemoryReference): The register that will hold the result of the transfer
                qubit measurement.

        Returns:
            A program that entangles and measures the qubits.
        """

        program = Program(
            # Entangle the original qubit with the transfer qubit
            CNOT(original_qubit, transfer_qubit),
            H(original_qubit),
            
            # Measure the original and transfer qubits
            MEASURE(original_qubit, original_measurement),
            MEASURE(transfer_qubit, transfer_measurement)
        )

        return program


    def reproduce_original(self, entanglement_state, original_measurement, transfer_measurement, reproduction_qubit):
        """
        Constructs a program that converts the state of the reproduction qubit into the former state of the original
        qubit. This is the actual "teleportation" step.

        Parameters:
            entanglement_state (int): Which of the four entanglement states the transfer and reproduction qubits were
                in at the start of the process.
                0 = |00> + |11>
                1 = |01> + |10>
                2 = |00> - |11>
                3 = |01> - |10>
            original_measurement (MemoryReference): The register that holds the result of the original
                qubit measurement.
            transfer_measurement (MemoryReference): The register that holds the result of the transfer
                qubit measurement.
            reproduction_qubit (QubitPlaceholder): The qubit that the original qubit's state will be
                transferred to. This is the "remote" qubit of the entangled pair.

        Returns:
            A program that puts the reproduction qubit into the original state.
        """
        
        # pyQuil has an interesting implementation of classical control flow. It lets you define two
        # separate programs: one that happens if a classical bit is 1, and another that happens if
        # the classical bit is 0. It calls these the "then/else" branch pair.
        # Essentially you construct the IF statement body and the ELSE statement body as two
        # separate programs, then you bring them together with an "if_then" call on an overall
        # master program.
        # This is a fairly intuitive and quite powerful way to do classical control flow, especially
        # compared to Qiskit. Props to the pyQuil team for making this work.

        program = Program()                         # This is the main program
        x_program = Program(X(reproduction_qubit))  # This is a branch that X's the reproduction qubit
        z_program = Program(Z(reproduction_qubit))  # This is a branch that Z's the reproduction qubit
        empty_program = Program()                   # This is an empty branch where nothing happens

        if(entanglement_state == 0):
            # If transfer_measurement == 1, X(reproduction_qubit), else do nothing
            program.if_then(transfer_measurement, x_program, empty_program)

            # If original_measurement == 1, Z(reproduction_qubit), else do nothing
            program.if_then(original_measurement, z_program, empty_program)

        elif(entanglement_state == 1):
            # Same as above, but now X(reproduction_qubit) if transfer_measurement == 0
            program.if_then(transfer_measurement, empty_program, x_program)
            program.if_then(original_measurement, z_program, empty_program)
        
        elif(entanglement_state == 2):
            program.if_then(transfer_measurement, x_program, empty_program)
            program.if_then(original_measurement, empty_program, z_program)
        
        elif(entanglement_state == 3):
            program.if_then(transfer_measurement, empty_program, x_program)
            program.if_then(original_measurement, empty_program, z_program)

        return program
    

    # ============================
	# == Test State Preparation ==
	# ============================

    
    def prepare_zero_state(self, qubit):
        """
        Constructs a program that prepares the qubit in the |0> state.

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare

        Returns:
            A program that puts the qubit into the desired state.
        """

        program = Program()
        program += I(qubit)
        return program


    def prepare_one_state(self, qubit):
        """
        Constructs a program that prepares the qubit in the |1> state.

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare

        Returns:
            A program that puts the qubit into the desired state.
        """
        
        program = Program()
        program += X(qubit)
        return program


    def prepare_plus_state(self, qubit):
        """
        Constructs a program that prepares the qubit in the |+> state 1/√2((|0> + |1>).

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare

        Returns:
            A program that puts the qubit into the desired state.
        """
        
        program = Program()
        program += H(qubit)
        return program


    def prepare_minus_state(self, qubit):
        """
        Constructs a program that prepares the qubit in the |-> state 1/√2((|0> - |1>).

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare

        Returns:
            A program that puts the qubit into the desired state.
        """
        
        program = Program()
        program += X(qubit)
        program += H(qubit)
        return program


    def prepare_i_plus_state(self, qubit):
        """
        Constructs a program that prepares the qubit in the |i+> state 1/√2((|0> + i|1>).

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare

        Returns:
            A program that puts the qubit into the desired state.
        """
        
        program = Program()
        program += H(qubit)
        program += S(qubit)
        return program


    def prepare_i_minus_state(self, qubit):
        """
        Constructs a program that prepares the qubit in the |i-> state 1/√2((|0> - i|1>).

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare

        Returns:
            A program that puts the qubit into the desired state.
        """
        
        program = Program()
        program += H(qubit)
        program += S(qubit)
        program += Z(qubit)
        return program


    def prepare_weird_rotation(self, qubit):
        """
        Constructs a program that prepares the qubit in an uneven superposition.

        Parameters:
            qubit (QubitPlaceholder): The qubit to prepare

        Returns:
            A program that puts the qubit into the desired state.
        """

        program = Program()
        program += RX(0.36325, qubit)
        program += RY(1.8892345, qubit)
        program += RZ(2.498235, qubit)
        return program
    
    
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
        
        # Try teleportation using all 4 of the Bell states for the entangled transfer qubit pair
        for entanglement_state in range(0, 4):

            # Construct the registers and program.
            original_qubit = QubitPlaceholder()
            transfer_qubit = QubitPlaceholder()
            reproduction_qubit = QubitPlaceholder()
            
            # Prepare the original qubit in the desired state, and the transfer qubits that will be used to teleport it
            program = prep_function(original_qubit)
            program += self.prepare_transfer_qubits(entanglement_state, transfer_qubit, reproduction_qubit)

            # Teleport the original qubit, turning the remote reproduction qubit's state into the original state 
            original_measurement = program.declare("original_measurement", "BIT", 1)
            transfer_measurement = program.declare("transfer_measurement", "BIT", 1)
            program += self.measure_message_parameters(original_qubit, transfer_qubit, original_measurement, transfer_measurement)
            program += self.reproduce_original(entanglement_state, original_measurement, transfer_measurement, reproduction_qubit)

            # Run the adjoint preparation function on the reproduction qubit, and measure it.
            # If it is now in the original state, this should turn it back into |0> every time.
            program += prep_function(reproduction_qubit).dagger()
            reproduction_measurement = program.declare("ro", "BIT", 1)
            program += MEASURE(reproduction_qubit, reproduction_measurement)

            # Run the program N times.
            assigned_program = address_qubits(program)
            assigned_program.wrap_in_numshots_loop(iterations)
            computer = get_qc(f"3q-qvm", as_qvm=True)
            executable = computer.compile(assigned_program)
            results = computer.run(executable)

            # Check each result to make sure the result qubit is always 0
            for result in results:
                if result[0] != 0:
                    self.fail(f"Test {description} failed with entanglement state {entanglement_state}. " +
                            f"Resulting state {result} had a 1 for the result, which means " +
                            "the qubit wasn't teleported properly.")

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
