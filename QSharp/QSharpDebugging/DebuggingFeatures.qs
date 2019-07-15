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


// This file contains demonstrations of QDK's debugging and diagnostic features.
namespace QSharpDebugging
{
    open Microsoft.Quantum.Preparation;
    open Microsoft.Quantum.Math;
    open Microsoft.Quantum.Arithmetic;
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Diagnostics;
    
    /// # Summary
    /// This function demonstrates how to use QDK to print the state vector of every
    /// step (moment) in a circuit. Note that unlike the other frameworks, QDK explicitly
    /// lets you specify which qubits you want to include in the printout instead of just
    /// printing the whole statevector for the entire circuit. The kets are included
    /// automatically in the statevector printout.
    operation StepByStepCircuitInspection_Test() : Unit
	{
        using (qubits = Qubit[3])
		{
			let bigEndianQubits = LittleEndianAsBigEndian(LittleEndian(qubits));

			H(qubits[0]);
			DumpRegister((), bigEndianQubits!);	// DumpRegister prints things in little-endian
												// notation, which is why we give it the reversed
												// qubit array.
			X(qubits[2]);
			DumpRegister((), bigEndianQubits!);
			CNOT(qubits[0], qubits[1]);
			DumpRegister((), bigEndianQubits!);

			ResetAll(qubits);
        }
    }


	/// # Summary
	/// This shows how to set the initial state of the qubits in a circuit.
	operation SetExplicitInitialState_Test() : Unit
	{
        using (qubits = Qubit[3])
		{
			let initialStatevector = [
				ComplexPolar(0.0, 0.0), ComplexPolar(0.0, 0.0), ComplexPolar(1.0, 0.0), ComplexPolar(0.0, 0.0), 
				ComplexPolar(0.0, 0.0), ComplexPolar(0.0, 0.0), ComplexPolar(0.0, 0.0), ComplexPolar(0.0, 0.0)
			];

			let littleEndianQubits = BigEndianAsLittleEndian(BigEndian(qubits));
			PrepareArbitraryState(initialStatevector, littleEndianQubits); // PrepareArbitraryState expects a LittleEndian
																		   // so if you define the state in big endian terms
																		   // (like I did above) then you have to flip the
																		   // register again.
			DumpRegister((), littleEndianQubits!);

			ResetAll(qubits);
        }
	}

}