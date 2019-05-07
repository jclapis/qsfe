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


// This file contains some basic tests to show how Q# deals with 
// entanglement. 
namespace QSharpFundamentals.Entanglement
{
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	

	// ==============================
	// == Algorithm Implementation ==
	// ==============================


	/// # Summary
	/// This is the simplest form of entanglement - each qubit will be entangled with
	/// the first one, meaning that if one is |0>, they're all |0> and vice versa.
	/// It will put them in an equal superposition of |0...0> and |1...1>, but the
	/// weighting of the superpositions doesn't really matter here.
	/// 
	/// # Input
	/// ## Qubits
	/// The qubits to transform for the test
    operation BasicEntanglement (Qubits : Qubit[]) : Unit
    {
		body (...)
		{
			H(Qubits[0]);
			for(i in 1..Length(Qubits) - 1)
			{
				CNOT(Qubits[0], Qubits[i]);
			}
		}

		adjoint invert; // Notice that this is adjoint, because I use it in the
						// test below to entangle and disentangle two qubits. It's
						// set to invert mode because disentangling requires running
						// the entanglement process in reverse.
    }
	
	/// # Summary
	/// This test will make sure Q#'s entanglement works properly with respect to
	/// modifying an entangled qubit just by messing with its partner. Specifically,
	/// this will use a combination of entanglement and a phase flip (Z operator) on
	/// the second qubit to flip the first one without touching it.
	/// 
	/// # Input
	/// ## Qubits
	/// The qubits to transform for the test
	operation EntangledPhaseFlip (Qubits : Qubit[]) : Unit
	{
		BasicEntanglement(Qubits);
		Z(Qubits[1]);
		Adjoint BasicEntanglement(Qubits); // Disentangle (Adjoint means run the
										   // given operation in reverse)
	}

	/// # Summary
	/// This tests quantum gates that use multiple qubits as the controls, instead
	/// of just one qubit. It will flip the target qubit if all of the control
	/// qubits are |1>.
	/// 
	/// # Input
	/// ## Qubits
	/// The qubits register to use. The last qubit will be the target, and all of
	/// the qubits before it will be the controls.
	operation MultiControl(Qubits : Qubit[]) : Unit
	{
		let length = Length(Qubits);
		let controls = Qubits[0..length - 2];
		let target = Qubits[length - 1];
		
		// ApplyToEach is a helper function that basically runs the given operation
		// (in this case, the H gate) on each qubit in the given register.
		ApplyToEach(H, controls);

		// Controlled X means the controlled variant of the X gate, using the first
		// argument as the list of control qubits.
		Controlled X(controls, target);
	}


	// ====================
	// == Test Case Code ==
	// ====================
	

	/// # Summary
	/// Tests the simplest possible entanglement - the Bell State.
	/// This should produce two even possibilities where both qubits
	/// have the same result 100% of the time: |00> or |11>.
	operation BellState_Test() : Unit
	{
		let validStates = [
			[Zero, Zero],
			[One, One]
		];
		RunTest(BasicEntanglement, "Bell State", 1000, validStates);
	}
	
	/// # Summary
	/// Tests an extension of the Bell State, called the GHZ State,
	/// which is just the same thing but with more than two qubits.
	operation GhzState_Test() : Unit
	{
		let validStates = [
			[Zero, Zero, Zero, Zero, Zero, Zero, Zero, Zero],
			[One, One, One, One, One, One, One, One]
		];
		RunTest(BasicEntanglement, "GHZ State with 8 qubits", 1000, validStates);
	}
	
	/// # Summary
	/// Tests the entangled phase flip to show that you can change a
	/// qubit just by changing its entangled partner.
	operation PhaseFlip_Test() : Unit
	{
		let validStates = [
			[One, Zero]
		];
		RunTest(EntangledPhaseFlip, "entangled phase flip", 1000, validStates);
	}

	/// # Summary
	/// Tests entanglement with more than one control qubit.
	operation MultiControl_Test() : Unit
	{
		let validStates = [
			[Zero, Zero, Zero, Zero],
			[Zero, Zero, One, Zero],
			[Zero, One, Zero, Zero],
			[Zero, One, One, Zero],
			[One, Zero, Zero, Zero],
			[One, Zero, One, Zero],
			[One, One, Zero, Zero],
			[One, One, One, One]
		];
		RunTest(MultiControl, "multi-controlled operation", 1000, validStates);
	}
	
	/// # Summary
	/// Runs the provided unit test, measuring the results and ensuring that the resulting
	/// state matches one of the provided target states.
	/// 
	/// # Input
	/// ## TestFunction
	/// The function that implements the actual test, by converting the qubits into the
	/// target state.
	/// 
	/// ## Description
	/// A human-readable description of the test, which will be printed to the log.
	/// 
	/// ## Iterations
	/// The number of times to run the test and check that the results match a valid state.
	/// 
	/// ## ValidStates
	/// An array of valid states that the qubits could be in. Each time the test is run,
	/// this function will check the result and make sure it matches one of these states.
	/// If it doesn't match any of these states, the test has failed.
	operation RunTest(
		TestFunction : (Qubit[] => Unit), 
		Description : String,
		Iterations : Int, 
		ValidStates : Result[][]
	) : Unit
	{
		Message($"Running test: {Description}.");
		let arrayLength = Length(ValidStates[0]);
		mutable matchingStateCount = new Int[Length(ValidStates)];

		using(qubits = Qubit[arrayLength])
		{
			for(i in 1..Iterations)
			{
				// Run the test implementation and measure the qubit states
				TestFunction(qubits);
				mutable results = new Result[arrayLength];
				for(j in 0..arrayLength - 1)
				{
					set results w/= j <- M(qubits[j]);
				}
				ResetAll(qubits); // Lazy reinitialization to |0> on all qubits

				// Go through each of the valid target states and find one that
				// matches the results
				mutable matchedValidState = false;
				for(j in 0..Length(ValidStates) - 1)
				{
					// Q# doesn't have a "break" statement, so we have to
					// go through the whole array and only run the check if
					// there isn't a matching state yet.
					if(not matchedValidState)
					{
						let candidateState = ValidStates[j];
						mutable allQubitsMatch = true;
						for(k in 0..arrayLength - 1)
						{
							// As soon as one of the result qubits doesn't match
							// this state, consider it a failure. This is normally
							// where a break would go.
							if(results[k] != candidateState[k])
							{
								set allQubitsMatch = false;
							}
						}

						// Found a valid state!
						if(allQubitsMatch)
						{
							set matchedValidState = true;
							set matchingStateCount w/= j <- matchingStateCount[j] + 1;
						}
					}
				}

				// If none of the candidate states match, the test failed.
				if(not matchedValidState)
				{
					mutable stateString = "[ ";
					for(j in 0..arrayLength - 1)
					{
						set stateString = stateString + $"{results[j] == Zero ? 0 | 1} ";
					}
					set stateString = stateString + "]";
					fail $"Test {Description} failed. Resulting state {stateString} " + 
						"didn't match any valid target states.";
				}

			}
		}
		
		// If all of the iterations passed, the test was a success.
		// Print each target state along with the number of times it was found,
		// just for our own edification.
		for(i in 0..Length(ValidStates) - 1)
		{
			let candidateState = ValidStates[i];
			mutable stateString = "Found state [ ";
			for(j in 0..arrayLength - 1)
			{
				set stateString = stateString + $"{candidateState[j] == Zero ? 0 | 1} ";
			}
			set stateString = stateString + $"] {matchingStateCount[i]} times.";
			Message(stateString);
		}
		Message("Passed!");
		Message("");
	}

}
