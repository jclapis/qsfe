# Quantum Software Framework Evaluation

This project contains the code written by MITRE during our evaluation of the most prominent quantum computing
software frameworks in 2019. The evaluation is meant to gauge the software engineering experience in using each
framework on a daily basis, to assess their strengths, weaknesses, and applicability to our work program.

#### Evaluation Criteria
Each framework is evaluated and scored according to these criteria:

- **Ease of Use** (learning curve, documentation, language features, control flow, development tooling, debugging support)
- **Maturity and Activity** (community size, frequency of updates, support, standard library functionality)
- **Flexibility and Modularity** (algorithm support, platform independence, compilation process, open source status)
- **Additional Criteria** (compiler and simulator performance, quantum error correction support, hardware tooling support,
  cost of access and training)

#### Selected Frameworks
We selected eight full-stack frameworks for evaluation, based on [the list maintained
by the Quantum Open Source Foundation](https://github.com/qosf/os_quantum_software). The frameworks being evaluated are:

- Microsoft's [Quantum Development Kit (Q#)](https://www.microsoft.com/en-us/quantum/development-kit)
- IBM's [Quantum Information Sciences Kit (Qiskit)](https://qiskit.org/)
- [Cirq](https://github.com/quantumlib/Cirq) (formerly by Google)
- Rigetti's [Pyquil / Forest](https://github.com/rigetticomputing/pyquil)
- D-Wave's [Ocean](https://github.com/dwavesystems/dwave-ocean-sdk)
- [ProjectQ](https://github.com/ProjectQ-Framework/ProjectQ)
- Eclipse's [XACC](https://github.com/eclipse/xacc)
- Xanadu's [Strawberry Fields](https://github.com/xanaduai/strawberryfields)

#### Standard Test Algorithms
Our evaluation approach is to implement a standard set of well-known quantum algorithms and functions in each language,
and score our experience against each of the evaluation criteria as we go. The algorithms we selected are as follows:

- **Fundamentals**
  - Superposition
  - Entanglement
  - [Quantum Telportation](https://en.wikipedia.org/wiki/Quantum_teleportation)
  - [Superdense Coding](https://en.wikipedia.org/wiki/Superdense_coding)
- **Error Correction**
  - The simple [bit-flip error code](https://en.wikipedia.org/wiki/Quantum_error_correction#The_bit_flip_code) (3 qubits)
  - [Shor's ECC](https://arxiv.org/pdf/0905.2794.pdf) (9 qubits)
  - [Steane's ECC](https://www.mitre.org/sites/default/files/publications/syndrome-measurement-strategies-14-1102.pdf) (7 qubits)
- **Oracle Algorithms**
  - [Deutsch-Jozsa](https://en.wikipedia.org/wiki/Deutsch%E2%80%93Jozsa_algorithm)
  - [Grover's Algorithm](https://en.wikipedia.org/wiki/Grover%27s_algorithm)
  - [Simon's Problem](https://en.wikipedia.org/wiki/Simon%27s_problem)
- **Non-Oracle Algorithms**
  - [Quantum Fourier Transform](https://en.wikipedia.org/wiki/Quantum_Fourier_transform)
  - [Shor's Algorithm](https://en.wikipedia.org/wiki/Shor%27s_algorithm)

This repository contains our implementations of these algorithms in each of the quantum software frameworks.


## Installation and Usage
All of our code was built and executed using [Visual Studio 2019](https://visualstudio.microsoft.com/downloads/).
Each framework comes with a Visual Studio solution. There are four projects contained within each solution, corresponding to the
four categories of standard test algorithms. The algorithms have been implemented within these projects, and each project contains
a set of unit tests that ensure the algorithm works for various inputs. Use 
[Visual Studio's built-in Test Explorer](https://docs.microsoft.com/en-us/visualstudio/test/run-unit-tests-with-test-explorer?view=vs-2019)
to run them, or use your own test runner of choice.

Installation instructions vary per framework; each framework's folder contains a README that describes the installation procedure,
or at least how we set up our own machines during our evaluation.




## License

Copyright (C) 2019 The MITRE Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This project contains content developed by The MITRE Corporation.
If this code is used in a deployment or embedded within another project,
it is requested that you send an email to [opensource@mitre.org](mailto:opensource@mitre.org)
in order to let us know where this software is being used.