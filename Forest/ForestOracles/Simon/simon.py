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


# This file contains the implementation and test oracles for Simon's Problem.
# This is a very math-heavy problem that requires a lot of work to prove
# properly, but here's the best basic explanation I can come up with:
# 
# Let's say you have a function F that takes in a bit string (an array of
# 0s and 1s), of size N. It produces an output of size N too. So if you give it
# a 3-bit string, it will give you back a 3-bit string.
# 
# In this function, every possible output has exactly two inputs that produce it
# (call them A and B). So F(A) = F(B), and A != B. No other input produces that
# specific output; just A and B. There is a pair like this for every single output
# value. F is what is called a "two-to-one" function in this case, because every
# output has a pair of inputs that produce it.
# 
# Now, what makes this function special is that it has a secret bit string inside
# it, also of size N. Let's call it "S" for "secret". If A and B are a pair that
# produce the same output, then A ⊕ B = S (where ⊕ means XOR). Doesn't matter which
# pair it is, doesn't matter which output it is. Any pair A and B will give you S
# when XOR'd. this also means A ⊕ S = B, and B ⊕ S = A.
#
# That's a lot of abstract nonsense, so here are two examples to help visualize
# what this is talking about.
#
# Here are two functions that match the description above, where N = 3:
# Input | Output				Input | Output
# --------------				--------------
#  000	|  000					 000  |  101
#  001  |  000					 001  |  010
#  010  |  001					 010  |  000
#  011  |  001					 011  |  110
#  100  |  010					 100  |  000
#  101  |  010					 101  |  110
#  110  |  011					 110  |  101
#  111  |  011					 111  |  010
# 
# In the first function, S = 001. You can check this yourself; take any two
# inputs that produce the same output (like 100 and 101), and check that one
# XOR'd with 001 produces the other. 100 ⊕ 001 = 101, etc. This works for any
# pair of inputs that have the same output.
# The same is true of the second function, where S = 110. For example,
# the inputs 010 and 100 both produce the output 000. 010 ⊕ 110 = 100.
#
# (There's a special case if S = 000 where things get weird, but that just means
# the function is one-to-one instead of two-to-one and will be explained later.)
# 
# Now, normally, you have to do something like (2^N)/2 queries to find a pair
# that produced the same output so you could XOR them together and get S.
# Thus the problem on a classical computer is O(2^N). Simon's Algorithm is
# a way to do it with a quantum computer that is more like O(N) or O(N^2)
# depending on how you end up implementing it.
# 
# This is one of the first problems to be explored that offers a real, nontrivial
# quantum speedup on problems that would take exponential time on a classical
# computer. At first it was regarded as a "toy" problem like Deutsch-Jozsa, but
# lately it's been finding some real use cases in cryptography so it's worth
# learning.
# 
# As a final note, this is a hybrid algorithm kind of like Shor's: it does some
# classical preprocessing, runs a quantum component, then does some classical
# postprocessing to get the answer. It isn't exclusively a quantum thing like
# many of these tests.


from pyquil import Program, get_qc
from pyquil.quil import address_qubits
from pyquil.quilatom import QubitPlaceholder
from pyquil.gates import *
import q_math
    

# ==============================
# == Algorithm Implementation ==
# ==============================


def simon_quantum_step(function, input_size):
    """
    Performs the quantum portion of Simon's algorithm, by finding an input
	string X where (X · S) % 2 = 0 (AKA x0*s0 ⊕ x1*s1 ⊕ ... ⊕ xN*sN = 0).

    Parameters:
        function (function): The black-box function to run the algorithm on (the function being
	        evaluated). It should take a Program as its first input, an input list[QubitPlaceholder]
            as its second argument, and an output list[QubitPlaceholder] as its third argument.

        input_size (int): The number of bits that the function expects in its input and output
	        registers.

    Returns:
        A bit string representing the measured result of the function. This bit
	    string is a vector X where (X · S) % 2 = 0. Note that this will be the
	    measured result of the INPUT register after it's been evaluated. The OUTPUT
	    register is thrown away, because it doesn't actually matter to the algorithm
	    at all.

    Remarks:
        A lot of literature out there will say that this returns a string where
	    s · x = 0. This is misleading, because what they really mean is
	    "dot product mod-2" and they don't usually say the "mod-2" part.
	    Basically, this finds an input value that, when dot product'd with S,
	    gives an even number.
    """

    # Construct the program and registers
    input = QubitPlaceholder.register(input_size)
    output = QubitPlaceholder.register(input_size)
    program = Program()

    # Run the function with |+...+> as the input and |0...0> as the output
    for qubit in input:
        program += H(qubit)
    function(program, input, output)
    for qubit in input:
        program += H(qubit)

    # At this point, the input bit string has been transformed
    # from |0...0> into X, where X is some string that is guaranteed
    # to be even when dot product'd with S. The math behind why this
    # is true is way beyond an explanation here - you have to look
    # at the literature to see why this is the case.

    # Measure the resulting input register
    measurement = program.declare("ro", "BIT", input_size)
    for i in range(0, input_size):
        program += MEASURE(input[i], measurement[i])

    # Run the program
    assigned_program = address_qubits(program)
    computer = get_qc(f"{input_size * 2}q-qvm", as_qvm=True)
    executable = computer.compile(assigned_program)
    results = computer.run(executable)

    # Return the measurement as a list[bool] for classical postprocessing
    for result in results:
        measurement = [False] * input_size
        for i in range(0, input_size):
            measurement[i] = (result[i] == 1)
        return measurement


def run_function_in_classical_mode(function, input):
    """
    Runs the given function on the provided input, returning the results.
	The function will not be run on a superposition on the input, the input
	state will directly match what is provided here; thus, this is basically
	just running the function classically.

    Parameters:
        function (function): The black-box function to run the algorithm on (the function being
	        evaluated). It should take a Program as its first input, an input list[QubitPlaceholder]
            as its second argument, and an output list[QubitPlaceholder] as its third argument.

        input (list[bool]): The bit string you want to provide as input to the function

    Returns:
        A bit string representing the measured result of the function.
    """
    
    # Construct the program and registers
    input_size = len(input)
    input_register = QubitPlaceholder.register(input_size)
    output = QubitPlaceholder.register(input_size)
    program = Program()

    # Sets up the input register so it has the requested input state,
	#and runs the function on it.
    for i in range(0, input_size):
        if input[i]:
            program += X(input_register[i])
    function(program, input_register, output)

    measurement = program.declare("ro", "BIT", input_size)
    for i in range(0, input_size):
        program += MEASURE(output[i], measurement[i])

    # Run the program
    assigned_program = address_qubits(program)
    computer = get_qc(f"{input_size * 2}q-qvm", as_qvm=True)
    executable = computer.compile(assigned_program)
    results = computer.run(executable)
    
    # Return the measurement as a list[bool] for classical postprocessing
    for result in results:
        measurement = [False] * input_size
        for i in range(0, input_size):
            measurement[i] = (result[i] == 1)
        return measurement

    
# ====================
# == Test Case Code ==
# ====================


def wiki_test_function(program, input, output):
    """
    This is a reverse-engineered implementation of the example function
	provided on the Wiki article for Simon's problem:
	https://en.wikipedia.org/wiki/Simon's_problem#Example

    Parameters:
        program (Program): The program being constructed
        input (list[QubitPlaceholder]): The register that contains the input.
            This can be in any arbitrary state.
        output (list[QubitPlaceholder]): The register that will hold the function output.
            This must be in the state |0...0>.
    """

    # Prepare the first answer qubit
    program += X(input[0])
    for i in range(0, 3):
        program += CNOT(input[i], output[0])
    program += X(input[0])

    # Prepare the second answer qubit
    program += CNOT(input[2], output[1])

     # Prepare the third answer qubit
    program += X(output[1])
    program += CCNOT(output[0], output[1], output[2])
    program += X(output[1])


def identity(program, input, output):
    """
    This is basically the identity matrix, CNOT'ing each element of the
	input with the corresponding index of the output array.

    Parameters:
        program (Program): The program being constructed
        input (list[QubitPlaceholder]): The register that contains the input.
            This can be in any arbitrary state.
        output (list[QubitPlaceholder]): The register that will hold the function output.
            This must be in the state |0...0>.
    """
    
    for i in range(0, len(input)):
        program += CNOT(input[i], output[i])


def left_shift_by_1(program, input, output):
    """
    Left shifts the input register by 1 bit.

    Parameters:
        program (Program): The program being constructed
        input (list[QubitPlaceholder]): The register that contains the input.
            This can be in any arbitrary state.
        output (list[QubitPlaceholder]): The register that will hold the function output.
            This must be in the state |0...0>.
    """

    q_math.left_shift(program, input, output, 1)


def right_shift_by_1(program, input, output):
    """
    Right shifts the input register by 1 bit.

    Parameters:
        program (Program): The program being constructed
        input (list[QubitPlaceholder]): The register that contains the input.
            This can be in any arbitrary state.
        output (list[QubitPlaceholder]): The register that will hold the function output.
            This must be in the state |0...0>.
    """

    q_math.right_shift(program, input, output, 1)