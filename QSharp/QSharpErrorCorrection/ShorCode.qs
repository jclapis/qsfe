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


// This file contains the implementation and tests for Shor's 9-qubit error
// correction algorithm. It employs 8 extra qubits to protect 1 original qubit,
// and can recover from one bit flip and/or one phase flip (not necessarily on
// the same qubit).
// See the paper at https://arxiv.org/pdf/0905.2794.pdf for more details.
namespace QSharpErrorCorrection.Shor
{
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Characterization;
	open QSharpErrorCorrection.Testing;


	// ==============================
	// == Algorithm Implementation ==
	// ==============================


	/// # Summary
	/// Creates an error-protected qubit, wrapping the original with 8 spares that
	/// protect against bit and/or phase flips.
	/// 
	/// # Input
	/// ## Original
	/// The original qubit to protect. It can be in an arbitrary state A|0> + B|1>.
	/// 
	/// ## Spares
	/// The eight ancilla qubits to use in the QEC algorithm.
	/// They should be |0...0>.
	operation PrepareFullRegister(Original : Qubit, Spares : Qubit[]) : Unit
	{
		body (...)
		{
			// Construct the error-corrected register, based on the canonical algorithm.
			// Note the use of the helper function "ApplyToEachA" and the use of partial
			// functions like CNOT(XYZ, _) here. I may as well abuse as much of the Q#
			// syntax and library as I can, so the differences between this and the
			// other software frameworks are really clear.
			ApplyToEachA( CNOT(Original, _), Spares[2..3..5] ); // CNOT Original on q2 and q5
			ApplyToEachA( H, [Original, Spares[2], Spares[5]] ); // H on Original, q2, q5
			ApplyToEachA( CNOT(Original, _), Spares[0..1] );
			ApplyToEachA( CNOT(Spares[2], _), Spares[3..4] );
			ApplyToEachA( CNOT(Spares[5], _), Spares[6..7] );
		}

		adjoint invert; // Note this is adjoint so we can run it in
						// reverse to undo it, and get back to |0...0>
						// at the end of the test.
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
	/// must be of size 9 for this algorithm.
    operation EnsureCorrectState(Register : Qubit[]) : Unit
    {
		// Make sure the register has 9 qubits, just for good practice.
        EqualityFactI(Length(Register), 9,
			$"The register must have 9 qubits, but it had {Length(Register)}.");

		// Run the error detection algorithm - first, look at the 3 blocks
		// (q0-q2, q3-q5, and q6-q8) to make sure there are no bit flips on any
		// of their qubits. Next, look for a phase flip between any 2 blocks and
		// correct that if it exists.
		CorrectBitFlips(Register[0..2], 0);
		CorrectBitFlips(Register[3..5], 3);
		CorrectBitFlips(Register[6..8], 6);
		// CorrectPhaseFlips_Canonical(Register);
		CorrectPhaseFlips_JointMeasurement(Register);
    }

	/// # Summary
	/// Checks to see if any one block of 3 qubits in the given register has suffered
	/// a phase flip, and corrects it accordingly.
	/// 
	/// # Input
	/// ## Register
	/// The register of 9 qubits that represent the error-corrected version of the
	/// original logical qubit.
	/// 
	/// # Remarks
	/// This is the canonical implementation of the phase correction part of the Shor
	/// algorithm, as defined in this paper: https://arxiv.org/pdf/0905.2794.pdf.
	/// It should be fairly adaptable to any software framework, because all it really uses
	/// is H, CNOT, M, X, and Z. Any frameworks worth their salt should be able to deal with
	/// these gates.
	operation CorrectPhaseFlips_Canonical(Register : Qubit[]) : Unit
	{
		using(phaseQubits = Qubit[2])
		{
			// Run the phase queries on the three qubit blocks. Apparently Hadamarding, and CNOT'ing
			// all 6 qubits in any two blocks against an ancilla, then Hadamarding again, gives you the
			// phase parity between those two blocks.
			ApplyToEach(H, Register);
			ApplyToEach( CNOT(_, phaseQubits[0]), Register[0..5] ); // CNOT blocks 0 and 1
			ApplyToEach( CNOT(_, phaseQubits[1]), Register[0..2] + Register[6..8] ); // CNOT blocks 0 and 2
			ApplyToEach(H, Register);

			// If two blocks have different phases, the ancilla measurement will be One.
			// We can use that to figure out which block, if any, is busted.
			let different01 = M(phaseQubits[0]) == One;
			let different02 = M(phaseQubits[1]) == One;

			// Check if blocks 0 or 1 are broken
			if(different01)
			{
				X(phaseQubits[0]); // Reset the ancilla to 0, since Q# requires all qubits allocated
								   // with a "using" block to be 0 at the end of its scope. This is
								   // just cleanup, it doesn't impact the function at all.
				if(different02)
				{
					// If 01 and 02 returned 1, that means 0 is different from 1 and 2 so it's broken.
					X(phaseQubits[1]); // Qubit cleanup, same as above
					Message($"Detected a flipped phase on block 0! Correcting it.");
					Z(Register[0]); // According to the paper, it doesn't matter which qubit in the busted
									// block you do the phase flip on. If any of them are busted, you can
									// just pick any of the 3 and phase flip it, and the block will be fixed.
				}
				else
				{
					// 1 is busted, because 01 are different but 02 are the same.
					Message($"Detected a flipped phase on block 1! Correcting it.");
					Z(Register[3]);
				}
			}
			// 0 and 1 are fine, check block 2
			elif(different02)
			{
				X(phaseQubits[1]); // Qubit cleanup, same as above
				Message($"Detected a flipped phase on block 2! Correcting it.");
				Z(Register[6]);
			}
		}
	}

	/// # Summary
	/// Checks to see if any one block of 3 qubits in the given register has suffered
	/// a phase flip, and corrects it accordingly.
	/// 
	/// # Input
	/// ## Register
	/// The register of 9 qubits that represent the error-corrected version of the
	/// original logical qubit.
	/// 
	/// # Remarks
	/// This is the cleaner, Q#-style way of doing the phase flip correction
	/// that leverages joint measurements. When you joint measure a bunch of qubits
	/// against PauliX instead of PauliZ, it checks the parity of their phases rather
	/// than their 0 vs 1 states.
	operation CorrectPhaseFlips_JointMeasurement(Register : Qubit[]) : Unit
	{
		// Do a joint measurement of the X axis on blocks 0 and 1, and again on
		// 0 and 2. This will tell us if the block pairs have any phase
		// descrepancies.
		let xArray = [PauliX, PauliX, PauliX, PauliX, PauliX, PauliX];
		let different01 = Measure(xArray, Register[0..5]) == One; // Blocks 0 and 1
		let different02 = Measure(xArray, Register[0..2] + Register[6..8] ) == One; // Blocks 0 and 2

		if(different01)
		{
			if(different02)
			{
				Message($"Detected a flipped phase on block 0! Correcting it.");
				Z(Register[0]); 
			}
			else
			{
				Message($"Detected a flipped phase on block 1! Correcting it.");
				Z(Register[3]);
			}
		}
		elif(different02)
		{
			Message($"Detected a flipped phase on block 2! Correcting it.");
			Z(Register[6]);
		}
	}

	/// # Summary
	/// Checks to see if any one qubit in the given block has suffered
	/// a bit flip, and corrects it accordingly.
	/// 
	/// # Input
	/// ## Block
	/// The qubit array representing the logical qubit block being checked. It
	/// must be of size 3 for this algorithm.
	/// 
	/// ## Offset
	/// The offset of the block in the parent register (for logging purposes)
	/// 
	/// # Remarks
	/// This is derived from the BitFlipCode test, so see that for more
	/// details on what this is doing if it's not immediately obvious.
	operation CorrectBitFlips(Block : Qubit[], Offset : Int) : Unit
	{
		// Get the parity checks for the first group (q0 and q1) and the second (q0 and q2)
		let different01 = MeasureAllZ(Block[0..1]) == One;
		let different02 = MeasureAllZ(Block[0..2..2]) == One;

		// Correct any errors
		if(different01)
		{
			if(different02)
			{
				// 0 is different from 1 and 2, so it's broken
				Message($"Detected a flipped qubit at position {Offset}! Correcting it.");
				X(Block[0]);
			}
			else
			{
				// 1 is different from 0 and 2, so it's broken
				Message($"Detected a flipped qubit at position {Offset + 1}! Correcting it.");
				X(Block[1]);
			}
		}
		elif(different02)
		{
			// 2 is different from 0 and 1, so it's broken
			Message($"Detected a flipped qubit at position {Offset + 2}! Correcting it.");
			X(Block[2]);
		}
	}
	

	// ====================
	// == Test Case Code ==
	// ====================


	/// # Summary
	/// Runs the Shor code test.
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
	operation ShorTest(EnableBitFlip : Bool, EnablePhaseFlip : Bool, TestDescription : String) : Unit
	{
		let numberOfRandomTests = 25;
		let testStates = GenerateTestStates(numberOfRandomTests); // Generate a bunch of arbitrary
																  // initial states to put the qubit in
		let registerPrepFunction = RegisterPrepFunctionType(PrepareFullRegister);
		let correctionFunction = CorrectionFunctionType(EnsureCorrectState);

		Message($"Running {Length(testStates)} {TestDescription} tests...");
		for(i in 0..Length(testStates) - 1)
		{
			RunTestsWithInitialState(
				9,
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
	/// Runs the test without any errors (just to make sure it behaves properly when
	/// nothing wrong actually happened to the bits).
	operation T1_NoFlip_Test() : Unit
	{
		ShorTest(false, false, "normal (no error)");
	}
	
	/// # Summary
	/// Runs the bit flip tests while leaving the phase unchanged.
	operation T2_BitFlip_Test() : Unit
	{
		ShorTest(true, false, "bit flip");
	}
	
	/// # Summary
	/// Runs the phase flip tests without flipping the actual bits.
	operation T3_PhaseFlip_Test() : Unit
	{
		ShorTest(false, true, "phase flip");
	}

	/// # Summary
	/// Runs tests where there will be both one bit flip and one phase flip.
	operation T4_Combo_Test() : Unit
	{
		ShorTest(true, true, "combo");
	}

}
