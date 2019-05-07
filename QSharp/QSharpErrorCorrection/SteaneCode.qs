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

// This file contains the implementation and tests for Steane's 7-qubit error
// correction algorithm. It employs 6 extra qubits to protect 1 original qubit,
// and can recover from one bit flip and/or one phase flip (not necessarily on
// the same qubit).
// See the paper at https://link.springer.com/article/10.1007/s11128-015-0988-y for
// more details.
// 
// Note that Q# actually has its own version of this code built in:
// https://docs.microsoft.com/en-us/qsharp/api/canon/microsoft.quantum.canon.steanecode
// Here's the source for it:
// https://github.com/Microsoft/QuantumLibraries/blob/master/Canon/src/Qecc/7QubitCode.qs
namespace QSharpErrorCorrection.Steane
{
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	open Microsoft.Quantum.Extensions.Testing;
	open QSharpErrorCorrection.Testing;
	

	// ==============================
	// == Algorithm Implementation ==
	// ==============================


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
	/// 
	/// # Remarks
	/// The circuit for this preparation (called the encoding circuit) can be seen
	/// in Figure 8 of this paper:
	/// https://arxiv.org/pdf/quant-ph/9705031.pdf
	operation PrepareFullRegister(Original : Qubit, Spares : Qubit[]) : Unit
	{
		body (...)
		{
			// Construct the error-corrected register, based on the canonical algorithm.
			// Note the use of the helper function "ApplyToEachA" and the use of partial
			// functions like CNOT(XYZ, _) here. I may as well abuse as much of the Q#
			// syntax and library as I can, so the differences between this and the
			// other software frameworks are really clear.
			ApplyToEachA(H, Spares[3..5]);
			ApplyToEachA( CNOT(Original, _), Spares[0..1]);
			ApplyToEachA( CNOT(Spares[5], _), [Original, Spares[0], Spares[2]]);
			ApplyToEachA( CNOT(Spares[4], _), [Original, Spares[1], Spares[2]]);
			ApplyToEachA( CNOT(Spares[3], _), Spares[0..2]);
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
	/// must be of size 7 for this algorithm.
	/// 
	/// # Remarks
	/// For details on the implementation of this algorithm, please see
	/// the paper at https://link.springer.com/article/10.1007/s11128-015-0988-y.
    operation EnsureCorrectState (Register : Qubit[]) : Unit
    {
		// Make sure the register has 7 qubits, just for good practice.
        EqualityFactI(Length(Register), 7,
			$"The register must have 7 qubits, but it had {Length(Register)}.");

		// This one is pretty simple conceptually, it only has two parts.
		CorrectBitFlips(Register);
		CorrectPhaseFlips(Register);
    }

	/// # Summary
	/// Checks to see if any one qubit in the given register has suffered
	/// a bit flip, and corrects it accordingly.
	/// 
	/// # Input
	/// ## Register
	/// The qubit array representing the logical qubit being checked. It
	/// must be of size 7 for this algorithm.
	operation CorrectBitFlips(Register : Qubit[]) : Unit
	{
		// With 7 qubits, there are 8 possible error states: one for nothing being
		// broken, and one for each qubit being broken. You can encode those 8 numbers
		// into a 3-bit binary number. Steane does exactly this, by organizing the 7
		// qubits into 3 blocks of 4 qubits each and by using 3 ancilla qubits for measurement.
		// The blocks are organized in such a way that 3 of the qubits are unique to any given
		// block, 3 belong to 2 blocks, and the last belongs to all 3 blocks. That way, you
		// can turn the ancilla measurements into the 3-bit binary number that tells you exactly
		// which qubit is broken, and flip it accordingly.
		using(syndromeQubits = Qubit[3])
		{
			// Block 0: 0, 2, 4, 6
			// Block 1: 1, 2, 5, 6
			// Block 2: 3, 4, 5, 6
			ApplyToEachA( CNOT(_, syndromeQubits[0]), Register[0..2..6] );
			ApplyToEachA( CNOT(_, syndromeQubits[1]), Register[1..2] + Register[5..6] );
			ApplyToEachA( CNOT(_, syndromeQubits[2]), Register[3..6] );
			
			// Fix the broken bit if there is one.
			let brokenIndex = DetermineBrokenQubit(syndromeQubits);
			if(brokenIndex >= 0)
			{
				Message($"Detected a flipped qubit at position {brokenIndex}! Correcting it.");
				X(Register[brokenIndex]);
			}
			
			ResetAll(syndromeQubits); // Ancilla cleanup required by Q# in a "using" block
		}
	}
	
	/// # Summary
	/// Checks to see if any one qubit in the given register has suffered
	/// a phase flip, and corrects it accordingly.
	/// 
	/// # Input
	/// ## Register
	/// The qubit array representing the logical qubit being checked. It
	/// must be of size 7 for this algorithm.
	operation CorrectPhaseFlips(Register : Qubit[]) : Unit
	{
		// The rationale here is the same as the bit flip correction above, with two key
		// differences: first, the ancilla qubits are intialized to |+> and read in the X
		// basis. Second, now we're using the ancilla qubits as the controls during the CNOTs
		// instead of the targets. You might ask, how does this make sense? If we're using
		// them as the controls and then just measuring them, how can we possibly get any
		// useful information from the encoded qubit register?
		// Turns out, if one of the register qubits has a phase flip, then that will propagate
		// back to the control qubit during a CNOT. This is called a phase kickback, and it's used
		// all the time in quantum algorithms. Don't believe me? Try it yourself.
		// Do this sequence on your simulator of choice:
		// Start with |00>, then do H(0); CNOT(0, 1); Z(1); CNOT(0, 1); H(0);
		// You'll end up with |10>.
		// Entanglement is black magic. Fun fact: this property is why phase queries work, and
		// how superdense coding actually does something useful.
		using(syndromeQubits = Qubit[3])
		{
			// Block 0: 0, 2, 4, 6
			// Block 1: 1, 2, 5, 6
			// Block 2: 3, 4, 5, 6
			ApplyToEachA(H, syndromeQubits);
			ApplyToEachA( CNOT(syndromeQubits[0], _), Register[0..2..6] );
			ApplyToEachA( CNOT(syndromeQubits[1], _), Register[1..2] + Register[5..6] );
			ApplyToEachA( CNOT(syndromeQubits[2], _), Register[3..6] );
			ApplyToEachA(H, syndromeQubits);

			// Fix the broken bit if there is one.
			let brokenIndex = DetermineBrokenQubit(syndromeQubits);
			if(brokenIndex >= 0)
			{
				Message($"Detected a flipped phase on qubit {brokenIndex}! Correcting it.");
				Z(Register[brokenIndex]);
			}

			ResetAll(syndromeQubits); // Ancilla cleanup required by Q# in a "using" block
		}
	}

	/// # Summary
	/// Determines the index of a faulty qubit based on measurements of the Steane code syndrome
	/// measurement qubits (the ancilla).
	/// This index is the same for the bit flip and phase flip measurements, as long as both use
	/// the same blocks (the same qubits in the error-corrected register).
	/// 
	/// # Input
	/// ## SyndromeQubits
	/// The ancilla qubits used in the error correction algorithm, which should have already
	/// interacted with the error-corrected register and are now ready to be measured.
	/// Measurement will be done in the PauliZ basis here, so adjust the qubits accordingly.
	/// 
	/// # Output
	/// The 0-based index of the broken qubit, or -1 if none of the qubits are broken.
	operation DetermineBrokenQubit(SyndromeQubits : Qubit[]) : Int
	{
		// Perform the ancilla measurement - notice the blocks are organized in MSB order,
		// so this measurement is rearranged to be LSB (i.e. parityQubits[2] actually contains
		// the most significant bit). These will be stored as ints (0 or 1) so we can do some
		// math using them later.
		let syndrome2 = M(SyndromeQubits[0]) == One ? 1 | 0;
		let syndrome1 = M(SyndromeQubits[1]) == One ? 1 | 0;
		let syndrome0 = M(SyndromeQubits[2]) == One ? 1 | 0;

		// Now for the fun part. 
		// Here's the table of possibilities, where each term corresponds to the parity bit index.
		// So for example, 000 means all 3 measurements were 0 and 011 means syndrome1 and syndrome2
		// were measured to be 1.
		// -----------------------
		// 000 = No error
		// 001 = Error or qubit 0
		// 010 = Error on qubit 1
		// 011 = Error on qubit 2
		// 100 = Error on qubit 3
		// 101 = Error on qubit 4
		// 011 = Error on qubit 5
		// 110 = Error on qubit 6
		// 111 = Error on qubit 7
		// -----------------------
		// Rather than do a bunch of if/elses, let's just do some bit shifting to get the proper index.
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
	/// Runs the Steane code test.
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
	operation SteaneTest(EnableBitFlip : Bool, EnablePhaseFlip : Bool, TestDescription : String) : Unit
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
				7,
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
		SteaneTest(false, false, "normal (no error)");
	}
	
	/// # Summary
	/// Runs the bit flip tests while leaving the phase unchanged.
	operation T2_BitFlip_Test() : Unit
	{
		SteaneTest(true, false, "bit flip");
	}
	
	/// # Summary
	/// Runs the phase flip tests without flipping the actual bits.
	operation T3_PhaseFlip_Test() : Unit
	{
		SteaneTest(false, true, "phase flip");
	}
	
	/// # Summary
	/// Runs tests where there will be both one bit flip and one phase flip.
	operation T4_Combo_Test() : Unit
	{
		SteaneTest(true, true, "combo");
	}

}
