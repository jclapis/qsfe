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


// This file contains some basic tests to show how Q# deals with qubits in
// superpositions. The premise here is that each of these test cases will
// alter a given array, putting the qubits into individual superpositions.
// The goal of each test is to change the probability that each qubit is
// measured to be |0> - the specific probability depends on the test.
// These tests ensure that Q#'s compiler and simulator behave as expected
// with respect to quantum computation theory.
namespace QSharpFundamentals.Superposition
{
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Convert;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;


	// ==============================
	// == Algorithm Implementation ==
	// ==============================


	/// # Summary
	/// This tests the Identity gate, which does nothing. It's used to test
	/// that qubits are initialized to |0> in Q# and they should always be
	/// measured as |0> with 100% probability.
	/// 
	/// # Input
	/// ## Qubits
	/// The qubits to transform for the test
    operation Identity(Qubits : Qubit[]) : Unit
    {
        ApplyToEach(I, Qubits);
    }
	
	/// # Summary
	/// This inverts each of the qubits, flipping them from |0> to |1>.
	/// If |0> is passed in, |1> should be measured with 100% probability
	/// after this.
	/// 
	/// # Input
	/// ## Qubits
	/// The qubits to transform for the test
    operation Invert(Qubits : Qubit[]) : Unit
    {
		// This runs the Pauli X gate, which acts as a bit flip.
        ApplyToEach(X, Qubits);
    }
	
	/// # Summary
	/// Converts the qubits from |0> into a completely uniform superposition
	/// of all possible states. For example: if |00> is provided, this will
	/// transform it into ( |00> + |01> + |10> + |11> ) / 2, so each state
	/// has the same possibility of being measured. Thus, each qubit should
	/// have a 50% chance of being measured as |0> independently.
	/// 
	/// # Input
	/// ## Qubits
	/// The qubits to transform for the test
	operation UniformSuperposition(Qubits : Qubit[]) : Unit
	{
		// This uses the Hadamard gate, which turns |0> into an equal
		// superposition of |0> and |1>:
		// H(0) = (|0> + |1>) / √2
		ApplyToEach(H, Qubits);
	}
	
	/// # Summary
	/// This will perform an even rotation around the Y axis for each
	/// qubit. The first will be set to |1> (so a 0% chance of being
	/// measured as |0>), the final one should become |0> with 100% chance,
	/// and every qubit in between will be spaced out at regular,
	/// discrete intervals. For example: if 4 qubits are passed in, the
	/// resulting |0> measurement probabilities for the 4 qubits should be
	/// [0, 1/3, 2/3, 1]. This ensures that Q# can handle arbitrary
	/// superpositions, not just 90 degree rotations around the Bloch
	/// sphere.
	/// 
	/// # Input
	/// ## Qubits
	/// The qubits to transform for the test
	operation EvenRotation(Qubits : Qubit[]) : Unit
	{
		// This is the interval we'll use when changing each qubit's probability
		// of being |0>, AKA the probability assigned to the 2nd qubit. So if
		// we're given 5 qubits (where the first one will have a 0% chance), this
		// will be 1/4.
		let stepInterval = 1.0 / IntAsDouble(Length(Qubits) - 1);

		for(i in 0..Length(Qubits) - 1)
		{
			// This is the desired probability of measuring |0> for this qubit
			let desiredProbability = IntAsDouble(i) * stepInterval;

			// To get that probability, we have to rotate around the Y axis
			// (AKA just moving around on the X and Z plane) by this angle. 
			// The Bloch equation is |q> = cos(θ/2)|0> + e^iΦ*sin(θ/2)|1>,
			// where θ is the angle from the +Z axis on the Z-X plane, and Φ
			// is the angle from the +X axis on the X-Y plane. Since we aren't
			// going to bring imaginary numbers into the picture for this test,
			// we can leave Φ at 0 and ignore it entirely. We just want to rotate
			// along the unit circle defined by the Z-X plane, thus a rotation
			// around the Y axis.
			// 
			// The amplitude of |0> is given by cos(θ/2) as shown above. The
			// probability of measuring |0> is the amplitude squared, so
			// P = cos²(θ/2). So to get the angle, it's:
			// √P = cos(θ/2)
			// cos⁻¹(√P) = θ/2
			// θ = 2cos⁻¹(√P)
			// Then we just rotate the qubit by that angle around the Y axis,
			// and we should be good.
			//
			// See https://en.wikipedia.org/wiki/Bloch_sphere for more info on
			// the Bloch sphere, and how rotations around it affect the qubit's
			// probabilities of measurement.
			let angle = 2.0 * ArcCos(Sqrt(desiredProbability));
			Ry(angle, Qubits[i]);
		}
	}


	// ====================
	// == Test Case Code ==
	// ====================
	

	/// # Summary
	/// This tests the Identity function, leaving the qubits in the |0> state. They
	/// should always be measured at |0> with 100% probability.
	operation Identity_Test() : Unit
	{
		let targetProbabilities = [1.0];
		RunTest(Identity, "Identity", 10000, targetProbabilities, 0.0);
	}
	
	/// # Summary
	/// This tests inversion, flipping the qubits to |1>. They should always be
	/// measured at |1> with 100% probability.
	operation Invert_Test() : Unit
	{
		let targetProbabilities = [0.0, 0.0];
		RunTest(Invert, "Invert", 10000, targetProbabilities, 0.0);
	}
	
	/// # Summary
	/// This tests equal superpositions, giving the qubits an even chance of being |0>
	/// or |1>. Thus they should have a 50% chance of being measured as |0>.
	operation Hadamard_Test() : Unit
	{
		// I arbitrarily tested on an array of 4 qubits, just to make sure they all were
		// truly independent (i.e. not entangled).
		// Since this isn't going to be a perfect 50% but it should trend towards it, I
		// used a small margin of error (0.02) to account for some variance. 
		let targetProbabilities = [0.5, 0.5, 0.5, 0.5];
		RunTest(UniformSuperposition, "UniformSuperposition", 10000, targetProbabilities, 0.02);
	}
	
	/// # Summary
	/// This tests arbitrary rotations around the Y axis to make sure Q# can really deal
	/// with any given superposition.
	operation Rotation_Test() : Unit
	{
		// This test is run a bunch of times on various intervals, ranging from 50% to 1/6
		// (16.667%).
		for(i in 2..6)
		{
			mutable targetProbabilities = new Double[i+1];
			let interval = 1.0 / IntAsDouble(i);
			for(j in 0..i)
			{
				set targetProbabilities w/= j <- IntAsDouble(j) * interval;
			}
			let stepString = DoubleAsStringWithFormat(100.0 / IntAsDouble(i), "0.####");
			RunTest(EvenRotation, $"Rotation with steps of 1/{i} ({stepString}%)",
				2000, targetProbabilities, 0.05);
		}
	}

	/// # Summary
	/// Runs the provided unit test, measuring the results and ensuring that the resulting
	/// state matches the target state.
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
	/// The number of times to run the test before determining the cumulative probability
	/// of each qubit being measured as |0>. With more iterations, each qubit should hopefully
	/// trend towards the target probability.
	/// 
	/// ## TargetProbabilities
	/// The array of probabilities that each qubit in the test should be measured as |0>
	/// once testing is done.
	/// 
	/// ## Margin
	/// The margin-of-error (AKA the tolerance) for the test. For each qubit, the 
	/// measured probability will be allowed to deviate from the target probability by
	/// this much.
	operation RunTest(
		TestFunction : (Qubit[] => Unit), 
		Description : String,
		Iterations : Int, 
		TargetProbabilities : Double[], 
		Margin : Double
	) : Unit
	{
		Message($"Running test: {Description}.");
		let arrayLength = Length(TargetProbabilities);
		mutable zeroCounts = new Int[arrayLength];

		// Run N iterations of the test, counting the cumulative number of times
		// that each qubit was measured as |0>.
		using(qubits = Qubit[arrayLength])
		{
			for(i in 1..Iterations)
			{
				TestFunction(qubits); // Run the test implementation

				for(qubitIndex in 0..arrayLength - 1)
				{
					let result = M(qubits[qubitIndex]); // Measure each qubit and increment the 0 count
					if(result == Zero)
					{
						set zeroCounts w/= qubitIndex <- zeroCounts[qubitIndex] + 1;
					}
					else
					{
						// Reset the qubit to 0 for the next iteration
						X(qubits[qubitIndex]);
					}
				}
			}
		}

		// Get the probabilities of each qubit and compare them to the targets
		let iterationsDouble = IntAsDouble(Iterations);
		mutable targetString = "Target: [ ";
		mutable resultString = "Result: [ ";
		for(i in 0..arrayLength - 1)
		{
			let targetProbability = TargetProbabilities[i];
			set targetString = targetString + DoubleAsStringWithFormat(targetProbability, "N4") + " ";

			let measuredProbability = IntAsDouble(zeroCounts[i]) / iterationsDouble;
			set resultString = resultString + DoubleAsStringWithFormat(measuredProbability, "N4") + " ";

			let discrepancy = AbsD(targetProbability - measuredProbability);
			if(discrepancy > Margin)
			{
				fail $"Test {Description} failed. Qubit {i} had a |0> probability of " +
					$"{measuredProbability}, but it should have been {targetProbability} " +
					$"(with a margin of {Margin}).";
			}
		}

		// If the test passed, print the results.
		set targetString = targetString + "]";
		set resultString = resultString + "]";
		Message(targetString);
		Message(resultString);
		Message("Passed!");
		Message("");
	}

}
