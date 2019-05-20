# ========================================================================
# Copyright (C) 2019 The MITRE Corporation.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http:#www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================


import unittest
import shor
import math


class ShorTests(unittest.TestCase):
    """
    This class contains the classical portion of Shor's Algorithm,
    and the unit tests to run the whole thing.
    """
    
    
    # ====================
	# == Test Case Code ==
	# ====================


    def run_shor(self, number_to_factor):
        """
        Runs a test of Shor's algorithm to factor the given integer.

        Parameters:
            number_to_factor (int): The number to factor

        Returns:
            A tuple with two factors of the number, or (-1, -1) if it couldn't be factored.

        Remarks:
            This algorithm takes a lot of explanation to understand. I've written up
            all of it in my report, but I've tried to add code comments to explain things
            in the quantum code. For details on what's going on, please check there.
        """

        # The number is supposed to be a composite odd number, so this
        # is just a quick sanity check to weed out even numbers.
        if(number_to_factor % 2 == 0):
            print(f"Number is even so the factors are 2 and {number_to_factor / 2}.")
            return (2, number_to_factor / 2)

        for guess in range(3, number_to_factor):
            # Instead of picking random numbers, I'm just going to go through all of them iteratively.
            print(f"Trying A = {guess}")
            gcd = math.gcd(number_to_factor, guess)
            if gcd != 1:
                print(f"{number_to_factor} and {guess} have a common factor of {gcd} " +
                      "which doesn't help testing the quantum algorithm. Trying again with something harder.")
                continue

            # Get the period of the function A^X mod N, where A is the guess and N is the number to factor -
            # this is the quantum speedup part of the algorithm (even though it's painfully slow on a simulator).
            period = shor.find_period_of_modular_exponentiation(number_to_factor, guess)
            if period == -1:
                continue

            # Now that we have the period, we can use it to factor N. Remember the period equation is 
            # A^P mod N = 1. This can be rewritten as (A^P - 1) mod N = 0, which means that N is a
            # factor of (A^P - 1). Since all of these terms are integers, we can say (A^P - 1) = ZN,
            # where Z is some scaling constant. Since any integer is the product of 2 integers, we
            # can rewrite this as (A^P - 1) = Z_1 * Z_2 * N_1 * N_2, where Z_1 and Z_2 are the factors
            # of Z, and N_1 and N_2 are the factors of N. We want to find N_1 and N_2.
            # 
            # We can reverse FOIL the left-hand side to show that: (A^P - 1) = (A^(P/2) + 1) * (A^(P/2) - 1).
            # Writing the whole thing out:
            # (A^(P/2) + 1) * (A^(P/2) - 1) = Z_1 * Z_2 * N_1 * N_2.
            # 
            # If we're lucky, then (A^(P/2) + 1) will contain N_1 but not N_2, so that we can use GCD
            # to figure out what N_1 is:
            # GCD(N_1 * N_2, C * N_1) = N_1, where C can be anything except N_2. It can be 1, it can be Z_1,
            # it can be Z_2, it can be Z_1 * Z_2... doesn't matter. As long as N_1 is only in (A^(P/2) + 1)
            # and N_2 is only in (A^(P/2) - 1), we can use GCD to get these factors.
            # 
            # If the period is odd, it's no good because we need to find the numbers (A^(P/2) + 1) and
            # (A^(P/2) - 1), and odd numbers can't be divided by 2.
            if period % 2 == 1:
                print("Period was odd so it can't be used, trying a new guess.")
                continue

            # Now the terms that could contain the factors are:
            # 1. A^(P/2) + 1
            # 2. A^(P/2) - 1
            # If N evenly divides either of these terms, then it means one of the terms contains both
            # N_1 and N_2. After the GCD, the resulting factors will just end up being N and 1, which
            # isn't helpful. To check if this is the case, we need to see if either term, mod N, is 0.
            # This would require calculating the entire power term, which would take a lot of space.
            # We can do it more efficiently by calculating
            # (A^(P/2) mod N) == 1 or N-1.
            print("Period was even, checking the validity of the factor terms...")
            factor_term_base = pow(guess, period // 2, number_to_factor)

            if factor_term_base == 1 or factor_term_base == (number_to_factor - 1):
                print(f"{number_to_factor} is a factor of one of the terms so the factors will " +
                      f"just end up being {number_to_factor} and 1... trying a new guess.")
                continue

            # The period works, and neither factoring term is a multiple of N, so we can get N_1 and N_2 from them.
            factor_term_a = factor_term_base + 1
            factor_term_b = factor_term_base - 1
            print(f"Factor terms are valid: modulus values are {factor_term_a} and {factor_term_b}. Finding GCDs...")

            factor_a = math.gcd(number_to_factor, factor_term_a)
            factor_b = math.gcd(number_to_factor, factor_term_b)
            print(f"Found factors {factor_a} and {factor_b}. Verifying they are the correct factors...")

            # Sanity checks to make sure we got the right ones.
            if factor_a < 2 or factor_a > number_to_factor:
                print(f"{factor_a} isn't greater than 2 and less than {number_to_factor} " +
                      "so it failed the sanity test. Either the code is broken, or the quantum subroutine got extremely " +
                      "unlucky and didn't actually find the right period. Trying a new guess...")
                continue

            if factor_b < 2 or factor_b > number_to_factor:
                print(f"{factor_b} isn't greater than 2 and less than {number_to_factor} " +
                      "so it failed the sanity test. Either the code is broken, or the quantum subroutine got extremely " +
                      "unlucky and didn't actually find the right period. Trying a new guess...")
                continue

            if factor_a * factor_b != number_to_factor:
                print(f"{factor_a} * {factor_b} = {factor_a * factor_b} instead of {number_to_factor} " +
                      "so they failed the sanity test. Either the code is broken, or the quantum subroutine got extremely " +
                      "unlucky and didn't actually find the right period. Trying a new guess...")
                continue

            # If all of the tests passed, we actually found the factors and we're good!
            print("Verification passed! Factoring complete.")
            return (factor_a, factor_b)

        print(f"We ran through every possible integer from 2 to {number_to_factor} " +
              "and didn't find any factors... either it's a prime number, or there's a bug in this code.")
        return (-1, -1)
    

    def run_shor_test_on_number(self, number_to_factor, true_factor_a, true_factor_b):
        """
        Tests Shor's algorithm to make sure it returns the expected factors.

        Parameters:
            number_to_factor (int): The number to factor
            true_factor_a (int): One of the number's factors
            true_factor_b (int): The number's other factor
        """

        (factor_a, factor_b) = self.run_shor(number_to_factor)
        if factor_a != true_factor_a and factor_a != true_factor_b:
            self.fail(f"Shor failed to factor {number_to_factor}: factor A was {factor_a} " +
                      f"but expected {true_factor_a} or {true_factor_b}.")
        if factor_b != true_factor_a and factor_b != true_factor_b:
            self.fail(f"Shor failed to factor {number_to_factor}: factor B was {factor_b} " +
                      f"but expected {true_factor_a} or {true_factor_b}.")

        print("Passed!")


    # ================
	# == Unit Tests ==
	# ================


    # -- Factorable Numbers -- #


    def test_shor_12(self):
        """
        Tests Shor's algorithm for integer factorization on the number 12.
        This should immediately reutrn 2 and 6, since 12 is an even number.
        """

        self.run_shor_test_on_number(12, 2, 6)


    def test_shor_15(self):
        """
        Tests Shor's algorithm for integer factorization on the number 15.
        """

        self.run_shor_test_on_number(15, 3, 5)


    def test_shor_21(self):
        """
        Tests Shor's algorithm for integer factorization on the number 21.
        """

        self.run_shor_test_on_number(21, 3, 7)


    def test_shor_35(self):
        """
        Tests Shor's algorithm for integer factorization on the number 35.
        """

        self.run_shor_test_on_number(35, 5, 7)


    # -- Prime Numbers -- #

    def test_shor_7(self):
        """
        Tests Shor's algorithm for integer factorization on the number 7.
        Since 7 is prime, this should fail to find any factors.
        """

        self.run_shor_test_on_number(7, -1, -1)


    def test_shor_11(self):
        """
        Tests Shor's algorithm for integer factorization on the number 11.
        Since 11 is prime, this should fail to find any factors.
        """

        self.run_shor_test_on_number(11, -1, -1)


    def test_shor_17(self):
        """
        Tests Shor's algorithm for integer factorization on the number 17.
        Since 17 is prime, this should fail to find any factors.
        """

        self.run_shor_test_on_number(17, -1, -1)


    
if __name__ == '__main__':
    unittest.main()
