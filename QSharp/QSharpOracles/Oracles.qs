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


// This file contains implementations for some common and useful
// quantum oracles. The way I'm going to define an oracle here is this:
// it's a function that takes in an arbitrary input qubit register and
// a single "result" qubit, runs some kind of code to check for a
// certain value or condition or something, and flips the result qubit
// if the input meets that condition / passes that check. Oracles are
// basically quantum "if-statements" that conform to a standard
// function signature.
// 
// The signature I'm describing here is called a "bit-flip" oracle,
// because it flips the result qubit if the input meets the specific
// condition the oracle checks for. This is usually the easiest way
// to write them from a conceptual understanding and maintainability
// perspective, and I have some utility functions in the Utility
// file that convert them to other kinds of oracles automatically
// (like "phase-flip" ones, which are usually a lot more useful from
// an algorithm perspective).
// 
// Note that all of these oracles are written with adjoint compatibility
// (meaning they end in "adjoint invert" or "adjoint self" or
// something). This is useful because a lot of algorithms need the oracles
// to be reversible in order to clean up the input register after the
// check has been performed.
namespace QSharpOracles
{
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
	
	/// # Summary
	/// This is a quantum oracle that will flip the target qubit if
	/// and only if the entire input register was all zeros - that is,
	/// it was in the state |0...0>.
	/// 
	/// # Input
	/// ## Register
	/// The input register to evaluate
	/// 
	/// ## Target
	/// The target (result) qubit to flip if the input was all zeros.
	operation CheckIfAllZeros(Register : Qubit[], Target : Qubit) : Unit
	{
		body (...)
		{
			// Since this is a zero-controlled check, flip all of the input
			// qubits so they'll flag the target if they were 0 instead of 1
			ApplyToEachA(X, Register);

			// Run an X on the target, controlled by the entire input register
			// (so the target will only get flipped if the whole input register
			/// is 1)
			Controlled X(Register, Target);

			// Put the input register back in its original state
			ApplyToEachA(X, Register);
		}

		adjoint self;
	}

	/// # Summary
	/// This is a bit-flipping oracle that checks to see if the provided
	/// pad key, XOR'd with the encoded message, provides the desired result.
	/// Basically this checks to see if the provided pad was used to encrypt
	/// the original message.
	/// 
	/// # Input
	/// ## PadKey
	/// The qubit array containing the candidate pad key that you want to check
	/// for correctness.
	/// 
	/// ## EncodedMessage
	/// The "ciphertext", or in this case, the encrypted version of the original
	/// message that was XOR'd with the actual pad.
	/// 
	/// ## DesiredResult
	/// The "plaintext", or in this case, the original message before it got
	/// encrypted. This is used to validate that the pad gives the correct
	/// answer.
	/// 
	/// ## IsSuccess
	/// The target qubit in the oracle. If the pad is correct, this is the bit
	/// that will get flipped.
	operation CheckXorPad(
		PadKey : Qubit[],
		EncodedMessage : Bool[],
		DesiredResult : Bool[],
		IsSuccess : Qubit
	) : Unit
	{
		body (...)
		{
			// EncodedMessage = PadKey XOR EncodedMessage
			InplaceXor(EncodedMessage, PadKey);

			// This is a convenience function included in Q# that basically
			// creates a new function for us to use. The returned function
			// will look at the bit string and for each bit that's a zero,
			// it will flip the qubit in the input array. Then it will
			// do a controlled X with the entire input array as the control
			// on the target qubit. It's essentially an oracle that checks
			// "does the given qubit array match the given bit string".
			// We can implement this pretty easily but why bother? The QDK
			// does it for us.
			let matchChecker = ControlledOnBitString(DesiredResult, X);

			// Check to see if the XOR'd result matches the desired state
			matchChecker(PadKey, IsSuccess);

			// Undo the in-place XOR to get the candidate pad back
			Adjoint InplaceXor(EncodedMessage, PadKey);
		}

		adjoint invert;
	}

	/// # Summary
	/// This oracle always "returns" zero, so it never flips the target qubit.
	/// 
	/// # Input
	/// ## Register
	/// The input register to evaluate
	/// 
	/// ## Target
	/// The target (result) qubit to flip
	operation AlwaysZero(Register : Qubit[], Target : Qubit) : Unit
	{
		body (...)
		{
			// This literally does nothing, no matter what the input is.
		}

		adjoint self;
	}

	/// # Summary
	/// This oracle always "returns" one, so it always flips the target qubit.
	/// 
	/// # Input
	/// ## Register
	/// The input register to evaluate
	/// 
	/// ## Target
	/// The target (result) qubit to flip
	operation AlwaysOne(Register : Qubit[], Target : Qubit) : Unit
	{
		body (...)
		{
			// All this does is flip the target. The input is useless here.
			X(Target);
		}

		adjoint self;
	}
	
	/// # Summary
	/// This oracle checks to see if there are an odd number of |1> qubits in the
	/// input. It will flip the target qubit if there are, or leave it alone if
	/// there are an even number of |1> qubits.
	/// 
	/// # Input
	/// ## Register
	/// The input register to evaluate
	/// 
	/// ## Target
	/// The target (result) qubit to flip
	operation CheckForOddNumberOfOnes(Register : Qubit[], Target : Qubit) : Unit
	{
		body (...)
		{
			// If there are an odd number of |1> qubits, we want the target to get
			// flipped. If there are an even number, we want to leave it alone.
			// Consider a simple two-qubit register. Here is the desired result
			// in table form (where the first two terms are the input register and
			// the third term is the target qubit):
			// 000  =>  000
			// 010  =>  011
			// 100  =>  101
			// 110  =>  110
			// This is kind of like XORing across all of the qubits. However, since
			// we know the target qubit is going to start in |0> (or at least, all we
			// care about is flipping it from whatever arbitrary state it could be
			// in), the XOR op basically ends up doing the same thing as CNOT. So to
			// do a bunch of XORs on all of the input qubits, we just have to CNOT
			// the target over and over, using each input qubit as the control.
			// 
			// ApplyToEachA is a helper function that is basically the Q# equivalent
			// of "foreach". Take a look at the MSDN docs for details on it.
			ApplyToEachA( CNOT(_, Target), Register );
		}

		adjoint self;
	}

	/// # Summary
	/// This oracle checks to see if the qubit in the Nth position is |0> or
	/// |1>. "Nth" here means the qubit in the input array at the given index.
	/// If it's |1>, it flips the target qubit.
	/// 
	/// # Input
	/// ## Register
	/// The input register to evaluate
	/// 
	/// ## Index
	/// The 0-based index in the register of the qubit to check
	/// 
	/// ## Target
	/// The target (result) qubit to flip
	operation CheckIfQubitIsOne(Register : Qubit[], Index : Int, Target : Qubit) : Unit
	{
		body (...)
		{
			// Quick sanity check
			if(Index < 0 or Index > Length(Register) - 1)
			{
				fail "Can't check if the qubit is |0> or |1> because the index was out of bounds.";
			}

			// This really is as easy as you think: CNOT the target with the Nth qubit.
			CNOT(Register[Index], Target);
		}

		adjoint self;
	}

}
