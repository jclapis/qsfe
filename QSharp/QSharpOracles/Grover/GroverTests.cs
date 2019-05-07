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

namespace QSharpOracles.Grover
{
    /// <summary>
    /// This class contains some special tests that run Grover's algorithm.
    /// I purposefully designed these tests to demonstrate how a user would
    /// write a hybrid algorithm that does some classical processing and some
    /// quantum processing, since almost every useful algorithm involves both
    /// domains.
    /// </summary>
    public class GroverTests
    {
        /// <summary>
        /// The output logger for showing messages written by 
        /// <see cref="Message"/> calls during quantum operations.
        /// </summary>
        private readonly ITestOutputHelper Logger;

        /// <summary>
        /// A random number generator used to create one-time pads.
        /// </summary>
        private readonly Random Random;

        /// <summary>
        /// Creates a new GroverTests instance.
        /// </summary>
        /// <param name="Logger">The output logger provided by the
        /// test runner implementation</param>
        public GroverTests(ITestOutputHelper Logger)
        {
            this.Logger = Logger;
            Random = new Random();
        }

        /// <summary>
        /// Runs a test of the quantum Grover implementation. This will use
        /// Grover to search for a lost encryption key when given a ciphertext
        /// and a plaintext (i.e. the original message and the encrypted version
        /// of it). The algorithm being used is XOR, which is trivial but an easy
        /// example for this kind of problem. You could just as easily apply this
        /// on a harder problem like SHA256 or AES or something.
        /// </summary>
        /// <param name="OriginalMessage">The original message to encrypt as part
        /// of the test. This should really be a bit string, so every byte should
        /// be 0 or 1.</param>
        [Theory(DisplayName = "Grover's Algorithm")]
        [InlineData(new byte[] {1, 0, 0, 1, 1})]
        [InlineData(new byte[] {0, 1, 0, 1, 0, 0, 1, 0, 1, 1})]
        [InlineData(new byte[] {0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0})]
        public void TestGroverOnXor(byte[] OriginalMessage)
        {
            using (QuantumSimulator simulator = new QuantumSimulator())
            {
                simulator.OnLog += HandleTestLogMessage;
                Stopwatch timer = new Stopwatch();
                
                // Get bit string versions of the original message, the random
                // one-time pad (AKA the encryption key), and the resulting
                // encrypted message.
                bool[] originalBits = GetBitArrayForMessage(OriginalMessage);
                bool[] pad = GetRandomPad(originalBits.Length);
                bool[] message = GetEncodedMessage(originalBits, pad);

                // Get the Q# versions of the bit strings, so we can send them down to
                // the quantum coprocessor.
                QArray<bool> quantumMessage = new QArray<bool>(message);
                QArray<bool> quantumTarget = new QArray<bool>(originalBits);

                // Write some details about the test
                HandleTestLogMessage("Running Grover's Algorithm on the XOR code with a random pad.");
                HandleTestLogMessage($"Target bitstring: {PrintBitString(originalBits)}");
                HandleTestLogMessage($"Encoded message: {PrintBitString(message)}");
                HandleTestLogMessage("");

                // Run the algorithm with √N iterations. Try it a bunch of times just in case
                // it ends up failing on the first few attempts.
                double keySpaceSize = Math.Pow(2, originalBits.Length);
                int groverIterations = (int)Math.Round(Math.Sqrt(keySpaceSize));
                int attempts = 10;
                for (int i = 0; i < attempts; i++)
                {
                    // Run Grover's algorithm once and time it
                    HandleTestLogMessage($"Running {groverIterations} iterations (vs {keySpaceSize} for brute force)...");
                    timer.Restart();
                    IQArray<bool> result = RunGroverSearchOnXOR.Run(
                        simulator, quantumMessage, quantumTarget).Result;
                    timer.Stop();
                    HandleTestLogMessage($"Run finished in {timer.Elapsed.TotalSeconds.ToString("0.###")} seconds.");

                    // Check to see if it found the correct answer
                    if(pad.SequenceEqual(result))
                    {
                        HandleTestLogMessage($"Found the pad! {PrintBitString(result)}");
                        return;
                    }

                    // If it didn't, just try again.
                    HandleTestLogMessage($"Incorrect result returned: {PrintBitString(result)}");
                    HandleTestLogMessage("Trying again...");
                    HandleTestLogMessage("");
                }

                // Fail message if all of the attempts fail (which really shouldn't happen, but is
                // technically possible).
                Assert.True(false, $"Couldn't find the pad after {attempts} attempts.");
            }
        }

        /// <summary>
        /// Converts a bit string to a human-readable form.
        /// </summary>
        /// <param name="BitString">The bit string to print</param>
        /// <returns>A human-readable representation of the bit string.</returns>
        private string PrintBitString(IReadOnlyList<bool> BitString)
        {
            StringBuilder builder = new StringBuilder();
            builder.Append("[ ");
            for(int i = 0; i < BitString.Count; i++)
            {
                builder.Append(BitString[i] ? 1 : 0);
                builder.Append(" ");
            }
            builder.Append("]");
            return builder.ToString();
        }

        /// <summary>
        /// Converts a bit string in byte[] form to the standard bool[]
        /// used by this algorithm.
        /// </summary>
        /// <param name="Message">The bit string representing the
        /// original message to be encrypted during the test</param>
        /// <returns>A bool[] version of the given bit string</returns>
        private bool[] GetBitArrayForMessage(byte[] Message)
        {
            bool[] bitArray = new bool[Message.Length];
            for(int i = 0; i < Message.Length; i++)
            {
                bitArray[i] = (Message[i] == 1);
            }

            return bitArray;
        }

        /// <summary>
        /// Encodes a message with the XOR cipher.
        /// </summary>
        /// <param name="Message">The original message to encode</param>
        /// <param name="Pad">A pad / key to use while encrypting the
        /// original message</param>
        /// <returns>An encrypted string, which represents 
        /// Message XOR Pad.</returns>
        private bool[] GetEncodedMessage(bool[] Message, bool[] Pad)
        {
            bool[] encodedMessage = new bool[Message.Length];
            for(int i = 0; i < encodedMessage.Length; i++)
            {
                encodedMessage[i] = Message[i] ^ Pad[i];
            }

            return encodedMessage;
        }

        /// <summary>
        /// Creates a random pad to use as the encryption key
        /// during a test.
        /// </summary>
        /// <param name="MessageLength">The number of bits in the 
        /// message to encrypt</param>
        /// <returns>A random bit string with the same size as
        /// the message to encrypt.</returns>
        private bool[] GetRandomPad(int MessageLength)
        {
            bool[] pad = new bool[MessageLength];
            for(int i = 0; i < MessageLength; i++)
            {
                int randomBit = Random.Next(0, 2); // Generate a random 0 or 1
                pad[i] = (randomBit == 1);
            }
            return pad;
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
