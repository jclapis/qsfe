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


import vs_test_path_fixup
import unittest
import math
import simon
import matrix_math


class SimonTests(unittest.TestCase):
    """
    This class contains the classical portion of Simon's Algorithm, and
    the unit tests to run the whole thing.

    Remarks:
        For a simple explanation of Simon's Algorithm and what the quantum part
        does, please see the top comments in the Simon.qs source file.
        
        For a really thorough explanation of what's going on here, including the
        theory and math behind the code, please see this excellent document by
        Michael Loceff:
        http://lapastillaroja.net/wp-content/uploads/2016/09/Intro_to_QC_Vol_1_Loceff.pdf
        
        The relevant section starts in Chapter 18: Simon's Algorithm for Period Finding.
    """

    def print_bit_string(self, bit_string):
        """
        Converts a bit string to a human-readable form.

        Parameters:
            bit_string (list[bool]): The bit string to print

        Returns:
            A human-readable representation of the bit string.
        """

        string = "[ "
        for bit in bit_string:
            string += ("1 " if bit else "0 ")
        string += ("]")
        return string


    def run_test(self, description, function, input_size, desired_success_chance):
        """
        Runs Simon's Algorithm on the provided function, finding the secret bit string
        that it contains.

        Parameters:
            description (str): A human-readable description of this test
            function (function): The function to run Simon's algorithm on
            input_size (int): The number of bits that the function expects for its
                input and output
            desired_success_chance (float): A number representing what chance you want the
                algorithm to have of solving the problem. A higher chance means potentially
                more iterations. This must be at least 0.5, and less than 1.0.

        Returns:
            The secret string S for the provided function.
        """

        if desired_success_chance <= 0.5 or desired_success_chance >= 1:
            self.fail("Desired success chance must be at least 0.5 and less than 1.")

        # The chance of failure is 1 / 2^T, where T is the number of extra
        # rounds to run. This just gets that value based on the desired chance
        # of success.
        t = math.log(1 / (1 - desired_success_chance), 2)
        extra_rounds = math.ceil(t)

        # This list will contain the input bit strings returned by the quantum
        # step of the algorithm.
        valid_inputs = []

        print(f"Running Simon's algorithm on test [{description}] " +
                f"with up to {input_size + extra_rounds} iterations.")

        found_enough_strings = False
        for i in range(0, input_size + extra_rounds):
            # Get a new candidate input string from the quantum part of the algorithm
            input_string = simon.simon_quantum_step(function, input_size)
            message = f"Found input {self.print_bit_string(input_string)}... "

            # If it's linearly independent with the strings found so far, add it to the list
            was_valid = matrix_math.check_linear_independence(input_string, valid_inputs)
            if was_valid:
                message += "valid, added it to the collection."
            else:
                message += "not linearly independent, ignoring it."

            print(message)

            # If we have enough strings, we're done.
            if len(valid_inputs) == input_size - 1:
                found_enough_strings = True
                break

        if not found_enough_strings:
            self.fail(f"Didn't find enough independent inputs. Found {len(valid_inputs)}, but " +
                    f"this problem required {input_size - 1}. Try again, or use a higher success chance.")

        # Add one more linearly-independent string to the list so we have N total equations,
        # and get the right-hand-side vector that represents the solution to each equation.
        right_hand_side = matrix_math.complete_matrix(valid_inputs)

        # Now we have enough strings to figure out what the secret is!
        secret_string = matrix_math.solve_matrix(valid_inputs, right_hand_side)
        print(f"Matrix solved, secret = {self.print_bit_string(secret_string)}")

        # If this secret is correct, then f(0) should equal f(S). Run them both and compare them to
        # verify the input. If the output values differ, then that means this function isn't 2-to-1
        # and thus S = 0.
        zeros = [False] * input_size
        zero_output = simon.run_function_in_classical_mode(function, zeros)
        secret_output = simon.run_function_in_classical_mode(function, secret_string)

        if zero_output == secret_output:
            return secret_string
        else:
            print("Secret string doesn't provide the same output as all zeros, so this function " +
                    "isn't actually 2-to-1. Secret must be all zeros.")
            return zeros


    def left_shift_test(self, number_of_bits):
        """
        Runs Simon's algorithm on the "Left Shift by 1" function.

        Parameters:
            number_of_bits (int): The number of bits to use for the function's input
                and output registers
        """

        answer = [False] * number_of_bits
        answer[0] = True
        secret = self.run_test(f"left shift by 1 on {number_of_bits} bits", 
                               simon.left_shift_by_1, number_of_bits, 0.99)
        self.assertEqual(answer, secret)


    def right_shift_test(self, number_of_bits):
        """
        Runs Simon's algorithm on the "Right Shift by 1" function.

        Parameters:
            number_of_bits (int): The number of bits to use for the function's input
                and output registers
        """

        answer = [False] * number_of_bits
        answer[-1] = True
        secret = self.run_test(f"right shift by 1 on {number_of_bits} bits", 
                               simon.right_shift_by_1, number_of_bits, 0.99)
        self.assertEqual(answer, secret)


    def identity_test(self, number_of_bits):
        """
        Run's Simon's algorithm on the Identity function, CNOT'ing each element in the
        input vector with the corresponding index of the output vector.

        Parameters:
            number_of_bits (int): The number of bits to use for the function's input
                and output registers
        """

        answer = [False] * number_of_bits
        secret = self.run_test(f"identity with {number_of_bits} bits", 
                               simon.identity, number_of_bits, 0.99)
        self.assertEqual(answer, secret)


    def test_wiki_example(self):
        """
        Runs Simon's algorithm on the example function provided in the Wikipedia article
        for Simon's Problem. See https://en.wikipedia.org/wiki/Simon's_problem#Example
        for the full table of inputs and outputs.
        """

        answer = [True, True, False]
        secret = self.run_test("wiki example", simon.wiki_test_function, 3, 0.99)
        self.assertEqual(answer, secret)


    def test_left_shift_3_bits(self):
        """
        Tests Simon's algorithm on left-shift-by-1 with 3-bit registers.
        """

        self.left_shift_test(3)


    def test_left_shift_6_bits(self):
        """
        Tests Simon's algorithm on left-shift-by-1 with 6-bit registers.
        """

        self.left_shift_test(6)


    def test_left_shift_9_bits(self):
        """
        Tests Simon's algorithm on left-shift-by-1 with 9-bit registers.
        """

        self.left_shift_test(9)


    def test_right_shift_3_bits(self):
        """
        Tests Simon's algorithm on right-shift-by-1 with 3-bit registers.
        """

        self.right_shift_test(3)


    def test_right_shift_6_bits(self):
        """
        Tests Simon's algorithm on right-shift-by-1 with 6-bit registers.
        """

        self.right_shift_test(6)


    def test_right_shift_9_bits(self):
        """
        Tests Simon's algorithm on right-shift-by-1 with 9-bit registers.
        """

        self.right_shift_test(9)


    def test_identity_3_bits(self):
        """
        Tests Simon's algorithm on the identity function with 3-bit registers.
        """

        self.identity_test(3)


    def test_identity_6_bits(self):
        """
        Tests Simon's algorithm on the identity function with 6-bit registers.
        """

        self.identity_test(6)


    def test_identity_9_bits(self):
        """
        Tests Simon's algorithm on the identity function with 9-bit registers.
        """

        self.identity_test(9)



if __name__ == '__main__':
    unittest.main()
