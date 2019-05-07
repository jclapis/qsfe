﻿/* ========================================================================
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

using Microsoft.Quantum.Simulation.XUnit;
using Microsoft.Quantum.Simulation.Simulators;
using Xunit.Abstractions;
using System.Diagnostics;

namespace QSharpFundamentals
{
    /// <summary>
    /// This class contains all of the test drivers that run each test in this project.
    /// </summary>
    public class TestSuiteRunner
    {
        /// <summary>
        /// The output logger for showing messages written by 
        /// <see cref="Message"/> calls during quantum operations.
        /// </summary>
        private readonly ITestOutputHelper Logger;

        /// <summary>
        /// Creates a new TestSuiteRunner instance.
        /// </summary>
        /// <param name="Logger">The output logger provided by the
        /// test runner implementation</param>
        public TestSuiteRunner(ITestOutputHelper Logger)
        {
            this.Logger = Logger;
        }

        /// <summary>
        /// This driver runs all of the superposition tests.
        /// </summary>
        [OperationDriver(TestNamespace = "QSharpFundamentals.Superposition",
            TestCasePrefix = "Superposition_",
            Suffix = "_Test")]
        public void SuperpositionTests(TestOperation Operation)
        {
            RunTest(Operation);
        }

        /// <summary>
        /// This driver runs all of the entanglement tests.
        /// </summary>
        [OperationDriver(TestNamespace = "QSharpFundamentals.Entanglement",
            TestCasePrefix = "Entanglement_",
            Suffix = "_Test")]
        public void EntanglementTests(TestOperation Operation)
        {
            RunTest(Operation);
        }

        /// <summary>
        /// This driver runs all of the teleportation tests.
        /// </summary>
        [OperationDriver(TestNamespace = "QSharpFundamentals.Teleportation",
            TestCasePrefix = "Teleportation_",
            Suffix = "_Test")]
        public void TeleportationTests(TestOperation Operation)
        {
            RunTest(Operation);
        }

        /// <summary>
        /// This driver runs all of the superdense coding tests.
        /// </summary>
        [OperationDriver(TestNamespace = "QSharpFundamentals.Superdense",
            TestCasePrefix = "Superdensen_",
            Suffix = "_Test")]
        public void SuperdenseTests(TestOperation Operation)
        {
            RunTest(Operation);
        }

        /// <summary>
        /// Executes a quantum test operation.
        /// </summary>
        /// <param name="Operation">The operation to run</param>
        private void RunTest(TestOperation Operation)
        {
            using (QuantumSimulator simulator = new QuantumSimulator())
            {
                simulator.OnLog += HandleTestLogMessage;
                Operation.TestOperationRunner(simulator);
            }
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
