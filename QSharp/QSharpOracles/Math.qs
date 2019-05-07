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


// This file contains some useful math and logic functions used by some of
// the oracles defined in this assembly.
namespace QSharpOracles
{
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	
	/// # Summary
	/// Performs an XOR on a classical bit string and a qubit array. This
	/// is an in-place implementation, meaning the qubit array will contain
	/// the results of the XOR when this function returns.
	/// 
	/// # Input
	/// ## ClassicBits
	/// The classical bit array to use in the XOR
	/// 
	/// ## Qubits
	/// The qubit array to use in the XOR
	/// 
	/// # Remarks
	/// The reason I do an in-place XOR here is because qubits are really, really
	/// expensive resources. In a world where even the most powerful quantum
	/// coprocessors only have a handful of available qubits, you can't just
	/// arbitrarily allocate as many spares / ancilla qubits as you want. You
	/// seriously want to keep the number of qubit allocations down to an absolute
	/// minimum. I originally took two qubit arrays here (an input and an output)
	/// instead of an in-place XOR, and the algorithm was pretty much limited to like
	/// 12 qubits on my system because of it because the simulator would eat all of
	/// my RAM. By doing it in-place, I let the original message be twice as long
	/// while using the same amount of resources.
	operation InplaceXor(
		ClassicBits : Bool[],
		Qubits : Qubit[]
	) : Unit
	{
		body (...)
		{
			for(i in 0..Length(ClassicBits) - 1)
			{
				// My XOR implementation here takes advantage of the fact that
				// we know what the classic bits are. Here's the table, where
				// the first bit is the classic bit and the second is the qubit.
				// The left-hand side is before the XOR, the right-hand is after.
				// |00>  =>  |00>
				// |01>  =>  |01>
				// |10>  =>  |11>
				// |11>  =>  |10>
				// So if the classical bit is a zero, we don't actually have to
				// do anything to the qubit. If the classical bit is one, we just
				// end up flipping the qubit. This is basically just a CNOT with
				// the classical bit as the control!
				if(ClassicBits[i])
				{
					X(Qubits[i]);
				}
			}
		}
		adjoint self;
	}

	/// # Summary
	/// Left-shifts the input qubit array by the specified number of bits.
	/// 
	/// # Input
	/// ## Input
	/// The register that contains the qubits to shift. This can be in any
	/// arbitrary state.
	/// 
	/// ## Output
	/// The register that will hold the shifted qubits. This must be in
	/// the state |0...0>.
	/// 
	/// ## Amount
	/// The number of bits to shift the input register by.
	operation LeftShift(
		Input : Qubit[],
		Output : Qubit[],
		Amount : Int
	) : Unit
	{
		AssertIntEqual(Length(Input), Length(Output), "Input and Output " + 
			"registers must have the same size.");
		for(inputIndex in Amount..Length(Input) - 1)
		{
			let outputIndex = inputIndex - Amount;
			CNOT(Input[inputIndex], Output[outputIndex]);
		}
	}

	/// # Summary
	/// Right-shifts the input qubit array by the specified number of bits.
	/// 
	/// # Input
	/// ## Input
	/// The register that contains the qubits to shift. This can be in any
	/// arbitrary state.
	/// 
	/// ## Output
	/// The register that will hold the shifted qubits. This must be in
	/// the state |0...0>.
	/// 
	/// ## Amount
	/// The number of bits to shift the input register by.
	operation RightShift(
		Input : Qubit[],
		Output : Qubit[],
		Amount : Int
	) : Unit
	{
		AssertIntEqual(Length(Input), Length(Output), "Input and Output " + 
			"registers must have the same size.");
		for(inputIndex in 0..Length(Input) - 1 - Amount)
		{
			let outputIndex = inputIndex + Amount;
			CNOT(Input[inputIndex], Output[outputIndex]);
		}
	}

}
