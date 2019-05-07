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


// This file contains a simple implementation of the superdense coding
// protocol.
namespace QSharpFundamentals.Superdense
{
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	

	// ==============================
	// == Algorithm Implementation ==
	// ==============================


	/// # Summary
	/// Encodes the bits of a 2-bit buffer into an entangled qubit pair, so it can be
	/// safely retrieved by the receiver once both qubits are disentangled.
	/// 
	/// # Input
	/// ## Buffer
	/// The buffer containing the two bits to send.
	/// 
	/// ## PairA
	/// The local qubit (the sender's qubit), which is entangled with the remote
	/// (receiver's) qubit.
    operation EncodeMessage (Buffer : Bool[], PairA : Qubit) : Unit
    {
		// Superposition takes advantage of the fact that if you start with |00> + |11>,
		// you can modify it with X and Z on one qubit in a way that will affect both
		// qubits.
		// Nothing, X, Z, and XZ will all produce discrete, measureable states when
		// both qubits are disentangled.
		// We're going to use this lookup table to encode the given bits into the qubit
		// pair:
		// 00 = |00> + |11> (nothing happens)
		// 01 = |01> + |10> (X, the parity is flipped)
		// 10 = |00> - |11> (Z, the phase is flipped)
		// 11 = |01> - |10> (XZ, parity and phase are flipped)
        if(Buffer[1]) // The lowest bit
		{
			X(PairA);
		}
		if(Buffer[0]) // The highest bit
		{
			Z(PairA);
		}
    }

	/// # Summary
	/// Decodes an entangled qubit pair on the receiving end into the original
	/// 2-bit buffer.
	/// 
	/// # Input
	/// ## PairA
	/// The sender's qubit
	/// 
	/// ## PairB
	/// The receiver's qubit
	/// 
	/// # Output
	/// A 2-bit array containing the bits that the sender sent using the
	/// entangled qubit pair.
	operation DecodeMessage (PairA : Qubit, PairB : Qubit) : Bool[]
	{
		CNOT(PairA, PairB);
		H(PairA);
		let aMeasurement = M(PairA);
		let bMeasurement = M(PairB);

		// Here's the decoding table based on the states after running
		// them through CNOT(A, B) and H(A):
		// |00> + |11>  =>  |00> + |10>  =>  |00>, so 00 means nothing happened
		// |01> + |10>  =>  |01> + |11>  =>  |01>, so 01 means X happened
		// |00> - |11>  =>  |00> - |10>  =>  |10>, so 10 means Z happened
		// |01> - |10>  =>  |01> - |11>  =>  |11>, so 11 means XZ happened
		// Notice how all 4 options align with the bit string used by the encoding
		// table, so measuring these qubits gives us the original bits where 
		// PairB corresponds to whether or not X was used, and PairA corresponds
		// to Z.
		let result = [
			aMeasurement == One,
			bMeasurement == One
		];
		return result;
	}
	

	// ====================
	// == Test Case Code ==
	// ====================
	
	
	/// # Summary
	/// Runs the superdense coding test on [00].
	operation Superdense_00_Test() : Unit
	{
		RunTest("Superdense [00]", 100, [false, false]);
	}
	
	/// # Summary
	/// Runs the superdense coding test on [01].
	operation Superdense_01_Test() : Unit
	{
		RunTest("Superdense [01]", 100, [false, true]);
	}
	
	/// # Summary
	/// Runs the superdense coding test on [10].
	operation Superdense_10_Test() : Unit
	{
		RunTest("Superdense [10]", 100, [true, false]);
	}
	
	/// # Summary
	/// Runs the superdense coding test on [11].
	operation Superdense_11_Test() : Unit
	{
		RunTest("Superdense [11]", 100, [true, true]);
	}
	
	/// # Summary
	/// Runs the superdense coding algorithm on the given classical buffer.
	/// 
	/// # Input
	/// ## Descrption
	/// A human-readable description of the test, which will be printed to the log.
	/// 
	/// ## Iterations
	/// The number of times to run the test. If any iteration fails, the whole test
	/// will fail.
	/// 
	/// ## Buffer
	/// The buffer containing the two bits to send.
	operation RunTest(
		Description : String,
		Iterations : Int,
		Buffer : Bool[]
	) : Unit
	{
		Message($"Running test: {Description}.");

		using(qubits = Qubit[2])
		{
			for(i in 1..Iterations)
			{
				// Entangle the qubits
				H(qubits[0]);
				CNOT(qubits[0], qubits[1]);

				// This is the part where you can ship the qubits to the
				// different users.

				// Once the sender gets their qubit, encode the message in it.
				EncodeMessage(Buffer, qubits[0]);

				// This is the part where the sender sends their qubit to
				// the receiver.

				// Once the receiver gets both qubits, they can decode the
				// original buffer.
				let decodedBits = DecodeMessage(qubits[0], qubits[1]);

				// Ensure the received bits match the original bits
				AllEqualityFactB(Buffer, decodedBits, $"Test {Description} failed: " +
					$"original buffer was [{Buffer[0]}{Buffer[1]}] but the decoded buffer " + 
					$"was [{decodedBits[0]}{decodedBits[1]}].");

				ResetAll(qubits); // Lazy qubit cleanup
			}
		}

		// If all iterations passed, we're done.
		Message("Passed!");
		Message("");
	}
}
