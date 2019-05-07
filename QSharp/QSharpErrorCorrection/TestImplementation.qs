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


// This file contains a bunch of common helper functions used to run
// the error correction tests in this project, including the actual
// test execution logic.
namespace QSharpErrorCorrection.Testing
{
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;

	/// # Summary
	/// This is a function that can turn a qubit from |0> into
	/// whatever arbitrary state A|0> + B|1> that you want. It must be
	/// reversible (adjoint).
	newtype StatePrepFunctionType = (Qubit => Unit is Adj);

	/// # Summary
	/// This function type should take in a single qubit in an arbitrary state
	/// and construct an error-corrected register based on it. The nature of
	/// the register and this function will depend on the error code being tested.
	newtype RegisterPrepFunctionType = ((Qubit, Qubit[]) => Unit is Adj);

	/// # Summary
	/// This function should take an error-corrected register, check it for
	/// a single bit flip and/or phase flip error (the position of either error
	/// can be anywhere in the register, they don't have to be on the same qubit),
	/// and correct the error in-place. The nature of the register and this function
	/// will depend on the error code being tested.
	newtype CorrectionFunctionType = (Qubit[] => Unit);

	/// # Summary
	/// This is a wrapper for an initial test state. It contains a function that
	/// transforms the qubit into the desired initial state, and a description of
	/// the desired state for human readability.
	newtype TestStateType = (StatePrepFunctionType, String);
	
	
	/// # Summary
	/// This contains the actual test implementation code - everything
	/// needed to run an individual test case is contained here.
	/// 
	/// # Input
	/// ## NumberOfQubits
	/// The total number of qubits that the error code is expecting (the original 
	/// qubit and all of the spare qubits)
	/// 
	/// ## StatePrepFunction
	/// A function that will put the original qubit (starting at |0>) into the
	/// desired state to be tested. This can be any arbitrary state A|0> + B|1>.
	/// 
	/// ## RegisterPrepFunction
	/// A function that will prepare the logical qubit register, turning the original
	/// single unprotected qubit into an error-corrected array of qubits.
	/// 
	/// ## CorrectionFunction
	/// The error correction function that will evaluate the qubit register, detect any
	/// errors, and correct them in-place.
	/// 
	/// ## BitFlipIndex
	/// The 0-based index of the bit to flip during the test (simulating
	/// a quantum bit flip error), or -1 if none of the bits should be flipped.
	/// 
	/// ## PhaseFlipIndex
	/// The 0-based index of the bit to phase flip during the test (simulating
	/// a quantum phase flip error), or -1 if none of the bits should be flipped.
	operation RunTest(
		NumberOfQubits : Int,
		StatePrepFunction : StatePrepFunctionType,
		RegisterPrepFunction : RegisterPrepFunctionType,
		CorrectionFunction : CorrectionFunctionType,
		BitFlipIndex : Int,
		PhaseFlipIndex : Int
	) : Unit
	{
		using(register = Qubit[NumberOfQubits])
		{
			// Create the initial state and the full error-protected register
			StatePrepFunction!(register[0]);
			RegisterPrepFunction!(register[0], register[1..NumberOfQubits - 1]);

			// Simulate the requested error(s)
			if(BitFlipIndex >= 0)
			{
				X(register[BitFlipIndex]);
			}
			if(PhaseFlipIndex >= 0)
			{
				Z(register[PhaseFlipIndex]);
			}

			// This is the meat of the test - run the error correction
			CorrectionFunction!(register);

			// Undo the register and initial state prep
			Adjoint RegisterPrepFunction!(register[0], register[1..NumberOfQubits - 1]);
			Adjoint StatePrepFunction!(register[0]);

			// Ensure we're back at |0...0>, otherwise the test failed and the algorithm
			// is broken!
			AssertAllZero(register);
		}
	}

	/// # Summary
	/// Runs a series of tests on the given error correction functions while using
	/// the provided initial state for the qubit to protect.
	/// 
	/// # Input
	/// ## NumberOfQubits
	/// The total number of qubits that the error code is expecting (the original 
	/// qubit and all of the spare qubits)
	/// 
	/// ## TestState
	/// A function (and accompanying description) that will put the original qubit
	/// (starting at |0>) into the desired state to be tested.
	/// 
	/// ## RegisterPrepFunction
	/// A function that will prepare the logical qubit register, turning the original
	/// single unprotected qubit into an error-corrected array of qubits.
	/// 
	/// ## CorrectionFunction
	/// The error correction function that will evaluate the qubit register, detect any
	/// errors, and correct them in-place.
	/// 
	/// ## EnableBitFlip
	/// True to enable bit flipping during the tests, false to disable it so no bits
	/// are flipped. If enabled, this will test the flipping of every single bit one at
	/// a time to ensure that the actual position of the flipped bit doesn't matter.
	/// 
	/// ## EnablePhaseFlip
	/// True to enable phase flipping during the tests, false to disable it so no
	/// phases are flipped. If enabled, this will test the flipping of every single bit's
	/// phase one at a time to ensure that the actual position of the bit doesn't matter.
	operation RunTestsWithInitialState(
		NumberOfQubits : Int,
		TestState : TestStateType,
		RegisterPrepFunction : RegisterPrepFunctionType,
		CorrectionFunction : CorrectionFunctionType,
		EnableBitFlip : Bool,
		EnablePhaseFlip : Bool
	) : Unit
	{
		let (testStateFunction, stateDescription) = TestState!;

		// Set up the number of tests to do bit and phase flips on
		let numberOfBitFlipTests = EnableBitFlip ? NumberOfQubits | 0;
		let numberOfPhaseFlipTests = EnablePhaseFlip ? NumberOfQubits | 0;

		for(bitFlipIndex in -1..numberOfBitFlipTests - 1)
		{
			for(phaseFlipIndex in -1..numberOfPhaseFlipTests - 1)
			{
				// Set up the description string for this test
				mutable descriptionString = "Testing ";
				if(bitFlipIndex >= 0)
				{
					set descriptionString = descriptionString + $" q{bitFlipIndex} flipped, ";
				}
				if(phaseFlipIndex >= 0)
				{
					set descriptionString = descriptionString + $" q{phaseFlipIndex} phased, ";
				}
				set descriptionString = descriptionString + $"with state: {stateDescription}.";
				Message(descriptionString);

				// Run the actual test
				RunTest(
					NumberOfQubits,
					testStateFunction,
					RegisterPrepFunction,
					CorrectionFunction,
					bitFlipIndex,
					phaseFlipIndex
				);
				Message(""); // Empty line, to help with clarity
			}
		}

		Message("Passed!");
		Message("");
	}

	/// # Summary
	/// Generates an array of states to put the original qubit in prior to running
	/// error correction. This is used to ensure that the algorithm really does work
	/// on arbitrary states.
	/// The first six test states will be I, H, X, Y, Z, and S. The other ones will
	/// be completely random rotations around the Bloch sphere - you can request as
	/// many of these as you want.
	/// 
	/// # Input
	/// ## NumberOfRandomCases
	/// The number of random states to generate in addition to the standard 6.
	/// 
	/// # Output
	/// An array of test states, accompanied by string descriptions of what they are
	/// for debugging or examination purposes.
	operation GenerateTestStates(NumberOfRandomCases : Int) : TestStateType[]
	{
		mutable testStates = new TestStateType[NumberOfRandomCases + 6];

		// These are the standard six test cases
		set testStates w/= 0 <- TestStateType(StatePrepFunctionType(I), "I");
		set testStates w/= 1 <- TestStateType(StatePrepFunctionType(H), "H");
		set testStates w/= 2 <- TestStateType(StatePrepFunctionType(X), "X");
		set testStates w/= 3 <- TestStateType(StatePrepFunctionType(Y), "Y");
		set testStates w/= 4 <- TestStateType(StatePrepFunctionType(Z), "Z");
		set testStates w/= 5 <- TestStateType(StatePrepFunctionType(S), "S");

		for(i in 0..NumberOfRandomCases - 1)
		{
			// Generate 3 random angles, from 0 to pi.
			let pi = PI();
			let randomX = RandomReal(32) * pi;
			let randomY = RandomReal(32) * pi;
			let randomZ = RandomReal(32) * pi;
			let description = $"[X = {randomX}, Y = {randomY}, Z = {randomZ}]";

			// Create a new test state with the random rotation. This needs to be 
			// done as a partial function so that it can be run and then adjointed
			// (run inversely) by the test function. 
			set testStates w/= (i + 6) <- TestStateType(
				StatePrepFunctionType(RotateQubit(_, randomX, randomY, randomZ)),
				description
			);
		}

		return testStates;
	}

	/// # Summary
	/// Rotates a qubit around all three Pauli axes.
	/// 
	/// # Input
	/// ## Target
	/// The target qubit to rotate.
	/// 
	/// ## XAngle
	/// The angle to rotate around the X axis, in radians.
	/// 
	/// ## YAngle
	/// The angle to rotate around the Y axis, in radians.
	/// 
	/// ## ZAngle
	/// The angle to rotate around the Z axis, in radians.
	operation RotateQubit(Target : Qubit, XAngle : Double, YAngle : Double, ZAngle : Double) : Unit
	{
		body (...)
		{
			Rx(XAngle, Target);
			Ry(YAngle, Target);
			Rz(ZAngle, Target);
		}

		adjoint invert;
	}
}
