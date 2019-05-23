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
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import execute
from qiskit import Aer


class TeleportationTests(unittest.TestCase):
    """
    This class contains some test implementations of the standard quantum teleportation
    protocols using Qiskit, along with a few extra variations for good measure.

    Note that Qiskit's circuit and register system is pretty flexible, so you can achieve this
    a few different ways. This implementation breaks the algorithm down into parts and each
    part constructs its own circuit. It then merges those circuits together and executes the
    "master circuit".

    You could also do this with a single circuit, and just pass that around each function.
    That's analogous to how something like Q# works.
    """


    # ==============================
	# == Algorithm Implementation ==
	# ==============================


    def prepare_transfer_qubits(self, entanglement_state, transfer_qubit, reproduction_qubit):
        """
        Constructs a circuit that prepares a pair of entangled qubits that can be used for quantum
        teleportation.

        Parameters:
            entanglement_state (int): Which of the four entanglement states to put the qubits into.
                0 = |00> + |11>
                1 = |01> + |10>
                2 = |00> - |11>
                3 = |01> - |10>
            transfer_qubit (QuantumRegister): The qubit that will transfer the state of the original qubit
                to the reproduction qubit. This is the "local" qubit of the entangled pair.
            reproduction_qubit (QuantumRegister): The qubit that the original qubit's state will be
                transferred to. This is the "remote" qubit of the entangled pair.

        Returns:
            A circuit that prepares the entangled qubits.
        """
        
        circuit = QuantumCircuit(transfer_qubit, reproduction_qubit)
        circuit.h(transfer_qubit)
        circuit.cx(transfer_qubit, reproduction_qubit)

        if((entanglement_state & 0b01) == 0b01):
            circuit.x(transfer_qubit)

        if((entanglement_state & 0b10) == 0b10):
            circuit.z(transfer_qubit)

        return circuit


    def measure_message_parameters(self, original_qubit, transfer_qubit, original_measurement, transfer_measurement):
        """
        Constructs a circuit that entangles the original qubit with the transfer qubit, and measures them.
        These measurements can then be sent to the "remote end" to reproduce the original qubit.

        Parameters:
            original_qubit (QuantumRegister): The qubit containing the unknown state that will be teleported.
            transfer_qubit (QuantumRegister): The qubit that will transfer the state of the original qubit
                to the reproduction qubit. This is the "local" qubit of the entangled pair.
            original_measurement (ClassicalRegister): The register that will hold the result of the original
                qubit measurement.
            transfer_measurement (ClassicalRegister): The register that will hold the result of the transfer
                qubit measurement.

        Returns:
            A circuit that entangles and measures the qubits.
        """

        circuit = QuantumCircuit(original_qubit, transfer_qubit, original_measurement, transfer_measurement)

        # Entangle the original qubit with the transfer qubit
        circuit.cx(original_qubit, transfer_qubit)
        circuit.h(original_qubit)

        # Measure the original and transfer qubits
        circuit.measure(original_qubit, original_measurement)
        circuit.measure(transfer_qubit, transfer_measurement)

        return circuit


    def reproduce_original(self, entanglement_state, original_measurement, transfer_measurement, reproduction_qubit):
        """
        Constructs a circuit that converts the state of the reproduction qubit into the former state of the original
        qubit. This is the actual "teleportation" step.

        Parameters:
            entanglement_state (int): Which of the four entanglement states the transfer and reproduction qubits were
                in at the start of the process.
                0 = |00> + |11>
                1 = |01> + |10>
                2 = |00> - |11>
                3 = |01> - |10>
            original_measurement (ClassicalRegister): The register that holds the result of the original
                qubit measurement.
            transfer_measurement (ClassicalRegister): The register that holds the result of the transfer
                qubit measurement.
            reproduction_qubit (QuantumRegister): The qubit that the original qubit's state will be
                transferred to. This is the "remote" qubit of the entangled pair.

        Returns:
            A circuit that puts the reproduction qubit into the original state.
        """
        
        # Note: Qiskit doesn't let you explicitly measure a register, then change the quantum circuit
        # depending on the result. The way you do measure-then-modify is with a c_if() call after an
        # instruction. This essentially turns the entire circuit into a deferred-measurement system.

        circuit = QuantumCircuit(original_measurement, transfer_measurement, reproduction_qubit)

        if(entanglement_state == 0):
            circuit.x(reproduction_qubit).c_if(transfer_measurement, 1)
            circuit.z(reproduction_qubit).c_if(original_measurement, 1)

        elif(entanglement_state == 1):
            circuit.x(reproduction_qubit).c_if(transfer_measurement, 0)
            circuit.z(reproduction_qubit).c_if(original_measurement, 1)
        
        elif(entanglement_state == 2):
            circuit.x(reproduction_qubit).c_if(transfer_measurement, 1)
            circuit.z(reproduction_qubit).c_if(original_measurement, 0)
        
        elif(entanglement_state == 3):
            circuit.x(reproduction_qubit).c_if(transfer_measurement, 0)
            circuit.z(reproduction_qubit).c_if(original_measurement, 0)

        return circuit
    

    # ============================
	# == Test State Preparation ==
	# ============================

    
    def prepare_zero_state(self, qubit, adjoint):
        """
        Constructs a circuit that prepares the qubit in the |0> state.

        Parameters:
            qubit (QuantumRegister): The qubit to prepare
            adjoint (bool): True to run the adjoint version of the circuit, for turning
                the qubit back into the |0> state.

        Returns:
            A circuit that puts the qubit into the desired state.
        """

        circuit = QuantumCircuit(qubit)
        circuit.iden(qubit)
        return circuit


    def prepare_one_state(self, qubit, adjoint):
        """
        Constructs a circuit that prepares the qubit in the |1> state.

        Parameters:
            qubit (QuantumRegister): The qubit to prepare
            adjoint (bool): True to run the adjoint version of the circuit, for turning
                the qubit back into the |0> state.

        Returns:
            A circuit that puts the qubit into the desired state.
        """
        
        circuit = QuantumCircuit(qubit)
        circuit.x(qubit)
        return circuit


    def prepare_plus_state(self, qubit, adjoint):
        """
        Constructs a circuit that prepares the qubit in the |+> state 1/√2((|0> + |1>).

        Parameters:
            qubit (QuantumRegister): The qubit to prepare
            adjoint (bool): True to run the adjoint version of the circuit, for turning
                the qubit back into the |0> state.

        Returns:
            A circuit that puts the qubit into the desired state.
        """
        
        circuit = QuantumCircuit(qubit)
        circuit.h(qubit)
        return circuit


    def prepare_minus_state(self, qubit, adjoint):
        """
        Constructs a circuit that prepares the qubit in the |-> state 1/√2((|0> - |1>).

        Parameters:
            qubit (QuantumRegister): The qubit to prepare
            adjoint (bool): True to run the adjoint version of the circuit, for turning
                the qubit back into the |0> state.

        Returns:
            A circuit that puts the qubit into the desired state.
        """
        
        circuit = QuantumCircuit(qubit)
        if not adjoint:
            circuit.x(qubit)
            circuit.h(qubit)

        else:
            circuit.h(qubit)
            circuit.x(qubit)
        return circuit


    def prepare_i_plus_state(self, qubit, adjoint):
        """
        Constructs a circuit that prepares the qubit in the |i+> state 1/√2((|0> + i|1>).

        Parameters:
            qubit (QuantumRegister): The qubit to prepare
            adjoint (bool): True to run the adjoint version of the circuit, for turning
                the qubit back into the |0> state.

        Returns:
            A circuit that puts the qubit into the desired state.
        """
        
        circuit = QuantumCircuit(qubit)
        if not adjoint:
            circuit.h(qubit)
            circuit.s(qubit)

        else:
            circuit.sdg(qubit) # Note sdg is the adjoint of the S gate, since it isn't self-adjoint.
            circuit.h(qubit)
        return circuit


    def prepare_i_minus_state(self, qubit, adjoint):
        """
        Constructs a circuit that prepares the qubit in the |i-> state 1/√2((|0> - i|1>).

        Parameters:
            qubit (QuantumRegister): The qubit to prepare
            adjoint (bool): True to run the adjoint version of the circuit, for turning
                the qubit back into the |0> state.

        Returns:
            A circuit that puts the qubit into the desired state.
        """
        
        circuit = QuantumCircuit(qubit)
        if not adjoint:
            circuit.h(qubit)
            circuit.s(qubit)
            circuit.z(qubit)

        else:
            circuit.z(qubit)
            circuit.sdg(qubit)
            circuit.h(qubit)
        return circuit


    def prepare_weird_rotation(self, qubit, adjoint):
        """
        Constructs a circuit that prepares the qubit in an uneven superposition.

        Parameters:
            qubit (QuantumRegister): The qubit to prepare
            adjoint (bool): True to run the adjoint version of the circuit, for turning
                the qubit back into the |0> state.

        Returns:
            A circuit that puts the qubit into the desired state.
        """

        circuit = QuantumCircuit(qubit)
        if not adjoint:
            circuit.rx(0.36325, qubit)
            circuit.ry(1.8892345, qubit)
            circuit.rz(2.498235, qubit)
        else:
            circuit.rz(-2.498235, qubit)
            circuit.ry(-1.8892345, qubit)
            circuit.rx(-0.36325, qubit)
        return circuit
    
    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_test(self, description, iterations, prep_function):
        """
        Runs a unit test of the teleportation protocol with the provided state preparation function.

        Parameters:
            description (str): A description of the test, for logging.
            iterations (int): The number of times to run the circuit.
            prep_function (function): The function that can prepare (and un-prepare) the desired state
                to be teleported.
        """
        
        print(f"Running test: {description}")
        
        # Try teleportation using all 4 of the Bell states for the entangled transfer qubit pair
        for entanglement_state in range(0, 4):

            # Construct the registers and circuit. Note that this has to be in the loop because if it's
            # outside, its state will actually persist between simulation runs and totally ruin the test.
            original_qubit = QuantumRegister(1, "original")
            transfer_qubit = QuantumRegister(1, "transfer")
            reproduction_qubit = QuantumRegister(1, "reproduction")
            original_measurement = ClassicalRegister(1, "original_measurement")
            transfer_measurement = ClassicalRegister(1, "transfer_measurement")
            reproduction_measurement = ClassicalRegister(1, "reproduction_measurement")
        
            # Prepare the original qubit in the desired state, and the transfer qubits that will be used to teleport it
            circuit = prep_function(original_qubit, False)
            circuit.extend(self.prepare_transfer_qubits(entanglement_state, transfer_qubit, reproduction_qubit))

            # Teleport the original qubit, turning the remote reproduction qubit's state into the original state 
            circuit.extend(self.measure_message_parameters(original_qubit, transfer_qubit, original_measurement, transfer_measurement))
            circuit.extend(self.reproduce_original(entanglement_state, original_measurement, transfer_measurement, reproduction_qubit))

            # Run the adjoint preparation function on the reproduction qubit, and measure it.
            # If it is now in the original state, this should turn it back into |0> every time.
            circuit.extend(prep_function(reproduction_qubit, True))
            circuit.add_register(reproduction_measurement)
            circuit.measure(reproduction_qubit, reproduction_measurement)

            # Run the circuit N times.
            simulator = Aer.get_backend('qasm_simulator')
            simulation = execute(circuit, simulator, shots=iterations)
            result = simulation.result()
            counts = result.get_counts(circuit)

            # Check each result to make sure the result qubit is always 0
            # (Since the result measurement was added last, it'll be the first qubit in the state because
            # of Qiskit's little-endian encoding)
            for(state, count) in counts.items():
                if state[0] != "0":
                    self.fail(f"Test {description} failed with entanglement state {entanglement_state}. " +
                            f"Resulting state {state} had a 1 for the result, which means " +
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
