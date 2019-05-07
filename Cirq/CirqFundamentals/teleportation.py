# ========================================================================
# Copyright (C) 2019 The MITRE Corporation.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================


# This module is supposed to test the quantum teleportation protocol, which
# transforms one "target" qubit into the state of another "source" qubit (which
# gets destroyed in the process). The protocol requires what's called "feed-
# forward" processing, meaning some of the qubits are measured in the middle
# of the circuit and the rest of the circuit changes depending on their 
# measurements. In more general terms, it requires the ability to change a
# quantum circuit based on classical information.
# 
# Cirq doesn't support this capability yet, as described in this issue on their
# repository:
# https://github.com/quantumlib/Cirq/issues/762
# Basically the maintainers are developing Cirq in a tight coupling with the
# Google quantum hardware, and since it can't support feed forward operations,
# Cirq doesn't have support for it either.