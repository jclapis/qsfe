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


// This file contains the implementation and tests for Grover's algorithm.
// It's an intriguing approach at "reversing a function" - essentially
// if you have a function f(x) = y, Grover's algorithm figures out
// x given f and y. If you're interested in trying all possible inputs of a
// fixed search space (like, say, finding the password for for an encrypted
// file or something), Grover can do it in O(√N) steps instead of brute
// force searching the entire space (which is O(N)).
//
// As a note, this is the first time I'll be writing a traditional hybrid
// quantum-and-classical unit test setup instead of a purely quantum one,
// because this particular algorithm is one of those building blocks that
// you could use in everyday algorithms for real work as part of a classical
// computation workload.
namespace QSharpOracles.Grover
{
    open Microsoft.Quantum.Diagnostics;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	open QSharpOracles;


	// ==============================
	// == Algorithm Implementation ==
	// ==============================


	/// # Summary
	/// Runs Grover's algorithm on the provided oracle, turning the input into
	/// a superposition where the correct answer's state has a very large amplitude
	/// relative to all of the other states.
	///
	/// # Input
	/// ## Register
	/// The register that will contain the correct result at the end of the
	/// function. It should be provided in state |0...0> at the start.
	/// 
	/// ## Oracle
	/// The oracle function containing the implementation of the problem you're
	/// trying to solve. It should be a standard bit flipping oracle, which
	/// will flip the target qubit if and only if the input register meets some
	/// particular criteria.
	operation GroversAlgorithm(
		Register : Qubit[],
		Oracle : ((Qubit[], Qubit) => Unit is Adj)
	) : Unit 
	{
		// This is just a convenient way to get the phase flip version of the
		// marking oracle provided, since most oracles are easier to implement
		// as target bit flippers.
		let phaseMarkerOracle = ConvertFlipMarkerToPhaseMarker(Oracle);

		// Run the algorithm for √N iterations.
		ApplyToEach(H, Register);
		let iterations = Round(PowD(2.0, IntAsDouble(Length(Register)) / 2.0));
        for(i in 1..iterations)
		{
			GroverIteration(Register, phaseMarkerOracle);
		}
    }

	/// # Summary
	/// Runs a single iteration of the main loop in Grover's algorithm,
	/// which is the oracle followed by the diffusion operator.
	/// 
	/// # Input
	/// ## Register
	/// The register containing the qubits being evaluated by the algorithm
	/// 
	/// ## Oracle 
	/// An oracle containing the implementation of the problem being solved.
	/// This should be a phase-flipping oracle instead of a bit-flipping one.
	/// 
	/// # Remarks
	/// See this circuit for more information:
	/// https://en.wikipedia.org/wiki/File:Grovers_algorithm.svg
	operation GroverIteration(
		Register : Qubit[], 
		Oracle : (Qubit[] => Unit is Adj)
	) : Unit
	{
		// Run the oracle on the input to see if it was a correct result
		Oracle(Register);

		// Run the diffusion operator
		ApplyToEach(H, Register);
		RunFlipMarkerAsPhaseMarker(CheckIfAllZeros, Register);
		ApplyToEach(H, Register);
	}
	

	// ====================
	// == Test Case Code ==
	// ====================


	/// # Summary
	/// Runs Grover's Algorithm to try and find the pad that was used to encrypt
	/// the given message. In this case, the encryption algorithm is just XOR.
	/// 
	/// # Input
	/// ## EncodedMessage
	/// The "ciphertext", or in this case, the encrypted version of the original
	/// message that was XOR'd with the actual pad.
	/// 
	/// ## DesiredResult
	/// The "plaintext", or in this case, the original message before it got
	/// encrypted. You need this value in any brute-force key search against an
	/// encryption algorithm, otherwise you won't know if your key is correct;
	/// that's why these are called "plaintext attacks"!
	/// 
	/// # Output
	/// A bit string (false = 0, true = 1) that represents what the algorithm
	/// thinks the original pad was. This isn't guaranteed to be correct, but it
	/// has a pretty high chance if you put it a large number of iterations. If
	/// it ends up being wrong, you can always just run it again.
	/// 
	/// # Remarks
	/// I know what you're thinking. XOR is a stupid example here because if
	/// you have the ciphertext (the encoded message) and the plaintext (the
	/// original message), you can just XOR them together and that gives you
	/// the pad. That's not the point though - this is just an example of a
	/// quantum oracle that only returns "yes" if the pad is correct, and the
	/// pad could be any number in the entire 2^N search space. You can replace
	/// XOR with any function, like a cryptographic hash or AES or something,
	/// and that could just as easily if in here.
	operation RunGroverSearchOnXOR(
		EncodedMessage : Bool[],
		DesiredResult : Bool[]
	) : Bool[]
	{
		// Sanity check to make sure the arrays are all the same length
		let length = Length(EncodedMessage);
		EqualityFactI(length, Length(DesiredResult),
			"Encoded message and target result must be the same length.");
			
		// Convert the XOR oracle into the form that Grover's expects,
		// which just means making it a partial function with the 
		// known bitstrings already in place.
		let xorOracle = CheckXorPad(_, EncodedMessage, DesiredResult, _);

		mutable resultPad = new Bool[length];
		using(padKey = Qubit[length])
		{
			// Run the algorithm
			GroversAlgorithm(padKey, xorOracle);

			// Convert the qubit array into a classical bit array
			for(i in 0..length - 1)
			{
				set resultPad w/= i <- M(padKey[i]) == One;
			}

			// Clean up the qubits
			ResetAll(padKey);
		}

		return resultPad;
	}

}
