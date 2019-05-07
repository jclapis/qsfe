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


// This file contains tests for the canonical implementations of the bit flip
// and Steane error correction codes (3-bit and 7-bit codes, respectively) that
// are included in Q#. The tests ensure that the canon code works properly and
// demonstrates how to use it, which is something that the documentation doesn't
// really cover.
namespace QSharpErrorCorrection.Canon
{
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.ErrorCorrection;
	open QSharpErrorCorrection.Testing;


	// ===================
	// == Bit Flip Code ==
	// ===================

	
	/// # Summary
	/// Creates an error-protected qubit, transforming A|000> + B|100> into
	/// A|000> + B|111> which will be used for the 3-qubit error correction code.
	/// 
	/// # Input
	/// ## Original
	/// The original qubit to protect. It can be in an arbitrary state A|0> + B|1>.
	/// 
	/// ## Spares
	/// The two ancilla qubits to use in the QEC algorithm. They should be |00>.
	operation PrepareRegister_BitFlip(Original : Qubit, Spares : Qubit[]) : Unit
    {
		body(...)
		{
			BFEncoderImpl(false, [Original], Spares);
		}
		adjoint invert;
    }
	
	/// # Summary
	/// Ensures that all of the provided qubits are in the same state.
	/// This will correct for a single bit flip error if one is present.
	/// 
	/// # Input
	/// ## Register
	/// The qubit array representing the logical qubit being checked. It
	/// must be of size 3 for this algorithm.
	operation EnsureCorrectState_BitFlip(Register : Qubit[]) : Unit
    {
		let (encoder, decoder, bitFlipChecker) = (BitFlipCode())!;
		let logicalRegister = LogicalRegister(Register);

		// Run the bit flip check, and see if any of the syndrome measurements
		// disagree with the others. Note that the measurements they use are 
		// 0 vs 1 and 1 vs 2, instead of 0 vs 1 and 0 vs 2 like my implementation
		// used.
		let bitFlipResult = bitFlipChecker!(logicalRegister);
		let different01 = bitFlipResult![0] == One;
		let different12 = bitFlipResult![1] == One;

		// Perform the correction (note the slightly different order due to the
		// fact that they use 0 vs 1 and 1 vs 2 measurements)
		if(different01)
		{
			if(different12)
			{
				Message($"Detected a flipped qubit at position 1! Correcting it.");
				X(Register[1]); // 1 is different from 0 and 2, so it's broken
			}
			else
			{
				Message($"Detected a flipped qubit at position 0! Correcting it.");
				X(Register[0]); // 0 is different from 1 and 2, so it's broken
			}
		}
		elif(different12)
		{
			Message($"Detected a flipped qubit at position 2! Correcting it.");
			X(Register[2]); // 2 is different from 0 and 1, so it's broken
		}
	}


	// =================
	// == Steane Code ==
	// =================


	/// # Summary
	/// Creates an error-protected qubit, wrapping the original with 6 spares that
	/// protect against bit and/or phase flips.
	/// 
	/// # Input
	/// ## Original
	/// The original qubit to protect. It can be in an arbitrary state A|0> + B|1>.
	/// 
	/// ## Spares
	/// The six ancilla qubits to use in the QEC algorithm.
	/// They should be |0...0>.
    operation PrepareRegister_Steane(Original : Qubit, Spares : Qubit[]) : Unit
    {
		body(...)
		{
			SteaneCodeEncoderImpl([Original], Spares);
		}
		adjoint invert;
    }

	/// # Summary
	/// Ensures that all of the provided qubits are in the same state.
	/// This will correct for a single bit flip and/or a single phase
	/// flip error if one is present. The bit flip and phase flip don't
	/// need to be on the same qubit.
	/// 
	/// # Input
	/// ## Register
	/// The qubit array representing the logical qubit being checked. It
	/// must be of size 7 for this algorithm.
	operation EnsureCorrectState_Steane(Register : Qubit[]) : Unit
    {
		// Note that the phase flip and bit flip checkers are backwards in the Canon
		// implementation when compared to mine, so the phase flip checker is returned first.
		let (encoder, decoder, phaseFlipChecker, bitFlipChecker) = (SteaneCode())!;
		let logicalRegister = LogicalRegister(Register);

		// This runs the bit and phase flip checks, returning the results in an array of 3
		// measurements each (very similar to my implementation).
		let bitFlipResult = bitFlipChecker!(logicalRegister);
		let phaseFlipResult = phaseFlipChecker!(logicalRegister);

		// Correct for bit flips
		let bitFlipIndex = DetermineBrokenQubit_Steane(bitFlipResult);
		if(bitFlipIndex >= 0)
		{
			Message($"Detected a flipped qubit at position {bitFlipIndex}! Correcting it.");
			X(Register[bitFlipIndex]);
		}

		// Correct for phase flips
		let phaseFlipIndex = DetermineBrokenQubit_Steane(phaseFlipResult);
		if(phaseFlipIndex >= 0)
		{
			Message($"Detected a flipped phase on qubit {phaseFlipIndex}! Correcting it.");
			Z(Register[phaseFlipIndex]);
		}
    }
	
	/// # Summary
	/// Determines the index of a faulty qubit based on measurements of the Steane code syndrome
	/// measurement qubits (the ancilla).
	/// This index is the same for the bit flip and phase flip measurements, as long as both use
	/// the same blocks (the same qubits in the error-corrected register).
	/// 
	/// # Input
	/// ## CheckResult
	/// The syndrome measurement to interpret.
	/// 
	/// # Output
	/// The 0-based index of the broken qubit, or -1 if none of the qubits are broken.
	operation DetermineBrokenQubit_Steane(CheckResult : Syndrome) : Int
	{
		// This is similar to my own Steane implementation, but in this case, the measurement
		// is already done. All that's left to do is figure out which qubit is broken based
		// on the syndrome measurement results, and the math here is identical. See my
		// implementation for details on this code.
		let syndrome2 = CheckResult![0] == One ? 1 | 0;
		let syndrome1 = CheckResult![1] == One ? 1 | 0;
		let syndrome0 = CheckResult![2] == One ? 1 | 0;

		mutable brokenIndex = 0;
		set brokenIndex = brokenIndex ||| syndrome2;
		set brokenIndex = brokenIndex ||| (syndrome1 <<< 1);
		set brokenIndex = brokenIndex ||| (syndrome0 <<< 2);

		return brokenIndex - 1;
	}
	

	// ====================
	// == Test Case Code ==
	// ====================

	
	/// # Summary
	/// Runs a series of tests on the provided error correction functions using various states for the
	/// initial input qubit.
	/// 
	/// # Input
	/// ## EnableBitFlip
	/// True to enable bit flipping during the tests, false to disable it so no bits are flipped.
	/// 
	/// ## EnablePhaseFlip
	/// True to enable phase flipping during the tests, false to disable it so no phases are flipped.
	/// 
	/// ## TestDescription
	/// A simple description of what this test will be checking for.
	/// 
	/// ## RegisterPrepFunction
	/// A function that will prepare the logical qubit register, turning the original
	/// single unprotected qubit into an error-corrected array of qubits.
	/// 
	/// ## CorrectionFunction
	/// The error correction function that will evaluate the qubit register, detect any
	/// errors, and correct them in-place.

	/// ## NumberOfQubits
	/// The total number of qubits that the error code is expecting (the original 
	/// qubit and all of the spare qubits)
	operation RunTest(
		EnableBitFlip : Bool, 
		EnablePhaseFlip : Bool, 
		TestDescription : String,
		RegisterPrepFunction : ((Qubit, Qubit[]) => Unit is Adj),
		CorrectionFunction : (Qubit[] => Unit),
		NumberOfQubits: Int
	) : Unit
	{
		let numberOfRandomTests = 25;
		let testStates = GenerateTestStates(numberOfRandomTests); // Generate a bunch of arbitrary
																  // initial states to put the qubit in
		let registerPrepFunction = RegisterPrepFunctionType(RegisterPrepFunction);
		let correctionFunction = CorrectionFunctionType(CorrectionFunction);

		Message($"Running {Length(testStates)} {TestDescription} tests...");
		for(i in 0..Length(testStates) - 1)
		{
			RunTestsWithInitialState(
				NumberOfQubits,
				testStates[i],
				registerPrepFunction,
				correctionFunction,
				EnableBitFlip,
				EnablePhaseFlip
			);
		}
		Message("Done! All tests passed.");
	}

	/// # Summary
	/// Tests the bit flip code without any errors (just to make sure it behaves properly when
	/// nothing wrong actually happened to the bits).
	operation BitFlip_NoFlip_Test() : Unit
	{
		RunTest(false, false, "bit flip code, normal (no error)", PrepareRegister_BitFlip, EnsureCorrectState_BitFlip, 3);
	}
	
	/// # Summary
	/// Tests the bit flip code by flipping a bit.
	operation BitFlip_Flip_Test() : Unit
	{
		RunTest(true, false, "bit flip code, bit flip", PrepareRegister_BitFlip, EnsureCorrectState_BitFlip, 3);
	}

	/// # Summary
	/// Tests the Steane code without any errors (just to make sure it behaves properly when
	/// nothing wrong actually happened to the bits).
	operation Steane_NoFlip_Test() : Unit
	{
		RunTest(false, false, "Steane code, normal (no error)", PrepareRegister_Steane, EnsureCorrectState_Steane, 7);
	}
	
	/// # Summary
	/// Tests the Steane code by flipping a bit while leaving the phase unchanged.
	operation Steane_BitFlip_Test() : Unit
	{
		RunTest(true, false, "Steane code, bit flip", PrepareRegister_Steane, EnsureCorrectState_Steane, 7);
	}
	
	/// # Summary
	/// Tests the Steane code by flipping the phase without flipping the actual bits.
	operation Steane_PhaseFlip_Test() : Unit
	{
		RunTest(false, true, "Steane code, phase flip", PrepareRegister_Steane, EnsureCorrectState_Steane, 7);
	}
	
	/// # Summary
	/// Tests the Steane code with one bit flip and one phase flip.
	operation Steane_Combo_Test() : Unit
	{
		RunTest(true, true, "Steane code, combo", PrepareRegister_Steane, EnsureCorrectState_Steane, 7);
	}
}
