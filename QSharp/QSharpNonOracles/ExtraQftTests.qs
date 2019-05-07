// ========================================================================
// Copyright (C) 2019 The MITRE Corporation.
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ========================================================================


// This file contains extra tests for QFT, including some customized
// implementations of a few simple sine and cosine sampling vectors. These
// could be handy when testing other frameworks that don't come with an
// analog of the "PrepareArbitraryState" function or the Ry(...) function,
// so I can just directly implement circuits that put the register into the
// proper states for these tests.
namespace QSharpNonOracles.Qft
{
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	

	// ====================
	// == Test Case Code ==
	// ====================
	

	/// # Summary
	/// Prepares a register so that the real component of each state's amplitude
	/// corresponds to a sine wave with a 1 Hz frequency, f(x) = sin(2πx). The 8
	/// possible states of the register will take on the role of the time steps
	/// from 0 to 7/8 of a second.
	/// For a classical DFT, the input would be the following array:
	/// [0, 0.707, 1, 0.707, 0, -0.707, -1, -0.707]
	/// where the first element is for t = 0, the second is for t = 1/8, and so on.
	/// For the quantum variation, these values are encoded into the amplitudes of
	/// each register state (and normalized so the whole vector has a magnitude of
	/// 1). Thus, the total thing will become:
	/// 0.354*|001⟩ + 0.5*|010⟩ + 0.354*|011⟩ - 0.354*|101⟩ - 0.5*|110⟩ - 0.354*|111⟩.
	/// 
	/// # Input
	/// ## Register
	/// The register to prepare with the sine wave state. It must be |000⟩.
	operation Prepare1HzSine_8Samples_Test(Register : Qubit[]) : Unit
	{
		// Sanity checks on the input register
		EqualityFactI(Length(Register), 3, "Register must be 3 qubits.");
		AssertAllZero(Register);

		// Okay. So this algorithm is going to look weird at first considering it has nothing to do with
		// sine waves, and that's fine. I'm going to walk you through how I designed this, step by step.
		// Hopefully you can learn something from it and use it to design your own circuits for weird
		// qubit states!
		// 
		// The original classical array for 8 measurements over 1 second of the sine wave is this:
		// [0, 1/√2, 1, 1/√2, 0, -1/√2, -1, -1/√2]
		// 
		// We want to encode that into the real component of the amplitudes of a 3 qubit register, so we
		// get this:
		// 0*|000⟩ + 1/√2|001⟩ + 1*|010⟩ + 1/√2*|011⟩ + 0*|100⟩ - 1/√2*|101⟩ - 1*|110⟩ - 1/√2*|111⟩
		// 
		// Immediately, there's a problem: these amplitudes are too big. Quantum state vectors need the
		// sum of squares to add to 1, and these add to:
		// 2*(1/√2)^2 + 2*1^2 + 2*(-1/√2)^2
		// = 2*1/2 + 2*1 + 2*1/2
		// = 4
		// So to fix this, we need to divide each state's probability by 4 (and thus, each state's
		// amplitude by √4 = 2.
		// This is the target state once it's been normalized:
		// 0*|000⟩ + 1/2√2*|001⟩ + 1/2*|010⟩ + 1/2√2*|011⟩ + 0*|100⟩ - 1/2√2*|101⟩ - 1/2*|110⟩ - 1/2√2*|111⟩
		// = 1/2( 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩ - 1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩ )
		// 
		// Now that we have the target state, we can start designing a circuit for it.
		// The first thing I notice about the general structure of the state is that it's really in two
		// halves: when q0 = 0, it's 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩.
		// when q0 = 1, it's -1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩.
		// The second half is just the negative version of the first half (with q0 flipped), so I know
		// 2 things:
		//		1. q0 isn't entangled with anything
		//		2. q0 is in an equal superposition of |0⟩ and |-1⟩.
		// Thus, we can reduce q0 to the |-⟩ state which is 1/√2*(|0⟩ - |1⟩). We know that whatever else
		// happens, we're going to put q0 into |-⟩ at the start of the circuit and ignore it after that.
		// Here's the reduction:
		// 1/2( 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩ - 1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩ )
		// = 1/2( √2*1/√2( 1/√2*|001⟩ + |010⟩ + 1/√2*|011⟩ - 1/√2*|101⟩ - |110⟩ - 1/√2*|111⟩ ) )
		// = 1/2( √2( 1/√2*|-01⟩ + |-10⟩ + 1/√2*|-11⟩ ) )
		// = 1/2( |-01⟩ + √2*|-10⟩ + |-11⟩ )
		// 
		// Okay, now we're getting somewhere. Next, I notice that when q2 is 1, q1 has an equal
		// probability of being |0⟩ or |1⟩. It might be more obvious if I rearrange the terms like this:
		// = 1/2( |-01⟩ + |-11⟩ + √2*|-10⟩ )
		// 
		// In other words, when q2 is 1, q1 = |+⟩ which is 1/√2*(|0⟩ + |1⟩). Let's use that to reduce the
		// qubit state even further:
		// 1/2( |-01⟩ + |-11⟩ + √2*|-10⟩ )
		// = 1/2( √2*1/√2( |-01⟩ + |-11⟩ ) + √2*|-10⟩ )
		// = 1/2( √2( |-+1⟩ ) + √2*|-10⟩ )
		// = √2/2( |-+1⟩ + |-10⟩ )
		// = 1/√2( |-+1⟩ + |-10⟩ )
		//
		// This is as far as the reduction can go. You might think that you can reduce q2 into |+⟩ here,
		// but note that the state of qubit 1 changes depending on what qubit 2 is. That means we can't
		// reduce it; it also means that q1 and q2 are going to be entangled.
		// Anyway, now that the state is reduced, we can figure out how to create the states with a
		// circuit. We know that q0 is going to be |-⟩ no matter what, so that's easy: X and H will put
		// it into that state, and then we can ignore it. The other two qubits are then described by
		// this state:
		// 1/√2( |+1⟩ + |10⟩ )
		// 
		// q2 has an equal probability of being |0⟩ or |1⟩ (probability 1/√2), so it can just be prepared
		// with a simple H.
		// Now for q1, the weird one: assuming it starts at |0⟩, then if q2 == 1, q1 should be Hadamard'd.
		// If q2 == 0, then q1 should be flipped instead. That's actually pretty easy to do: we can just
		// do a Controlled H with q2 as the control and q1 as the target, and a zero-controlled X (AKA a
		// 0-CNOT) with q2 as the control and q1 as the target. We just have to make sure q2 is H'd first.
		// 
		// And thus, at the end of the day, this is how you construct a 3-qubit state where the real part
		// of the amplitudes maps to a 1 Hz sine wave, sampled at 8 samples per second:

		// Set up q0
		X(Register[0]);
		H(Register[0]);

		// Set up q2
		H(Register[2]);

		// Set up q1: if q2 is 1, H it. Otherwise, X it.
		Controlled H([Register[2]], Register[1]);

		// 0-controlled CNOT
		X(Register[2]);
		CNOT(Register[2], Register[1]);
		X(Register[2]);

		// I hope that writeup helped explain how these 7 lines create the sine wave, and help you do
		// circuit design like this in the future!
	}

	/// # Summary
	/// Prepares a register so that the real component of each state's amplitude
	/// corresponds to a cosine wave with a 1 Hz frequency, f(x) = cos(2πx). The 8
	/// possible states of the register will take on the role of the time steps
	/// from 0 to 7/8 of a second.
	/// For a classical DFT, the input would be the following array:
	/// [1, 0.707, 0, -0.707, -1, -0.707, 0, 0.707]
	/// where the first element is for t = 0, the second is for t = 1/8, and so on.
	/// For the quantum variation, these values are encoded into the amplitudes of
	/// each register state (and normalized so the whole vector has a magnitude of
	/// 1). Thus, the total thing will become:
	/// 0.5*|000⟩ + 0.354*|001⟩ - 0.354*|011⟩ - 0.5*|100⟩ - 0.354*|101⟩ + 0.354*|111⟩.
	/// 
	/// # Input
	/// ## Register
	/// The register to prepare with the cosine wave state. It must be |000⟩.
	operation Prepare1HzCosine_8Samples_Test(Register : Qubit[]) : Unit
	{
		// Sanity checks on the input register
		EqualityFactI(Length(Register), 3, "Register must be 3 qubits.");
		AssertAllZero(Register);

		// This operation is going to look quite different from the sine example, but that's okay. The
		// structure itself isn't really that important - the key is the methodology that lets you figure
		// out a circuit to generate the state you're looking for. The process for this one is the same,
		// so this is just going to be another example of it. I'll walk you through it.
		// 
		// First things first: here's the conventional array of samples from cos(2πx) that you'd normally
		// feed into DFT:
		// [1, 1/√2, 0, -1/√2, -1, -1/√2, 0, 1/√2]
		// 
		// Using the same normalization process as before, so this can be represented in qubits, gives us:
		// 1/2*|000⟩ + 1/2√2*|001⟩ + 0*|010⟩ - 1/2√2*|011⟩ - 1/2*|100⟩ - 1/2√2*|101⟩ + 0*|110⟩ + 1/2√2*|111⟩
		// = 1/2( |000⟩ + 1/√2*|001⟩ - 1/√2*|011⟩ - |100⟩ - 1/√2*|101⟩ + 1/√2*|111⟩ )
		// 
		// There aren't any immediately obvious patterns with respect to the + and - parts (or at least,
		// I couldn't find any), so I just reorganized it a little bit to group the common parts together:
		// 1/2( |000⟩ - |100⟩ + 1/√2( |001⟩ - |011⟩ - |101⟩ + |111⟩ ) )
		// 
		// Now with this, I do notice a commonality. In the first 2 terms, q2 is always 0. In the last 4
		// terms (the 1/√2 group), q2 is always 1. Both groups have a 50% chance of occurring, so really
		// we could break it down into this algorithm:
		//		H(q2)
		//		if(q2 == 0), put q0 and q1 in the first group
		//		else, put q0 and q1 into the second group
		// Obviously we can't perform a classical "if-else" on qubits in superpositions... but we CAN
		// leverage the Controlled functor which effectively does the same thing!
		// So, with that in mind, let's figure out how to create the groups.
		// 
		// The first group is just [|00⟩ - |10⟩]0⟩, which reduces to √2*|-00⟩. That's easy to write a
		// circuit for: we just do X and H on q0 to put it into the |-⟩ state. So for the first group,
		// we can do this:
		//		if(q2 == 0)... (the gates below will be zero-controlled on q2)
		//		X(q0);
		//		H(q0);
		// 
		// The second group is a little harder: [|00⟩ - |01⟩ - |10⟩ + |11⟩]1⟩. Written as a state vector
		// of q0 and q1, it looks like this: [1, -1, -1, 1]. We need some way to get the qubits into
		// this state. I did a little reverse engineering on it: we know that H on both qubits will give
		// the state [1, 1, 1, 1]. There are 2 negative phases, and we know that Z on q0 would give the
		// state [-1, 1, -1, 1]; Z on q1 would give [1, -1, 1, -1]. We could do either of those but we'd
		// need a way to swap the 1st and 2nd qubits, or the 3rd and 4th terms, respectively.
		// Wait! We have one! CNOT on q0 and q1 will swap the 3rd and 4th terms! So to get this state,
		// we could do the following:
		//		if(q2 == 1)... (the gates below will be controlled on q2)
		//		H(q0);
		//		H(q1);
		//		Z(q1);
		//		CNOT(q0, q1);
		//
		// Finally, note that the last operation of the first group is H(q0) and the first operation of
		// the second group is H(q0), so we can just remove that step from both groups and perform it
		// unconditionally in-between their execution.
		// 
		// You can verify that the amplitudes of each state work out with this setup. I wrote it up below,
		// and lo and behold, it produced the cosine measurement array. I'm sure there's a prettier way to
		// do this that looks more like the sine function, but this is meant to be another good example of
		// how to tackle circuit design to get to a target state.

		// Set up q2
		H(Register[2]);

		// If q2 == 0
		X(Register[2]);
		Controlled X([Register[2]], Register[0]);
		X(Register[2]);

		H(Register[0]);

		// Else if(q2 == 1)
		Controlled X([Register[2]], Register[1]);
		Controlled H([Register[2]], Register[1]);
		CCNOT(Register[2], Register[0], Register[1]);
	}
	
	/// # Summary
	/// Prepares a register so that the real component of each state's amplitude
	/// corresponds to a sine wave with a 2 Hz frequency, f(x) = sin(4πx). The 8
	/// possible states of the register will take on the role of the time steps
	/// from 0 to 7/8 of a second.
	/// For a classical DFT, the input would be the following array:
	/// [0, 1, 0, -1, 0, 1, 0, -1]
	/// where the first element is for t = 0, the second is for t = 1/8, and so on.
	/// For the quantum variation, these values are encoded into the amplitudes of
	/// each register state (and normalized so the whole vector has a magnitude of
	/// 1). Thus, the total thing will become:
	/// 0.5*|001⟩ - 0.5*|011⟩ + 0.5*|101⟩ - 0.5*|111⟩.
	/// 
	/// # Input
	/// ## Register
	/// The register to prepare with the sine wave state. It must be |000⟩.
	operation Prepare2HzSine_8Samples_Test(Register : Qubit[]) : Unit
	{
		// Sanity checks on the input register
		EqualityFactI(Length(Register), 3, "Register must be 3 qubits.");
		AssertAllZero(Register);

		// This one's really easy. Here's the full target state:
		// 1/2( |001⟩ - |011⟩ + |101⟩ - |111⟩ )
		// 
		// Right off the bat: q2 is always 1. Removing it, we get:
		// 1/2( |00⟩ - |01⟩ + |10⟩ - |11⟩ )|1⟩
		// 
		// q0 and q1 are both in uniform superpositions, but the sign is inverted
		// when q1 == 1. It should be pretty obvious that q0 = |+⟩ and q1 = |-⟩, but
		// here's the decomposition anyway:
		// 1/2( |00⟩ - |01⟩ + |10⟩ - |11⟩ )|1⟩
		// = 1/2( √2*1/√2( |00⟩ - |01⟩ + |10⟩ - |11⟩ ))|1⟩
		// = 1/2( √2( |+0⟩ - |+1⟩ ))|1⟩
		// = 1/2( √2*√2*1/√2( |+0⟩ - |+1⟩ ))|1⟩
		// = 1/2( 2( |+-⟩ ))|1⟩
		// = |+-1>
		// 
		// Yep, it reduces down to a single state with no entanglement.

		H(Register[0]);

		X(Register[1]);
		H(Register[1]);
		
		X(Register[2]);
	}

	/// # Summary
	/// Prepares a register so that the real component of each state's amplitude
	/// corresponds to a cosine wave with a 2 Hz frequency, f(x) = cos(4πx). The 8
	/// possible states of the register will take on the role of the time steps
	/// from 0 to 7/8 of a second.
	/// For a classical DFT, the input would be the following array:
	/// [1, 0, -1, 0, 1, 0, -1, 0]
	/// where the first element is for t = 0, the second is for t = 1/8, and so on.
	/// For the quantum variation, these values are encoded into the amplitudes of
	/// each register state (and normalized so the whole vector has a magnitude of
	/// 1). Thus, the total thing will become:
	/// 0.5*|000⟩ - 0.5*|010⟩ + 0.5*|100⟩ - 0.5*|110⟩.
	/// 
	/// # Input
	/// ## Register
	/// The register to prepare with the cosine wave state. It must be |000⟩.
	operation Prepare2HzCosine_8Samples_Test(Register : Qubit[]) : Unit
	{
		// Sanity checks on the input register
		EqualityFactI(Length(Register), 3, "Register must be 3 qubits.");
		AssertAllZero(Register);

		// This is exactly the same as the 2Hz sine, except q2 is 0.

		H(Register[0]);

		X(Register[1]);
		H(Register[1]);
	}
	

	// ================
	// == Unit Tests ==
	// ================
	

	/// # Summary
	/// Tests QFT by giving it a sine wave of 1 Hz, with 8 samples, at 8 samples
	/// per second.
	operation Sine_1Hz_8Samples_Test() : Unit
	{
		TestQftWithWaveformSamples(Prepare1HzSine_8Samples_Test, 3, 8.0, 1.0);
	}

	/// # Summary
	/// Tests QFT by giving it a cosine wave of 1 Hz, with 8 samples, at 8 samples
	/// per second.
	operation Cosine_1Hz_8Samples_Test() : Unit
	{
		TestQftWithWaveformSamples(Prepare1HzCosine_8Samples_Test, 3, 8.0, 1.0);
	}

	/// # Summary
	/// Tests QFT by giving it a sine wave of 2 Hz, with 8 samples, at 8 samples
	/// per second.
	operation Sine_2Hz_8Samples_Test() : Unit
	{
		TestQftWithWaveformSamples(Prepare2HzSine_8Samples_Test, 3, 8.0, 2.0);
	}

	/// # Summary
	/// Tests QFT by giving it a cosine wave of 2 Hz, with 8 samples, at 8 samples
	/// per second.
	operation Cosine_2Hz_8Samples_Test() : Unit
	{
		TestQftWithWaveformSamples(Prepare2HzCosine_8Samples_Test, 3, 8.0, 2.0);
	}
}
