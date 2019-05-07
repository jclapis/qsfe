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


// This file contains the implementation and tests for as simple 3-qubit error
// correction algorithm. It employs 2 extra qubits to protect 1 original qubit,
// and can recover from one bit flip on any qubit (but does not offer any phase
// flip protection).
// See the paper at https://arxiv.org/pdf/0905.2794.pdf for more details.
namespace QSharpErrorCorrection.BitFlip
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
	/// Creates an error-protected logical qubit, transforming A|000> + B|100> into
	/// A|000> + B|111> which will be used for the 3-qubit error correction code.
	/// 
	/// # Input
	/// ## Original
	/// The original qubit to protect. It can be in an arbitrary state A|0> + B|1>.
	/// 
	/// ## Spares
	/// The two ancilla qubits to use in the QEC algorithm. They should be |00>.
	operation PrepareFullRegister(Original : Qubit, Spares : Qubit[]) : Unit
	{
		body (...)
		{
			// Construct the error-corrected register, based on the canonical algorithm
			CNOT(Original, Spares[0]);
			CNOT(Original, Spares[1]);
		}

		adjoint invert; // Note this is adjoint so we can run it in
						// reverse to undo it, and get back to |000>
						// at the end of the test.
	}


	/// # Summary
	/// Ensures that all of the provided qubits are in the same state.
	/// This will correct for a single bit flip error if one is present.
	/// 
	/// # Input
	/// ## Register
	/// The qubit array representing the logical qubit being checked. It
	/// must be of size 3 for this algorithm.
    operation EnsureCorrectState (Register : Qubit[]) : Unit
    {
		// Make sure the register has 3 qubits, just for good practice.
        EqualityFactI(Length(Register), 3,
			$"The register must have 3 qubits, but it had {Length(Register)}.");

		// Run the error detection algorithm, and flip the broken bit if there is one
		//let detectionResult = ErrorDetection_Canonical(Register);
		let detectionResult = ErrorDetection_JointMeasurements(Register);
		if(detectionResult >= 0)
		{
			Message($"Detected a flipped qubit at position {detectionResult}! Correcting it.");
			X(Register[detectionResult]);
		}
    }
	
	/// # Summary
	/// Checks to see if any of the qubits in the given register have suffered
	/// a bit flip, and disagree with the other two. 
	/// 
	/// # Input
	/// ## Register
	/// The qubit array representing the logical qubit being checked. It
	/// must be of size 3 for this algorithm.
	/// 
	/// # Output
	/// -1 if no error is present,
	/// 0 if the first qubit is flipped (|100> + |011>),
	/// 1 if the second qubit is flipped (|010> + |101>),
	/// 2 if the third qubit is flipped (|001> + |110>).
	/// 
	/// # Remarks
	/// This version uses the standard two ancilla qubit measurement technique,
	/// and is the "traditional" implementation of this algorithm.
	/// See https://arxiv.org/pdf/0905.2794.pdf for information.
	operation ErrorDetection_Canonical(Register : Qubit[]) : Int
	{
		// The plan here is to check if q0 and q1 have the same parity (00 or 11), and if q0 and q2
		// have the same parity. If both checks come out true, then there isn't an error. Otherwise,
		// if one of the checks reveals a parity discrepancy, we can use the other check to tell us
		// which qubit is broken.
		// This could be done with q1 and q2 as well if you wanted to.
		// Here is the table of possibile outcomes:
		// 
		// 01 = 0 and 02 = 0: Everything is the same so this is the correct state.
		// 01 = 0 and 02 = 1: 2 is busted, because 0 & 1 are the same but 0 & 2 are different.
		// 01 = 1 and 02 = 0: 1 is busted, beacuse 0 & 1 are different but 0 & 2 are the same.
		// 01 = 1 and 02 = 1: 0 is busted, because 0 & 1 are different and 0 & 2 are different.
		mutable result = -1;

		using(parityQubits = Qubit[2])
		{
			// This will check to see if q0 and q1 have the same parity.
			// If they're 00 or 11, this will be 0. In the case of 01 or 10,
			// this will be 1 signifying that one of them is broken.
			CNOT(Register[0], parityQubits[0]);
			CNOT(Register[1], parityQubits[0]);
			
			// This will check to see if q0 and q2 have the same parity.
			// Same logic as above.
			CNOT(Register[0], parityQubits[1]);
			CNOT(Register[2], parityQubits[1]);

			// Perform the actual ancilla measurement
			let different01 = M(parityQubits[0]) == One;
			let different02 = M(parityQubits[1]) == One;

			// Check if 0 or 1 is broken
			if(different01)
			{
				X(parityQubits[0]);  // Q# requires that all of the qubits allocated in a "using" block
									 // are reset to Zero before exiting the block, so this is just
									 // cleanup; At this point we know the qubit is One and we don't
									 // need it anymore, so we can just reset it. This doesn't actually
									 // have any effect on the result.
				if(different02)
				{
					X(parityQubits[1]); // Qubit cleanup, same as above
					set result = 0; // 0 is different from 1 and 2, so it's broken
				}
				else
				{
					set result = 1; // 1 is different from 0 and 2, so it's broken
				}
			}
			// 0 and 1 are fine, check if 2 is also fine
			elif(different02)
			{
				X(parityQubits[1]); // Qubit cleanup, same as above
				set result = 2; // 2 is different from 0 and 1, so it's broken
			}
		}

		return result;
	}

	/// # Summary
	/// Checks to see if any of the qubits in the given register have suffered
	/// a bit flip, and disagree with the other two.
	/// 
	/// # Input
	/// ## Register
	/// The qubit array representing the logical qubit being checked. It
	/// must be of size 3 for this algorithm.
	/// 
	/// # Output
	/// -1 if no error is present,
	/// 0 if the first qubit is flipped (|100> + |011>),
	/// 1 if the second qubit is flipped (|010> + |101>),
	/// 2 if the third qubit is flipped (|001> + |110>).
	/// 
	/// # Remarks
	/// This version uses joint measurements to do the check, instead of the
	/// traditional algorithm.
	operation ErrorDetection_JointMeasurements(Register : Qubit[]) : Int
	{
		// This is a Q#-specific technique which leverages the general-purpose "Measure" function to
		// do a joint measurement. That means we can pull some information about the relationship between
		// two or more qubits out of them, without actually changing their state. In this case, we're going
		// to do a ZxZ measurement against two qubits which tells us if they have the same parity (00 or 11)
		// or if they have inverse parity (01 or 10).
		// The plan is to do 2 of these measurements: one on q0 and q1, and one on q0 and q2.
		// Here is the table of possibile outcomes:
		// 
		// 01 = 0 and 02 = 0: Everything is the same so this is the correct state.
		// 01 = 0 and 02 = 1: 2 is busted, because 0 & 1 are the same but 0 & 2 are different.
		// 01 = 1 and 02 = 0: 1 is busted, beacuse 0 & 1 are different but 0 & 2 are the same.
		// 01 = 1 and 02 = 1: 0 is busted, because 0 & 1 are different and 0 & 2 are different.

		let different01 = MeasureAllZ(Register[0..1]) == One; // Run ZxZ on q0 and q1
		let different02 = MeasureAllZ(Register[0..2..2]) == One; // Q# range syntax: start at 0, increment by 2, stop at 2.
															     // AKA give me an array with only q0 and q2 in it.

		if(different01)
		{
			if(different02)
			{
				return 0; // 0 is different from 1 and 2, so it's broken
			}
			else
			{
				return 1; // 1 is different from 0 and 2, so it's broken
			}
		}
		elif(different02)
		{
			return 2; // 2 is different from 0 and 1, so it's broken
		}

		return -1; // Correct state
	}


	// ====================
	// == Test Case Code ==
	// ====================
	

	/// # Summary
	/// Runs the Bit Flip code test.
	/// 
	/// # Input
	/// ## EnableBitFlip
	/// True to enable bit flipping during the tests, false to disable it so no bits are flipped.
	/// 
	/// ## TestDescription
	/// A simple description of what this test will be checking for.
	operation BitFlipTest(EnableBitFlip : Bool, TestDescription : String) : Unit
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
				3,
				testStates[i],
				registerPrepFunction,
				correctionFunction,
				EnableBitFlip,
				false
			);
		}
		Message("Done! All tests passed.");
	}
	
	/// # Summary
	/// Runs the test without any errors (just to make sure it behaves properly when
	/// nothing wrong actually happened to the bits).
	operation T1_NoFlip_Test() : Unit
	{
		BitFlipTest(false, "normal (no error)");
	}

	/// # Summary
	/// Runs the bit flip tests on each qubit.
	operation T2_Flip_Test() : Unit
	{
		BitFlipTest(true, "bit flip");
	}

}
