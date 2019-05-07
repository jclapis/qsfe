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

using Microsoft.Quantum.Simulation.Simulators;
using System.Diagnostics;
using System.Numerics;
using Xunit;
using Xunit.Abstractions;

namespace QSharpNonOracles.Shor
{
    /// <summary>
    /// This class contains the classical portion of Shor's Algorithm,
    /// and the unit tests to run the whole thing.
    /// </summary>
    public class ShorTests
    {
        /// <summary>
        /// The output logger for showing messages during test execution
        /// </summary>
        private readonly ITestOutputHelper Logger;


        /// <summary>
        /// Creates a new ShorTests instance.
        /// </summary>
        /// <param name="Logger">The output logger for showing messages
        /// during test execution</param>
        public ShorTests(ITestOutputHelper Logger)
        {
            this.Logger = Logger;
        }


        /// <summary>
        /// Tests Shor's algorithm for integer factorization on a
        /// factorable number.
        /// </summary>
        /// <param name="NumberToFactor">The number to factor</param>
        [Theory(DisplayName = "Shor's Algorithm - Factorable Number")]
        [InlineData(12)]
        [InlineData(15)]
        [InlineData(21)]
        [InlineData(35)]
        public void TestShorOnFactorableNumber(int NumberToFactor)
        {
            HandleTestLogMessage($"Factoring {NumberToFactor}.");
            (int factor1, int factor2) = RunTest(NumberToFactor);
            Assert.Equal(factor1 * factor2, NumberToFactor);
            HandleTestLogMessage("Passed!");
        }


        /// <summary>
        /// Tests Shor's algorithm for integer factorization on a 
        /// prime number, to make sure it can't find any nonexistent
        /// factors.
        /// </summary>
        /// <param name="NumberToFactor">The number to factor</param>
        [Theory(DisplayName = "Shor's Algorithm - Prime Number")]
        [InlineData(7)]
        [InlineData(11)]
        [InlineData(17)]
        public void TestShorOnPrimeNumber(int NumberToFactor)
        {
            HandleTestLogMessage($"Factoring {NumberToFactor}.");
            (int factor1, int factor2) = RunTest(NumberToFactor);
            Assert.Equal(factor1, -1);
            Assert.Equal(factor2, -1);
            HandleTestLogMessage("Passed!");
        }


        /// <summary>
        /// Runs a test of Shor's algorithm to factor the given integer.
        /// </summary>
        /// <param name="NumberToFactor">The number to factor</param>
        /// <returns>A tuple with two factors of the number, or (-1, -1) if it
        /// couldn't be factored.</returns>
        /// <remarks>
        /// This algorithm takes a lot of explanation to understand. I've written up
        /// all of it in my report, but I've tried to add code comments to explain things
        /// in the quantum code. For details on what's going on, please check there.
        /// </remarks>
        public (int, int) RunTest(int NumberToFactor)
        {
            // The number is supposed to be a composite odd number, so this
            // is just a quick sanity check to weed out even numbers.
            if (NumberToFactor % 2 == 0)
            {
                HandleTestLogMessage($"Number is even so the factors are 2 and {NumberToFactor / 2}.");
                return (2, NumberToFactor / 2);
            }

            using (QuantumSimulator simulator = new QuantumSimulator())
            {
                simulator.OnLog += HandleTestLogMessage;
                // Instead of picking random numbers, I'm just going to go through all of them iteratively.
                for (int guess = 3; guess < NumberToFactor; guess++)
                {
                    HandleTestLogMessage($"Trying A = {guess}");
                    int gcd = FindGreatestCommonDenominator(NumberToFactor, guess);
                    if (gcd != 1)
                    {
                        HandleTestLogMessage($"{NumberToFactor} and {guess} have a common factor of {gcd} " +
                            "which doesn't help testing the quantum algorithm. Trying again with something harder.");
                        continue;
                    }

                    // Get the period of the function A^X mod N, where A is the guess and N is the number to factor -
                    // this is the quantum speedup part of the algorithm (even though it's painfully slow on a simulator).
                    int period = (int)FindPeriodOfModularExponentiation.Run(simulator, NumberToFactor, guess).Result;
                    if (period == -1)
                    {
                        continue;
                    }

                    // Now that we have the period, we can use it to factor N. Remember the period equation is 
                    // A^P mod N = 1. This can be rewritten as (A^P - 1) mod N = 0, which means that N is a
                    // factor of (A^P - 1). Since all of these terms are integers, we can say (A^P - 1) = ZN,
                    // where Z is some scaling constant. Since any integer is the product of 2 integers, we
                    // can rewrite this as (A^P - 1) = Z_1 * Z_2 * N_1 * N_2, where Z_1 and Z_2 are the factors
                    // of Z, and N_1 and N_2 are the factors of N. We want to find N_1 and N_2.
                    // 
                    // We can reverse FOIL the left-hand side to show that: (A^P - 1) = (A^(P/2) + 1) * (A^(P/2) - 1).
                    // Writing the whole thing out:
                    // (A^(P/2) + 1) * (A^(P/2) - 1) = Z_1 * Z_2 * N_1 * N_2.
                    // 
                    // If we're lucky, then (A^(P/2) + 1) will contain N_1 but not N_2, so that we can use GCD
                    // to figure out what N_1 is:
                    // GCD(N_1 * N_2, C * N_1) = N_1, where C can be anything except N_2. It can be 1, it can be Z_1,
                    // it can be Z_2, it can be Z_1 * Z_2... doesn't matter. As long as N_1 is only in (A^(P/2) + 1)
                    // and N_2 is only in (A^(P/2) - 1), we can use GCD to get these factors.
                    // 
                    // If the period is odd, it's no good because we need to find the numbers (A^(P/2) + 1) and
                    // (A^(P/2) - 1), and odd numbers can't be divided by 2.
                    if (period % 2 == 1)
                    {
                        HandleTestLogMessage("Period was odd so it can't be used, trying a new guess.");
                        continue;
                    }

                    // Now the terms that could contain the factors are:
                    // 1. A^(P/2) + 1
                    // 2. A^(P/2) - 1
                    // If N evenly divides either of these terms, then it means one of the terms contains both
                    // N_1 and N_2. After the GCD, the resulting factors will just end up being N and 1, which
                    // isn't helpful. To check if this is the case, we need to see if either term, mod N, is 0.
                    // This would require calculating the entire power term, which would take a lot of space.
                    // We can do it more efficiently by calculating
                    // (A^(P/2) mod N) == 1 or N-1.
                    HandleTestLogMessage("Period was even, checking the validity of the factor terms...");
                    int factorTermBase = (int)BigInteger.ModPow(guess, period / 2, NumberToFactor);

                    if (factorTermBase == 1 ||
                        factorTermBase == NumberToFactor - 1)
                    {
                        HandleTestLogMessage($"{NumberToFactor} is a factor of one of the terms so the factors will " +
                            $"just end up being {NumberToFactor} and 1... trying a new guess.");
                        continue;
                    }

                    // The period works, and neither factoring term is a multiple of N, so we can get N_1 and N_2 from them.
                    int factorTermA = factorTermBase + 1;
                    int factorTermB = factorTermBase - 1;
                    HandleTestLogMessage($"Factor terms are valid: modulus values are {factorTermA} and {factorTermB}. Finding GCDs...");

                    int factorA = FindGreatestCommonDenominator(NumberToFactor, factorTermA);
                    int factorB = FindGreatestCommonDenominator(NumberToFactor, factorTermB);
                    HandleTestLogMessage($"Found factors {factorA} and {factorB}. Verifying they are the correct factors...");

                    // Sanity checks to make sure we got the right ones.
                    if (factorA < 2 ||
                        factorA > NumberToFactor)
                    {
                        HandleTestLogMessage($"{factorA} isn't greater than 2 and less than {NumberToFactor} " +
                            "so it failed the sanity test. Either the code is broken, or the quantum subroutine got extremely " +
                            "unlucky and didn't actually find the right period. Trying a new guess...");
                        continue;
                    }
                    if (factorB < 2 ||
                        factorB > NumberToFactor)
                    {
                        HandleTestLogMessage($"{factorB} isn't greater than 2 and less than {NumberToFactor} " +
                            "so it failed the sanity test. Either the code is broken, or the quantum subroutine got extremely " +
                            "unlucky and didn't actually find the right period. Trying a new guess...");
                        continue;
                    }
                    if(factorA * factorB != NumberToFactor)
                    {
                        HandleTestLogMessage($"{factorA} * {factorB} = {factorA * factorB} instead of {NumberToFactor} " +
                            "so they failed the sanity test. Either the code is broken, or the quantum subroutine got extremely " +
                            "unlucky and didn't actually find the right period. Trying a new guess...");
                    }

                    // If all of the tests passed, we actually found the factors and we're good!
                    HandleTestLogMessage("Verification passed! Factoring complete.");
                    return (factorA, factorB);
                }

                HandleTestLogMessage($"We ran through every possible integer from 2 to {NumberToFactor} " +
                    "and didn't find any factors... either it's a prime number, or there's a bug in this code.");
                return (-1, -1);
            }
        }


        /// <summary>
        /// Finds the greatest common denominator (GCD) for two numbers.
        /// This is an implementation of Euclid's algorithm.
        /// </summary>
        /// <param name="A">The first number</param>
        /// <param name="B">The second number</param>
        /// <returns>The GCD of the two numbers.</returns>
        private int FindGreatestCommonDenominator(int A, int B)
        {
            while (B != 0)
            {
                int oldB = B;
                B = A % B;
                A = oldB;
            }

            return A;
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
