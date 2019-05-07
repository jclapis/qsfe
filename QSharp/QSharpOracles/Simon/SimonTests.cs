/* ========================================================================
 * Copyright (C) 2019 The MITRE Corporation.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ======================================================================== */

using Microsoft.Quantum.Simulation.Core;
using Microsoft.Quantum.Simulation.Simulators;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using Xunit;
using Xunit.Abstractions;

namespace QSharpOracles.Simon
{
    /// <summary>
    /// This class contains the classical portion of Simon's Algorithm, and
    /// the unit tests to run the whole thing.
    /// </summary>
    /// <remarks>
    /// For a simple explanation of Simon's Algorithm and what the quantum part
    /// does, please see the top comments in the Simon.qs source file.
    /// 
    /// For a really thorough explanation of what's going on here, including the
    /// theory and math behind the code, please see this excellent document by
    /// Michael Loceff:
    /// http://lapastillaroja.net/wp-content/uploads/2016/09/Intro_to_QC_Vol_1_Loceff.pdf
    /// 
    /// The relevant section starts in Chapter 18: Simon's Algorithm for Period Finding.
    /// </remarks>
    public class SimonTests
    {
        /// <summary>
        /// The output logger for showing messages during test execution
        /// </summary>
        private readonly ITestOutputHelper Logger;

        /// <summary>
        /// The simulator to run the quantum functions with
        /// </summary>
        private readonly QuantumSimulator Simulator;

        /// <summary>
        /// Creates a new SimonTests instance.
        /// </summary>
        /// <param name="Logger">The output logger for showing messages
        /// during test execution</param>
        public SimonTests(ITestOutputHelper Logger)
        {
            this.Logger = Logger;
            Simulator = new QuantumSimulator();
        }


        /// <summary>
        /// Runs Simon's algorithm on the "Left Shift by 1" function.
        /// </summary>
        /// <param name="NumberOfBits">The number of qubits to run the
        /// function with</param>
        [Theory(DisplayName = "Simon's Algorithm: Left Shift")]
        [InlineData(3)]
        [InlineData(6)]
        [InlineData(9)]
        public void TestSimonOnLeftShift(int NumberOfBits)
        {
            ICallable function = GetLeftShiftBy1.Run(Simulator).Result;
            bool[] answer = new bool[NumberOfBits];
            answer[0] = true;

            IList<bool> secret = RunTest($"left shift by 1 on {NumberOfBits} bits",
                function, NumberOfBits, 0.99);
            Assert.Equal(answer, secret);
        }


        /// <summary>
        /// Runs Simon's algorithm on the "Right Shift by 1" function.
        /// </summary>
        /// <param name="NumberOfBits">The number of qubits to run the
        /// function with</param>
        [Theory(DisplayName = "Simon's Algorithm: Right Shift")]
        [InlineData(3)]
        [InlineData(6)]
        [InlineData(9)]
        public void TestSimonOnRightShift(int NumberOfBits)
        {
            ICallable function = GetRightShiftBy1.Run(Simulator).Result;
            bool[] answer = new bool[NumberOfBits];
            answer[NumberOfBits - 1] = true;

            IList<bool> secret = RunTest($"right shift by 1 on {NumberOfBits} bits",
                function, NumberOfBits, 0.99);
            Assert.Equal(answer, secret);
        }


        /// <summary>
        /// Runs Simon's algorithm on the example function provided in the Wikipedia article
        /// for Simon's Problem. See https://en.wikipedia.org/wiki/Simon's_problem#Example
        /// for the full table of inputs and outputs.
        /// </summary>
        [Fact]
        public void TestSimonOnWikiExample()
        {
            ICallable function = Simulator.Get<ICallable>(typeof(WikiTestFunction));
            bool[] answer = { true, true, false };

            IList<bool> secret = RunTest($"wiki example", function, 3, 0.99);
            Assert.Equal(answer, secret);
        }


        /// <summary>
        /// Run's Simon's algorithm on the Identity function, CNOT'ing each element in the
        /// input vector with the corresponding index of the output vector.
        /// </summary>
        /// <param name="NumberOfBits">The number of qubits to run the
        /// function with</param>
        [Theory(DisplayName = "Simon's Algorithm: Identity")]
        [InlineData(3)]
        [InlineData(6)]
        [InlineData(9)]
        public void TestSimonOnIdentity(int NumberOfBits)
        {
            ICallable function = Simulator.Get<ICallable>(typeof(Identity));
            bool[] answer = new bool[NumberOfBits];

            IList<bool> secret = RunTest($"identity with {NumberOfBits} bits",
                function, NumberOfBits, 0.99);
            Assert.Equal(answer, secret);
        }


        /// <summary>
        /// Runs Simon's Algorithm on the provided function, finding the secret bit string
        /// that it contains.
        /// </summary>
        /// <param name="Description">A human-readable description of this test</param>
        /// <param name="FunctionToTest">The type of the class representing the Q# function to
        /// evaluate using the algorithm</param>
        /// <param name="InputSize">The number of bits that the function expects for its
        /// input and output</param>
        /// <param name="DesiredSuccessChance">A number representing what chance you want the
        /// algorithm to have of solving the problem. A higher chance means potentially 
        /// more iterations. This must be at least 0.5, and less than 1.0.</param>
        /// <returns>
        /// The secret string S for the provided function.
        /// </returns>
        private bool[] RunTest(
            string Description, 
            ICallable FunctionToTest,
            int InputSize, 
            double DesiredSuccessChance)
        {
            if (DesiredSuccessChance <= 0.5 ||
                DesiredSuccessChance >= 1)
            {
                Assert.True(false, $"{nameof(DesiredSuccessChance)} must be at least " +
                    $"0.5 and less than 1.");
            }
            
            // The chance of failure is 1 / 2^T, where T is the number of extra
            // rounds to run. This just gets that value based on the desired chance
            // of success.
            double t = Math.Log(1.0 / (1 - DesiredSuccessChance), 2);
            int extraRounds = (int)Math.Ceiling(t); // Round up

            // This set will contain the input bit strings returned by the quantum
            // step of the algorithm.
            List<IList<bool>> validInputs = new List<IList<bool>>();

            HandleTestLogMessage($"Running Simon's algorithm on test [{Description}] " +
                $"with up to {InputSize + extraRounds} iterations.");

            bool foundEnoughStrings = false;
            for (int i = 0; i < InputSize + extraRounds; i++)
            {
                // Get a new candidate input string from the quantum part of the algorithm
                IReadOnlyList<bool> inputString = SimonQuantumStep.Run(Simulator, FunctionToTest, InputSize).Result;
                string message = $"Found input {PrintBitString(inputString)}... ";

                // If it's linearly independent with the strings found so far, add it to the list
                bool wasValid = MatrixMath.CheckLinearIndependence(inputString, validInputs);
                if (wasValid)
                {
                    message += "valid, added it to the collection.";
                }
                else
                {
                    message += "not linearly independent, ignoring it.";
                }
                HandleTestLogMessage(message);

                // If we have enough strings, we're done.
                if (validInputs.Count == InputSize - 1)
                {
                    foundEnoughStrings = true;
                    break;
                }
            }

            if (!foundEnoughStrings)
            {
                Assert.True(false, $"Didn't find enough independent inputs. Found {validInputs.Count}, but " +
                    $"this problem required {InputSize - 1}. Try again, or use a higher success chance.");
            }

            // Add one more linearly-independent string to the list so we have N total equations,
            // and get the right-hand-side vector that represents the solution to each equation.
            IList<bool> rightHandSide = MatrixMath.CompleteMatrix(validInputs);

            // Now we have enough strings to figure out what the secret is!
            IList<bool> secretString = MatrixMath.SolveMatrix(validInputs, rightHandSide);
            HandleTestLogMessage($"Matrix solved, secret = {PrintBitString(secretString)}");

            // If this secret is correct, then f(0) should equal f(S). Run them both and compare them to
            // verify the input. If the output values differ, then that means this function isn't 2-to-1
            // and thus S = 0.
            bool[] zeros = new bool[InputSize];
            QArray<bool> zeroInput = new QArray<bool>(zeros);
            QArray<bool> secretInput = new QArray<bool>(secretString);
            IReadOnlyList<bool> zeroOutput = RunFunctionInClassicalMode.Run(Simulator, FunctionToTest, zeroInput).Result;
            IReadOnlyList<bool> secretOutput = RunFunctionInClassicalMode.Run(Simulator, FunctionToTest, secretInput).Result;

            if(zeroOutput.SequenceEqual(secretOutput))
            {
                return secretString.ToArray();
            }
            else
            {
                HandleTestLogMessage("Secret string doesn't provide the same output as all zeros, so this function " +
                    "isn't actually 2-to-1. Secret must be all zeros.");
                return zeros;
            }
        }


        /// <summary>
        /// Converts a bit string to a human-readable form.
        /// </summary>
        /// <param name="BitString">The bit string to print</param>
        /// <returns>A human-readable representation of the bit string.</returns>
        private string PrintBitString(IEnumerable<bool> BitString)
        {
            StringBuilder builder = new StringBuilder();
            builder.Append("[ ");
            foreach(bool bit in BitString)
            {
                builder.Append(bit ? 1 : 0);
                builder.Append(" ");
            }
            builder.Append("]");
            return builder.ToString();
        }


        /// <summary>
        /// Displays log messages to the test runner output logger,
        /// and to the Visual Studio output console.
        /// </summary>
        /// <param name="Message">The log message to write</param>
        private void HandleTestLogMessage(string Message)
        {
            Logger.WriteLine(Message);
            Debug.WriteLine(Message);
        }

    }
}
