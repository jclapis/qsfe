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


// This file contains helper functions that make it easier to work
// with quantum oracles.
namespace QSharpOracles
{
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	
	/// # Summary
	/// Converts a traditional bit flip oracle (one that flips the
	/// target from |0> to |1> if the input is "correct") into a
	/// phase flip oracle (one that flips the phase of the input
	/// register if the input is "correct").
	/// 
	/// # Input
	/// ## FlipMarker
	/// The normal, bit-flip-on-target oracle to convert.
	/// 
	/// # Output
	/// Returns a version of the oracle that flips the phase of the
	/// input on success, instead of flipping the target bit.
	function ConvertFlipMarkerToPhaseMarker(
		FlipMarker : ((Qubit[], Qubit) => Unit is Adj))
	: (Qubit[] => Unit is Adj)
	{
        return RunFlipMarkerAsPhaseMarker(FlipMarker, _);
	}
	
	/// # Summary
	/// Runs an oracle, flipping the phase of the input array if the result was |1>
	/// instead of flipping the target qubit.
	/// 
	/// # Input
	/// ## Oracle
	/// The normal bit-flip oracle to run.
	/// 
	/// ## InputArray
	/// The array of qubits to run the oracle on.
	operation RunFlipMarkerAsPhaseMarker(
		Oracle : ((Qubit[], Qubit) => Unit is Adj),
		InputArray : Qubit[]
	) : Unit
	{
		body (...)
		{
			using(target = Qubit())
			{
				// Set the target to |->
				X(target);
				H(target);

				// Run the oracle on the input array and the target;
				// since the target is |-> instead of |0>, when the oracle
				// tries to mark it with a bit flip, it will end up phase
				// flipping the entire input array instead.
				Oracle(InputArray, target);
				
				// Set the target back to |0>
				H(target);
				X(target);
			}
		}
		
        adjoint self;
	}
}
