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


# This file contains the implementation for the quantum part of Shor's algorithm.
# This is the world-famous algorithm developed by Peter Shor way back in 1994
# that breaks asymmetric cryptography and is one of the main drivers behind
# quantum computing. Essentially, it figures out the prime factors of numbers in
# something like O(log(N)^2) instead of O(e^2N) which is a massive speedup. Like
# Simon's Problem, this one is a hybrid algorithm that has a quantum part and a
# classical part.


import cirq
import qft
import shor_math
import math


def find_continued_fraction_convergent(numerator, denominator, denominator_threshold):
    """
    Takes in a fraction and expands it into its continued fraction form,
	finding the convergent value with the largest denominator that doesn't
	exceed the provided threshold.

    Parameters:
        numerator (int): The numerator of the input fraction
        denominator (int): The denominator of the input fraction
        denominator_threshold (int): The largest possible value that a covergent's denominator
            is allowed to have in order to be considered a valid result

    Returns:
        The minified (irreducible) fraction representing the largest convergent
	    of the input fraction's continued form that doesn't exceed the given
	    threshold. It is returned as a (numerator, denominator) tuple.
    """

    # Some background on what this step of the algorithm does:
	# Any rational number can be represented by the fraction P/Q, where
	# P and Q are integers. This can also be represented as what's called
	# a continued fraction, which is a number of the form
	# a_0 + 1/(a_1 + 1/(a_2 + 1/(a_3 + ...))).
	# The terms a_i here are called the coefficients.
	# Calculating the convergents is easy with an iterative process:
	# set P_0 = P, Q_0 = Q
	# a_i = P_i / Q_i;		<== Coefficient
	# r_i = P_i % Q_i;		<== Remainder
	# P_i+1 = Q_i;
	# Q_i+1 = r_i;
	# When r_i == 0, this is the last term in the continued fraction.
	# 
	# Continued fractions have things called convergents, which are
	# versions of the fraction but only with i coefficients. Essentially they
	# are closed and closer approximations to the full continued fraction.
	# So if we call
	# v_0 the first convergent, they look like this:
	# v_0 = a_0
	# v_1 = a_0 + 1/a_1
	# v_2 = a_0 + 1/(a_1 + 1/a_2)
	# v_3 = a_0 + 1/(a_1 + 1/(a_2 + 1/a_3)) ...
	# For any convergent, the numerator and denominator will both be integers.
	# The math works out so that for the i-th convergent, you can easily
	# calculate the numerator (n_i) and the denominator (d_i):
	# n_i = a_i * n_(i-1) + n_(i-2)
	# d_i = a_i * d_(i-1) + d_(i-2)
	# 
	# Shor's algorithm finds the convergent of the fraction |X>' / N, where
	# |X>' is the result of the quantum measurement and N = the total
	# number of possible states in the X register, with the largest
	# denominator less than B (the original number being factored).

    coefficient = 0                                     # a_i
    coefficient_calculation_numerator = numerator       # P_i
    coefficient_calculation_denominator = denominator   # Q_i
    coefficient_calculation_remainder = 0               # r_i

    convergent_numerator = 0                            # n_i
    convergent_numerator_1_before = 1                   # n_(i-1)
    convergent_numerator_2_before = 0                   # n_(i-2)

    convergent_denominator = 0                          # d_i
    convergent_denominator_1_before = 0                 # d_(i-1)
    convergent_denominator_2_before = 1                 # d_(i-2)

    while True:
        coefficient = coefficient_calculation_numerator // coefficient_calculation_denominator
        convergent_numerator = coefficient * convergent_numerator_1_before + convergent_numerator_2_before
        convergent_denominator = coefficient * convergent_denominator_1_before + convergent_denominator_2_before

        # We need to calculate this here to check if this was the final term
        coefficient_calculation_remainder = coefficient_calculation_numerator % coefficient_calculation_denominator

        if convergent_denominator > denominator_threshold or coefficient_calculation_remainder == 0:
            if convergent_denominator > denominator_threshold:
                # If the threshold got hit during this iteration, return the previous terms
                convergent_numerator = convergent_numerator_1_before
                convergent_denominator = convergent_denominator_1_before
            return (convergent_numerator, convergent_denominator)
        else:
            # Calculate the terms that will be used for the next round
            coefficient_calculation_numerator = coefficient_calculation_denominator
            coefficient_calculation_denominator = coefficient_calculation_remainder
            convergent_numerator_2_before = convergent_numerator_1_before
            convergent_numerator_1_before = convergent_numerator
            convergent_denominator_2_before = convergent_denominator_1_before
            convergent_denominator_1_before = convergent_denominator


def modular_exponentiation(circuit, input, output, a, b):
    """
    Calculates the modular exponentiation value |O> = A^|X> mod B. The input register
	should contain the exponent and the output register will contain the result of
	the function. If |X> is in a superposition, it and |O> will be entangled so that
	whatever state |X> is measured to be, |O> will always be the solution to the function.

    Parameters:
        input (list[Qid]): The register representing X, the exponent of the power term.
            This can be in any superposition you want, so you can calculate the value for
            multiple inputs simultaneously.
        output (list[Qid]): The register representing O, which will contain the
            solution to the function.
        a (int): The base of the power term
        b (int): The modulus
    """

    circuit.append(cirq.X(output[len(output) - 1]))  # Output = |0...01>

    # Essentially, this works by converting modular exponentiation into a bunch of modular
	# multiplications. It will take n multiplications (where n is the length of the input
	# register). If the input is a uniform superposition, then it will contain 2^n possible states,
	# all of which will be calculated at the same time by this function. Thus, this offers an
	# exponential quantum speedup over classical computation.
	# 
	# The reason this works is kind of mathy, and it's not hard to explain but it does require a lot
	# of math notation which is really hard to write in code comments. Nevertheless, here goes...
	# 
	# Basically you can represent any number in binary, where each digit is a power of 2.
	# Take 13 for example. 13 in big-endian binary is 1101, which = 1*2^3 + 1*2^2 + 0*2^1 + 1*2^0.
	# Since you're a developer reading this code, I'm going to assume you understand how binary works.
	# So the expression A^X mod B can be rewritten by expanding X into its binary form:
	# A^X mod B = ( (A^X_0*2^n-1 mod B) * (A^X_1*2^n-2 mod B) * ... * (A^X_n-1*2^0 mod B) ) mod B.
	# When X_i == 0, the term is ignored. When X_i == 1, the term becomes A^2^(n-i-1) mod B.
	# Essentially that means we can do a modular multiplication for each term, and just use the bits of X
	# as controls for it. A^2^(n-i-1) is easy for a classical computer to calculate, so basically this
	# implements quantum modular exponentiation by turning it into a bunch of quantum modular
	# multiplications and classical modular exponentiations. Since it only does n iterations of either one,
	# but can run on 2^n states simultaneously, this is a big win. 
	# 
	# This would normally be a fine way to calculate things if you had an input and output register,
	# but the Q# version of modular multiplication runs in-place which means it only has one register for
	# the input and output.
	# (Note: since Cirq doesn't come with one of these functions, I ported Q#'s code over to Cirq so I
	# can actually implement Shor's algorihtm).
	# This means we have to redo the equation a little bit which involves way too many parentheses to write
	# here, but the end result is the same: repeat the calculation |O> = |O> * c mod B for each qubit in
	# the input register, where X_i controls the multiplication and c = A^(2^(n-i-1)) mod B.

    input_size = len(input)
    for i in range(0, input_size):
        power_of_two = input_size - 1 - i       # n-i-1
        power_of_guess = 2 ** power_of_two      # 2^(n-i-1)
        constant = pow(a, power_of_guess, b)    # c = A^(2^(n-i-1)) mod B
        shor_math.controlled_modular_multiply(circuit, input[i], constant, b, output)   # |O> = |O> * c mod B


def shor_quantum_subroutine(guess, number_to_factor):
    """
    Runs the quantum subroutine of Shor's algorithm. This will find a value called X', where
	X' is the nearest integer for any value of N * i / P where N = 2^(2b), b = the number of
	bits needed to represent NumberToFactor as a binary integer, i is any integer 0 <= i < P,
	and P is the period of the modular exponentiation function:
	Y = Guess^X mod NumberToFactor. Wow. A better name for this function might be
	"Get_Approximate_Multiple_Of_Reciprocal_Of_Modular_Exponentiation_Period", but that would
	just be pushing it.

    Parameters:
        guess (int): The random number that was guessed as a factor of number_to_factor. This
            will be used as the base of the power term in the modular exponentiation function.
        number_to_factor (int): The number being factored by the algorithm. This will be used
            as the modulus in the modular exponentiation function.

    Returns:
        A tuple of ints where the first term is the nearest integer value for X', and the second
	    term is N.
    """

    # Number of bits needed to represent number_to_factor
    output_size = math.ceil(math.log(number_to_factor + 1, 2))
    input_size = output_size * 2

    # Construct the circuit and registers
    input = cirq.NamedQubit.range(input_size, prefix="input")
    output = cirq.NamedQubit.range(output_size, prefix="output")
    circuit = cirq.Circuit()

    circuit.append(cirq.H.on_each(*input))    # Input = |+...+>, so all possible states at once

    # Run the quantum modular exponentiation function,
	# |output> = guess ^ |input> mod number_to_factor.
	# This will entangle input and output so that for each state of input,
	# output will correspond to the solution to the equation.
    modular_exponentiation(circuit, input, output, guess, number_to_factor)

    # Since guess and number_to_factor are coprime, the modular exponentiation function
	# with them is going to be periodic. By encoding all possible input and output
	# values into these two entangled registers, we can use QFT to measure the period...
	# sort of. I'll explain below.
    qft.iqft(circuit, input)

	# Ok, so really what we'll end up measuring is an approximation of a fraction that
	# has the period P on the denominator, and N * i on the numerator (where N = the number
	# of states in the input register, so 2^Length(input) and i is an integer where
	# 0 <= i < P).
	#
	# That's not going to make a lot of sense, so let me give you an example. Say the
	# number we want to factor is 21 and our guess is 11. 21 takes 5 bits to represent in
	# binary, so length(output) = 5 and length(input) = 10. Input has 2^10 = 1024 possible
	# states in it, so N = 1024. QFT will modify the input so all of the output values
	# will basically have zero probability except for P values, where P is the period
	# (in this case, 6). These values will be N * 0 / P, N * 1 / P ... N * (P-1) / P.
	# For the example, with 11^X mod 21, QFT will modify the states so these 6 have very
	# high probabilities:
	# 1024 * 0 / 6 = 0
	# 1024 * 1 / 6 = 170.666...
	# 1024 * 2 / 6 = 341.333...
	# 1024 * 3 / 6 = 512
	# 1024 * 4 / 6 = 682.666...
	# 1024 * 5 / 6 = 853.333...
	# 
	# The reason for this is way too hard to explain in code comments - you're going to
	# have to read some papers to understand why it does this. All you need to know is this
	# is what's going to happen. Anyway, since we're dealing with binary integers here, we
	# can't get these exact values. So when we measure X, it's going to be the closest integer
	# approximation of one of these 6 values. Thus the 6 possibilities we can measure for
	# this example are 0, 171, 341, 512, 683, and 853. I'll explain what to do with this value
	# in the next step.

    # Measure the result from QFT
    circuit.append(cirq.measure(*input, key="result"))

    # Run the circuit
    simulator = cirq.Simulator()
    result = simulator.run(circuit, repetitions=1)
    result_states = result.histogram(key="result")
    for(state, count) in result_states.items():
        return (state, 2 ** (input_size))
    
    
def find_period_of_modular_exponentiation(number_to_factor, guess):
    """
    Uses Shor's quantum subroutine to find the period, P, for the function
	f(x) = (Guess ^ x) mod NumberToFactor. This takes care of the quantum portion and the
	classical portion of getting the period.

    Parameters:
        number_to_factor (int): The number that the algorithm is trying to factor
        guess (int): The random guess for the factor of the number

    Returns:
        The best guess at the period for the modular exponentiation function. This has a very
	    high chance of being correct, but it's not 100%, so you still have to verify that it
	    produces the correct results when used for factoring.
    """

    period = 1
    remainder = 0
    number_of_zero_measurements = 0

    # When A and B are coprime (one isn't a factor of the other, and they don't have any common factors
	# other than 1), the modular exponentiation function will be periodic. For example, consider when
	# A = 11 and B = 21:
	# -----------------
	#  x | 11^x mod 21
	# -----------------
	#  0 | 1
	#  1 | 11
	#  2 | 16
	#  3 | 8
	#  4 | 4
	#  5 | 2
	#  6 | 1	<== Pattern repeats here, after 6 entries
	#  7 | 11
	#  8 | 16
	#  ...
	# 
	# The "period" of the function refers the the number of terms in the cycle. For thie example, it's 6.
	# Formally, the period is defined as the smallest number of x where A^x mod B == 1, when x > 0. Since
	# 0 indicates the first entry in the cycle and A^0 is always 1, A^P mod X == 1 means that P is the
	# start of a new cycle, thus there are P terms in the cycle. So for this algorithm, we want to find the
	# smallest number X where Guess^X mod P == 1.

    while remainder != 1:
        # Run the quantum subroutine to get a value, X', which is best described if you read the comments for
        # the ShorQuantumSubroutine function.
        (approximate_multiple_of_period_reciprocal, number_of_states) = shor_quantum_subroutine(guess, number_to_factor)
        
        # Once we have this approximate number, we have to figure out what number it was trying to approximate.
        # The fraction X' / N is approximately equal to i / P, where i is some number between 0 and P, and P is
        # the period we're looking for. So what we really want to find is the numerator i and the denominator P
        # of the value that X' is approximating. (Technically we just want P and can ignore i). We can actually
        # get this by doing what's called "finding the convergent of a continued fraction", and that whole
        # thing is described in the FindContinuedFractionConvergent code comments.

        # If the approximation gives us a 0 in the numerator, we can't find a convergent because the whole number
        # X' / N will be 0 no matter what.
        if approximate_multiple_of_period_reciprocal == 0:
            print("The quantum subroutine measured |0> so we got unlucky and can't use it, need to try again.")
            number_of_zero_measurements += 1
            if number_of_zero_measurements == 3:
                print("That's three strikes, this guess is not performing well. The period must be really small. " +
                      "Breaking out so we can try another guess, hopefully get better luck with a bigger period.")
                return -1

        else:
            print("Quantum subroutine gave the approximate fraction " + 
					f"{approximate_multiple_of_period_reciprocal} / {number_of_states}")

            # Okay, now we can find the convergent of X' / N to figure out what i / P originally was. If we're
			# lucky, i and P don't have any common factors so the fraction won't be reduced. If we're unlucky,
			# this will be reduced. For example, if P = 6, i could have 6 possibilities: 0, 1, 2, 3, 4, and 5.
			# If the quantum measurement resulted in i = 1, then the convergent would be 1/6 and we'd have the
			# period P. If i = 3, i / P = 3/6 which reduces to 1/2, so the convergent would be 1/2. This isn't
			# the end of the world, it just means that we have a factor of P instead of P itself.
			# 
			# To fix this, we can just run the whole iteration again to get a new value of X', which will
			# hopefully have a different value of i, and thus hopefully find a convergent with a different 
			# denominator. We can then use the original denominator an this new denominator to find a larger
			# factor of P. We can keep doing this over and over until we have found enough factors that we
			# end up getting P itself.

            (useless_numerator, factor_of_period) = find_continued_fraction_convergent(
                approximate_multiple_of_period_reciprocal, number_of_states, number_to_factor)
            print(f"Closest convergent: {useless_numerator} / {factor_of_period}")

            # Grow the period factor by incorporating the newly found factor into it
            period = factor_of_period * period // math.gcd(factor_of_period, period)
            remainder = pow(guess, period, number_to_factor)
            print(f"Current factor: {period}")

            if remainder != 1:
                print(f"{guess}^{period} mod {number_to_factor} = {remainder}, " + 
				f"so {period} is still just a factor of the period. Finding another factor to incorporate " +
				"into this one...")

    # Once Guess^X mod NumberToFactor == 1, we found the period!
    print(f"Got it! The period of {guess}^x mod {number_to_factor} is {period}.")
    return period