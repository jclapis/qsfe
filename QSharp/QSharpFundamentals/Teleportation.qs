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


// This file contains some test implementations of the standard quantum teleportation
// protocols using Q#, along with a few extra variations for good measure.
namespace QSharpFundamentals.Teleportation
{
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	

	// ==============================
	// == Algorithm Implementation ==
	// ==============================


	/// # Summary
	/// Prepares the transfer and reproduction qubits by entangling them in
	/// the requested state.
	/// 
	/// # Input
	/// ## Transfer
	/// The transfer qubit, which will interact with the original unknown state
	/// and "bridge" it over to the reproduction qubit.
	/// 
	/// ## Reproduction
	/// The remote qubit that will be given the state of the original at the
	/// end of the teleportation process.
	/// 
	/// ## EntanglementState
	/// A flag that describes the entanglement state you want to use between the
	/// transfer and reproduction qubits during the teleportation process. The
	/// standard method is to use the Bell State (|00> + |11>), but this particular
	/// implementation lets you select other states as a mode of extra security.
	/// 0 = |00> + |11>
	/// 1 = |01> + |10>
	/// 2 = |00> - |11>
	/// 3 = |01> - |10>
	operation PrepareQubits(
		Transfer : Qubit,
		Reproduction : Qubit, 
		EntanglementState : Int
	) : Unit
	{
		// Normal entanglement
		H(Transfer);
		CNOT(Transfer, Reproduction);

		// If the lower state bit is on, flip the qubits
		if((EntanglementState &&& 0b01) == 1)
		{
			X(Transfer);
		}

		// If the upper state bit is on, flip the phases
		if((EntanglementState &&& 0b10) == 2)
		{
			Z(Transfer);
		}
	}
	
	/// # Summary
	/// Entangles the original qubit with the transfer qubit and measures both of them,
	/// providing the classical information that the remote end needs when reproducing
	/// the original qubit.
	/// 
	/// # Input
	/// ## Original
	/// The original qubit, containing the unknown state that needs to be transferred.
	/// 
	/// ## Transfer
	/// The transfer qubit, which has been entangled with the remote end already via the
	/// PrepareQubits operation.
	/// 
	/// # Output
	/// Returns the results of the two measurements.
	/// The first value is the measurement of the original qubit.
	/// The second value is the measurement of the transfer qubit.
    operation GetMessageParameters (Original : Qubit, Transfer : Qubit) : (Result, Result)
    {
		// Entangle the original qubit with the transfer qubit
		CNOT(Original, Transfer);
		H(Original);

		// Measure the two, so their values can be passed to the remote end
		let originalMeasurement = M(Original);
		let transferMeasurement = M(Transfer);
		return (originalMeasurement, transferMeasurement);
    }

	/// # Summary
	/// Reproduces the original qubit's state into the reproduction qubit.
	/// 
	/// # Input
	/// ## Reproduction
	/// The reproduction qubit on the (conceptual) remote end, which will be given the
	/// original qubit's state.
	/// 
	/// ## OriginalMeasurement
	/// The value that was measured on the original qubit after it was entangled with
	/// the transfer qubit.
	/// 
	/// ## TransferMeasurement
	/// The value that was measured on the transfer qubit after it was entangled with
	/// the original qubit.
	/// 
	/// ## EntanglementState
	/// The entanglement state that was used to entangle the transfer qubit with the
	/// reproduction qubit. This is used to determine what to do with the two
	/// measurements in order to properly reproduce the original qubit.
	operation ReproduceOriginal(
		Reproduction : Qubit, 
		OriginalMeasurement : Result, 
		TransferMeasurement : Result,
		EntanglementState : Int
	) : Unit
	{
		// There is a ton of math that goes into figuring these instructions out.
		// I can't explain it all here, but this link has a pretty good explanation
		// of it: https://docs.microsoft.com/en-us/quantum/techniques/putting-it-all-together
		// Basically just plug in the original entangled state, do the number crunching,
		// and figure out which instructions to run for any given state.

		// For |00> + |11>
		if(EntanglementState == 0)
		{
			if(TransferMeasurement == One)
			{
				X(Reproduction);
			}
			if(OriginalMeasurement == One)
			{
				Z(Reproduction);
			}
		}
		// For |01> + |10>
		elif(EntanglementState == 1)
		{
			if(TransferMeasurement == Zero)
			{
				X(Reproduction);
			}
			if(OriginalMeasurement == One)
			{
				Z(Reproduction);
			}
		}
		// For |00> - |11>
		elif(EntanglementState == 2)
		{
			if(TransferMeasurement == One)
			{
				X(Reproduction);
			}
			if(OriginalMeasurement == Zero)
			{
				Z(Reproduction);
			}
		}
		// For |01> - |10>
		elif(EntanglementState == 3)
		{
			if(TransferMeasurement == Zero)
			{
				X(Reproduction);
			}
			if(OriginalMeasurement == Zero)
			{
				Z(Reproduction);
			}
		}
	}


	// ====================
	// == Test Case Code ==
	// ====================
	
	
	/// # Summary
	/// Prepares the |-> state.
	/// 
	/// # Input
	/// ## Target
	/// The target qubit to prepare. It must be in the |0> state.
	operation PrepareNegativeH(Target : Qubit) : Unit
	{
		body (...)
		{
			X(Target);
			H(Target);
		}
		adjoint invert;
	}
	
	/// # Summary
	/// Prepares the |Y> state (|0> + i|1>).
	/// 
	/// # Input
	/// ## Target
	/// The target qubit to prepare. It must be in the |0> state.
	operation PrepareY(Target : Qubit) : Unit
	{
		body (...)
		{
			H(Target);
			S(Target);
		}
		adjoint invert;
	}
	
	/// # Summary
	/// Prepares the |-Y> state (|0> - i|1>).
	/// 
	/// # Input
	/// ## Target
	/// The target qubit to prepare. It must be in the |0> state.
	operation PrepareNegativeY(Target : Qubit) : Unit
	{
		body (...)
		{
			H(Target);
			S(Target);
			Z(Target);
		}
		adjoint invert;
	}
	
	/// # Summary
	/// Rotates a qubit around the X, Y, and Z axes by the specified
	/// angles (in radians).
	/// 
	/// # Input
	/// ## Target
	/// The target qubit to rotate.
	/// 
	/// ## XAngle
	/// The angle (in radians) to rotate around the X axis of the Bloch sphere.
	/// 
	/// ## YAngle
	/// The angle (in radians) to rotate around the Y axis of the Bloch sphere.
	/// 
	/// ## ZAngle
	/// The angle (in radians) to rotate around the Z axis of the Bloch sphere.
	operation RotateQubit(
		Target : Qubit, 
		XAngle : Double, 
		YAngle : Double,
		ZAngle : Double
	) : Unit
	{
		body (...)
		{
			Rx(XAngle, Target);
			Ry(YAngle, Target);
			Rz(ZAngle, Target);
		}

		adjoint invert;
	}

	/// # Summary
	/// Runs teleportation on |0>, just to ensure that things don't get messed up
	/// in the most basic case.
	operation TeleportZero_Test() : Unit
	{
		RunTest("Teleport |0>", 100, I);
	}

	/// # Summary
	/// Runs teleportation on |1>.
	operation TeleportOne_Test() : Unit
	{
		RunTest("Teleport |1>", 100, X);
	}

	/// # Summary
	/// Runs teleportation on |+>.
	operation TeleportH_Test() : Unit
	{
		RunTest("Teleport |+>", 100, H);
	}

	/// # Summary
	/// Runs teleportation on |->.
	operation TeleportNegativeH_Test() : Unit
	{
		RunTest("Teleport |->", 100, PrepareNegativeH);
	}

	/// # Summary
	/// Runs teleportation on |Y>.
	operation TeleportY_Test() : Unit
	{
		RunTest("Teleport |Y>", 100, PrepareY);
	}

	/// # Summary
	/// Runs teleportation on |-Y>.
	operation TeleportNegativeY_Test() : Unit
	{
		RunTest("Teleport |-Y>", 100, PrepareNegativeY);
	}

	/// # Summary
	/// Runs teleportation on a weird uneven rotation around the Bloch sphere.
	operation TeleportRotation_Test() : Unit
	{
		RunTest("Teleport weird arbitrary rotation", 100,
			RotateQubit(_, 0.36325, 1.8892345, 2.498235));
	}

	/// # Summary
	/// Runs the teleportation algorithm on the given original qubit state and
	/// ensures that the remote end matches the original state.
	/// 
	/// # Input
	/// ## Descrption
	/// A human-readable description of the test, which will be printed to the log.
	/// 
	/// ## Iterations
	/// The number of times to run the test. If any iteration fails, the whole test
	/// will fail.
	/// 
	/// ## OriginalQubitFunction
	/// A reversible function that will put the original qubit (starting at |0>)
	/// into the desired state, which will be teleported to the remote qubit as part
	/// of the test.
	operation RunTest(
		Description : String,
		Iterations : Int,
		OriginalQubitFunction : (Qubit => Unit is Adj)
	) : Unit
	{
		Message($"Running test: {Description}.");

		using(qubits = Qubit[3])
		{
			let original = qubits[0];
			let transfer = qubits[1];
			let reproduction = qubits[2];

			for(i in 1..Iterations)
			{
				// Run the algorithm on all of the entanglement states.
				for(entanglementState in 0..3)
				{
					// Create the original state, and entangle the send/receive pair
					OriginalQubitFunction(original);
					PrepareQubits(transfer, reproduction, entanglementState);

					// Get the measurements on the local end
					let (originalMeasurement, transferMeasurement) = 
						GetMessageParameters(original, transfer);

					// This part here is where you send those measurements to the
					// remote end, in an actual teleportation session

					// Reproduce the original state on the remote end with the 
					// provided measurements
					ReproduceOriginal(reproduction, originalMeasurement, 
						transferMeasurement, entanglementState);

					// Run the original function in reverse on the reproduction qubit
					// which should put it back in the |0> state if it is now in the
					// original qubit's state
					Adjoint OriginalQubitFunction(reproduction);
					Assert([PauliZ], [reproduction], Zero, $"Test {Description} failed " + 
						$"during entanglement state {entanglementState}: " +
						"the reproduction qubit didn't match the original qubit.");

					ResetAll(qubits);
				}
			}
		}

		// If all iterations passed, we're done.
		Message("Passed!");
		Message("");
	}

}
