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
import math
import unittest
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import execute
from qiskit import Aer
import qft
import shor_math


class QftTests(unittest.TestCase):
    """
    This class contains the tests for QFT, including some customized
    implementations of a few simple sine and cosine sampling vectors. These
    could be handy when testing other frameworks that don't come with an
    analog of the "PrepareArbitraryState" function or the Ry(...) function,
    so I can just directly implement circuits that put the register into the
    proper states for these tests.
    """

    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_iqft_with_waveform_samples(self, number_of_qubits, sample_rate,
                                       correct_frequency, prep_function, prep_args):
        """
        Tests my QFT implementation by comparing it to the classical DFT, ensuring it produces the
        same output as DFT when given the same input (after being normalized for quantum operations).

        Parameters:
            number_of_qubits (int): The size of the processing register to use, in qubits.
                This will be used to represent 2^N samples of the input signal.
            sample_rate (float): The sampling rate used by the prep opration. This is used to
                determine the actual frequency of the measured value once QFT is finished, which can
                vary based on the number of samples and the sample rate.
            correct_frequency (double): The correct answer that QFT should provide after running on
                the prepared input state.
            prep_function (function): The function that prepares the qubit register in the desired
                state for this test.
            prep_args (anything): Arguments to pass to the preparation function.
        """

        qubits = QuantumRegister(number_of_qubits)
        measurement = ClassicalRegister(number_of_qubits)
        circuit = QuantumCircuit(qubits, measurement)

        # Set up the register so it's in the correct state for the test
        if prep_args is None:
            prep_function(circuit, qubits)
        else:
            prep_function(circuit, qubits, prep_args)

        # Run the inverse QFT, which corresponds to the normal DFT
        qft.iqft(circuit, qubits)

        # Measure the result from QFT
        circuit.measure(qubits, measurement)

        # Run the circuit
        simulator = Aer.get_backend("qasm_simulator")
        simulation = execute(circuit, simulator, shots=1)
        result = simulation.result()
        counts = result.get_counts(circuit)
        for(state, count) in counts.items():
            state = state[::-1]
            result = int(state, 2)
            break

        # QFT suffers from the same Nyquist-frequency mirroring as DFT, but we can't just
        # look at all of the output details and ignore the mirrored results. If we end up
		# measuring a mirrored result, this will flip it back to the proper result in the
		# 0 < X < N/2 space.
        number_of_states = 2 ** number_of_qubits
        if result > number_of_states / 2:
            result = number_of_states - result

        # Correct for the sample rate.
        total_time = number_of_states / sample_rate
        result = result / total_time

        # Verify we got the right result.
        if result != correct_frequency:
            raise ValueError(f"Expected frequency {correct_frequency} but measured {result}.")


    def prepare_1hz_sine_8_samples(self, circuit, qubits):
        """
        Prepares a register so that the real component of each state's amplitude
	    corresponds to a sine wave with a 1 Hz frequency, f(x) = sin(2πx). The 8
	    possible states of the register will take on the role of the time steps
	    from 0 to 7/8 of a second.
	    For a classical DFT, the input would be the following array:
	    [0, 0.707, 1, 0.707, 0, -0.707, -1, -0.707]
	    where the first element is for t = 0, the second is for t = 1/8, and so on.
	    For the quantum variation, these values are encoded into the amplitudes of
	    each register state (and normalized so the whole vector has a magnitude of
	    1). Thus, the total thing will become:
	    0.354*|001⟩ + 0.5*|010⟩ + 0.354*|011⟩ - 0.354*|101⟩ - 0.5*|110⟩ - 0.354*|111⟩.

        Parameters:
            circuit (QuantumCircuit): The circuit being constructed
            qubits (QuantumRegister): The register that will hold the sine wave samples
                in its superposition amplitudes
        """

        # Okay. So this algorithm is going to look weird at first considering it has nothing to do with
		# sine waves, and that's fine. I'm going to walk you through how I designed this, step by step.
		# Hopefully you can learn something from it and use it to design your own circuits for weird
		# qubit states!
		# 
		# The original classical array for 8 measurements over 1 second of the sine wave is this:
		# [0, 1/√2, 1, 1/√2, 0, -1/√2, -1, -1/√2]
		# 
		# We want to encode that into the real component of the amplitudes of a 3 qubit register, so we
		# get this:
		# 0*|000⟩ + 1/√2|001⟩ + 1*|010⟩ + 1/√2*|011⟩ + 0*|100⟩ - 1/√2*|101⟩ - 1*|110⟩ - 1/√2*|111⟩
		# 
		# Immediately, there's a problem: these amplitudes are too big. Quantum state vectors need the
		# sum of squares to add to 1, and these add to:
		# 2*(1/√2)^2 + 2*1^2 + 2*(-1/√2)^2
		# = 2*1/2 + 2*1 + 2*1/2
		# = 4
		# So to fix this, we need to divide each state's probability by 4 (and thus, each state's
		# amplitude by √4 = 2.
		# This is the target state once it's been normalized:
		# 0*|000⟩ + 1/2√2*|001⟩ + 1/2*|010⟩ + 1/2√2*|011⟩ + 0*|100⟩ - 1/2√2*|101⟩ - 1/2*|110⟩ - 1/2√2*|111⟩
		# = 1/2( 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩ - 1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩ )
		# 
		# Now that we have the target state, we can start designing a circuit for it.
		# The first thing I notice about the general structure of the state is that it's really in two
		# halves: when q0 = 0, it's 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩.
		# when q0 = 1, it's -1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩.
		# The second half is just the negative version of the first half (with q0 flipped), so I know
		# 2 things:
		#		1. q0 isn't entangled with anything
		#		2. q0 is in an equal superposition of |0⟩ and |-1⟩.
		# Thus, we can reduce q0 to the |-⟩ state which is 1/√2*(|0⟩ - |1⟩). We know that whatever else
		# happens, we're going to put q0 into |-⟩ at the start of the circuit and ignore it after that.
		# Here's the reduction:
		# 1/2( 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩ - 1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩ )
		# = 1/2( √2*1/√2( 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩ - 1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩ ) )
		# = 1/2( √2( 1/√2*|-01⟩ + |-10⟩ + 1/√2*|-11⟩ ) )
		# = 1/2( |-01⟩ + √2*|-10⟩ + |-11⟩ )
		# 
		# Okay, now we're getting somewhere. Next, I notice that when q2 is 1, q1 has an equal
		# probability of being |0⟩ or |1⟩. It might be more obvious if I rearrange the terms like this:
		# = 1/2( |-01⟩ + |-11⟩ + √2*|-10⟩ )
		# 
		# In other words, when q2 is 1, q1 = |+⟩ which is 1/√2*(|0⟩ + |1⟩). Let's use that to reduce the
		# qubit state even further:
		# 1/2( |-01⟩ + |-11⟩ + √2*|-10⟩ )
		# = 1/2( √2*1/√2( |-01⟩ + |-11⟩ ) + √2*|-10⟩ )
		# = 1/2( √2( |-+1⟩ ) + √2*|-10⟩ )
		# = √2/2( |-+1⟩ + |-10⟩ )
		# = 1/√2( |-+1⟩ + |-10⟩ )
		#
		# This is as far as the reduction can go. You might think that you can reduce q2 into |+⟩ here,
		# but note that the state of qubit 1 changes depending on what qubit 2 is. That means we can't
		# reduce it; it also means that q1 and q2 are going to be entangled.
		# Anyway, now that the state is reduced, we can figure out how to create the states with a
		# circuit. We know that q0 is going to be |-⟩ no matter what, so that's easy: X and H will put
		# it into that state, and then we can ignore it. The other two qubits are then described by
		# this state:
		# 1/√2( |+1⟩ + |10⟩ )
		# 
		# q2 has an equal probability of being |0⟩ or |1⟩ (probability 1/√2), so it can just be prepared
		# with a simple H.
		# Now for q1, the weird one: assuming it starts at |0⟩, then if q2 == 1, q1 should be Hadamard'd.
		# If q2 == 0, then q1 should be flipped instead. That's actually pretty easy to do: we can just
		# do a Controlled H with q2 as the control and q1 as the target, and a zero-controlled X (AKA a
		# 0-CNOT) with q2 as the control and q1 as the target. We just have to make sure q2 is H'd first.
		# 
		# And thus, at the end of the day, this is how you construct a 3-qubit state where the real part
		# of the amplitudes maps to a 1 Hz sine wave, sampled at 8 samples per second:

        # Set up q0
        circuit.x(qubits[0])
        circuit.h(qubits[0])

        # Set up q2
        circuit.h(qubits[2])

        # Set up q1: if q2 is 1, H it. Otherwise, X it.
        circuit.ch(qubits[2], qubits[1])

        # 0-controlled CNOT
        circuit.x(qubits[2])
        circuit.cx(qubits[2], qubits[1])
        circuit.x(qubits[2])

        # I hope that writeup helped explain how these 7 lines create the sine wave, and help you do
		# circuit design like this in the future!


    def prepare_1hz_cosine_8_samples(self, circuit, qubits):
        """
        Prepares a register so that the real component of each state's amplitude
	    corresponds to a cosine wave with a 1 Hz frequency, f(x) = cos(2πx). The 8
	    possible states of the register will take on the role of the time steps
	    from 0 to 7/8 of a second.
	    For a classical DFT, the input would be the following array:
	    [1, 0.707, 0, -0.707, -1, -0.707, 0, 0.707]
	    where the first element is for t = 0, the second is for t = 1/8, and so on.
	    For the quantum variation, these values are encoded into the amplitudes of
	    each register state (and normalized so the whole vector has a magnitude of
	    1). Thus, the total thing will become:
	    0.5*|000⟩ + 0.354*|001⟩ - 0.354*|011⟩ - 0.5*|100⟩ - 0.354*|101⟩ + 0.354*|111⟩.

        Parameters:
            circuit (QuantumCircuit): The circuit being constructed
            qubits (QuantumRegister): The register that will hold the cosine wave samples
                in its superposition amplitudes
        """

        # This operation is going to look quite different from the sine example, but that's okay. The
		# structure itself isn't really that important - the key is the methodology that lets you figure
		# out a circuit to generate the state you're looking for. The process for this one is the same,
		# so this is just going to be another example of it. I'll walk you through it.
		# 
		# First things first: here's the conventional array of samples from cos(2πx) that you'd normally
		# feed into DFT:
		# [1, 1/√2, 0, -1/√2, -1, -1/√2, 0, 1/√2]
		# 
		# Using the same normalization process as before, so this can be represented in qubits, gives us:
		# 1/2*|000⟩ + 1/2√2*|001⟩ + 0*|010⟩ - 1/2√2*|011⟩ - 1/2*|100⟩ - 1/2√2*|101⟩ + 0*|110⟩ + 1/2√2*|111⟩
		# = 1/2( |000⟩ + 1/√2*|001⟩ - 1/√2*|011⟩ - |100⟩ - 1/√2*|101⟩ + 1/√2*|111⟩ )
		# 
		# There aren't any immediately obvious patterns with respect to the + and - parts (or at least,
		# I couldn't find any), so I just reorganized it a little bit to group the common parts together:
		# 1/2( |000⟩ - |100⟩ + 1/√2( |001⟩ - |011⟩ - |101⟩ + |111⟩ ) )
		# 
		# Now with this, I do notice a commonality. In the first 2 terms, q2 is always 0. In the last 4
		# terms (the 1/√2 group), q2 is always 1. Both groups have a 50% chance of occurring, so really
		# we could break it down into this algorithm:
		#		H(q2)
		#		if(q2 == 0), put q0 and q1 in the first group
		#		else, put q0 and q1 into the second group
		# Obviously we can't perform a classical "if-else" on qubits in superpositions... but we CAN
		# leverage the Controlled functor which effectively does the same thing!
		# So, with that in mind, let's figure out how to create the groups.
		# 
		# The first group is just [|00⟩ - |10⟩]0⟩, which reduces to √2*|-00⟩. That's easy to write a
		# circuit for: we just do X and H on q0 to put it into the |-⟩ state. So for the first group,
		# we can do this:
		#		if(q2 == 0)... (the gates below will be zero-controlled on q2)
		#		X(q0);
		#		H(q0);
		# 
		# The second group is a little harder: [|00⟩ - |01⟩ - |10⟩ + |11⟩]1⟩. Written as a state vector
		# of q0 and q1, it looks like this: [1, -1, -1, 1]. We need some way to get the qubits into
		# this state. I did a little reverse engineering on it: we know that H on both qubits will give
		# the state [1, 1, 1, 1]. There are 2 negative phases, and we know that Z on q0 would give the
		# state [-1, 1, -1, 1]; Z on q1 would give [1, -1, 1, -1]. We could do either of those but we'd
		# need a way to swap the 1st and 2nd qubits, or the 3rd and 4th terms, respectively.
		# Wait! We have one! CNOT on q0 and q1 will swap the 3rd and 4th terms! So to get this state,
		# we could do the following:
		#		if(q2 == 1)... (the gates below will be controlled on q2)
		#		H(q0);
		#		H(q1);
		#		Z(q1);
		#		CNOT(q0, q1);
		#
		# Finally, note that the last operation of the first group is H(q0) and the first operation of
		# the second group is H(q0), so we can just remove that step from both groups and perform it
		# unconditionally in-between their execution.
		# 
		# You can verify that the amplitudes of each state work out with this setup. I wrote it up below,
		# and lo and behold, it produced the cosine measurement array. I'm sure there's a prettier way to
		# do this that looks more like the sine function, but this is meant to be another good example of
		# how to tackle circuit design to get to a target state.

        # Set up q2
        circuit.h(qubits[2])

        # If q2 == 0
        circuit.x(qubits[2])
        circuit.cx(qubits[2], qubits[0])
        circuit.x(qubits[2])

        circuit.h(qubits[0])

        # Else if(q2 == 1)
        circuit.cx(qubits[2], qubits[1])
        circuit.ch(qubits[2], qubits[1])
        circuit.ccx(qubits[2], qubits[0], qubits[1])


    def prepare_2hz_sine_8_samples(self, circuit, qubits):
        """
        Prepares a register so that the real component of each state's amplitude
	    corresponds to a sine wave with a 2 Hz frequency, f(x) = sin(4πx). The 8
	    possible states of the register will take on the role of the time steps
	    from 0 to 7/8 of a second.
	    For a classical DFT, the input would be the following array:
	    [0, 1, 0, -1, 0, 1, 0, -1]
	    where the first element is for t = 0, the second is for t = 1/8, and so on.
	    For the quantum variation, these values are encoded into the amplitudes of
	    each register state (and normalized so the whole vector has a magnitude of
	    1). Thus, the total thing will become:
	    0.5*|001⟩ - 0.5*|011⟩ + 0.5*|101⟩ - 0.5*|111⟩.

        Parameters:
            circuit (QuantumCircuit): The circuit being constructed
            qubits (QuantumRegister): The register that will hold the sine wave samples
                in its superposition amplitudes
        """

        # This one's really easy. Here's the full target state:
		# 1/2( |001⟩ - |011⟩ + |101⟩ - |111⟩ )
		# 
		# Right off the bat: q2 is always 1. Removing it, we get:
		# 1/2( |00⟩ - |01⟩ + |10⟩ - |11⟩ )|1⟩
		# 
		# q0 and q1 are both in uniform superpositions, but the sign is inverted
		# when q1 == 1. It should be pretty obvious that q0 = |+⟩ and q1 = |-⟩, but
		# here's the decomposition anyway:
		# 1/2( |00⟩ - |01⟩ + |10⟩ - |11⟩ )|1⟩
		# = 1/2( √2*1/√2( |00⟩ - |01⟩ + |10⟩ - |11⟩ ))|1⟩
		# = 1/2( √2( |+0⟩ - |+1⟩ ))|1⟩
		# = 1/2( √2*√2*1/√2( |+0⟩ - |+1⟩ ))|1⟩
		# = 1/2( 2( |+-⟩ ))|1⟩
		# = |+-1>
		# 
		# Yep, it reduces down to a single state with no entanglement.

        circuit.h(qubits[0])

        circuit.x(qubits[1])
        circuit.h(qubits[1])

        circuit.x(qubits[2])


    def prepare_2hz_cosine_8_samples(self, circuit, qubits):
        """
        Prepares a register so that the real component of each state's amplitude
	    corresponds to a cosine wave with a 2 Hz frequency, f(x) = cos(4πx). The 8
	    possible states of the register will take on the role of the time steps
	    from 0 to 7/8 of a second.
	    For a classical DFT, the input would be the following array:
	    [1, 0, -1, 0, 1, 0, -1, 0]
	    where the first element is for t = 0, the second is for t = 1/8, and so on.
	    For the quantum variation, these values are encoded into the amplitudes of
	    each register state (and normalized so the whole vector has a magnitude of
	    1). Thus, the total thing will become:
	    0.5*|000⟩ - 0.5*|010⟩ + 0.5*|100⟩ - 0.5*|110⟩.

        Parameters:
            circuit (QuantumCircuit): The circuit being constructed
            qubits (QuantumRegister): The register that will hold the cosine wave samples
                in its superposition amplitudes
        """

        # This is exactly the same as the 2Hz sine, except q2 is 0.

        circuit.h(qubits[0])

        circuit.x(qubits[1])
        circuit.h(qubits[1])


    def prepare_sine_wave_samples(self, circuit, qubits, prep_args):
        """
        Prepares a qubit register so the amplitudes of each state correspond to the values
	    of the sine or cosine function at the timestep represented by that state. For example:
	    with a 1 Hz sine wave, 8 samples per second and 8 total samples, the sine wave samples
	    will be [0, 0.707, 1, 0.707, 0, -0.707, -1, -0.707]. This function will put the register
	    into the corresponding quantum state: 0.354*|001⟩ + 0.5*|010⟩ + 0.354*|011⟩ - 0.354*|101⟩
	    - 0.5*|110⟩ - 0.354*|111⟩. Note that the amplitudes will be normalized so the state is a
	    unit vector.

        Parameters:
            circuit (QuantumCircuit): The circuit being constructed
            qubits (QuantumRegister): The register that will hold the sine wave samples
                in its superposition amplitudes
            prep_args (tuple(double, double, bool)):
                - The frequency of the wave (in Hz),
                - The number of samples to take per second,
                - True to use the cosine function, false to use the sine function.
        """

        (frequency, sample_rate, use_cosine) = prep_args

        number_of_samples = 2 ** len(qubits)
        # Since quantum states need to be unit vectors, this will be used to reduce the
		# sin / cos output properly.
        normalization_factor = math.sqrt(number_of_samples / 2)

        samples = [0] * number_of_samples
        for i in range(0, number_of_samples):
            timestamp = i / sample_rate
            sample = 0
            if use_cosine:
                sample = math.cos(frequency * 2 * math.pi * timestamp) / normalization_factor
            else:
                sample = math.sin(frequency * 2 * math.pi * timestamp) / normalization_factor
            
            # Qiskit's arbitrary state initialization function expects the provided states to be in
            # little endian order, so we can't just put the i-th term into the i-th slot. We actually
            # have to convert i to a little-endian number to figure out which index to put it in.

            # Get i as a big-endian binary string, padded with 0's at the front to match the number of
            # qubits in the register
            big_endian_index_string = bin(i)[2:].zfill(len(qubits))

            # Reverse the bit order
            little_endian_index_string = big_endian_index_string[::-1]

            # Turn it back into an int
            little_endian_index = int(little_endian_index_string, 2)

            # Put the sample into a complex number at that index
            samples[little_endian_index] = complex(sample, 0)

        # Construct the circuit that will put the qubits into the desired state
        circuit.initialize(samples, qubits)


    # ================
	# == Unit Tests ==
	# ================


    def test_1hz_sine_8_samples(self):
        """
        Tests QFT by giving it a sine wave of 1 Hz, with 8 samples, at 8 samples per second.
        """

        self.run_iqft_with_waveform_samples(3, 8, 1, self.prepare_1hz_sine_8_samples, None)


    def test_1hz_cosine_8_samples(self):
        """
        Tests QFT by giving it a cosine wave of 1 Hz, with 8 samples, at 8 samples per second.
        """

        self.run_iqft_with_waveform_samples(3, 8, 1, self.prepare_1hz_cosine_8_samples, None)


    def test_2hz_sine_8_samples(self):
        """
        Tests QFT by giving it a sine wave of 2 Hz, with 8 samples, at 8 samples per second.
        """

        self.run_iqft_with_waveform_samples(3, 8, 2, self.prepare_2hz_sine_8_samples, None)


    def test_2hz_cosine_8_samples(self):
        """
        Tests QFT by giving it a cosine wave of 2 Hz, with 8 samples, at 8 samples per second.
        """

        self.run_iqft_with_waveform_samples(3, 8, 2, self.prepare_2hz_cosine_8_samples, None)

        
    def test_sine(self):
        """
        Tests QFT on a number of sine and cosine waves, ranging in frequency from 1 to 3. It will
	    try each frequency with 8 to 256 samples per second, and 8 to 512 samples (encoded in 3
	    to 9 qubits). 
        """

        print("Running sine and cosine tests with sample rates from 2 to 256 (in powers of 2), " +
              "frequencies from 1 to 3 Hz, and qubit lengths from the sample rate power to 9.")
        for sample_rate_power in range(3, 9):
            sample_rate = 2 ** sample_rate_power
            
            for frequency in range(1, 4):
                for number_of_qubits in range(sample_rate_power, 10):
                    try:
                        prep_args = (frequency, sample_rate, False)
                        self.run_iqft_with_waveform_samples(number_of_qubits, sample_rate, frequency,
                                                            self.prepare_sine_wave_samples, prep_args)
                    except ValueError as error:
                        self.fail(f"Error running sine test for {frequency} Hz, {number_of_qubits} " + 
						      f"qubits ({2^number_of_qubits} samples), {sample_rate} samples per second: " +
                              repr(error))

                    try:
                        prep_args = (frequency, sample_rate, True)
                        self.run_iqft_with_waveform_samples(number_of_qubits, sample_rate, frequency,
                                                            self.prepare_sine_wave_samples, prep_args)
                    except ValueError as error:
                        self.fail(f"Error running cosine test for {frequency} Hz, {number_of_qubits} " + 
						      f"qubits ({2^number_of_qubits} samples), {sample_rate} samples per second: " +
                              repr(error))

        print("Passed!")


    def test_period_6(self):
        """
        Tests QFT by running a single iteration of the period-finding subroutine from
	    Shor's algorithm. This test will use 21 as the number to factor, 11 as the
	    original guess, and ensure that QFT reports that the modular exponential
	    equation has a period of 6.
        """

        # So this test basically just runs a hardcoded iteration of the quantum portion
		# of Shor's algorithm. I don't want to explain the entire thing here; you can
		# look at shor.py for my implementation, which has plenty of documentation
		# attached to it. For this test, I'm trying to factor 21. That means the
		# "output" register needs to be 5 qubits (because 2^4 = 16 and 2^5 = 32, so it
		# needs 5 qubits to be represented in binary). For the input register, I'm going
		# with 9 qubits: 21^2 = 441, 2^8 = 256, and 2^9 = 512, so 21^2 needs 9 qubits to
		# be represented in binary. That will give 512 discrete states. For a guess of
		# 11, the period will be 6:
		# -------------------------
		#  State (i) | 11^i mod 21
		# -------------------------
		#          0 | 1
		#          1 | 11
		#          2 | 16
		#          3 | 8
		#          4 | 4
		#          5 | 2
		#          6 | 1	<== Pattern repeats here, after 6 entries
		#          7 | 11
		#          8 | 16
		#          ...
		#
		# QFT should return some value X which, when divided by 512, should be really
		# close to 0/6, 1/6, 2/6, 3/6, 4/6, or 5/6. The amplitude peaks (the expected
		# values) are 0, 85, 171, 256, 341, and 427.

        input_length = 9
        output_length = 5
        number_to_factor = 21
        guess = 11

        input = QuantumRegister(input_length)
        output = QuantumRegister(output_length)
        measurement = ClassicalRegister(input_length)
        circuit = QuantumCircuit(input, output, measurement)

        circuit.h(input)                    # Input = |+...+>
        circuit.x(output[output_length-1])  # Output = |0...01>

        # Do the arithmetic so the input register is entangled with the output register; after
		# this, if the state X is measured on the input register, the output register will always
		# be measured as 11^X mod 21.
        for i in range(0, input_length):
            power_of_two = input_length - 1 - i
            power_of_guess = 2 ** power_of_two
            constant = pow(guess, power_of_guess, number_to_factor)
            shor_math.controlled_modular_multiply(circuit, input[i], constant, 
                                                  number_to_factor, output)

        # Run inverse QFT (the analog of the normal DFT) to find the period
        qft.iqft(circuit, input)
        circuit.measure(input, measurement)

        # Run the circuit
        simulator = Aer.get_backend("qasm_simulator")
        simulation = execute(circuit, simulator, shots=1)
        result = simulation.result()
        counts = result.get_counts(circuit)
        measurement = 0
        for(state, count) in counts.items():
            state = state[::-1]
            measurement = int(state, 2)
            break

        # Measure the resulting period and make sure it's close to a multiple of 1/6,
        # with a tolerance of 0.01.
        scaled_measurement = measurement / 512 * 6
        nearest_multiple = round(scaled_measurement)
        delta = abs(scaled_measurement - nearest_multiple)

        print(f"Measured {measurement}/512 => {scaled_measurement}, delta = {delta}")
        if delta >= 0.01:
            self.fail(f"QFT failed, delta of {delta} is too high.")
            
        print("Passed!")


    
if __name__ == '__main__':
    unittest.main()
